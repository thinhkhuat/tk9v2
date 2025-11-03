"""
Enhanced Brave Search Provider
Includes robust health monitoring, error handling, and failover support
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from ..enhanced_base import (
    EnhancedBaseSearchProvider,
    SearchProviderError,
    SearchResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)


class EnhancedBraveSearchProvider(EnhancedBaseSearchProvider):
    """Enhanced Brave Search provider with robust error handling and monitoring"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        self.api_key = config.get("api_key")
        if not self.api_key:
            raise SearchProviderError("Brave API key is required", "brave")

        # Basic configuration
        self.base_url = "https://api.search.brave.com/res/v1"
        self.max_results = config.get("max_results", 10)
        self.search_depth = config.get("search_depth", "standard")

        # Enhanced configuration
        self.request_timeout = config.get("request_timeout", 30)
        self.max_retries_per_request = config.get("max_retries_per_request", 2)
        self.backoff_factor = config.get("backoff_factor", 1.5)

        # Brave-specific parameters
        self.country = config.get("country", "US")
        self.search_lang = config.get("search_lang", "en")
        self.ui_lang = config.get("ui_lang", "en-US")
        self.safesearch = config.get("safesearch", "moderate")  # off, moderate, strict
        self.freshness = config.get("freshness", None)  # pd, pw, pm, py

        # Rate limiting - enhanced with better tracking
        self.requests_per_minute = config.get("requests_per_minute", 60)  # Brave API limit
        self.request_history = []
        self.daily_request_limit = config.get("daily_request_limit", 10000)  # Default daily limit
        self.daily_request_count = 0
        self.daily_reset_time = None

        # Connection pooling
        self.connector_limit = config.get("connector_limit", 10)
        self.connector_limit_per_host = config.get("connector_limit_per_host", 5)

        logger.info(
            f"Enhanced Brave search provider initialized with {self.requests_per_minute} RPM limit"
        )

    async def search(self, query: str, **kwargs) -> SearchResponse:
        """Perform web search using Brave Search API with enhanced error handling"""
        return await self._perform_search("web", query, **kwargs)

    async def news_search(self, query: str, **kwargs) -> SearchResponse:
        """Perform news search using Brave Search API with enhanced error handling"""
        return await self._perform_search("news", query, **kwargs)

    async def _perform_search(self, search_type: str, query: str, **kwargs) -> SearchResponse:
        """Enhanced search method with comprehensive error handling and retry logic"""
        # Check rate limiting
        await self._check_rate_limit()

        # Prepare parameters based on search type
        if search_type == "news":
            params = self._prepare_news_params(query, **kwargs)
            endpoint = f"{self.base_url}/news/search"
        else:
            params = self._prepare_search_params(query, **kwargs)
            endpoint = f"{self.base_url}/web/search"

        last_error = None

        for attempt in range(self.max_retries_per_request):
            start_time = time.time()

            try:
                # Create connector with optimized settings
                connector = aiohttp.TCPConnector(
                    limit=self.connector_limit,
                    limit_per_host=self.connector_limit_per_host,
                    ttl_dns_cache=300,  # 5 minutes DNS cache
                    use_dns_cache=True,
                    enable_cleanup_closed=True,
                )

                async with aiohttp.ClientSession(
                    connector=connector, timeout=aiohttp.ClientTimeout(total=self.request_timeout)
                ) as session:
                    headers = {
                        "X-Subscription-Token": self.api_key,
                        "Accept": "application/json",
                        "User-Agent": "DeepResearch-MultiAgent/2.0 (Enhanced)",
                        "Accept-Encoding": "gzip, deflate",
                        "Connection": "keep-alive",
                    }

                    async with session.get(endpoint, params=params, headers=headers) as response:
                        # Handle different HTTP status codes
                        if response.status == 200:
                            data = await response.json()
                            search_time_ms = int((time.time() - start_time) * 1000)

                            # Parse results based on search type
                            if search_type == "news":
                                results = self._parse_news_results(data)
                            else:
                                results = self._parse_web_results(data)

                            # Record successful request
                            self.request_history.append(time.time())
                            self.daily_request_count += 1

                            return SearchResponse(
                                results=results,
                                query=query,
                                provider="brave",
                                total_results=len(results),
                                search_time_ms=search_time_ms,
                                metadata={
                                    "search_type": search_type,
                                    "params": params,
                                    "api_response": data.get("query", {}),
                                    "attempt": attempt + 1,
                                    "request_id": f"brave_{search_type}_{int(time.time())}_{attempt}",
                                    "rate_limit_remaining": self._get_rate_limit_remaining(),
                                },
                            )

                        elif response.status == 401:
                            error_msg = "Invalid API key or authentication failed"
                            logger.error(f"Brave authentication error: {error_msg}")
                            raise SearchProviderError(error_msg, "brave", "auth_error")

                        elif response.status == 429:
                            # Rate limit exceeded - get retry-after header if available
                            retry_after = response.headers.get("Retry-After", 60)
                            try:
                                retry_after = int(retry_after)
                            except ValueError:
                                retry_after = 60

                            error_msg = f"Rate limit exceeded, retry after {retry_after}s"
                            logger.warning(f"Brave rate limit: {error_msg}")

                            if attempt < self.max_retries_per_request - 1:
                                logger.info(f"Waiting {retry_after}s before retry")
                                await asyncio.sleep(retry_after)
                                continue
                            else:
                                raise SearchProviderError(
                                    error_msg, "brave", "rate_limit", retry_after
                                )

                        elif response.status == 403:
                            error_msg = "Access forbidden - check API key permissions"
                            logger.error(f"Brave access forbidden: {error_msg}")
                            raise SearchProviderError(error_msg, "brave", "forbidden")

                        elif response.status in [500, 502, 503, 504]:
                            # Server errors - retry with backoff
                            error_text = await response.text()
                            error_msg = f"Server error {response.status}: {error_text[:200]}"
                            logger.warning(
                                f"Brave server error on attempt {attempt + 1}: {error_msg}"
                            )
                            last_error = SearchProviderError(
                                error_msg, "brave", f"server_error_{response.status}"
                            )

                        else:
                            # Other HTTP errors
                            error_text = await response.text()
                            error_msg = f"HTTP {response.status}: {error_text[:200]}"
                            logger.error(f"Brave HTTP error: {error_msg}")
                            raise SearchProviderError(error_msg, "brave", f"http_{response.status}")

            except asyncio.TimeoutError:
                error_msg = f"Request timeout after {self.request_timeout}s"
                logger.warning(f"Brave timeout on attempt {attempt + 1}: {error_msg}")
                last_error = SearchProviderError(error_msg, "brave", "timeout")

            except aiohttp.ClientError as e:
                error_msg = f"Network error: {str(e)}"
                logger.warning(f"Brave network error on attempt {attempt + 1}: {error_msg}")
                last_error = SearchProviderError(error_msg, "brave", "network_error")

            except Exception as e:
                if isinstance(e, SearchProviderError):
                    last_error = e
                    if e.error_code in ["auth_error", "forbidden"]:
                        # Don't retry authentication/permission errors
                        break
                else:
                    error_msg = f"Unexpected error: {str(e)}"
                    logger.warning(f"Brave unexpected error on attempt {attempt + 1}: {error_msg}")
                    last_error = SearchProviderError(error_msg, "brave", "unexpected_error")

            # Apply backoff if not the last attempt
            if attempt < self.max_retries_per_request - 1:
                backoff_time = self.backoff_factor**attempt
                logger.debug(f"Backing off for {backoff_time}s before retry")
                await asyncio.sleep(backoff_time)

        # All retries exhausted
        logger.error(
            f"Brave {search_type} search failed after {self.max_retries_per_request} attempts"
        )
        raise (
            last_error if last_error else SearchProviderError("All retry attempts failed", "brave")
        )

    def _prepare_search_params(self, query: str, **kwargs) -> Dict[str, Any]:
        """Enhanced parameter preparation for web search"""
        # Truncate query to meet BRAVE API 400 character limit
        truncated_query = self._truncate_query(query)

        params = {
            "q": truncated_query,
            "count": kwargs.get("max_results", self.max_results),
            "country": kwargs.get("country", self.country),
            "search_lang": kwargs.get("search_lang", self.search_lang),
            "ui_lang": kwargs.get("ui_lang", self.ui_lang),
            "safesearch": kwargs.get("safesearch", self.safesearch),
        }

        # Optional parameters
        freshness = kwargs.get("freshness", self.freshness)
        if freshness:
            params["freshness"] = freshness

        # Convert boolean parameters to strings
        text_decorations = kwargs.get("text_decorations", False)
        if text_decorations is not None:
            params["text_decorations"] = str(text_decorations).lower()

        extra_snippets = kwargs.get("extra_snippets", True)
        if extra_snippets is not None:
            params["extra_snippets"] = str(extra_snippets).lower()

        # Advanced parameters
        include_domains = kwargs.get("include_domains")
        if include_domains:
            params["site"] = " OR ".join([f"site:{domain}" for domain in include_domains])

        exclude_domains = kwargs.get("exclude_domains")
        if exclude_domains:
            exclude_clause = " ".join([f"-site:{domain}" for domain in exclude_domains])
            params["q"] = f"{params['q']} {exclude_clause}"

        return params

    def _prepare_news_params(self, query: str, **kwargs) -> Dict[str, Any]:
        """Enhanced parameter preparation for news search"""
        # Truncate query to meet BRAVE API 400 character limit
        truncated_query = self._truncate_query(query)

        params = {
            "q": truncated_query,
            "count": kwargs.get("max_results", self.max_results),
            "country": kwargs.get("country", self.country),
            "search_lang": kwargs.get("search_lang", self.search_lang),
            "ui_lang": kwargs.get("ui_lang", self.ui_lang),
            "safesearch": kwargs.get("safesearch", self.safesearch),
        }

        # News-specific parameters
        freshness = kwargs.get("freshness", self.freshness)
        if freshness:
            params["freshness"] = freshness

        # Sort by date for news (default) or relevance
        sort_method = kwargs.get("sort", "date")
        if sort_method in ["date", "relevance"]:
            params["sort"] = sort_method

        return params

    def _truncate_query(self, query: str, max_length: int = 400, max_words: int = 50) -> str:
        """
        Intelligently truncate query to meet BRAVE API limits:
        - 400 character limit
        - 50 word limit
        Preserves key terms and removes filler words
        """
        original_length = len(query)
        original_word_count = len(query.split())

        # Return early if within both limits
        if len(query) <= max_length and original_word_count <= max_words:
            return query

        # List of filler words to remove first
        filler_words = [
            "that",
            "would",
            "could",
            "should",
            "might",
            "will",
            "shall",
            "and so forth",
            "so on",
            "etc",
            "such as",
            "for example",
            "for instance",
            "compared to when",
            "significantly",
            "practical",
            "valuable",
            "available",
            "prepared",
            "readily",
        ]

        truncated = query

        # First, try removing filler words
        for filler in filler_words:
            current_word_count = len(truncated.split())
            if len(truncated) <= max_length and current_word_count <= max_words:
                break
            truncated = truncated.replace(filler, "")

        # Clean up extra spaces
        truncated = " ".join(truncated.split())

        # Check word count after filler word removal
        current_word_count = len(truncated.split())

        # If still too many words, truncate to word limit first
        if current_word_count > max_words:
            words = truncated.split()
            truncated = " ".join(words[:max_words])

        # If still too long by characters, truncate at word boundary
        if len(truncated) > max_length:
            # Find last complete word within character limit
            truncated = truncated[:max_length].rsplit(" ", 1)[0]

        final_word_count = len(truncated.split())
        logger.info(
            f"Query truncated: {original_word_count} words → {final_word_count} words, {original_length} chars → {len(truncated)} chars"
        )
        return truncated

    def _parse_web_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Enhanced parsing of web search results"""
        results = []

        web_results = data.get("web", {}).get("results", [])

        for idx, item in enumerate(web_results):
            try:
                # Extract and enhance content
                content = item.get("description", "")
                if item.get("extra_snippets"):
                    snippets = " | ".join(item["extra_snippets"])
                    content = f"{content} | {snippets}".strip()

                # Extract age/published date
                published_date = item.get("age")
                if published_date and "ago" not in published_date:
                    # Try to parse absolute dates
                    try:
                        published_date = datetime.fromisoformat(published_date).isoformat()
                    except:
                        pass  # Keep original format if parsing fails

                result = SearchResult(
                    title=item.get("title", "").strip(),
                    url=item.get("url", "").strip(),
                    content=content.strip(),
                    published_date=published_date,
                    score=item.get("score", 1.0 - (idx * 0.1)),  # Synthetic score based on rank
                    metadata={
                        "type": item.get("type", "web"),
                        "language": item.get("language"),
                        "family_friendly": item.get("family_friendly", True),
                        "subtype": item.get("subtype"),
                        "deep_results": item.get("deep_results", {}),
                        "favicon": item.get("profile", {}).get("img"),
                        "source_name": item.get("profile", {}).get("name"),
                        "rank": idx + 1,
                    },
                )

                if result.title and result.url:  # Only add results with essential fields
                    results.append(result)

            except Exception as e:
                logger.warning(f"Failed to parse web search result {idx}: {e}")
                continue

        return results

    def _parse_news_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Enhanced parsing of news search results"""
        results = []

        news_results = data.get("results", [])

        for idx, item in enumerate(news_results):
            try:
                # Extract published date with better handling
                published_date = item.get("age")
                if published_date:
                    # Handle relative dates (e.g., "2 hours ago")
                    if "ago" in published_date:
                        # Keep relative format for now
                        pass
                    else:
                        # Try to parse absolute dates
                        try:
                            published_date = datetime.fromisoformat(published_date).isoformat()
                        except:
                            pass

                # Extract source information
                meta_url = item.get("meta_url", {})
                source_name = meta_url.get("hostname", "").replace("www.", "")

                result = SearchResult(
                    title=item.get("title", "").strip(),
                    url=item.get("url", "").strip(),
                    content=item.get("description", "").strip(),
                    published_date=published_date,
                    score=1.0 - (idx * 0.05),  # News results get higher base scores
                    metadata={
                        "type": "news",
                        "source": source_name,
                        "source_url": meta_url.get("scheme", "")
                        + "://"
                        + meta_url.get("hostname", ""),
                        "language": item.get("language"),
                        "breaking": item.get("breaking", False),
                        "thumbnail": item.get("thumbnail"),
                        "category": item.get("category"),
                        "rank": idx + 1,
                    },
                )

                if result.title and result.url:  # Only add results with essential fields
                    results.append(result)

            except Exception as e:
                logger.warning(f"Failed to parse news search result {idx}: {e}")
                continue

        return results

    async def _check_rate_limit(self):
        """Enhanced rate limiting with daily limits and better tracking"""
        now = time.time()

        # Reset daily count if needed
        if self.daily_reset_time is None or now >= self.daily_reset_time:
            self.daily_request_count = 0
            # Set next reset time to tomorrow at midnight UTC
            import datetime

            tomorrow = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow += datetime.timedelta(days=1)
            self.daily_reset_time = tomorrow.timestamp()

        # Check daily limit
        if self.daily_request_count >= self.daily_request_limit:
            wait_until_reset = self.daily_reset_time - now
            if wait_until_reset > 0:
                logger.warning(
                    f"Daily request limit reached, waiting {wait_until_reset / 3600:.1f} hours"
                )
                raise SearchProviderError(
                    f"Daily request limit ({self.daily_request_limit}) exceeded",
                    "brave",
                    "daily_limit",
                    int(wait_until_reset),
                )

        # Remove requests older than 1 minute for per-minute tracking
        self.request_history = [
            req_time for req_time in self.request_history if now - req_time < 60
        ]

        # Check per-minute limit
        if len(self.request_history) >= self.requests_per_minute:
            # Calculate precise wait time
            oldest_request = min(self.request_history)
            wait_time = 60 - (now - oldest_request)

            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time + 0.1)  # Add small buffer
                # Refresh the history after waiting
                now = time.time()
                self.request_history = [
                    req_time for req_time in self.request_history if now - req_time < 60
                ]

    def _get_rate_limit_remaining(self) -> Dict[str, int]:
        """Get remaining rate limit counts"""
        now = time.time()

        # Per-minute remaining
        minute_used = len([t for t in self.request_history if now - t < 60])
        minute_remaining = max(0, self.requests_per_minute - minute_used)

        # Daily remaining
        daily_remaining = max(0, self.daily_request_limit - self.daily_request_count)

        return {
            "minute_remaining": minute_remaining,
            "daily_remaining": daily_remaining,
            "daily_reset_in_seconds": (
                int(self.daily_reset_time - now) if self.daily_reset_time else 0
            ),
        }

    def validate_config(self) -> List[str]:
        """Enhanced validation of Brave provider configuration"""
        issues = []

        # Basic validation
        if not self.api_key:
            issues.append("Brave API key is required")

        # Parameter validation
        if not (1 <= self.max_results <= 20):
            issues.append("Max results must be between 1 and 20")

        if self.safesearch not in ["off", "moderate", "strict"]:
            issues.append("Safesearch must be 'off', 'moderate', or 'strict'")

        if self.freshness and self.freshness not in ["pd", "pw", "pm", "py"]:
            issues.append("Freshness must be 'pd', 'pw', 'pm', or 'py'")

        # Enhanced validation
        if not (5 <= self.request_timeout <= 300):
            issues.append("Request timeout must be between 5 and 300 seconds")

        if not (1 <= self.max_retries_per_request <= 5):
            issues.append("Max retries per request must be between 1 and 5")

        if not (1.0 <= self.backoff_factor <= 3.0):
            issues.append("Backoff factor must be between 1.0 and 3.0")

        if not (1 <= self.requests_per_minute <= 600):
            issues.append("Requests per minute must be between 1 and 600")

        if not (100 <= self.daily_request_limit <= 100000):
            issues.append("Daily request limit must be between 100 and 100000")

        return issues

    def get_provider_info(self) -> Dict[str, Any]:
        """Get comprehensive provider information"""
        base_info = super().get_provider_info()

        # Add Brave-specific information
        brave_info = {
            "country": self.country,
            "search_lang": self.search_lang,
            "safesearch": self.safesearch,
            "capabilities": {
                "web_search": True,
                "news_search": True,
                "image_search": False,
                "video_search": False,
                "real_time": True,
                "freshness_filter": True,
                "safe_search": True,
                "domain_filtering": True,
            },
            "rate_limits": {
                "requests_per_minute": self.requests_per_minute,
                "daily_request_limit": self.daily_request_limit,
                **self._get_rate_limit_remaining(),
            },
            "performance": {
                "request_timeout": self.request_timeout,
                "max_retries": self.max_retries_per_request,
                "backoff_factor": self.backoff_factor,
            },
        }

        base_info.update(brave_info)
        return base_info

    async def test_connection(self) -> bool:
        """Enhanced connection test"""
        try:
            response = await self.search("test connection", max_results=1)
            return not response.metadata.get("error")
        except Exception as e:
            logger.error(f"Brave connection test failed: {e}")
            return False
