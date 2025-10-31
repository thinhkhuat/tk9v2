"""
BRAVE Custom Retriever that replaces GPT-researcher's default custom retriever
This module monkey-patches the default custom retriever when BRAVE is configured
"""

import os
import sys
from typing import Any, Dict, List, Optional

# Check if this is a BRAVE custom retriever request
def is_brave_retriever():
    """Check if we should use BRAVE retriever instead of default custom retriever"""
    return os.getenv('PRIMARY_SEARCH_PROVIDER') == 'brave'

# Only override if we're using BRAVE
if is_brave_retriever():
    try:
        # Import our BRAVE implementation
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from custom_brave_retriever import CustomRetriever as BraveCustomRetriever
        
        class CustomRetriever(BraveCustomRetriever):
            """
            Wrapper class that inherits from our BRAVE custom retriever
            This replaces GPT-researcher's default custom retriever when BRAVE is configured
            """
            
            def __init__(self, query: str, query_domains=None):
                """
                Initialize with BRAVE-specific behavior
                Override the endpoint requirement for BRAVE
                """
                # Set a dummy endpoint to satisfy GPT-researcher's requirement
                if not os.getenv('RETRIEVER_ENDPOINT'):
                    os.environ['RETRIEVER_ENDPOINT'] = 'https://brave-api-direct.local'
                
                # Call our BRAVE implementation
                super().__init__(query, query_domains)
            
            def search(self, max_results: int = 5) -> Optional[List[Dict[str, Any]]]:
                """
                Use BRAVE search instead of HTTP requests
                """
                # Override to use BRAVE search directly
                return super().search(max_results)
        
        # Print confirmation that BRAVE retriever is loaded
        print("✅ BRAVE Custom Retriever loaded successfully")
        
    except Exception as e:
        print(f"⚠️ Failed to load BRAVE custom retriever: {e}")
        # Fallback to default custom retriever behavior
        import requests
        
        class CustomRetriever:
            """Fallback to default custom retriever if BRAVE fails"""
            
            def __init__(self, query: str, query_domains=None):
                self.endpoint = os.getenv('RETRIEVER_ENDPOINT')
                if not self.endpoint:
                    raise ValueError("RETRIEVER_ENDPOINT environment variable not set")
                self.params = self._populate_params()
                self.query = query

            def _populate_params(self) -> Dict[str, Any]:
                return {
                    key[len('RETRIEVER_ARG_'):].lower(): value
                    for key, value in os.environ.items()
                    if key.startswith('RETRIEVER_ARG_')
                }

            def search(self, max_results: int = 5) -> Optional[List[Dict[str, Any]]]:
                try:
                    response = requests.get(self.endpoint, params={**self.params, 'query': self.query})
                    response.raise_for_status()
                    return response.json()
                except requests.RequestException as e:
                    print(f"Failed to retrieve search results: {e}")
                    return None

else:
    # Not using BRAVE, use default custom retriever
    import requests
    
    class CustomRetriever:
        """Default custom retriever for non-BRAVE configurations"""
        
        def __init__(self, query: str, query_domains=None):
            self.endpoint = os.getenv('RETRIEVER_ENDPOINT')
            if not self.endpoint:
                raise ValueError("RETRIEVER_ENDPOINT environment variable not set")
            self.params = self._populate_params()
            self.query = query

        def _populate_params(self) -> Dict[str, Any]:
            return {
                key[len('RETRIEVER_ARG_'):].lower(): value
                for key, value in os.environ.items()
                if key.startswith('RETRIEVER_ARG_')
            }

        def search(self, max_results: int = 5) -> Optional[List[Dict[str, Any]]]:
            try:
                response = requests.get(self.endpoint, params={**self.params, 'query': self.query})
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"Failed to retrieve search results: {e}")
                return None