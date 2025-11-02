"""
BRAVE Retriever Integration for GPT-Researcher
Clean integration that doesn't modify installed packages
"""

import asyncio
import concurrent.futures
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def setup_brave_custom_retriever():
    """
    Set up environment for BRAVE custom retriever integration.
    This patches the GPT-researcher custom retriever with BRAVE implementation.

    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        # Only setup if BRAVE is configured
        if os.getenv("PRIMARY_SEARCH_PROVIDER") != "brave":
            logger.info("BRAVE not configured, skipping custom retriever setup")
            return False

        logger.info("Setting up BRAVE custom retriever integration")

        # Configure GPT-researcher to use custom retriever
        os.environ["RETRIEVER"] = "custom"
        os.environ["RETRIEVER_ENDPOINT"] = "https://brave-direct-api.local"  # Valid URL format

        # Import GPT-researcher's custom retriever module
        import gpt_researcher.retrievers.custom.custom as custom_module

        from .config.providers import SearchConfig, SearchProvider

        # Import BRAVE components
        from .providers.factory import ProviderFactory
        from .utils.format_converter import BraveToGPTResearcherConverter

        class BraveCustomRetriever:
            """
            BRAVE implementation of GPT-researcher custom retriever interface
            """

            def __init__(self, query: str, query_domains=None):
                self.query = query
                self.query_domains = query_domains or []

                # Required for GPT-researcher compatibility
                self.endpoint = os.getenv("RETRIEVER_ENDPOINT", "brave-direct-api")
                self.params = self._populate_params()

                logger.info(f"Initializing BRAVE custom retriever for query: {query}")

                # Initialize BRAVE provider
                try:
                    search_config = SearchConfig(
                        provider=SearchProvider.BRAVE, max_results=10, search_depth="advanced"
                    )
                    self.brave_provider = ProviderFactory.create_search_provider(search_config)
                    logger.info("BRAVE provider initialized successfully")
                    print("✅ BRAVE Custom Retriever: Provider loaded")

                except Exception as e:
                    logger.error(f"Failed to initialize BRAVE provider: {e}")
                    print(f"❌ BRAVE Custom Retriever: Provider initialization failed - {e}")
                    raise

            def _populate_params(self) -> Dict[str, Any]:
                """
                Populates parameters from environment variables (for compatibility)
                """
                return {
                    key[len("RETRIEVER_ARG_") :].lower(): value
                    for key, value in os.environ.items()
                    if key.startswith("RETRIEVER_ARG_")
                }

            def search(self, max_results: int = 5) -> List[Dict[str, Any]]:
                """
                Perform search using BRAVE API and return results in GPT-researcher format.

                Args:
                    max_results: Maximum number of results to return

                Returns:
                    List of search results in GPT-researcher format
                """
                try:
                    logger.info(f"BRAVE search for: {self.query}")
                    print(f"🔍 BRAVE Custom Retriever: Searching '{self.query}'...")

                    # Handle async/sync boundary properly
                    search_response = self._run_search_safely(max_results)

                    # Convert to GPT-researcher format
                    results = BraveToGPTResearcherConverter.convert_search_response(
                        search_response, max_results
                    )

                    # Validate format
                    if BraveToGPTResearcherConverter.validate_gpt_researcher_format(results):
                        logger.info(f"BRAVE search returned {len(results)} valid results")
                        print(f"✅ BRAVE Custom Retriever: {len(results)} results found")

                        # Log sample result for debugging
                        if results:
                            sample = results[0]
                            logger.debug(f"Sample result: {sample.get('href', 'No URL')[:50]}...")

                        return results
                    else:
                        logger.error("BRAVE search format validation failed")
                        print("❌ BRAVE Custom Retriever: Format validation failed")
                        return []

                except Exception as e:
                    logger.error(f"BRAVE search error: {e}")
                    print(f"❌ BRAVE Custom Retriever error: {e}")
                    return []

            def _run_search_safely(self, max_results: int):
                """
                Safely run async search in sync context
                """
                try:
                    # Check if we're already in an async context
                    loop = asyncio.get_running_loop()
                    # We're in an async context, use thread pool
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_async_search, max_results)
                        return future.result(timeout=60)

                except RuntimeError:
                    # No event loop running, can use asyncio.run
                    return asyncio.run(
                        self.brave_provider.search(self.query, max_results=max_results)
                    )

            def _run_async_search(self, max_results: int):
                """
                Run async search in new event loop
                """
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        self.brave_provider.search(self.query, max_results=max_results)
                    )
                finally:
                    try:
                        # Clean up the loop
                        pending = asyncio.all_tasks(new_loop)
                        for task in pending:
                            task.cancel()

                        if pending:
                            try:
                                new_loop.run_until_complete(
                                    asyncio.wait_for(
                                        asyncio.gather(*pending, return_exceptions=True),
                                        timeout=5.0,
                                    )
                                )
                            except asyncio.TimeoutError:
                                pass
                            except Exception:
                                pass

                        if not new_loop.is_closed():
                            new_loop.close()
                    except Exception:
                        pass

        # Replace the CustomRetriever class in the module
        custom_module.CustomRetriever = BraveCustomRetriever

        logger.info("BRAVE custom retriever integration completed successfully")
        print("✅ BRAVE Integration: Custom retriever patched successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to setup BRAVE custom retriever: {e}")
        print(f"❌ BRAVE Integration: Setup failed - {e}")
        return False


def is_brave_configured():
    """
    Check if BRAVE is properly configured for use

    Returns:
        bool: True if BRAVE is configured, False otherwise
    """
    return (
        os.getenv("PRIMARY_SEARCH_PROVIDER") == "brave" and os.getenv("BRAVE_API_KEY") is not None
    )


def get_brave_retriever_status():
    """
    Get the current status of BRAVE retriever integration

    Returns:
        dict: Status information
    """
    return {
        "configured": is_brave_configured(),
        "primary_provider": os.getenv("PRIMARY_SEARCH_PROVIDER"),
        "retriever": os.getenv("RETRIEVER"),
        "endpoint": os.getenv("RETRIEVER_ENDPOINT"),
        "api_key_set": bool(os.getenv("BRAVE_API_KEY")),
    }
