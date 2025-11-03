"""
Enhanced Base Classes for LLM and Search Providers
Includes robust failover mechanisms, health monitoring, and state management
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


class ProviderHealth(Enum):
    """Provider health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class FailoverReason(Enum):
    """Reasons for provider failover"""

    HEALTH_CHECK_FAILED = "health_check_failed"
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    MANUAL_SWITCH = "manual_switch"
    COST_LIMIT = "cost_limit"


@dataclass
class LLMResponse:
    """Standardized response from LLM providers"""

    content: str
    model: str
    provider: str
    tokens_used: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if the response indicates success"""
        return bool(self.content and not self.metadata.get("error"))

    @property
    def error_message(self) -> Optional[str]:
        """Get error message if any"""
        return self.metadata.get("error")


@dataclass
class SearchResult:
    """Individual search result"""

    title: str
    url: str
    content: str
    published_date: Optional[str] = None
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Standardized response from search providers"""

    results: List[SearchResult]
    query: str
    provider: str
    total_results: int = 0
    search_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_results(self) -> bool:
        """Check if search returned valid results"""
        return len(self.results) > 0 and not self.metadata.get("error")

    @property
    def error_message(self) -> Optional[str]:
        """Get error message if any"""
        return self.metadata.get("error")


@dataclass
class HealthCheckResult:
    """Result of a provider health check"""

    provider: str
    status: ProviderHealth
    response_time_ms: int
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailoverEvent:
    """Record of a failover event"""

    timestamp: datetime
    from_provider: str
    to_provider: str
    reason: FailoverReason
    error_message: Optional[str] = None
    recovery_time_ms: Optional[int] = None


class EnhancedBaseLLMProvider(ABC):
    """Enhanced base class for all LLM providers with health monitoring"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self.__class__.__name__.lower().replace("provider", "")
        self._health_status = ProviderHealth.UNKNOWN
        self._last_health_check = None
        self._consecutive_failures = 0
        self._lock = asyncio.Lock()

        # Health check configuration
        self.health_check_interval = config.get("health_check_interval", 300)  # 5 minutes
        self.health_check_timeout = config.get("health_check_timeout", 10)
        self.max_consecutive_failures = config.get("max_consecutive_failures", 3)

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> LLMResponse:
        """Generate text from the LLM"""
        pass

    @abstractmethod
    async def generate_stream(
        self, prompt: str, system_prompt: str = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming text from the LLM"""
        pass

    @abstractmethod
    def estimate_cost(self, prompt: str, response: str = "") -> float:
        """Estimate cost for the API call"""
        pass

    @abstractmethod
    def validate_config(self) -> List[str]:
        """Validate provider configuration"""
        pass

    async def health_check(self) -> HealthCheckResult:
        """Perform health check on the provider"""
        start_time = time.time()

        try:
            # Simple test generation
            test_prompt = "Health check test"
            response = await asyncio.wait_for(
                self.generate(test_prompt, max_tokens=10), timeout=self.health_check_timeout
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            if response.success:
                self._health_status = ProviderHealth.HEALTHY
                self._consecutive_failures = 0
                result = HealthCheckResult(
                    provider=self.provider_name,
                    status=ProviderHealth.HEALTHY,
                    response_time_ms=response_time_ms,
                )
            else:
                self._consecutive_failures += 1
                status = (
                    ProviderHealth.UNHEALTHY
                    if self._consecutive_failures >= self.max_consecutive_failures
                    else ProviderHealth.DEGRADED
                )
                self._health_status = status
                result = HealthCheckResult(
                    provider=self.provider_name,
                    status=status,
                    response_time_ms=response_time_ms,
                    error_message=response.error_message,
                )

        except asyncio.TimeoutError:
            self._consecutive_failures += 1
            self._health_status = ProviderHealth.UNHEALTHY
            response_time_ms = int((time.time() - start_time) * 1000)
            result = HealthCheckResult(
                provider=self.provider_name,
                status=ProviderHealth.UNHEALTHY,
                response_time_ms=response_time_ms,
                error_message="Health check timeout",
            )

        except Exception as e:
            self._consecutive_failures += 1
            self._health_status = ProviderHealth.UNHEALTHY
            response_time_ms = int((time.time() - start_time) * 1000)
            result = HealthCheckResult(
                provider=self.provider_name,
                status=ProviderHealth.UNHEALTHY,
                response_time_ms=response_time_ms,
                error_message=str(e),
            )

        self._last_health_check = datetime.now()
        return result

    async def is_healthy(self, force_check: bool = False) -> bool:
        """Check if provider is healthy"""
        now = datetime.now()

        # Force health check if requested or if never checked
        if (
            force_check
            or not self._last_health_check
            or (now - self._last_health_check).seconds > self.health_check_interval
        ):
            async with self._lock:
                # Double-check pattern to avoid duplicate checks
                if (
                    force_check
                    or not self._last_health_check
                    or (now - self._last_health_check).seconds > self.health_check_interval
                ):
                    await self.health_check()

        return self._health_status in [ProviderHealth.HEALTHY, ProviderHealth.DEGRADED]

    def get_health_status(self) -> ProviderHealth:
        """Get current health status"""
        return self._health_status

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "provider": self.provider_name,
            "model": self.config.get("model", "unknown"),
            "max_tokens": self.config.get("max_tokens", 0),
            "temperature": self.config.get("temperature", 0.0),
            "health_status": self._health_status.value,
            "last_health_check": (
                self._last_health_check.isoformat() if self._last_health_check else None
            ),
            "consecutive_failures": self._consecutive_failures,
        }


class EnhancedBaseSearchProvider(ABC):
    """Enhanced base class for all search providers with health monitoring"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self.__class__.__name__.lower().replace("provider", "")
        self._health_status = ProviderHealth.UNKNOWN
        self._last_health_check = None
        self._consecutive_failures = 0
        self._lock = asyncio.Lock()

        # Health check configuration
        self.health_check_interval = config.get("health_check_interval", 300)  # 5 minutes
        self.health_check_timeout = config.get("health_check_timeout", 10)
        self.max_consecutive_failures = config.get("max_consecutive_failures", 3)

    @abstractmethod
    async def search(self, query: str, **kwargs) -> SearchResponse:
        """Perform web search"""
        pass

    @abstractmethod
    async def news_search(self, query: str, **kwargs) -> SearchResponse:
        """Perform news search"""
        pass

    @abstractmethod
    def validate_config(self) -> List[str]:
        """Validate provider configuration"""
        pass

    async def health_check(self) -> HealthCheckResult:
        """Perform health check on the search provider"""
        start_time = time.time()

        try:
            # Simple test search
            test_query = "test"
            response = await asyncio.wait_for(
                self.search(test_query, max_results=1), timeout=self.health_check_timeout
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            if not response.metadata.get("error"):
                self._health_status = ProviderHealth.HEALTHY
                self._consecutive_failures = 0
                result = HealthCheckResult(
                    provider=self.provider_name,
                    status=ProviderHealth.HEALTHY,
                    response_time_ms=response_time_ms,
                )
            else:
                self._consecutive_failures += 1
                status = (
                    ProviderHealth.UNHEALTHY
                    if self._consecutive_failures >= self.max_consecutive_failures
                    else ProviderHealth.DEGRADED
                )
                self._health_status = status
                result = HealthCheckResult(
                    provider=self.provider_name,
                    status=status,
                    response_time_ms=response_time_ms,
                    error_message=response.error_message,
                )

        except asyncio.TimeoutError:
            self._consecutive_failures += 1
            self._health_status = ProviderHealth.UNHEALTHY
            response_time_ms = int((time.time() - start_time) * 1000)
            result = HealthCheckResult(
                provider=self.provider_name,
                status=ProviderHealth.UNHEALTHY,
                response_time_ms=response_time_ms,
                error_message="Health check timeout",
            )

        except Exception as e:
            self._consecutive_failures += 1
            self._health_status = ProviderHealth.UNHEALTHY
            response_time_ms = int((time.time() - start_time) * 1000)
            result = HealthCheckResult(
                provider=self.provider_name,
                status=ProviderHealth.UNHEALTHY,
                response_time_ms=response_time_ms,
                error_message=str(e),
            )

        self._last_health_check = datetime.now()
        return result

    async def is_healthy(self, force_check: bool = False) -> bool:
        """Check if provider is healthy"""
        now = datetime.now()

        # Force health check if requested or if never checked
        if (
            force_check
            or not self._last_health_check
            or (now - self._last_health_check).seconds > self.health_check_interval
        ):
            async with self._lock:
                # Double-check pattern to avoid duplicate checks
                if (
                    force_check
                    or not self._last_health_check
                    or (now - self._last_health_check).seconds > self.health_check_interval
                ):
                    await self.health_check()

        return self._health_status in [ProviderHealth.HEALTHY, ProviderHealth.DEGRADED]

    def get_health_status(self) -> ProviderHealth:
        """Get current health status"""
        return self._health_status

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the search provider"""
        return {
            "provider": self.provider_name,
            "max_results": self.config.get("max_results", 10),
            "search_depth": self.config.get("search_depth", "basic"),
            "health_status": self._health_status.value,
            "last_health_check": (
                self._last_health_check.isoformat() if self._last_health_check else None
            ),
            "consecutive_failures": self._consecutive_failures,
        }


class ProviderError(Exception):
    """Base exception for provider errors"""

    def __init__(
        self, message: str, provider: str, error_code: str = None, retry_after: Optional[int] = None
    ):
        self.provider = provider
        self.error_code = error_code
        self.retry_after = retry_after
        super().__init__(f"[{provider}] {message}")


class LLMProviderError(ProviderError):
    """Exception for LLM provider errors"""

    pass


class SearchProviderError(ProviderError):
    """Exception for search provider errors"""

    pass


class EnhancedProviderManager:
    """Enhanced provider manager with robust failover, health monitoring, and state management"""

    def __init__(self):
        # Provider registries
        self.llm_providers: Dict[str, EnhancedBaseLLMProvider] = {}
        self.search_providers: Dict[str, EnhancedBaseSearchProvider] = {}

        # State management
        self._state_lock = asyncio.Lock()
        self._active_llm_provider = None
        self._active_search_provider = None

        # Statistics and monitoring
        self.usage_stats = {"llm": {}, "search": {}}
        self.failover_history: List[FailoverEvent] = []

        # Health monitoring
        self._health_check_tasks = {}
        self._monitoring_enabled = True

        # Configuration
        self.failover_enabled = True
        self.health_check_interval = 300  # 5 minutes
        self.max_failover_history = 100

        # Callbacks
        self.on_failover_callbacks: List[Callable[[FailoverEvent], None]] = []

    def register_llm_provider(
        self, name: str, provider: EnhancedBaseLLMProvider, is_primary: bool = False
    ):
        """Register an LLM provider with enhanced monitoring"""
        self.llm_providers[name] = provider
        self.usage_stats["llm"][name] = {
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "errors": 0,
            "last_used": None,
            "average_latency": 0.0,
            "success_rate": 100.0,
            "is_primary": is_primary,
        }

        if is_primary or not self._active_llm_provider:
            self._active_llm_provider = name

        # Start health monitoring
        if self._monitoring_enabled:
            self._start_health_monitoring(provider, name, "llm")

    def register_search_provider(
        self, name: str, provider: EnhancedBaseSearchProvider, is_primary: bool = False
    ):
        """Register a search provider with enhanced monitoring"""
        self.search_providers[name] = provider
        self.usage_stats["search"][name] = {
            "requests": 0,
            "results": 0,
            "errors": 0,
            "last_used": None,
            "average_latency": 0.0,
            "success_rate": 100.0,
            "is_primary": is_primary,
        }

        if is_primary or not self._active_search_provider:
            self._active_search_provider = name

        # Start health monitoring
        if self._monitoring_enabled:
            self._start_health_monitoring(provider, name, "search")

    def _start_health_monitoring(
        self,
        provider: Union[EnhancedBaseLLMProvider, EnhancedBaseSearchProvider],
        name: str,
        provider_type: str,
    ):
        """Start periodic health monitoring for a provider"""

        async def monitor():
            while self._monitoring_enabled:
                try:
                    await provider.health_check()
                    await asyncio.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(
                        f"Health monitoring failed for {provider_type} provider {name}: {e}"
                    )
                    await asyncio.sleep(60)  # Retry after 1 minute on error

        task_name = f"{provider_type}_{name}_health_monitor"
        self._health_check_tasks[task_name] = asyncio.create_task(monitor())

    async def llm_generate(
        self,
        prompt: str,
        provider_name: str = None,
        fallback: bool = True,
        max_retries: int = 3,
        **kwargs,
    ) -> LLMResponse:
        """Generate text with enhanced failover and retry logic"""
        async with self._state_lock:
            providers = self._get_llm_provider_order(provider_name)

        last_error = None
        retry_count = 0

        for provider_name in providers:
            if provider_name not in self.llm_providers:
                continue

            provider = self.llm_providers[provider_name]

            # Check provider health before using
            if not await provider.is_healthy():
                logger.warning(f"LLM provider {provider_name} is not healthy, trying next provider")
                if fallback and len(providers) > 1:
                    continue

            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    response = await provider.generate(prompt, **kwargs)
                    latency = time.time() - start_time

                    # Update statistics
                    self._update_llm_stats(provider_name, response, latency, success=True)

                    # Update active provider if this was successful
                    if self._active_llm_provider != provider_name:
                        await self._perform_llm_failover(
                            self._active_llm_provider, provider_name, FailoverReason.MANUAL_SWITCH
                        )

                    return response

                except Exception as e:
                    last_error = e
                    retry_count += 1

                    # Update error statistics
                    self._update_llm_stats(provider_name, None, 0, success=False)

                    # Determine if we should retry or failover
                    if isinstance(e, LLMProviderError) and e.retry_after:
                        await asyncio.sleep(e.retry_after)
                    elif attempt < max_retries - 1:
                        await asyncio.sleep(min(2**attempt, 10))  # Exponential backoff

                    if attempt == max_retries - 1:
                        # Max retries reached for this provider
                        logger.error(
                            f"LLM provider {provider_name} failed after {max_retries} attempts: {e}"
                        )
                        if fallback and len(providers) > 1:
                            # Try failover to next provider
                            await self._perform_llm_failover(
                                provider_name,
                                providers[providers.index(provider_name) + 1],
                                FailoverReason.API_ERROR,
                                str(e),
                            )
                            break
                        else:
                            raise LLMProviderError(str(e), provider_name)

        # All providers failed
        raise LLMProviderError(
            f"All LLM providers failed after {retry_count} attempts. Last error: {last_error}",
            "all",
        )

    async def search_query(
        self,
        query: str,
        provider_name: str = None,
        search_type: str = "web",
        fallback: bool = True,
        max_retries: int = 3,
        **kwargs,
    ) -> SearchResponse:
        """Perform search with enhanced failover and retry logic"""
        async with self._state_lock:
            providers = self._get_search_provider_order(provider_name)

        last_error = None
        retry_count = 0

        for provider_name in providers:
            if provider_name not in self.search_providers:
                continue

            provider = self.search_providers[provider_name]

            # Check provider health before using
            if not await provider.is_healthy():
                logger.warning(
                    f"Search provider {provider_name} is not healthy, trying next provider"
                )
                if fallback and len(providers) > 1:
                    continue

            for attempt in range(max_retries):
                try:
                    start_time = time.time()

                    if search_type == "news":
                        response = await provider.news_search(query, **kwargs)
                    else:
                        response = await provider.search(query, **kwargs)

                    latency = time.time() - start_time

                    # Update statistics
                    self._update_search_stats(provider_name, response, latency, success=True)

                    # Update active provider if this was successful
                    if self._active_search_provider != provider_name:
                        await self._perform_search_failover(
                            self._active_search_provider,
                            provider_name,
                            FailoverReason.MANUAL_SWITCH,
                        )

                    return response

                except Exception as e:
                    last_error = e
                    retry_count += 1

                    # Update error statistics
                    self._update_search_stats(provider_name, None, 0, success=False)

                    # Determine if we should retry or failover
                    if isinstance(e, SearchProviderError) and e.retry_after:
                        await asyncio.sleep(e.retry_after)
                    elif attempt < max_retries - 1:
                        await asyncio.sleep(min(2**attempt, 10))  # Exponential backoff

                    if attempt == max_retries - 1:
                        # Max retries reached for this provider
                        logger.error(
                            f"Search provider {provider_name} failed after {max_retries} attempts: {e}"
                        )
                        if fallback and len(providers) > 1:
                            # Try failover to next provider
                            next_idx = providers.index(provider_name) + 1
                            if next_idx < len(providers):
                                await self._perform_search_failover(
                                    provider_name,
                                    providers[next_idx],
                                    FailoverReason.API_ERROR,
                                    str(e),
                                )
                            break
                        else:
                            raise SearchProviderError(str(e), provider_name)

        # All providers failed
        raise SearchProviderError(
            f"All search providers failed after {retry_count} attempts. Last error: {last_error}",
            "all",
        )

    def _get_llm_provider_order(self, preferred: str = None) -> List[str]:
        """Get ordered list of LLM providers for failover"""
        if preferred and preferred in self.llm_providers:
            providers = [preferred]
            providers.extend([name for name in self.llm_providers.keys() if name != preferred])
        else:
            # Use active provider first, then others ordered by success rate
            providers = []
            if self._active_llm_provider:
                providers.append(self._active_llm_provider)

            # Add remaining providers sorted by success rate
            remaining = [
                name for name in self.llm_providers.keys() if name != self._active_llm_provider
            ]
            remaining.sort(key=lambda x: self.usage_stats["llm"][x]["success_rate"], reverse=True)
            providers.extend(remaining)

        return providers

    def _get_search_provider_order(self, preferred: str = None) -> List[str]:
        """Get ordered list of search providers for failover"""
        if preferred and preferred in self.search_providers:
            providers = [preferred]
            providers.extend([name for name in self.search_providers.keys() if name != preferred])
        else:
            # Use active provider first, then others ordered by success rate
            providers = []
            if self._active_search_provider:
                providers.append(self._active_search_provider)

            # Add remaining providers sorted by success rate
            remaining = [
                name
                for name in self.search_providers.keys()
                if name != self._active_search_provider
            ]
            remaining.sort(
                key=lambda x: self.usage_stats["search"][x]["success_rate"], reverse=True
            )
            providers.extend(remaining)

        return providers

    async def _perform_llm_failover(
        self,
        from_provider: str,
        to_provider: str,
        reason: FailoverReason,
        error_message: str = None,
    ):
        """Perform LLM provider failover"""
        if not self.failover_enabled or from_provider == to_provider:
            return

        start_time = time.time()
        self._active_llm_provider = to_provider

        # Record failover event
        event = FailoverEvent(
            timestamp=datetime.now(),
            from_provider=from_provider or "none",
            to_provider=to_provider,
            reason=reason,
            error_message=error_message,
            recovery_time_ms=int((time.time() - start_time) * 1000),
        )

        self.failover_history.append(event)
        if len(self.failover_history) > self.max_failover_history:
            self.failover_history.pop(0)

        logger.info(f"LLM failover: {from_provider} -> {to_provider} (reason: {reason.value})")

        # Notify callbacks
        for callback in self.on_failover_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Failover callback failed: {e}")

    async def _perform_search_failover(
        self,
        from_provider: str,
        to_provider: str,
        reason: FailoverReason,
        error_message: str = None,
    ):
        """Perform search provider failover"""
        if not self.failover_enabled or from_provider == to_provider:
            return

        start_time = time.time()
        self._active_search_provider = to_provider

        # Record failover event
        event = FailoverEvent(
            timestamp=datetime.now(),
            from_provider=from_provider or "none",
            to_provider=to_provider,
            reason=reason,
            error_message=error_message,
            recovery_time_ms=int((time.time() - start_time) * 1000),
        )

        self.failover_history.append(event)
        if len(self.failover_history) > self.max_failover_history:
            self.failover_history.pop(0)

        logger.info(f"Search failover: {from_provider} -> {to_provider} (reason: {reason.value})")

        # Notify callbacks
        for callback in self.on_failover_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Failover callback failed: {e}")

    def _update_llm_stats(
        self, provider_name: str, response: Optional[LLMResponse], latency: float, success: bool
    ):
        """Update LLM provider statistics"""
        stats = self.usage_stats["llm"][provider_name]
        stats["requests"] += 1
        stats["last_used"] = time.time()

        if success and response:
            stats["tokens"] += response.tokens_used
            stats["cost"] += response.cost
            # Update rolling average latency
            current_avg = stats["average_latency"]
            stats["average_latency"] = (current_avg * 0.9) + (latency * 1000 * 0.1)
        else:
            stats["errors"] += 1

        # Calculate success rate
        total_requests = stats["requests"]
        errors = stats["errors"]
        stats["success_rate"] = ((total_requests - errors) / total_requests) * 100

    def _update_search_stats(
        self, provider_name: str, response: Optional[SearchResponse], latency: float, success: bool
    ):
        """Update search provider statistics"""
        stats = self.usage_stats["search"][provider_name]
        stats["requests"] += 1
        stats["last_used"] = time.time()

        if success and response:
            stats["results"] += len(response.results)
            # Update rolling average latency
            current_avg = stats["average_latency"]
            stats["average_latency"] = (current_avg * 0.9) + (latency * 1000 * 0.1)
        else:
            stats["errors"] += 1

        # Calculate success rate
        total_requests = stats["requests"]
        errors = stats["errors"]
        stats["success_rate"] = ((total_requests - errors) / total_requests) * 100

    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all providers"""
        llm_status = {}
        for name, provider in self.llm_providers.items():
            health_result = await provider.health_check()
            llm_status[name] = {
                "available": health_result.status
                in [ProviderHealth.HEALTHY, ProviderHealth.DEGRADED],
                "health": health_result.status.value,
                "info": provider.get_model_info(),
                "stats": self.usage_stats["llm"][name],
                "is_active": name == self._active_llm_provider,
            }

        search_status = {}
        for name, provider in self.search_providers.items():
            health_result = await provider.health_check()
            search_status[name] = {
                "available": health_result.status
                in [ProviderHealth.HEALTHY, ProviderHealth.DEGRADED],
                "health": health_result.status.value,
                "info": provider.get_provider_info(),
                "stats": self.usage_stats["search"][name],
                "is_active": name == self._active_search_provider,
            }

        return {
            "llm_providers": llm_status,
            "search_providers": search_status,
            "active_providers": {
                "llm": self._active_llm_provider,
                "search": self._active_search_provider,
            },
            "failover_history": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "from_provider": event.from_provider,
                    "to_provider": event.to_provider,
                    "reason": event.reason.value,
                    "error_message": event.error_message,
                    "recovery_time_ms": event.recovery_time_ms,
                }
                for event in self.failover_history[-10:]  # Last 10 events
            ],
            "monitoring_enabled": self._monitoring_enabled,
            "failover_enabled": self.failover_enabled,
        }

    def add_failover_callback(self, callback: Callable[[FailoverEvent], None]):
        """Add callback to be notified of failover events"""
        self.on_failover_callbacks.append(callback)

    def enable_monitoring(self):
        """Enable health monitoring for all providers"""
        self._monitoring_enabled = True
        for name, provider in self.llm_providers.items():
            self._start_health_monitoring(provider, name, "llm")
        for name, provider in self.search_providers.items():
            self._start_health_monitoring(provider, name, "search")

    def disable_monitoring(self):
        """Disable health monitoring"""
        self._monitoring_enabled = False
        for task in self._health_check_tasks.values():
            task.cancel()
        self._health_check_tasks.clear()

    async def force_failover(self, provider_type: str, to_provider: str):
        """Force failover to a specific provider"""
        if provider_type == "llm" and to_provider in self.llm_providers:
            await self._perform_llm_failover(
                self._active_llm_provider, to_provider, FailoverReason.MANUAL_SWITCH
            )
        elif provider_type == "search" and to_provider in self.search_providers:
            await self._perform_search_failover(
                self._active_search_provider, to_provider, FailoverReason.MANUAL_SWITCH
            )
        else:
            raise ValueError(
                f"Invalid provider type or provider name: {provider_type}/{to_provider}"
            )

    async def cleanup(self):
        """Cleanup resources"""
        self.disable_monitoring()
        await asyncio.gather(
            *[task for task in self._health_check_tasks.values()], return_exceptions=True
        )
