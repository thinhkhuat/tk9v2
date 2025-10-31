"""
Monkey patch for GPT-researcher to support BRAVE custom retriever
This module patches GPT-researcher's custom retriever when BRAVE is configured
"""

import os
import sys

def patch_custom_retriever():
    """
    Patch GPT-researcher's custom retriever to use our BRAVE implementation
    """
    try:
        # Check if we should use BRAVE
        if os.getenv('PRIMARY_SEARCH_PROVIDER') != 'brave':
            return False
            
        # Import GPT-researcher's custom retriever module
        import gpt_researcher.retrievers.custom.custom as custom_module
        
        # Import our BRAVE implementation
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from custom_brave_retriever import CustomRetriever as BraveCustomRetriever
        
        # Create a wrapper that handles the endpoint issue
        class PatchedCustomRetriever:
            def __init__(self, query: str, query_domains=None):
                # Set dummy endpoint to satisfy original requirements
                if not os.getenv('RETRIEVER_ENDPOINT'):
                    os.environ['RETRIEVER_ENDPOINT'] = 'https://brave-direct.local'
                
                # Initialize our BRAVE retriever
                self.brave_retriever = BraveCustomRetriever(query, query_domains)
                self.query = query
                self.endpoint = os.getenv('RETRIEVER_ENDPOINT')
                self.params = {}
            
            def _populate_params(self):
                return {}
            
            def search(self, max_results: int = 5):
                # Use BRAVE search instead of HTTP requests
                return self.brave_retriever.search(max_results)
        
        # Replace the CustomRetriever class in the module
        custom_module.CustomRetriever = PatchedCustomRetriever
        
        print("✅ GPT-researcher custom retriever patched for BRAVE")
        return True
        
    except Exception as e:
        print(f"⚠️ Failed to patch GPT-researcher custom retriever: {e}")
        return False

# Auto-patch when this module is imported
if __name__ != "__main__":
    patch_custom_retriever()