#!/usr/bin/env python
"""
Network Reliability Patch for GPT-Researcher
Fixes critical timeout and connection issues causing research failures

This patch addresses:
1. 4-second timeout errors in web scraping
2. Connection reset by peer errors
3. Content too short or empty responses
4. HTTPSConnectionPool connection management issues
"""

import time

import requests
from requests.adapters import HTTPAdapter

try:
    from requests.packages.urllib3.util.retry import Retry
except ImportError:
    from urllib3.util.retry import Retry

import logging
from functools import wraps
from typing import Optional

logger = logging.getLogger(__name__)


class NetworkReliabilityConfig:
    """Configuration for network reliability improvements"""

    # Timeout settings (increased from 4 seconds)
    REQUEST_TIMEOUT = 30  # Main request timeout
    CONNECT_TIMEOUT = 10  # Connection establishment timeout
    READ_TIMEOUT = 25  # Read response timeout

    # Retry configuration
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 1.5  # Exponential backoff multiplier
    RETRY_STATUS_CODES = [500, 502, 503, 504, 429, 408, 104]

    # Connection pooling
    POOL_CONNECTIONS = 10
    POOL_MAXSIZE = 20

    # Request headers to appear more like a real browser
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }


class SSLConfig:
    """Configuration for SSL certificate handling"""

    # SSL verification settings
    VERIFY_SSL = True  # Set to False to disable SSL verification (not recommended for production)

    # List of domains to skip SSL verification for (use with caution)
    SSL_VERIFICATION_EXCEPTIONS = [
        "www.tayninh.gov.vn",
        "www.nso.gov.vn",
        "www.gso.gov.vn",
        # Add other problematic .gov.vn sites as needed
    ]

    # Custom certificate bundle path (optional)
    CERT_BUNDLE_PATH = None  # Set to path of custom CA bundle if needed


def create_robust_session() -> requests.Session:
    """
    Create a requests session with robust retry logic, connection pooling, and SSL handling
    """
    session = requests.Session()

    # Configure retry strategy
    retry_strategy = Retry(
        total=NetworkReliabilityConfig.MAX_RETRIES,
        read=NetworkReliabilityConfig.MAX_RETRIES,
        connect=NetworkReliabilityConfig.MAX_RETRIES,
        backoff_factor=NetworkReliabilityConfig.BACKOFF_FACTOR,
        status_forcelist=NetworkReliabilityConfig.RETRY_STATUS_CODES,
        allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
    )

    # Create HTTP adapter with retry strategy
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=NetworkReliabilityConfig.POOL_CONNECTIONS,
        pool_maxsize=NetworkReliabilityConfig.POOL_MAXSIZE,
    )

    # Mount the adapter for both HTTP and HTTPS
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set default headers
    session.headers.update(NetworkReliabilityConfig.DEFAULT_HEADERS)

    # Configure SSL verification
    if SSLConfig.CERT_BUNDLE_PATH:
        session.verify = SSLConfig.CERT_BUNDLE_PATH
    elif not SSLConfig.VERIFY_SSL:
        session.verify = False
        # Suppress SSL warnings if verification is disabled
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return session


def robust_get_with_fallback(
    url: str, session: Optional[requests.Session] = None, **kwargs
) -> Optional[requests.Response]:
    """
    Perform a robust GET request with fallback mechanisms and SSL handling

    Args:
        url: URL to fetch
        session: Optional session to use
        **kwargs: Additional arguments for requests.get

    Returns:
        Response object or None if all attempts fail
    """
    if session is None:
        session = create_robust_session()

    # Check if this domain needs special SSL handling
    from urllib.parse import urlparse

    parsed_url = urlparse(url)
    domain = parsed_url.hostname

    # Handle SSL verification exceptions
    original_verify = session.verify
    if domain in SSLConfig.SSL_VERIFICATION_EXCEPTIONS:
        logger.warning(f"Disabling SSL verification for known problematic domain: {domain}")
        session.verify = False
        # Suppress SSL warnings for this specific request
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Set default timeout if not provided
    if "timeout" not in kwargs:
        kwargs["timeout"] = (
            NetworkReliabilityConfig.CONNECT_TIMEOUT,
            NetworkReliabilityConfig.READ_TIMEOUT,
        )

    attempts = 0
    last_error = None

    while attempts < NetworkReliabilityConfig.MAX_RETRIES:
        try:
            response = session.get(url, **kwargs)
            response.raise_for_status()

            # Restore original SSL verification setting
            session.verify = original_verify

            return response

        except requests.exceptions.SSLError as e:
            last_error = e
            logger.warning(f"SSL error for {url}: {e}")

            # On SSL error, retry with verification disabled
            if session.verify:
                logger.info(f"Retrying {url} without SSL verification")
                session.verify = False
                attempts += 1
                continue

        except requests.exceptions.ConnectTimeout as e:
            last_error = e
            logger.warning(f"Connection timeout for {url}: {e}")
            attempts += 1

        except requests.exceptions.ReadTimeout as e:
            last_error = e
            logger.warning(f"Read timeout for {url}: {e}")
            attempts += 1

        except requests.exceptions.ConnectionError as e:
            last_error = e
            logger.warning(f"Connection error for {url}: {e}")
            attempts += 1

        except requests.exceptions.HTTPError as e:
            last_error = e
            if e.response.status_code in NetworkReliabilityConfig.RETRY_STATUS_CODES:
                logger.warning(f"HTTP {e.response.status_code} error for {url}, retrying...")
                attempts += 1
            else:
                logger.error(f"Non-retryable HTTP error for {url}: {e}")
                break

        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error fetching {url}: {e}")
            break

        # Exponential backoff between retries
        if attempts < NetworkReliabilityConfig.MAX_RETRIES:
            wait_time = NetworkReliabilityConfig.BACKOFF_FACTOR**attempts
            logger.debug(f"Waiting {wait_time:.1f}s before retry {attempts + 1}")
            time.sleep(wait_time)

    # Restore original SSL verification setting
    session.verify = original_verify

    logger.error(f"All attempts failed for {url}. Last error: {last_error}")
    return None


def patch_scraper_method(original_method):
    """
    Decorator to patch scraper methods with robust network handling
    """

    @wraps(original_method)
    def patched_method(self, *args, **kwargs):
        # Replace the session.get call with our robust version
        original_get = self.session.get if hasattr(self, "session") else None

        if original_get:

            def robust_get(url, **get_kwargs):
                # Remove the problematic 4-second timeout if present
                get_kwargs.pop("timeout", None)
                return robust_get_with_fallback(url, self.session, **get_kwargs)

            # Temporarily replace the get method
            self.session.get = robust_get

        try:
            result = original_method(self, *args, **kwargs)
            return result
        finally:
            # Restore original method
            if original_get:
                self.session.get = original_get

    return patched_method


def apply_network_reliability_patches():
    """
    Apply network reliability patches to gpt-researcher scrapers
    """
    patches_applied = []

    try:
        # Patch Beautiful Soup scraper
        try:
            from gpt_researcher.scraper.beautiful_soup.beautiful_soup import BeautifulSoupScraper

            original_scrape = BeautifulSoupScraper.scrape
            BeautifulSoupScraper.scrape = patch_scraper_method(original_scrape)
            patches_applied.append("BeautifulSoupScraper.scrape")
            logger.info("✅ Patched BeautifulSoupScraper with network reliability improvements")
        except ImportError as e:
            logger.warning(f"Could not patch BeautifulSoupScraper: {e}")

        # Patch Tavily Extract scraper
        try:
            from gpt_researcher.scraper.tavily_extract.tavily_extract import TavilyExtractScraper

            original_scrape = TavilyExtractScraper.scrape
            TavilyExtractScraper.scrape = patch_scraper_method(original_scrape)
            patches_applied.append("TavilyExtractScraper.scrape")
            logger.info("✅ Patched TavilyExtractScraper with network reliability improvements")
        except ImportError as e:
            logger.warning(f"Could not patch TavilyExtractScraper: {e}")

        # Patch Firecrawl scraper
        try:
            from gpt_researcher.scraper.firecrawl.firecrawl import FirecrawlScraper

            original_scrape = FirecrawlScraper.scrape
            FirecrawlScraper.scrape = patch_scraper_method(original_scrape)
            patches_applied.append("FirecrawlScraper.scrape")
            logger.info("✅ Patched FirecrawlScraper with network reliability improvements")
        except ImportError as e:
            logger.warning(f"Could not patch FirecrawlScraper: {e}")

        # Patch any other scraper classes that might exist
        try:
            import gpt_researcher.scraper

            # Look for other scraper classes dynamically
            for attr_name in dir(gpt_researcher.scraper):
                attr = getattr(gpt_researcher.scraper, attr_name)
                if (
                    hasattr(attr, "__name__")
                    and "Scraper" in attr.__name__
                    and hasattr(attr, "scrape")
                    and attr.__name__
                    not in [
                        cls.__name__
                        for cls in [BeautifulSoupScraper, TavilyExtractScraper, FirecrawlScraper]
                    ]
                ):
                    try:
                        original_scrape = attr.scrape
                        attr.scrape = patch_scraper_method(original_scrape)
                        patches_applied.append(f"{attr.__name__}.scrape")
                        logger.info(
                            f"✅ Patched {attr.__name__} with network reliability improvements"
                        )
                    except Exception as e:
                        logger.warning(f"Could not patch {attr.__name__}: {e}")
        except Exception as e:
            logger.warning(f"Could not dynamically patch scrapers: {e}")

    except Exception as e:
        logger.error(f"Error applying network reliability patches: {e}")

    if patches_applied:
        logger.info(
            f"🚀 Network Reliability Patch Applied Successfully to: {', '.join(patches_applied)}"
        )
        logger.info("🔧 Improvements include:")
        logger.info(
            f"   • Timeout increased from 4s to {NetworkReliabilityConfig.REQUEST_TIMEOUT}s"
        )
        logger.info(f"   • Retry logic with {NetworkReliabilityConfig.MAX_RETRIES} attempts")
        logger.info(
            f"   • Exponential backoff with factor {NetworkReliabilityConfig.BACKOFF_FACTOR}"
        )
        logger.info("   • Proper connection pooling")
        logger.info("   • Realistic browser headers")
        logger.info("   • Enhanced error handling")
        return True
    else:
        logger.warning("⚠️  No scrapers were patched - network reliability improvements not applied")
        return False


def setup_global_session_defaults():
    """
    Set up global session defaults for requests library
    """
    # Monkey patch the requests module to use better defaults
    original_get = requests.get

    def improved_get(*args, **kwargs):
        # Set better default timeout if not specified
        if "timeout" not in kwargs:
            kwargs["timeout"] = (
                NetworkReliabilityConfig.CONNECT_TIMEOUT,
                NetworkReliabilityConfig.READ_TIMEOUT,
            )

        # Add better headers if not specified - but respect API headers
        if "headers" not in kwargs:
            kwargs["headers"] = NetworkReliabilityConfig.DEFAULT_HEADERS.copy()
        else:
            # Only merge with default headers if this is not an API call
            # API calls (like BRAVE API) should preserve their Accept headers
            user_headers = kwargs["headers"]
            if "Accept" in user_headers and user_headers["Accept"] == "application/json":
                # This is an API call - don't override the Accept header
                merged_headers = {
                    k: v
                    for k, v in NetworkReliabilityConfig.DEFAULT_HEADERS.items()
                    if k != "Accept"
                }
                merged_headers.update(user_headers)
                kwargs["headers"] = merged_headers
            else:
                # This is likely a web scraping call - use default browser headers
                merged_headers = NetworkReliabilityConfig.DEFAULT_HEADERS.copy()
                merged_headers.update(user_headers)
                kwargs["headers"] = merged_headers

        return original_get(*args, **kwargs)

    # Replace the global requests.get method
    requests.get = improved_get
    logger.info("✅ Global requests session defaults improved")


if __name__ == "__main__":
    # Test the network reliability improvements
    import logging

    logging.basicConfig(level=logging.INFO)

    print("🧪 Testing Network Reliability Patch...")

    # Apply patches
    success = apply_network_reliability_patches()
    if success:
        print("✅ Network reliability patch applied successfully")
    else:
        print("❌ Failed to apply network reliability patch")

    # Test robust request
    test_url = "https://httpbin.org/delay/2"
    print(f"\n🧪 Testing robust request to {test_url}...")

    response = robust_get_with_fallback(test_url)
    if response:
        print(f"✅ Test request successful: {response.status_code}")
    else:
        print("❌ Test request failed")
