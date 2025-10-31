#!/usr/bin/env python
"""
Simple BRAVE Search Custom Retriever for GPT-Researcher
Direct implementation following the BRAVE API example
"""

import os
import requests
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CustomRetriever:
    """
    Simple BRAVE Search Custom Retriever
    Direct implementation using the BRAVE API example pattern
    """
    
    def __init__(self, query: str, query_domains=None):
        print(f"🔧 Simple BRAVE Retriever: Initializing with query='{query}'")
        self.query = query
        self.query_domains = query_domains or []
        
        # Get BRAVE API key
        self.api_key = os.getenv('BRAVE_API_KEY')
        if not self.api_key:
            print("❌ BRAVE_API_KEY not found!")
            raise ValueError("BRAVE_API_KEY environment variable not set")
        
        print(f"✅ BRAVE API key found: {self.api_key[:10]}...")
        
        # BRAVE API endpoint
        self.endpoint = "https://api.search.brave.com/res/v1/web/search"
        
        # Required for GPT-researcher compatibility
        self.params = {}
        
        print("✅ Simple BRAVE Custom Retriever: Initialized")
    
    def _populate_params(self) -> Dict[str, Any]:
        """For compatibility with GPT-researcher"""
        return {}
    
    def _truncate_query(self, query: str, max_length: int = 400, max_words: int = 50) -> str:
        """
        Intelligently truncate query to meet BRAVE API limits:
        - 400 character limit
        - 50 word limit  
        Preserves key terms and removes filler words
        """
        original_length = len(query)
        original_word_count = len(query.split())
        
        # Return early if within both limits
        if len(query) <= max_length and original_word_count <= max_words:
            return query
        
        # List of filler words to remove first
        filler_words = [
            'that', 'would', 'could', 'should', 'might', 'will', 'shall',
            'and so forth', 'so on', 'etc', 'such as', 'for example',
            'for instance', 'compared to when', 'significantly', 'practical',
            'valuable', 'available', 'prepared', 'readily'
        ]
        
        truncated = query
        
        # First, try removing filler words
        for filler in filler_words:
            current_word_count = len(truncated.split())
            if len(truncated) <= max_length and current_word_count <= max_words:
                break
            truncated = truncated.replace(filler, '')
        
        # Clean up extra spaces
        truncated = ' '.join(truncated.split())
        
        # Check word count after filler word removal
        current_word_count = len(truncated.split())
        
        # If still too many words, truncate to word limit first
        if current_word_count > max_words:
            words = truncated.split()
            truncated = ' '.join(words[:max_words])
        
        # If still too long by characters, truncate at word boundary
        if len(truncated) > max_length:
            # Find last complete word within character limit
            truncated = truncated[:max_length].rsplit(' ', 1)[0]
        
        final_word_count = len(truncated.split())
        print(f"🔍 Query truncated: {original_word_count} words → {final_word_count} words, {original_length} chars → {len(truncated)} chars")
        return truncated

    def search(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search using BRAVE API and return results in GPT-researcher format
        """
        try:
            print(f"🔍 Simple BRAVE Search: '{self.query}' (max_results={max_results})...")
            
            # Truncate query to meet BRAVE API 400 character limit
            truncated_query = self._truncate_query(self.query)
            
            # Prepare clean parameters for BRAVE API
            params = {
                "q": truncated_query,
                "count": min(max_results, 20),  # BRAVE max is 20
                "country": "US",  # Use US instead of ALL
                "search_lang": "en",  # Use English to avoid language issues
            }
            
            print(f"🔍 BRAVE API request params: {params}")
            
            # Make request to BRAVE API with proper headers
            response = requests.get(
                self.endpoint,
                headers={
                    "X-Subscription-Token": self.api_key,
                    "Accept": "application/json",  # Required by BRAVE API
                    "User-Agent": "Deep-Research-MCP/1.0"
                },
                params=params,
                timeout=30
            )
            
            # Check response status with detailed error handling
            if response.status_code == 401:
                print("❌ BRAVE API: Invalid API key")
                return []
            elif response.status_code == 429:
                print("❌ BRAVE API: Rate limit exceeded")
                return []
            elif response.status_code == 422:
                # Parse validation errors
                try:
                    error_data = response.json()
                    print(f"❌ BRAVE API: Validation Error (HTTP 422)")
                    if 'error' in error_data and 'meta' in error_data['error']:
                        errors = error_data['error']['meta'].get('errors', [])
                        for error in errors:
                            if 'msg' in error and 'loc' in error:
                                location = ' -> '.join(str(x) for x in error['loc'])
                                print(f"   {location}: {error['msg']}")
                    return []
                except:
                    error_text = response.text
                    print(f"❌ BRAVE API: HTTP {response.status_code} - {error_text}")
                    return []
            elif response.status_code != 200:
                error_text = response.text
                print(f"❌ BRAVE API: HTTP {response.status_code} - {error_text}")
                return []
            
            # Parse JSON response
            data = response.json()
            
            # Extract web results
            web_results = data.get("web", {}).get("results", [])
            
            # Convert to GPT-researcher format
            gpt_results = []
            for item in web_results:
                result = {
                    "href": item.get("url", ""),
                    "body": item.get("description", ""),
                    "title": item.get("title", ""),
                    "raw_content": item.get("description", "")
                }
                
                # Only add results with valid URL and content
                if result["href"] and result["body"]:
                    gpt_results.append(result)
            
            print(f"✅ Simple BRAVE Search: {len(gpt_results)} results found")
            
            # Log sample result for debugging
            if gpt_results:
                sample = gpt_results[0]
                print(f"   Sample: {sample['href'][:50]}...")
            
            return gpt_results
            
        except requests.RequestException as e:
            print(f"❌ BRAVE API request error: {e}")
            return []
        except Exception as e:
            print(f"❌ BRAVE search error: {e}")
            return []
    
    def _populate_params(self):
        """For GPT-researcher compatibility"""
        return {}


def setup_simple_brave_retriever():
    """
    Replace GPT-researcher's custom retriever with simple BRAVE implementation
    """
    try:
        # Only setup if BRAVE is configured
        if os.getenv('PRIMARY_SEARCH_PROVIDER') != 'brave':
            return False
        
        print("🔧 Setting up Simple BRAVE Custom Retriever...")
        
        # Configure environment for GPT-researcher
        os.environ['RETRIEVER'] = 'custom'
        # Set dummy endpoint so GPT-researcher doesn't make real HTTP calls
        os.environ['RETRIEVER_ENDPOINT'] = 'https://brave-local-provider.local'
        
        # Import and replace the custom retriever
        import gpt_researcher.retrievers.custom.custom as custom_module
        
        print(f"🔍 Before patch: {custom_module.CustomRetriever}")
        print(f"🔍 Module file: {custom_module.__file__}")
        
        # Replace with our simple BRAVE implementation
        custom_module.CustomRetriever = CustomRetriever
        
        # Also patch sys.modules to ensure all imports get our version
        import sys
        sys.modules['gpt_researcher.retrievers.custom.custom'].CustomRetriever = CustomRetriever
        
        print(f"🔍 After patch: {custom_module.CustomRetriever}")
        print(f"🔍 sys.modules patch: {sys.modules['gpt_researcher.retrievers.custom.custom'].CustomRetriever}")
        
        # Verify the patch worked
        test_instance = custom_module.CustomRetriever("test")
        print(f"🔍 Test instance type: {type(test_instance)}")
        print(f"🔍 Has api_key: {hasattr(test_instance, 'api_key')}")
        
        # Also check if we can import and get our patched version
        import gpt_researcher.retrievers.custom.custom as test_import
        print(f"🔍 Fresh import test: {test_import.CustomRetriever}")
        
        # Monkey patch the entire module chain
        import gpt_researcher.retrievers.custom
        gpt_researcher.retrievers.custom.custom.CustomRetriever = CustomRetriever
        
        # CRITICAL: Also patch the main retrievers module that get_retriever imports from
        import gpt_researcher.retrievers
        gpt_researcher.retrievers.CustomRetriever = CustomRetriever
        
        # Verify the main import path works with our patched version
        try:
            from gpt_researcher.retrievers import CustomRetriever as MainImportTest
            print(f"🔍 Main import test: {MainImportTest}")
            test_main = MainImportTest("main import test")
            print(f"🔍 Main import instance type: {type(test_main)}")
            print(f"🔍 Main import has api_key: {hasattr(test_main, 'api_key')}")
        except Exception as e:
            print(f"⚠️  Main import test failed: {e}")
        
        print("✅ Simple BRAVE Custom Retriever: Integration complete")
        return True
        
    except Exception as e:
        print(f"❌ Simple BRAVE setup failed: {e}")
        return False