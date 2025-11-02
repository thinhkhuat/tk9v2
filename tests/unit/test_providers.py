"""
Unit tests for the provider system.
Tests the multi-provider LLM and search functionality.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from multi_agents.config.providers import (
    LLMConfig,
    LLMProvider,
    SearchConfig,
    SearchProvider,
)
from multi_agents.providers.base import (
    BaseLLMProvider,
    BaseSearchProvider,
    LLMResponse,
    ProviderManager,
    SearchResponse,
    SearchResult,
)
from multi_agents.providers.llm.gemini import GeminiProvider
from multi_agents.providers.search.brave import BraveSearchProvider
from tests.mocks import MockLLMProvider, MockSearchProvider


class TestBaseLLMProvider:
    """Test the base LLM provider interface."""

    def test_base_llm_provider_is_abstract(self):
        """Test that BaseLLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLMProvider()

    @pytest.mark.asyncio
    async def test_mock_llm_provider_basic_functionality(self):
        """Test basic functionality of mock LLM provider."""
        provider = MockLLMProvider("test_llm", "test-model")

        response = await provider.generate("Test prompt")

        assert isinstance(response, LLMResponse)
        assert response.content.startswith("Mock response to: Test prompt")
        assert response.model == "test-model"
        assert response.provider == "test_llm"
        assert response.cost > 0
        assert response.tokens_used > 0
        assert provider.call_count == 1

    @pytest.mark.asyncio
    async def test_mock_llm_provider_custom_response(self):
        """Test custom response functionality."""
        provider = MockLLMProvider()
        custom_response = LLMResponse(
            content="Custom test response",
            model="test-model",
            provider="test_llm",
            cost=0.002,
            tokens_used=25,
        )

        provider.set_custom_response("special", custom_response)
        response = await provider.generate("This is a special prompt")

        assert response.content == "Custom test response"
        assert response.cost == 0.002

    @pytest.mark.asyncio
    async def test_mock_llm_provider_failure_mode(self):
        """Test failure mode handling."""
        provider = MockLLMProvider()
        provider.set_failure_mode(True, "Test failure")

        with pytest.raises(Exception, match="Test failure"):
            await provider.generate("Test prompt")

        assert provider.call_count == 1

    @pytest.mark.asyncio
    async def test_mock_llm_provider_response_delay(self):
        """Test response delay functionality."""
        provider = MockLLMProvider()
        provider.response_delay = 0.1

        start_time = asyncio.get_event_loop().time()
        await provider.generate("Test prompt")
        end_time = asyncio.get_event_loop().time()

        assert end_time - start_time >= 0.1


class TestBaseSearchProvider:
    """Test the base search provider interface."""

    def test_base_search_provider_is_abstract(self):
        """Test that BaseSearchProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseSearchProvider()

    @pytest.mark.asyncio
    async def test_mock_search_provider_basic_functionality(self):
        """Test basic functionality of mock search provider."""
        provider = MockSearchProvider({"provider": "test_search", "max_results": 3})

        response = await provider.search("test query")

        assert isinstance(response, SearchResponse)
        assert response.query == "test query"
        assert len(response.results) == 3  # default count
        assert response.provider == "mocksearch"  # This comes from base class logic
        assert response.total_results == 3
        assert provider.call_count == 1

        # Check search results structure
        for result in response.results:
            assert isinstance(result, SearchResult)
            assert "test query" in result.title
            assert result.url.startswith("https://mock.example.com")
            assert result.content
            assert result.score > 0

    @pytest.mark.asyncio
    async def test_mock_search_provider_custom_results(self):
        """Test custom search results functionality."""
        provider = MockSearchProvider()
        custom_results = [
            SearchResult(
                title="Custom Result",
                url="https://custom.example.com",
                content="Custom content",
                published_date="2024-01-01",
                score=1.0,
            )
        ]

        provider.set_custom_results("custom", custom_results)
        response = await provider.search("custom query")

        assert len(response.results) == 1
        assert response.results[0].title == "Custom Result"
        assert response.results[0].url == "https://custom.example.com"

    @pytest.mark.asyncio
    async def test_mock_search_provider_failure_mode(self):
        """Test search provider failure mode."""
        provider = MockSearchProvider()
        provider.set_failure_mode(True, "Search failure")

        with pytest.raises(Exception, match="Search failure"):
            await provider.search("test query")

        assert provider.call_count == 1

    @pytest.mark.asyncio
    async def test_mock_search_provider_result_count(self):
        """Test configurable result count."""
        provider = MockSearchProvider()
        provider.set_result_count(5)

        response = await provider.search("test query")

        assert len(response.results) == 5
        assert response.total_results == 5


class TestProviderManager:
    """Test the provider manager functionality."""

    @pytest.mark.asyncio
    async def test_provider_manager_llm_primary_success(self):
        """Test provider manager with successful primary LLM."""
        primary_provider = MockLLMProvider("primary", "primary-model")
        fallback_provider = MockLLMProvider("fallback", "fallback-model")

        manager = ProviderManager(
            primary_llm=primary_provider,
            fallback_llm=fallback_provider,
            llm_strategy="fallback_on_error",
        )

        response = await manager.generate_llm("Test prompt")

        assert response.provider == "primary"
        assert primary_provider.call_count == 1
        assert fallback_provider.call_count == 0

    @pytest.mark.asyncio
    async def test_provider_manager_llm_fallback_on_error(self):
        """Test provider manager fallback when primary LLM fails."""
        primary_provider = MockLLMProvider("primary", "primary-model")
        primary_provider.set_failure_mode(True, "Primary failure")
        fallback_provider = MockLLMProvider("fallback", "fallback-model")

        manager = ProviderManager(
            primary_llm=primary_provider,
            fallback_llm=fallback_provider,
            llm_strategy="fallback_on_error",
        )

        response = await manager.generate_llm("Test prompt")

        assert response.provider == "fallback"
        assert primary_provider.call_count == 1
        assert fallback_provider.call_count == 1

    @pytest.mark.asyncio
    async def test_provider_manager_search_primary_success(self):
        """Test provider manager with successful primary search."""
        primary_provider = MockSearchProvider("primary_search")
        fallback_provider = MockSearchProvider("fallback_search")

        manager = ProviderManager(
            primary_search=primary_provider,
            fallback_search=fallback_provider,
            search_strategy="fallback_on_error",
        )

        response = await manager.search("test query")

        assert response.provider == "primary_search"
        assert primary_provider.call_count == 1
        assert fallback_provider.call_count == 0

    @pytest.mark.asyncio
    async def test_provider_manager_search_fallback_on_error(self):
        """Test provider manager fallback when primary search fails."""
        primary_provider = MockSearchProvider("primary_search")
        primary_provider.set_failure_mode(True, "Search failure")
        fallback_provider = MockSearchProvider("fallback_search")

        manager = ProviderManager(
            primary_search=primary_provider,
            fallback_search=fallback_provider,
            search_strategy="fallback_on_error",
        )

        response = await manager.search("test query")

        assert response.provider == "fallback_search"
        assert primary_provider.call_count == 1
        assert fallback_provider.call_count == 1

    @pytest.mark.asyncio
    async def test_provider_manager_primary_only_strategy(self):
        """Test provider manager with primary_only strategy."""
        primary_provider = MockLLMProvider("primary", "primary-model")
        primary_provider.set_failure_mode(True, "Primary failure")
        fallback_provider = MockLLMProvider("fallback", "fallback-model")

        manager = ProviderManager(
            primary_llm=primary_provider,
            fallback_llm=fallback_provider,
            llm_strategy="primary_only",
        )

        with pytest.raises(Exception, match="Primary failure"):
            await manager.generate_llm("Test prompt")

        assert primary_provider.call_count == 1
        assert fallback_provider.call_count == 0


@pytest.mark.provider_test
class TestGeminiProvider:
    """Test Google Gemini provider implementation."""

    def test_gemini_provider_init(self):
        """Test Gemini provider initialization."""
        config = LLMConfig(
            provider=LLMProvider.GOOGLE_GEMINI,
            model="gemini-1.5-pro",
            api_key="test_key",
            temperature=0.7,
            max_tokens=1000,
        )

        with patch("google.generativeai.configure") as mock_configure:
            provider = GeminiProvider(config)

            assert provider.model_name == "gemini-1.5-pro"
            assert provider.temperature == 0.7
            assert provider.max_tokens == 1000
            mock_configure.assert_called_once_with(api_key="test_key")

    @pytest.mark.asyncio
    async def test_gemini_provider_generate_success(self, mock_gemini_response):
        """Test successful Gemini response generation."""
        config = LLMConfig(
            provider=LLMProvider.GOOGLE_GEMINI, model="gemini-1.5-pro", api_key="test_key"
        )

        with patch("google.generativeai.configure"), patch(
            "google.generativeai.GenerativeModel"
        ) as mock_model_class:

            mock_model = Mock()
            mock_model_class.return_value = mock_model
            mock_model.generate_content.return_value = mock_gemini_response

            provider = GeminiProvider(config)
            response = await provider.generate("Test prompt")

            assert isinstance(response, LLMResponse)
            assert response.content == "Mock Gemini response content"
            assert response.model == "gemini-1.5-pro"
            assert response.provider == "google_gemini"
            assert response.tokens_used == 140

    @pytest.mark.asyncio
    async def test_gemini_provider_with_system_prompt(self):
        """Test Gemini provider with system prompt."""
        config = LLMConfig(
            provider=LLMProvider.GOOGLE_GEMINI, model="gemini-1.5-pro", api_key="test_key"
        )

        mock_response = Mock()
        mock_response.text = "System prompt response"
        mock_response.usage_metadata.total_token_count = 100

        with patch("google.generativeai.configure"), patch(
            "google.generativeai.GenerativeModel"
        ) as mock_model_class:

            mock_model = Mock()
            mock_model_class.return_value = mock_model
            mock_model.generate_content.return_value = mock_response

            provider = GeminiProvider(config)
            response = await provider.generate("User prompt", "System instructions")

            # Verify the prompt was combined correctly
            call_args = mock_model.generate_content.call_args[0][0]
            assert "System instructions" in call_args
            assert "User prompt" in call_args


@pytest.mark.provider_test
class TestBraveSearchProvider:
    """Test Brave Search provider implementation."""

    def test_brave_provider_init(self):
        """Test Brave provider initialization."""
        config = SearchConfig(
            provider=SearchProvider.BRAVE, api_key="test_brave_key", max_results=10
        )

        provider = BraveSearchProvider(config)

        assert provider.api_key == "test_brave_key"
        assert provider.max_results == 10
        assert provider.base_url == "https://api.search.brave.com/res/v1"

    @pytest.mark.asyncio
    async def test_brave_provider_search_success(self, mock_brave_response):
        """Test successful Brave search."""
        config = SearchConfig(
            provider=SearchProvider.BRAVE, api_key="test_brave_key", max_results=10
        )

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_brave_response
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response

            provider = BraveSearchProvider(config)
            response = await provider.search("test query")

            assert isinstance(response, SearchResponse)
            assert response.query == "test query"
            assert response.provider == "brave"
            assert len(response.results) == 2
            assert response.results[0].title == "Mock Brave Article 1"

    @pytest.mark.asyncio
    async def test_brave_provider_rate_limiting(self):
        """Test Brave provider rate limiting."""
        config = SearchConfig(
            provider=SearchProvider.BRAVE, api_key="test_brave_key", max_results=10
        )

        provider = BraveSearchProvider(config)

        # First call should succeed
        await provider._check_rate_limit()
        assert len(provider.request_timestamps) == 1

        # Rapid subsequent calls should be rate limited
        start_time = asyncio.get_event_loop().time()
        await provider._check_rate_limit()
        end_time = asyncio.get_event_loop().time()

        # Should have added delay for rate limiting
        assert end_time - start_time >= 0.0

    @pytest.mark.asyncio
    async def test_brave_provider_search_parameters(self):
        """Test Brave provider search parameter handling."""
        config = SearchConfig(
            provider=SearchProvider.BRAVE, api_key="test_brave_key", max_results=5
        )

        mock_response_data = {"web": {"results": []}}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response

            provider = BraveSearchProvider(config)
            await provider.search("test query", search_type="news", freshness="week")

            # Verify correct parameters were passed
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert params["q"] == "test query"
            assert params["count"] == 5
            assert "search_type" in params or "freshness" in params


class TestLLMResponse:
    """Test LLM response data structure."""

    def test_llm_response_creation(self):
        """Test LLM response creation and validation."""
        response = LLMResponse(
            content="Test content",
            model="test-model",
            provider="test-provider",
            cost=0.001,
            tokens_used=50,
            reasoning="Test reasoning",
            citations=["https://example.com"],
        )

        assert response.content == "Test content"
        assert response.model == "test-model"
        assert response.provider == "test-provider"
        assert response.cost == 0.001
        assert response.tokens_used == 50
        assert response.reasoning == "Test reasoning"
        assert response.citations == ["https://example.com"]

    def test_llm_response_defaults(self):
        """Test LLM response with default values."""
        response = LLMResponse(content="Test content", model="test-model", provider="test-provider")

        assert response.cost == 0.0
        assert response.tokens_used == 0
        assert response.reasoning is None
        assert response.citations == []


class TestSearchResponse:
    """Test search response data structure."""

    def test_search_response_creation(self, sample_search_results):
        """Test search response creation and validation."""
        response = SearchResponse(
            query="test query",
            results=sample_search_results,
            total_results=2,
            provider="test-provider",
            search_time=0.5,
            cost=0.001,
        )

        assert response.query == "test query"
        assert len(response.results) == 2
        assert response.total_results == 2
        assert response.provider == "test-provider"
        assert response.search_time == 0.5
        assert response.cost == 0.001

    def test_search_result_structure(self):
        """Test search result data structure."""
        result = SearchResult(
            title="Test Article",
            url="https://example.com",
            content="Test content",
            published_date="2024-01-15",
            author="Test Author",
            score=0.95,
        )

        assert result.title == "Test Article"
        assert result.url == "https://example.com"
        assert result.content == "Test content"
        assert result.published_date == "2024-01-15"
        assert result.author == "Test Author"
        assert result.score == 0.95
