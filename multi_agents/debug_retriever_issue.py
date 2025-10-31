#!/usr/bin/env python3
"""
Debug script to test BRAVE retriever integration and identify why GPT-researcher
is making direct HTTP calls instead of using our custom retriever.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment first
load_dotenv(override=True)

print("=== ENVIRONMENT CONFIGURATION ===")
print(f"PRIMARY_SEARCH_PROVIDER: {os.getenv('PRIMARY_SEARCH_PROVIDER')}")
print(f"RETRIEVER: {os.getenv('RETRIEVER')}")
print(f"RETRIEVER_ENDPOINT: {os.getenv('RETRIEVER_ENDPOINT')}")
print(f"BRAVE_API_KEY: {os.getenv('BRAVE_API_KEY', 'Not set')}")
print()

# Test 1: Check original GPT-researcher CustomRetriever
print("=== TEST 1: Original GPT-researcher CustomRetriever ===")
try:
    from gpt_researcher.retrievers.custom.custom import CustomRetriever
    print(f"Original CustomRetriever class: {CustomRetriever}")
    print(f"Module: {CustomRetriever.__module__}")
    print(f"File: {CustomRetriever.__module__.__file__ if hasattr(CustomRetriever.__module__, '__file__') else 'Unknown'}")
    
    # Try to create an instance with the current environment
    test_retriever = CustomRetriever("test query")
    print(f"✅ Successfully created original retriever instance")
    print(f"Endpoint: {test_retriever.endpoint}")
    print(f"Params: {test_retriever.params}")
    
    # Try a search to see what error we get
    print("🔍 Testing original retriever search...")
    try:
        results = test_retriever.search(max_results=1)
        print(f"Search results: {results}")
    except Exception as e:
        print(f"❌ Search failed: {e}")
        print(f"Error type: {type(e)}")
    
except Exception as e:
    print(f"❌ Failed to import or use original CustomRetriever: {e}")

print()

# Test 2: Apply BRAVE patching
print("=== TEST 2: Applying BRAVE Patching ===")
if os.getenv('PRIMARY_SEARCH_PROVIDER') == 'brave':
    try:
        from simple_brave_retriever import setup_simple_brave_retriever
        success = setup_simple_brave_retriever()
        print(f"BRAVE setup success: {success}")
        
        # Test the patched version
        print("🔍 Testing patched retriever...")
        from gpt_researcher.retrievers.custom.custom import CustomRetriever as PatchedRetriever
        
        print(f"Patched CustomRetriever class: {PatchedRetriever}")
        print(f"Module: {PatchedRetriever.__module__}")
        
        patched_instance = PatchedRetriever("test query")
        print(f"✅ Successfully created patched retriever instance")
        print(f"Instance type: {type(patched_instance)}")
        print(f"Has api_key: {hasattr(patched_instance, 'api_key')}")
        
        # Try a search
        try:
            results = patched_instance.search(max_results=1)
            print(f"✅ Patched search successful: {len(results) if results else 0} results")
            if results:
                print(f"Sample result keys: {list(results[0].keys())}")
        except Exception as e:
            print(f"❌ Patched search failed: {e}")
            
    except Exception as e:
        print(f"❌ BRAVE patching failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("PRIMARY_SEARCH_PROVIDER is not 'brave', skipping patching test")

print()

# Test 3: Check GPT-researcher configuration
print("=== TEST 3: GPT-researcher Configuration ===")
try:
    from gpt_researcher.config import Config
    config = Config()
    print(f"Config retrievers: {config.retrievers}")
    print(f"Config retriever attribute: {getattr(config, 'retriever', 'Not set')}")
    
    # Check what retriever classes would be used
    print("\nRetriever class resolution:")
    for retriever_name in config.retrievers:
        try:
            if retriever_name == "custom":
                from gpt_researcher.retrievers.custom.custom import CustomRetriever
                print(f"  {retriever_name} -> {CustomRetriever}")
            elif retriever_name == "tavily":
                from gpt_researcher.retrievers.tavily.tavily_search import TavilySearch
                print(f"  {retriever_name} -> {TavilySearch}")
            elif retriever_name == "brave":
                print(f"  {retriever_name} -> No built-in Brave retriever found")
        except ImportError as e:
            print(f"  {retriever_name} -> Import failed: {e}")
            
except Exception as e:
    print(f"❌ Failed to check GPT-researcher config: {e}")

print()

# Test 4: Simulate the actual GPT-researcher flow
print("=== TEST 4: Simulate GPT-researcher Flow ===")
try:
    from gpt_researcher import GPTResearcher
    
    # Create a researcher instance with minimal config
    researcher = GPTResearcher(
        query="test query",
        report_type="research_report", 
        verbose=True
    )
    
    print(f"Researcher retrievers: {[r.__name__ for r in researcher.retrievers]}")
    print(f"Researcher config retrievers: {researcher.cfg.retrievers}")
    
    # Check what retriever instance would be created
    if researcher.retrievers:
        first_retriever_class = researcher.retrievers[0]
        print(f"First retriever class: {first_retriever_class}")
        
        # Try to create an instance
        test_instance = first_retriever_class("test query")
        print(f"Created instance type: {type(test_instance)}")
        print(f"Has api_key attribute: {hasattr(test_instance, 'api_key')}")
        print(f"Has endpoint attribute: {hasattr(test_instance, 'endpoint')}")
        
        if hasattr(test_instance, 'endpoint'):
            print(f"Endpoint: {test_instance.endpoint}")
        
except Exception as e:
    print(f"❌ Failed to simulate GPT-researcher flow: {e}")
    import traceback
    traceback.print_exc()

print("\n=== SUMMARY ===")
print("This debug script shows:")
print("1. What CustomRetriever class is being used")
print("2. Whether the BRAVE patching is working")  
print("3. What endpoint the retriever is configured to use")
print("4. Whether the patch is being applied before or after GPT-researcher loads")