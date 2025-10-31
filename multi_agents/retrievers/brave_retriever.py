"""
BRAVE Search Retriever for GPT-Researcher
Integrates our BRAVE search provider with the GPT-researcher framework
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import time

from ..providers.factory import ProviderFactory
from ..config.providers import SearchConfig, SearchProvider

logger = logging.getLogger(__name__)


class BraveRetriever:
    """
    BRAVE Search retriever for GPT Researcher.
    
    This retriever bridges our multi-agent BRAVE search provider
    with the GPT-researcher framework, providing consistent search
    results using the BRAVE Search API.
    """

    def __init__(
        self, 
        query: str, 
        headers: Optional[Dict[str, str]] = None,
        query_domains: Optional[List[str]] = None,
        websocket=None,
        researcher=None,
        **kwargs
    ):
        """
        Initialize the BRAVE Retriever.
        
        Args:
            query (str): The search query string.
            headers (dict, optional): Additional headers (not used).
            query_domains (list, optional): List of domains to search (not supported by BRAVE).
            websocket: WebSocket for stream logging.
            researcher: Researcher instance (not used).
            **kwargs: Additional arguments.
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or []
        self.websocket = websocket
        self.researcher = researcher
        
        # Initialize BRAVE search provider
        self.search_config = SearchConfig(
            provider=SearchProvider.BRAVE,
            max_results=kwargs.get('max_results', 10),
            search_depth="advanced"
        )
        
        try:
            self.brave_provider = ProviderFactory.create_search_provider(self.search_config)
            logger.info(f"BRAVE retriever initialized for query: {self.query}")
            if self.websocket:
                self._stream_log_sync(f"🔍 BRAVE retriever initialized for query: {self.query}")
        except Exception as e:
            logger.error(f"Failed to initialize BRAVE provider: {e}")
            raise ValueError(f"BRAVE retriever initialization failed: {e}")

    def _stream_log_sync(self, message: str):
        """Log message to websocket synchronously if available"""
        if self.websocket:
            try:
                # Try to send message to websocket
                if hasattr(self.websocket, 'send'):
                    self.websocket.send(message)
                elif hasattr(self.websocket, 'write_message'):
                    self.websocket.write_message(message)
            except Exception:
                pass  # Ignore websocket errors

    async def search_async(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Perform an async search using BRAVE Search API.
        
        Args:
            max_results: Maximum number of results to return.
            
        Returns:
            List[Dict[str, str]]: The search results in GPT-researcher format.
        """
        logger.info(f"BraveRetriever.search_async called for query: {self.query}")
        
        try:
            # Log search start
            if self.websocket:
                await self._stream_log(f"🔍 Searching with BRAVE: {self.query}")
            
            start_time = time.time()
            
            # Perform search using our BRAVE provider
            search_response = await self.brave_provider.search(
                self.query, 
                max_results=max_results
            )
            
            search_time = time.time() - start_time
            
            # Convert search results to GPT-researcher format
            results = []
            for result in search_response.results:
                gpt_result = {
                    "href": result.url,
                    "title": result.title,
                    "body": result.content,
                    "raw_content": result.content  # Some retrievers provide this
                }
                results.append(gpt_result)
            
            # Log search completion
            logger.info(f"BRAVE search completed: {len(results)} results in {search_time:.2f}s")
            if self.websocket:
                await self._stream_log(f"✅ BRAVE search: {len(results)} results in {search_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in BRAVE search: {e}")
            if self.websocket:
                await self._stream_log(f"❌ BRAVE search error: {str(e)}")
            return []

    def search(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Perform a search using BRAVE Search API.
        
        This is the synchronous interface required by GPT Researcher.
        It wraps the async search_async method.
        
        Args:
            max_results: Maximum number of results to return.
            
        Returns:
            List[Dict[str, str]]: The search results in GPT-researcher format.
        """
        logger.info(f"BraveRetriever.search called for query: {self.query}")
        
        try:
            # Handle the async/sync boundary
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()
                # If we're in an async context, create a new thread
                import concurrent.futures
                import threading
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(self.search_async(max_results))
                        return result
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
                                            timeout=5.0
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
                
                # Run in thread pool
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    results = future.result(timeout=120)  # 2 minute timeout
                    
            except RuntimeError:
                # No event loop is running, we can run directly
                results = asyncio.run(self.search_async(max_results))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in BRAVE search: {e}")
            self._stream_log_sync(f"❌ BRAVE search error: {str(e)}")
            return []

    async def _stream_log(self, message: str):
        """Log message to websocket asynchronously if available"""
        if self.websocket:
            try:
                # Try to send message to websocket
                if hasattr(self.websocket, 'send'):
                    await self.websocket.send(message)
                elif hasattr(self.websocket, 'write_message'):
                    self.websocket.write_message(message)
                elif hasattr(self.websocket, 'send_text'):
                    await self.websocket.send_text(message)
            except Exception:
                pass  # Ignore websocket errors


# Create an alias to match GPT-researcher's naming convention
class BraveSearchRetriever(BraveRetriever):
    """Alias for BraveRetriever to match GPT-researcher naming"""
    pass