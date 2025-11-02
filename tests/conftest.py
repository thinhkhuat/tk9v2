"""
Pytest configuration and shared fixtures for the multi-agent deep research system.
"""

import asyncio
import os
import shutil

# Add the project root to Python path
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from multi_agents.config.providers import (
    LLMConfig,
    LLMProvider,
    MultiProviderConfig,
    SearchConfig,
    SearchProvider,
)
from multi_agents.providers.base import LLMResponse, SearchResponse, SearchResult


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_env_vars():
    """Sample environment variables for testing."""
    return {
        "OPENAI_API_KEY": "sk-test_openai_key_12345",
        "GOOGLE_API_KEY": "test_google_key_67890",
        "TAVILY_API_KEY": "tvly-test_tavily_key_abcdef",
        "BRAVE_API_KEY": "test_brave_key_ghijkl",
        "PRIMARY_LLM_PROVIDER": "openai",
        "PRIMARY_LLM_MODEL": "gpt-4o",
        "PRIMARY_SEARCH_PROVIDER": "tavily",
        "FALLBACK_LLM_PROVIDER": "google_gemini",
        "FALLBACK_LLM_MODEL": "gemini-1.5-pro",
        "FALLBACK_SEARCH_PROVIDER": "brave",
        "LLM_STRATEGY": "fallback_on_error",
        "SEARCH_STRATEGY": "primary_only",
        "LLM_TEMPERATURE": "0.7",
        "LLM_MAX_TOKENS": "4000",
        "SEARCH_MAX_RESULTS": "10",
    }


@pytest.fixture
def mock_env_vars(sample_env_vars):
    """Mock environment variables for testing."""
    with patch.dict(os.environ, sample_env_vars, clear=False):
        yield sample_env_vars


@pytest.fixture
def sample_llm_config():
    """Sample LLM configuration for testing."""
    return LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        temperature=0.7,
        max_tokens=4000,
        api_key="sk-test_key",
    )


@pytest.fixture
def sample_search_config():
    """Sample search configuration for testing."""
    return SearchConfig(provider=SearchProvider.TAVILY, max_results=10, api_key="tvly-test_key")


@pytest.fixture
def sample_provider_config(sample_llm_config, sample_search_config):
    """Sample provider configuration for testing."""
    return MultiProviderConfig(
        primary_llm=sample_llm_config,
        primary_search=sample_search_config,
        fallback_llm=LLMConfig(
            provider=LLMProvider.GOOGLE_GEMINI,
            model="gemini-1.5-pro",
            temperature=0.7,
            max_tokens=4000,
            api_key="test_google_key",
        ),
        fallback_search=SearchConfig(
            provider=SearchProvider.BRAVE, max_results=10, api_key="test_brave_key"
        ),
        llm_strategy="fallback_on_error",
        search_strategy="primary_only",
    )


@pytest.fixture
def sample_llm_response():
    """Sample LLM response for testing."""
    return LLMResponse(
        content="This is a test response from the LLM provider.",
        model="gpt-4o",
        provider="openai",
        tokens_used=150,
        cost=0.0123,
        latency_ms=250,
    )


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return [
        SearchResult(
            title="Test Article 1",
            url="https://example.com/article1",
            content="This is the content of test article 1.",
            published_date="2024-01-15",
            score=0.95,
        ),
        SearchResult(
            title="Test Article 2",
            url="https://example.com/article2",
            content="This is the content of test article 2.",
            published_date="2024-01-14",
            score=0.87,
        ),
    ]


@pytest.fixture
def sample_search_response(sample_search_results):
    """Sample search response for testing."""
    return SearchResponse(
        query="test search query",
        results=sample_search_results,
        total_results=2,
        provider="tavily",
        search_time_ms=450,
    )


@pytest.fixture
def sample_task_config():
    """Sample task configuration for testing."""
    return {
        "query": "Test research query about artificial intelligence",
        "model": "gpt-4o",
        "max_sections": 3,
        "include_human_feedback": False,
        "follow_guidelines": True,
        "verbose": True,
        "publish_formats": {"markdown": True, "pdf": True, "docx": True},
        "guidelines": [
            "The report MUST be written in APA format",
            "Each sub section MUST include supporting sources using hyperlinks",
            "The report MUST be factual and objective",
        ],
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Mock OpenAI response content"
    mock_response.usage.total_tokens = 150
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    return mock_response


@pytest.fixture
def mock_gemini_response():
    """Mock Google Gemini API response."""
    mock_response = Mock()
    mock_response.text = "Mock Gemini response content"
    mock_response.usage_metadata.total_token_count = 140
    mock_response.usage_metadata.prompt_token_count = 90
    mock_response.usage_metadata.candidates_token_count = 50
    return mock_response


@pytest.fixture
def mock_tavily_response():
    """Mock Tavily API response."""
    return {
        "query": "test query",
        "follow_up_questions": None,
        "answer": "Mock Tavily answer",
        "images": [],
        "results": [
            {
                "title": "Mock Article 1",
                "url": "https://example.com/mock1",
                "content": "Mock content 1",
                "raw_content": "Mock raw content 1",
                "published_date": "2024-01-15T00:00:00Z",
                "author": "Mock Author 1",
                "score": 0.95,
            },
            {
                "title": "Mock Article 2",
                "url": "https://example.com/mock2",
                "content": "Mock content 2",
                "raw_content": "Mock raw content 2",
                "published_date": "2024-01-14T00:00:00Z",
                "author": "Mock Author 2",
                "score": 0.87,
            },
        ],
    }


@pytest.fixture
def mock_brave_response():
    """Mock Brave Search API response."""
    return {
        "query": {
            "original": "test query",
            "show_strict_warning": False,
            "altered": "test query",
            "safesearch": "moderate",
        },
        "mixed": {
            "type": "search",
            "main": [{"type": "web", "index": 0, "all": True}],
            "top": [],
            "side": [],
        },
        "type": "search",
        "web": {
            "type": "search",
            "results": [
                {
                    "title": "Mock Brave Article 1",
                    "url": "https://example.com/brave1",
                    "is_source_local": False,
                    "is_source_both": False,
                    "description": "Mock description 1",
                    "published": "2024-01-15T00:00:00Z",
                    "author": "Mock Author 1",
                    "language": "en",
                    "family_friendly": True,
                },
                {
                    "title": "Mock Brave Article 2",
                    "url": "https://example.com/brave2",
                    "is_source_local": False,
                    "is_source_both": False,
                    "description": "Mock description 2",
                    "published": "2024-01-14T00:00:00Z",
                    "author": "Mock Author 2",
                    "language": "en",
                    "family_friendly": True,
                },
            ],
            "family_friendly": True,
        },
    }


# Test utilities
class TestUtils:
    """Utility functions for testing."""

    @staticmethod
    def assert_llm_response_valid(response: LLMResponse):
        """Assert that an LLM response has valid structure."""
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert response.model is not None
        assert response.provider is not None
        assert isinstance(response.cost, (int, float))
        assert isinstance(response.tokens_used, int)

    @staticmethod
    def assert_search_response_valid(response: SearchResponse):
        """Assert that a search response has valid structure."""
        assert isinstance(response, SearchResponse)
        assert response.query is not None
        assert isinstance(response.results, list)
        assert response.provider is not None
        assert isinstance(response.total_results, int)
        assert isinstance(response.search_time_ms, (int, float))

        # Validate search results
        for result in response.results:
            assert isinstance(result, SearchResult)
            assert result.title is not None
            assert result.url is not None
            assert result.content is not None


@pytest.fixture
def test_utils():
    """Provide test utility functions."""
    return TestUtils


# Markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_api_keys: mark test as requiring real API keys")
    config.addinivalue_line("markers", "provider_test: mark test as testing provider functionality")
