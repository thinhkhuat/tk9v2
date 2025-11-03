"""
Brave Search Provider
Supports web search and news search through Brave Search API
"""

import asyncio
import time
from typing import Any, Dict, List

import aiohttp

from ..base import BaseSearchProvider, SearchProviderError, SearchResponse, SearchResult


class BraveSearchProvider(BaseSearchProvider):
    """Brave Search provider implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        self.api_key = config.get("api_key")
        if not self.api_key:
            raise SearchProviderError("Brave API key is required", "brave")

        self.base_url = "https://api.search.brave.com/res/v1"
        self.max_results = config.get("max_results", 10)
        self.search_depth = config.get("search_depth", "standard")
        self.timeout = config.get("timeout", 30)

        # Brave-specific parameters
        self.country = config.get("country", "US")
        self.search_lang = config.get("search_lang", "en")
        self.ui_lang = config.get("ui_lang", "en-US")
        self.safesearch = config.get("safesearch", "moderate")  # off, moderate, strict
        self.freshness = config.get(
            "freshness", None
        )  # pd (past day), pw (past week), pm (past month), py (past year)

        # Rate limiting
        self.requests_per_minute = 60  # Brave API limit
        self.request_history = []

    async def search(self, query: str, **kwargs) -> SearchResponse:
        """Perform web search using Brave Search API"""
        start_time = time.time()

        # Check rate limiting
        await self._check_rate_limit()

        # Prepare parameters
        params = self._prepare_search_params(query, **kwargs)

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-Subscription-Token": self.api_key,
                    "Accept": "application/json",
                    "User-Agent": "DeepResearch-MultiAgent/1.0",
                }

                async with session.get(
                    f"{self.base_url}/web/search",
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status == 401:
                        raise SearchProviderError("Invalid API key", "brave", "auth_error")
                    elif response.status == 429:
                        raise SearchProviderError("Rate limit exceeded", "brave", "rate_limit")
                    elif response.status != 200:
                        error_text = await response.text()
                        raise SearchProviderError(
                            f"API error: {response.status} - {error_text}",
                            "brave",
                            f"http_{response.status}",
                        )

                    data = await response.json()

                    # Parse results
                    results = self._parse_web_results(data)

                    search_time_ms = int((time.time() - start_time) * 1000)

                    return SearchResponse(
                        results=results,
                        query=query,
                        provider="brave",
                        total_results=len(results),
                        search_time_ms=search_time_ms,
                        metadata={
                            "search_type": "web",
                            "params": params,
                            "api_response": data.get("query", {}),
                        },
                    )

        except aiohttp.ClientError as e:
            raise SearchProviderError(f"Network error: {str(e)}", "brave")
        except asyncio.TimeoutError:
            raise SearchProviderError("Request timeout", "brave", "timeout")
        except Exception as e:
            if isinstance(e, SearchProviderError):
                raise
            raise SearchProviderError(f"Unexpected error: {str(e)}", "brave")

    async def news_search(self, query: str, **kwargs) -> SearchResponse:
        """Perform news search using Brave Search API"""
        start_time = time.time()

        # Check rate limiting
        await self._check_rate_limit()

        # Prepare parameters for news search
        params = self._prepare_news_params(query, **kwargs)

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-Subscription-Token": self.api_key,
                    "Accept": "application/json",
                    "User-Agent": "DeepResearch-MultiAgent/1.0",
                }

                async with session.get(
                    f"{self.base_url}/news/search",
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise SearchProviderError(
                            f"News API error: {response.status} - {error_text}",
                            "brave",
                            f"news_http_{response.status}",
                        )

                    data = await response.json()

                    # Parse news results
                    results = self._parse_news_results(data)

                    search_time_ms = int((time.time() - start_time) * 1000)

                    return SearchResponse(
                        results=results,
                        query=query,
                        provider="brave",
                        total_results=len(results),
                        search_time_ms=search_time_ms,
                        metadata={
                            "search_type": "news",
                            "params": params,
                            "api_response": data.get("query", {}),
                        },
                    )

        except Exception as e:
            if isinstance(e, SearchProviderError):
                raise
            raise SearchProviderError(f"News search error: {str(e)}", "brave")

    def _prepare_search_params(self, query: str, **kwargs) -> Dict[str, Any]:
        """Prepare parameters for web search"""
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
        if self.freshness or kwargs.get("freshness"):
            params["freshness"] = kwargs.get("freshness", self.freshness)

        # Text decorations (for highlighting) - convert boolean to string
        text_decorations = kwargs.get("text_decorations", False)
        if text_decorations is not None:
            params["text_decorations"] = str(text_decorations).lower()

        # Include extra snippets - convert boolean to string
        extra_snippets = kwargs.get("extra_snippets", True)
        if extra_snippets is not None:
            params["extra_snippets"] = str(extra_snippets).lower()

        return params

    def _prepare_news_params(self, query: str, **kwargs) -> Dict[str, Any]:
        """Prepare parameters for news search"""
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
        if self.freshness or kwargs.get("freshness"):
            params["freshness"] = kwargs.get("freshness", self.freshness)

        # Sort by date for news
        params["sort"] = kwargs.get("sort", "date")

        return params

    def _truncate_query(self, query: str, max_length: int = 400, max_words: int = 50) -> str:
        """
        Intelligently truncate query to meet BRAVE API limits:
        - 400 character limit
        - 50 word limit
        Preserves key terms and removes filler words
        """
        len(query)
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

        return truncated

    def _parse_web_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Parse web search results from Brave API response"""
        results = []

        web_results = data.get("web", {}).get("results", [])

        for item in web_results:
            # Extract content from description or extra snippets
            content = item.get("description", "")
            if item.get("extra_snippets"):
                snippets = " ".join(item["extra_snippets"])
                content = f"{content} {snippets}".strip()

            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=content,
                published_date=item.get("age"),  # Brave provides relative age
                score=item.get("score", 0.0),
                metadata={
                    "type": item.get("type", "web"),
                    "language": item.get("language"),
                    "family_friendly": item.get("family_friendly", True),
                    "subtype": item.get("subtype"),
                    "deep_results": item.get("deep_results", {}),
                },
            )
            results.append(result)

        return results

    def _parse_news_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Parse news search results from Brave API response"""
        results = []

        news_results = data.get("results", [])

        for item in news_results:
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("description", ""),
                published_date=item.get("age"),
                score=1.0,  # News results don't have explicit scores
                metadata={
                    "type": "news",
                    "source": item.get("meta_url", {}).get("hostname"),
                    "language": item.get("language"),
                    "breaking": item.get("breaking", False),
                    "thumbnail": item.get("thumbnail"),
                },
            )
            results.append(result)

        return results

    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = time.time()

        # Remove requests older than 1 minute
        self.request_history = [
            req_time for req_time in self.request_history if now - req_time < 60
        ]

        # Check if we're at the limit
        if len(self.request_history) >= self.requests_per_minute:
            # Wait until the oldest request is older than 1 minute
            wait_time = 60 - (now - self.request_history[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                # Refresh the history after waiting
                now = time.time()
                self.request_history = [
                    req_time for req_time in self.request_history if now - req_time < 60
                ]

        # Record this request
        self.request_history.append(now)

    def validate_config(self) -> List[str]:
        """Validate Brave provider configuration"""
        issues = []

        if not self.api_key:
            issues.append("Brave API key is required")

        if not (1 <= self.max_results <= 20):
            issues.append("Max results must be between 1 and 20")

        if self.safesearch not in ["off", "moderate", "strict"]:
            issues.append("Safesearch must be 'off', 'moderate', or 'strict'")

        if self.freshness and self.freshness not in ["pd", "pw", "pm", "py"]:
            issues.append("Freshness must be 'pd', 'pw', 'pm', or 'py'")

        if not (5 <= self.timeout <= 60):
            issues.append("Timeout must be between 5 and 60 seconds")

        return issues

    def get_provider_info(self) -> Dict[str, Any]:
        """Get detailed provider information"""
        return {
            "provider": "brave",
            "max_results": self.max_results,
            "search_depth": self.search_depth,
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
            },
            "rate_limits": {
                "requests_per_minute": self.requests_per_minute,
                "current_usage": len(self.request_history),
            },
        }

    async def test_connection(self) -> bool:
        """Test connection to Brave Search API"""
        try:
            response = await self.search("test query", max_results=1)
            return len(response.results) >= 0  # Even 0 results is a successful connection
        except:
            return False
