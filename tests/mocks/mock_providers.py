"""
Mock provider implementations for testing the multi-provider system.
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional

from multi_agents.providers.base import (
    BaseLLMProvider,
    BaseSearchProvider,
    LLMResponse,
    SearchResponse,
    SearchResult,
)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing purposes."""

    def __init__(self, provider_name: str = "mock_llm", model_name: str = "mock-model"):
        self.provider_name = provider_name
        self.model_name = model_name
        self.call_count = 0
        self.call_history = []
        self.should_fail = False
        self.fail_message = "Mock provider failure"
        self.response_delay = 0.0
        self.custom_responses = {}

    async def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> LLMResponse:
        """Generate a mock response."""
        self.call_count += 1
        call_data = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "kwargs": kwargs,
            "timestamp": asyncio.get_event_loop().time(),
        }
        self.call_history.append(call_data)

        if self.should_fail:
            raise Exception(self.fail_message)

        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)

        # Check for custom responses based on prompt content
        for key, response in self.custom_responses.items():
            if key.lower() in prompt.lower():
                return response

        # Default mock response
        return LLMResponse(
            content=f"Mock response to: {prompt[:50]}...",
            model=self.model_name,
            provider=self.provider_name,
            tokens_used=len(prompt.split()) + 50,
            cost=0.001 * len(prompt.split()),
            latency_ms=100,
        )

    def set_custom_response(self, trigger_text: str, response: LLMResponse):
        """Set a custom response for prompts containing specific text."""
        self.custom_responses[trigger_text] = response

    def set_failure_mode(self, should_fail: bool, message: str = "Mock provider failure"):
        """Configure the provider to fail for testing error handling."""
        self.should_fail = should_fail
        self.fail_message = message

    async def generate_stream(
        self, prompt: str, system_prompt: str = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming mock response."""
        self.call_count += 1
        call_data = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "kwargs": kwargs,
            "timestamp": asyncio.get_event_loop().time(),
            "streaming": True,
        }
        self.call_history.append(call_data)

        if self.should_fail:
            raise Exception(self.fail_message)

        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)

        # Stream mock response in chunks
        response_text = f"Mock streaming response to: {prompt[:50]}..."
        words = response_text.split()

        for word in words:
            yield word + " "
            await asyncio.sleep(0.01)  # Small delay between words

    def estimate_cost(self, prompt: str, response: str = "") -> float:
        """Estimate cost for the API call."""
        prompt_tokens = len(prompt.split())
        response_tokens = len(response.split()) if response else 50
        return (prompt_tokens * 0.0001) + (response_tokens * 0.0002)  # Mock pricing

    def validate_config(self) -> List[str]:
        """Validate provider configuration."""
        issues = []
        if not self.provider_name:
            issues.append("Provider name is required")
        if not self.model_name:
            issues.append("Model name is required")
        return issues

    def reset_stats(self):
        """Reset call statistics."""
        self.call_count = 0
        self.call_history = []


class MockSearchProvider(BaseSearchProvider):
    """Mock search provider for testing purposes."""

    def __init__(self, config: Dict[str, Any] = None):
        # Initialize with config like the base class expects
        super().__init__(config or {"max_results": 3})
        self.call_count = 0
        self.call_history = []
        self.should_fail = False
        self.fail_message = "Mock search provider failure"
        self.response_delay = 0.0
        self.custom_results = {}
        self.default_result_count = config.get("max_results", 3) if config else 3

    async def search(self, query: str, **kwargs) -> SearchResponse:
        """Perform a mock search."""
        self.call_count += 1
        call_data = {"query": query, "kwargs": kwargs, "timestamp": asyncio.get_event_loop().time()}
        self.call_history.append(call_data)

        if self.should_fail:
            raise Exception(self.fail_message)

        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)

        # Check for custom results based on query content
        for key, results in self.custom_results.items():
            if key.lower() in query.lower():
                return SearchResponse(
                    query=query,
                    results=results,
                    total_results=len(results),
                    provider=self.provider_name,
                    search_time_ms=100,
                )

        # Generate default mock results
        results = []
        for i in range(self.default_result_count):
            results.append(
                SearchResult(
                    title=f"Mock Article {i + 1} for '{query}'",
                    url=f"https://mock.example.com/article{i + 1}",
                    content=f"Mock content for article {i + 1} related to query: {query}",
                    published_date=f"2024-01-{15 - i:02d}",
                    score=0.9 - (i * 0.1),
                )
            )

        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            provider=self.provider_name,
            search_time_ms=100,
        )

    def set_custom_results(self, trigger_text: str, results: List[SearchResult]):
        """Set custom search results for queries containing specific text."""
        self.custom_results[trigger_text] = results

    def set_failure_mode(self, should_fail: bool, message: str = "Mock search provider failure"):
        """Configure the provider to fail for testing error handling."""
        self.should_fail = should_fail
        self.fail_message = message

    def set_result_count(self, count: int):
        """Set the number of default mock results to return."""
        self.default_result_count = count

    async def news_search(self, query: str, **kwargs) -> SearchResponse:
        """Perform a mock news search."""
        # Use the same logic as regular search but with news-specific mock data
        results = []
        for i in range(min(self.default_result_count, 3)):  # Fewer news results
            results.append(
                SearchResult(
                    title=f"Mock News Article {i + 1} for '{query}'",
                    url=f"https://news.mock.example.com/article{i + 1}",
                    content=f"Breaking news content for article {i + 1} related to query: {query}",
                    published_date=f"2024-01-{15 - i:02d}",
                    score=0.95 - (i * 0.05),
                )
            )

        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            provider=self.provider_name + "_news",
            search_time_ms=80,
        )

    def validate_config(self) -> List[str]:
        """Validate provider configuration."""
        issues = []
        if not self.provider_name:
            issues.append("Provider name is required")
        if self.default_result_count <= 0:
            issues.append("Result count must be positive")
        return issues

    def reset_stats(self):
        """Reset call statistics."""
        self.call_count = 0
        self.call_history = []


class MockProviderFactory:
    """Mock provider factory for testing provider creation and management."""

    def __init__(self):
        self.llm_providers = {}
        self.search_providers = {}
        self.creation_history = []

    def create_llm_provider(self, provider_type: str, config: Dict[str, Any]) -> MockLLMProvider:
        """Create a mock LLM provider."""
        provider = MockLLMProvider(provider_type, config.get("model", "mock-model"))
        self.llm_providers[provider_type] = provider
        self.creation_history.append({"type": "llm", "provider": provider_type, "config": config})
        return provider

    def create_search_provider(
        self, provider_type: str, config: Dict[str, Any]
    ) -> MockSearchProvider:
        """Create a mock search provider."""
        provider = MockSearchProvider(provider_type)
        provider.set_result_count(config.get("max_results", 3))
        self.search_providers[provider_type] = provider
        self.creation_history.append(
            {"type": "search", "provider": provider_type, "config": config}
        )
        return provider

    def get_llm_provider(self, provider_type: str) -> Optional[MockLLMProvider]:
        """Get a created LLM provider."""
        return self.llm_providers.get(provider_type)

    def get_search_provider(self, provider_type: str) -> Optional[MockSearchProvider]:
        """Get a created search provider."""
        return self.search_providers.get(provider_type)

    def reset(self):
        """Reset all providers and history."""
        self.llm_providers = {}
        self.search_providers = {}
        self.creation_history = []


# Test helper functions
def create_sample_llm_responses() -> Dict[str, LLMResponse]:
    """Create sample LLM responses for different scenarios."""
    return {
        "research_query": LLMResponse(
            content="Based on current research, artificial intelligence shows significant promise in healthcare, finance, and education sectors. Key developments include machine learning algorithms, natural language processing, and computer vision technologies.",
            model="mock-research-model",
            provider="mock_llm",
            tokens_used=125,
            cost=0.005,
            latency_ms=300,
        ),
        "writing_task": LLMResponse(
            content="# Research Report\n\nThis report examines the current state of artificial intelligence research and its applications across various industries.\n\n## Executive Summary\n\nAI technologies continue to evolve rapidly...",
            model="mock-writing-model",
            provider="mock_llm",
            tokens_used=200,
            cost=0.008,
            latency_ms=400,
        ),
        "error_scenario": LLMResponse(
            content="I apologize, but I encountered an error processing your request.",
            model="mock-error-model",
            provider="mock_llm",
            tokens_used=25,
            cost=0.001,
            latency_ms=100,
        ),
    }


def create_sample_search_results() -> Dict[str, List[SearchResult]]:
    """Create sample search results for different scenarios."""
    return {
        "ai_research": [
            SearchResult(
                title="Advances in Artificial Intelligence Research 2024",
                url="https://example.com/ai-advances-2024",
                content="Recent breakthroughs in AI research include improved language models, computer vision systems, and autonomous decision-making algorithms.",
                published_date="2024-01-15",
                score=0.95,
            ),
            SearchResult(
                title="Machine Learning Applications in Healthcare",
                url="https://example.com/ml-healthcare",
                content="Healthcare providers are increasingly adopting machine learning technologies for diagnostic imaging, drug discovery, and personalized treatment plans.",
                published_date="2024-01-10",
                score=0.88,
            ),
        ],
        "technology_trends": [
            SearchResult(
                title="Top Technology Trends for 2024",
                url="https://example.com/tech-trends-2024",
                content="Emerging technology trends include quantum computing, edge computing, sustainable tech, and advanced AI systems.",
                published_date="2024-01-12",
                score=0.92,
            )
        ],
        "empty_results": [],
    }


# Mock agent implementations for testing
class MockAgent:
    """Base mock agent for testing agent interactions."""

    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.agent_type = agent_type
        self.call_count = 0
        self.execution_history = []
        self.should_fail = False
        self.fail_message = "Mock agent failure"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mock agent execution."""
        self.call_count += 1
        execution_data = {"input_state": state.copy(), "timestamp": asyncio.get_event_loop().time()}

        if self.should_fail:
            execution_data["status"] = "failed"
            execution_data["error"] = self.fail_message
            self.execution_history.append(execution_data)
            raise Exception(self.fail_message)

        # Mock processing
        output_state = state.copy()
        output_state[f"{self.name}_output"] = f"Mock output from {self.name}"
        output_state[f"{self.name}_status"] = "completed"

        execution_data["output_state"] = output_state
        execution_data["status"] = "success"
        self.execution_history.append(execution_data)

        return output_state

    def set_failure_mode(self, should_fail: bool, message: str = "Mock agent failure"):
        """Configure the agent to fail for testing error handling."""
        self.should_fail = should_fail
        self.fail_message = message

    def reset_stats(self):
        """Reset execution statistics."""
        self.call_count = 0
        self.execution_history = []


class MockResearchAgent(MockAgent):
    """Mock research agent for testing research workflows."""

    def __init__(self):
        super().__init__("research", "researcher")

    async def run_initial_research(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mock initial research execution."""
        output_state = await self.run(state)
        output_state["initial_research"] = "Mock initial research results"
        output_state["research_sources"] = [
            "https://example.com/source1",
            "https://example.com/source2",
        ]
        return output_state


class MockWriterAgent(MockAgent):
    """Mock writer agent for testing writing workflows."""

    def __init__(self):
        super().__init__("writer", "writer")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mock writing execution."""
        output_state = await super().run(state)
        output_state["final_report"] = (
            "# Mock Research Report\n\nThis is a mock research report generated for testing purposes."
        )
        output_state["report_sections"] = ["Introduction", "Main Content", "Conclusion"]
        return output_state


class MockEditorAgent(MockAgent):
    """Mock editor agent for testing editing workflows."""

    def __init__(self):
        super().__init__("editor", "editor")

    async def plan_research(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mock research planning."""
        output_state = await self.run(state)
        output_state["research_plan"] = "Mock research plan with structured approach"
        output_state["research_queries"] = ["Mock query 1", "Mock query 2", "Mock query 3"]
        return output_state
