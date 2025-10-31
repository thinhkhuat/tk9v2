"""
Custom BRAVE Retriever for GPT-Researcher
This file provides a custom retriever that GPT-researcher can import directly
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
import sys

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from providers.factory import ProviderFactory
    from config.providers import SearchConfig, SearchProvider
    from utils.format_converter import BraveToGPTResearcherConverter
except ImportError:
    # Fallback import path
    try:
        from multi_agents.providers.factory import ProviderFactory
        from multi_agents.config.providers import SearchConfig, SearchProvider
        from multi_agents.utils.format_converter import BraveToGPTResearcherConverter
    except ImportError:
        # Try absolute import with importlib
        import importlib.util
        
        # Import ProviderFactory
        factory_path = os.path.join(current_dir, 'providers', 'factory.py')
        spec = importlib.util.spec_from_file_location("factory", factory_path)
        factory_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(factory_module)
        ProviderFactory = factory_module.ProviderFactory
        
        # Import SearchConfig and SearchProvider
        config_path = os.path.join(current_dir, 'config', 'providers.py')
        spec = importlib.util.spec_from_file_location("providers_config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        SearchConfig = config_module.SearchConfig
        SearchProvider = config_module.SearchProvider
        
        # Import format converter
        converter_path = os.path.join(current_dir, 'utils', 'format_converter.py')
        spec = importlib.util.spec_from_file_location("format_converter", converter_path)
        converter_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(converter_module)
        BraveToGPTResearcherConverter = converter_module.BraveToGPTResearcherConverter

logger = logging.getLogger(__name__)


class CustomRetriever:
    """
    Custom BRAVE Search Retriever for GPT-Researcher
    
    This retriever uses our multi-agent BRAVE search provider
    to provide search results to GPT-researcher in the expected format.
    """

    def __init__(self, query: str, query_domains=None):
        """
        Initialize the custom BRAVE retriever.
        
        Args:
            query (str): The search query
            query_domains: List of domains (not used by BRAVE)
        """
        self.query = query
        self.query_domains = query_domains or []
        
        # Check for required environment variables (for compatibility with GPT-researcher)
        self.endpoint = os.getenv('RETRIEVER_ENDPOINT', None)
        self.params = self._populate_params()
        # Note: We don't use HTTP requests since we have direct API access via BRAVE provider
        
        # Initialize BRAVE search provider
        try:
            self.search_config = SearchConfig(
                provider=SearchProvider.BRAVE,
                max_results=10,
                search_depth="advanced"
            )
            
            self.brave_provider = ProviderFactory.create_search_provider(self.search_config)
            logger.info(f"Custom BRAVE retriever initialized for query: {self.query}")
            
        except Exception as e:
            logger.error(f"Failed to initialize BRAVE provider: {e}")
            # Don't raise exception - let GPT-researcher continue with other retrievers
            self.brave_provider = None

    def _populate_params(self) -> Dict[str, Any]:
        """
        Populates parameters from environment variables (for compatibility)
        """
        return {
            key[len('RETRIEVER_ARG_'):].lower(): value
            for key, value in os.environ.items()
            if key.startswith('RETRIEVER_ARG_')
        }

    def search(self, max_results: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Performs the search using BRAVE Search API.
        
        Args:
            max_results: Maximum number of results to return
            
        Returns:
            List of search results in the format expected by GPT-researcher:
            [
              {
                "url": "http://example.com/page1",
                "raw_content": "Content of page 1"
              },
              ...
            ]
        """
        if not self.brave_provider:
            logger.warning("BRAVE provider not available, returning empty results")
            return []
            
        try:
            logger.info(f"BRAVE custom retriever searching: {self.query}")
            
            # Handle async/sync boundary
            try:
                # Check if we're in an async context
                loop = asyncio.get_running_loop()
                # Create new event loop in thread
                import concurrent.futures
                
                def run_search():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            self.brave_provider.search(self.query, max_results=max_results)
                        )
                    finally:
                        try:
                            pending = asyncio.all_tasks(new_loop)
                            for task in pending:
                                task.cancel()
                            if pending:
                                try:
                                    new_loop.run_until_complete(
                                        asyncio.wait_for(
                                            asyncio.gather(*pending, return_exceptions=True),
                                            timeout=5.0
                                        )
                                    )
                                except:
                                    pass
                            if not new_loop.is_closed():
                                new_loop.close()
                        except:
                            pass
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_search)
                    search_response = future.result(timeout=60)
                    
            except RuntimeError:
                # No event loop running, can use asyncio.run
                search_response = asyncio.run(
                    self.brave_provider.search(self.query, max_results=max_results)
                )
            
            # Convert BRAVE response to GPT-researcher format using the converter
            results = BraveToGPTResearcherConverter.convert_search_response(
                search_response, 
                max_results=max_results
            )
            
            # Validate the format
            if BraveToGPTResearcherConverter.validate_gpt_researcher_format(results):
                logger.info(f"BRAVE custom retriever returned {len(results)} valid results")
                # Add debug information
                results = BraveToGPTResearcherConverter.add_content_summary(results)
                
                # Log first result for debugging
                if results:
                    first_result = results[0]
                    logger.debug(f"Sample result: URL={first_result['href'][:50]}..., "
                               f"Content={first_result.get('content_length', 0)} chars")
                
                return results
            else:
                logger.error("Format validation failed, returning empty results")
                return []
            
        except Exception as e:
            logger.error(f"Error in BRAVE custom retriever: {e}")
            print(f"BRAVE search error: {e}")
            return []


def setup_brave_integration():
    """
    Set up BRAVE custom retriever integration with GPT-researcher.
    
    This function patches GPT-researcher's custom retriever with our BRAVE implementation
    and configures the environment properly.
    
    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        # Only setup if BRAVE is configured
        if os.getenv('PRIMARY_SEARCH_PROVIDER') != 'brave':
            logger.info("BRAVE not configured, skipping custom retriever setup")
            return False
        
        logger.info("Setting up BRAVE custom retriever integration")
        
        # Configure GPT-researcher to use custom retriever
        os.environ['RETRIEVER'] = 'custom'
        # Set a dummy endpoint to satisfy GPT-researcher requirement but not make real HTTP calls
        os.environ['RETRIEVER_ENDPOINT'] = 'https://brave-direct-provider.local'
        
        # Import GPT-researcher's custom retriever module
        import gpt_researcher.retrievers.custom.custom as custom_module
        
        # Replace the CustomRetriever class in the module with our implementation
        custom_module.CustomRetriever = CustomRetriever
        
        logger.info("BRAVE custom retriever integration completed successfully")
        print("✅ BRAVE Integration: Custom retriever patched successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup BRAVE custom retriever: {e}")
        print(f"❌ BRAVE Integration: Setup failed - {e}")
        return False