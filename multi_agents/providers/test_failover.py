"""
Comprehensive Test Suite for Enhanced Provider Failover System
Tests various failover scenarios, race conditions, and error recovery mechanisms
"""

import asyncio
import logging
import time
from unittest.mock import AsyncMock, patch

import pytest

from .enhanced_base import (
    EnhancedProviderManager,
    FailoverReason,
    LLMProviderError,
    ProviderHealth,
    SearchProviderError,
)
from .failover_integration import FailoverIntegration, managed_failover_system

logger = logging.getLogger(__name__)


class MockLLMProvider:
    """Mock LLM provider for testing"""

    def __init__(self, name: str, should_fail: bool = False, fail_after: int = 0):
        self.name = name
        self.provider_name = name
        self.should_fail = should_fail
        self.fail_after = fail_after
        self.call_count = 0
        self._health_status = ProviderHealth.HEALTHY
        self.config = {"model": "test-model"}

    async def generate(self, prompt: str, **kwargs):
        self.call_count += 1

        if self.should_fail or (self.fail_after > 0 and self.call_count > self.fail_after):
            raise LLMProviderError("Mock LLM failure", self.name)

        from ..providers.enhanced_base import LLMResponse

        return LLMResponse(
            content=f"Mock response from {self.name}",
            model="test-model",
            provider=self.name,
            tokens_used=100,
            cost=0.01,
            latency_ms=100,
        )

    async def health_check(self):
        from ..providers.enhanced_base import HealthCheckResult

        status = ProviderHealth.UNHEALTHY if self.should_fail else ProviderHealth.HEALTHY
        return HealthCheckResult(
            provider=self.name,
            status=status,
            response_time_ms=50,
            error_message="Mock failure" if self.should_fail else None,
        )

    async def is_healthy(self, force_check=False):
        return not self.should_fail

    def get_health_status(self):
        return ProviderHealth.UNHEALTHY if self.should_fail else ProviderHealth.HEALTHY


class MockSearchProvider:
    """Mock search provider for testing"""

    def __init__(self, name: str, should_fail: bool = False, fail_after: int = 0):
        self.name = name
        self.provider_name = name
        self.should_fail = should_fail
        self.fail_after = fail_after
        self.call_count = 0
        self._health_status = ProviderHealth.HEALTHY
        self.config = {"max_results": 10}

    async def search(self, query: str, **kwargs):
        self.call_count += 1

        if self.should_fail or (self.fail_after > 0 and self.call_count > self.fail_after):
            raise SearchProviderError("Mock search failure", self.name)

        from ..providers.enhanced_base import SearchResponse, SearchResult

        return SearchResponse(
            results=[
                SearchResult(
                    title=f"Mock result from {self.name}",
                    url="https://example.com",
                    content=f"Mock content from {self.name}",
                )
            ],
            query=query,
            provider=self.name,
            total_results=1,
            search_time_ms=100,
        )

    async def health_check(self):
        from ..providers.enhanced_base import HealthCheckResult

        status = ProviderHealth.UNHEALTHY if self.should_fail else ProviderHealth.HEALTHY
        return HealthCheckResult(
            provider=self.name,
            status=status,
            response_time_ms=50,
            error_message="Mock failure" if self.should_fail else None,
        )

    async def is_healthy(self, force_check=False):
        return not self.should_fail

    def get_health_status(self):
        return ProviderHealth.UNHEALTHY if self.should_fail else ProviderHealth.HEALTHY


class TestEnhancedProviderManager:
    """Test cases for EnhancedProviderManager"""

    def setup_method(self):
        """Setup for each test method"""
        self.manager = EnhancedProviderManager()
        self.failover_events = []

        # Add callback to track failover events
        self.manager.add_failover_callback(self.failover_events.append)

    def test_provider_registration(self):
        """Test provider registration"""
        llm_provider = MockLLMProvider("test-llm")
        search_provider = MockSearchProvider("test-search")

        self.manager.register_llm_provider("primary", llm_provider, is_primary=True)
        self.manager.register_search_provider("primary", search_provider, is_primary=True)

        assert "primary" in self.manager.llm_providers
        assert "primary" in self.manager.search_providers
        assert self.manager._active_llm_provider == "primary"
        assert self.manager._active_search_provider == "primary"

    @pytest.mark.asyncio
    async def test_basic_llm_generation(self):
        """Test basic LLM generation without failover"""
        llm_provider = MockLLMProvider("test-llm")
        self.manager.register_llm_provider("primary", llm_provider, is_primary=True)

        response = await self.manager.llm_generate("test prompt")

        assert response.content == "Mock response from test-llm"
        assert response.provider == "test-llm"
        assert llm_provider.call_count == 1

    @pytest.mark.asyncio
    async def test_llm_failover_on_error(self):
        """Test LLM failover when primary provider fails"""
        primary_provider = MockLLMProvider("primary", should_fail=True)
        fallback_provider = MockLLMProvider("fallback")

        self.manager.register_llm_provider("primary", primary_provider, is_primary=True)
        self.manager.register_llm_provider("fallback", fallback_provider)

        response = await self.manager.llm_generate("test prompt", fallback=True)

        assert response.content == "Mock response from fallback"
        assert response.provider == "fallback"
        assert primary_provider.call_count > 0
        assert fallback_provider.call_count == 1
        assert len(self.failover_events) == 1
        assert self.failover_events[0].reason == FailoverReason.API_ERROR

    @pytest.mark.asyncio
    async def test_search_failover_on_error(self):
        """Test search failover when primary provider fails"""
        primary_provider = MockSearchProvider("primary", should_fail=True)
        fallback_provider = MockSearchProvider("fallback")

        self.manager.register_search_provider("primary", primary_provider, is_primary=True)
        self.manager.register_search_provider("fallback", fallback_provider)

        response = await self.manager.search_query("test query", fallback=True)

        assert response.results[0].title == "Mock result from fallback"
        assert response.provider == "fallback"
        assert primary_provider.call_count > 0
        assert fallback_provider.call_count == 1
        assert len(self.failover_events) == 1
        assert self.failover_events[0].reason == FailoverReason.API_ERROR

    @pytest.mark.asyncio
    async def test_retry_logic(self):
        """Test retry logic before failover"""
        # Provider that fails first 2 attempts then succeeds
        provider = MockLLMProvider("test", fail_after=2)
        provider.fail_after = 2

        def mock_generate(prompt, **kwargs):
            if provider.call_count < 2:
                raise LLMProviderError("Temporary failure", "test")
            return asyncio.create_task(provider.generate(prompt, **kwargs))

        provider.generate = mock_generate
        self.manager.register_llm_provider("primary", provider, is_primary=True)

        # This should succeed after retries without failover
        response = await self.manager.llm_generate("test prompt", max_retries=3)
        assert provider.call_count >= 2

    @pytest.mark.asyncio
    async def test_concurrent_failover_safety(self):
        """Test that concurrent failovers are handled safely"""
        primary_provider = MockLLMProvider("primary", should_fail=True)
        fallback_provider = MockLLMProvider("fallback")

        self.manager.register_llm_provider("primary", primary_provider, is_primary=True)
        self.manager.register_llm_provider("fallback", fallback_provider)

        # Start multiple concurrent requests
        tasks = []
        for i in range(10):
            task = self.manager.llm_generate(f"test prompt {i}", fallback=True)
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # All should succeed using fallback
        assert all(r.provider == "fallback" for r in responses)
        assert all(r.content == "Mock response from fallback" for r in responses)

        # Should have only one failover event despite multiple concurrent requests
        assert len(self.failover_events) == 1

    @pytest.mark.asyncio
    async def test_health_check_based_failover(self):
        """Test failover based on health checks"""
        primary_provider = MockLLMProvider("primary")
        fallback_provider = MockLLMProvider("fallback")

        self.manager.register_llm_provider("primary", primary_provider, is_primary=True)
        self.manager.register_llm_provider("fallback", fallback_provider)

        # First request should succeed
        response1 = await self.manager.llm_generate("test prompt 1")
        assert response1.provider == "primary"

        # Mark primary as unhealthy
        primary_provider.should_fail = True

        # Next request should failover to fallback
        response2 = await self.manager.llm_generate("test prompt 2", fallback=True)
        assert response2.provider == "fallback"

    @pytest.mark.asyncio
    async def test_comprehensive_status(self):
        """Test comprehensive status reporting"""
        llm_provider = MockLLMProvider("test-llm")
        search_provider = MockSearchProvider("test-search")

        self.manager.register_llm_provider("primary", llm_provider, is_primary=True)
        self.manager.register_search_provider("primary", search_provider, is_primary=True)

        status = await self.manager.get_comprehensive_status()

        assert "llm_providers" in status
        assert "search_providers" in status
        assert "active_providers" in status
        assert "failover_history" in status

        assert status["active_providers"]["llm"] == "primary"
        assert status["active_providers"]["search"] == "primary"

    @pytest.mark.asyncio
    async def test_forced_failover(self):
        """Test manual failover triggering"""
        primary_provider = MockLLMProvider("primary")
        fallback_provider = MockLLMProvider("fallback")

        self.manager.register_llm_provider("primary", primary_provider, is_primary=True)
        self.manager.register_llm_provider("fallback", fallback_provider)

        # Force failover to fallback
        await self.manager.force_failover("llm", "fallback")

        # Next request should use fallback
        response = await self.manager.llm_generate("test prompt")
        assert response.provider == "fallback"

        # Should have one manual failover event
        assert len(self.failover_events) == 1
        assert self.failover_events[0].reason == FailoverReason.MANUAL_SWITCH

    async def test_cleanup(self):
        """Test proper cleanup of resources"""
        llm_provider = MockLLMProvider("test-llm")
        self.manager.register_llm_provider("primary", llm_provider, is_primary=True)

        # Enable monitoring
        self.manager.enable_monitoring()
        assert self.manager._monitoring_enabled == True

        # Cleanup
        await self.manager.cleanup()

        # Monitoring should be disabled
        assert self.manager._monitoring_enabled == False


class TestFailoverIntegration:
    """Test cases for FailoverIntegration"""

    @pytest.mark.asyncio
    async def test_managed_failover_context(self):
        """Test managed failover system context manager"""
        async with managed_failover_system(enable_monitoring=False) as (integration, success):
            # Integration should be initialized
            if success:
                assert integration.is_initialized == True
                assert integration.fallback_mode == False
            else:
                # If initialization failed, should be in fallback mode
                assert integration.fallback_mode == True

        # After context exit, should be cleaned up
        assert integration.is_initialized == False

    @pytest.mark.asyncio
    async def test_integration_llm_response(self):
        """Test LLM response through integration layer"""
        integration = FailoverIntegration()

        # Test fallback mode
        integration.fallback_mode = True

        with patch.object(integration, "_fallback_llm_generate") as mock_fallback:
            mock_fallback.return_value = AsyncMock()

            await integration.get_llm_response("test prompt")
            mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_integration_search_response(self):
        """Test search response through integration layer"""
        integration = FailoverIntegration()

        # Test fallback mode
        integration.fallback_mode = True

        with patch.object(integration, "_fallback_search_query") as mock_fallback:
            mock_fallback.return_value = AsyncMock()

            await integration.get_search_results("test query")
            mock_fallback.assert_called_once()


class TestRaceConditions:
    """Test cases for race conditions and thread safety"""

    @pytest.mark.asyncio
    async def test_concurrent_provider_registration(self):
        """Test concurrent provider registration safety"""
        manager = EnhancedProviderManager()

        async def register_provider(name: str):
            provider = MockLLMProvider(f"llm-{name}")
            manager.register_llm_provider(name, provider)

        # Register providers concurrently
        tasks = [register_provider(f"provider-{i}") for i in range(10)]
        await asyncio.gather(*tasks)

        # All providers should be registered
        assert len(manager.llm_providers) == 10

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Test concurrent health checks don't interfere"""
        provider = MockLLMProvider("test")

        async def check_health():
            return await provider.is_healthy(force_check=True)

        # Run multiple health checks concurrently
        tasks = [check_health() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All should return the same result
        assert all(r == True for r in results)

    @pytest.mark.asyncio
    async def test_failover_under_load(self):
        """Test failover behavior under high load"""
        manager = EnhancedProviderManager()
        failover_events = []
        manager.add_failover_callback(failover_events.append)

        # Primary fails after 5 requests
        primary_provider = MockLLMProvider("primary", fail_after=5)
        fallback_provider = MockLLMProvider("fallback")

        manager.register_llm_provider("primary", primary_provider, is_primary=True)
        manager.register_llm_provider("fallback", fallback_provider)

        # Generate high load
        tasks = []
        for i in range(20):
            task = manager.llm_generate(f"test prompt {i}", fallback=True, max_retries=2)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Some should succeed with primary, some with fallback
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) > 0

        # Should have at least one failover event
        assert len(failover_events) >= 1


class TestErrorRecovery:
    """Test cases for error recovery mechanisms"""

    @pytest.mark.asyncio
    async def test_provider_recovery_after_failure(self):
        """Test provider recovery after temporary failure"""
        manager = EnhancedProviderManager()
        provider = MockLLMProvider("primary")

        manager.register_llm_provider("primary", provider, is_primary=True)

        # First request should succeed
        response1 = await manager.llm_generate("test 1")
        assert response1.provider == "primary"

        # Simulate temporary failure
        provider.should_fail = True

        # Request during failure should fail
        with pytest.raises(LLMProviderError):
            await manager.llm_generate("test 2", fallback=False)

        # Provider recovers
        provider.should_fail = False

        # Request after recovery should succeed
        response3 = await manager.llm_generate("test 3")
        assert response3.provider == "primary"

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff in retry logic"""
        provider = MockLLMProvider("test")

        call_times = []
        original_generate = provider.generate

        async def timed_generate(prompt, **kwargs):
            call_times.append(time.time())
            if len(call_times) < 3:
                raise LLMProviderError("Temporary failure", "test")
            return await original_generate(prompt, **kwargs)

        provider.generate = timed_generate

        manager = EnhancedProviderManager()
        manager.register_llm_provider("primary", provider, is_primary=True)

        start_time = time.time()
        await manager.llm_generate("test", max_retries=3, fallback=False)

        # Should have increasing delays between calls
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            assert delay2 > delay1


def run_comprehensive_tests():
    """Run comprehensive test suite"""
    logger.info("Starting comprehensive failover system tests...")

    # Configure pytest to run our tests
    pytest_args = [
        __file__,
        "-v",  # Verbose output
        "-s",  # Don't capture stdout
        "--tb=short",  # Short traceback format
        "-k",
        "test_",  # Run only test methods
    ]

    result = pytest.main(pytest_args)

    if result == 0:
        logger.info("✅ All failover system tests passed!")
    else:
        logger.error("❌ Some failover system tests failed!")

    return result == 0


async def run_integration_tests():
    """Run integration tests with real components"""
    logger.info("Starting integration tests...")

    try:
        # Test 1: Basic initialization
        async with managed_failover_system(enable_monitoring=False) as (integration, success):
            logger.info(f"Integration initialized: {success}")

            if success:
                # Test 2: Provider status
                status = await integration.get_comprehensive_status()
                logger.info(
                    f"Provider status obtained: {len(status.get('llm_providers', {})) + len(status.get('search_providers', {}))}"
                )

                # Test 3: Health checks
                health_results = await integration.health_check_all_providers()
                logger.info(
                    f"Health check completed for {len(health_results.get('llm_providers', {})) + len(health_results.get('search_providers', {}))}"
                )

        logger.info("✅ Integration tests completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Integration tests failed: {e}")
        return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run unit tests
    unit_test_success = run_comprehensive_tests()

    # Run integration tests
    integration_test_success = asyncio.run(run_integration_tests())

    if unit_test_success and integration_test_success:
        print("\n🎉 All failover system tests passed successfully!")
        exit(0)
    else:
        print("\n💥 Some tests failed. Please check the logs above.")
        exit(1)
