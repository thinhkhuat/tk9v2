#!/usr/bin/env python3
"""
Debug script to identify and reproduce the "Separator is not found, and chunk exceed the limit" error
"""

import os
import sys
import traceback
from typing import Any, Dict

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def trace_chunking_error():
    """
    Try to reproduce the chunking error by running a minimal research task
    and catching the exact exception source
    """
    print("🔍 Debugging chunking error - tracing exception source...")
    
    try:
        # Import and setup the research system
        from multi_agents.main import run_research_task
        from gpt_researcher.utils.enum import Tone
        import asyncio
        
        # Create a simple test query that might trigger large content chunks
        test_query = "What are the latest developments in artificial intelligence and machine learning in 2024, including breakthrough technologies, major research findings, and commercial applications across industries?"
        
        print(f"Testing with query: {test_query}")
        
        async def debug_research():
            try:
                result = await run_research_task(
                    query=test_query,
                    tone=Tone.Objective,
                    write_to_files=False,  # Disable file writing to focus on the core error
                    language="en"
                )
                print("✅ Research completed successfully - no chunking error occurred")
                return result
                
            except Exception as e:
                error_message = str(e)
                error_type = type(e).__name__
                
                print(f"\n❌ Exception caught:")
                print(f"   Type: {error_type}")
                print(f"   Message: {error_message}")
                
                # Check if this is our target error
                if "Separator is not found" in error_message and "chunk exceed" in error_message:
                    print("\n🎯 FOUND THE TARGET ERROR!")
                    print("   This is the chunking error we're looking for.")
                    
                    # Print full traceback to see the source
                    print("\n📋 Full traceback:")
                    traceback.print_exc()
                    
                    # Try to extract the specific library/module that raised this
                    tb = traceback.extract_tb(e.__traceback__)
                    print(f"\n🔍 Exception origin:")
                    for frame in tb:
                        if any(keyword in frame.filename.lower() for keyword in ['chunk', 'split', 'token', 'text']):
                            print(f"   📁 File: {frame.filename}")
                            print(f"   📍 Line: {frame.lineno}")
                            print(f"   ⚙️  Function: {frame.name}")
                            print(f"   📝 Code: {frame.line}")
                    
                    return {"error_identified": True, "error_source": str(e)}
                else:
                    print(f"\n⚠️  Different error occurred: {error_message}")
                    print("   This is not the target chunking error")
                    raise e  # Re-raise if it's a different error
        
        # Run the debug research
        result = asyncio.run(debug_research())
        return result
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're in the correct directory and dependencies are installed")
        return None
    except Exception as e:
        print(f"❌ Unexpected error in debug setup: {e}")
        traceback.print_exc()
        return None

def check_text_processing_libraries():
    """
    Check various text processing libraries for the error message
    """
    print("\n🔍 Checking text processing libraries for the error message...")
    
    libraries_to_check = [
        'tiktoken',
        'transformers', 
        'sentence_transformers',
        'langchain_text_splitters',
        'langchain_core',
        'gpt_researcher'
    ]
    
    for lib_name in libraries_to_check:
        try:
            print(f"\n📦 Checking {lib_name}...")
            
            # Import the library
            if lib_name == 'tiktoken':
                import tiktoken
                # Try to get encoding and see if we can trigger an error
                enc = tiktoken.get_encoding("cl100k_base")
                # Create a very long text to test chunking
                long_text = "test " * 10000  # 50,000 characters
                tokens = enc.encode(long_text)
                print(f"   ✅ {lib_name} - {len(tokens)} tokens encoded successfully")
                
            elif lib_name == 'transformers':
                from transformers import AutoTokenizer
                # Try a tokenizer that might have chunking issues
                try:
                    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
                    long_text = "test " * 5000
                    tokens = tokenizer.encode(long_text, max_length=512, truncation=True)
                    print(f"   ✅ {lib_name} - tokenized successfully")
                except Exception as e:
                    if "Separator is not found" in str(e) or "chunk exceed" in str(e):
                        print(f"   🎯 FOUND ERROR in {lib_name}: {e}")
                    else:
                        print(f"   ⚠️  {lib_name} - other error: {e}")
                        
            elif lib_name == 'langchain_text_splitters':
                from langchain_text_splitters import RecursiveCharacterTextSplitter
                # Try to create a text splitter with problematic separators
                long_text = "test " * 10000
                
                # Test various configurations that might fail
                configs_to_test = [
                    {"chunk_size": 100, "chunk_overlap": 50, "separators": ["\n\n", "\n", " "]},
                    {"chunk_size": 50, "chunk_overlap": 25, "separators": []},  # Empty separators
                    {"chunk_size": 10, "chunk_overlap": 5, "separators": ["\n\n", "\n", " "]},
                ]
                
                for i, config in enumerate(configs_to_test):
                    try:
                        splitter = RecursiveCharacterTextSplitter(**config)
                        chunks = splitter.split_text(long_text)
                        print(f"   ✅ {lib_name} config {i+1} - {len(chunks)} chunks created")
                    except Exception as e:
                        if "Separator is not found" in str(e) or "chunk exceed" in str(e):
                            print(f"   🎯 FOUND ERROR in {lib_name} config {i+1}: {e}")
                        else:
                            print(f"   ⚠️  {lib_name} config {i+1} - other error: {e}")
            
            elif lib_name == 'gpt_researcher':
                # We already checked this via the research task above
                print(f"   ✅ {lib_name} - checked via research task")
                
            else:
                # Generic import check
                __import__(lib_name)
                print(f"   ✅ {lib_name} - imported successfully")
                
        except ImportError:
            print(f"   ❌ {lib_name} - not available")
        except Exception as e:
            if "Separator is not found" in str(e) or "chunk exceed" in str(e):
                print(f"   🎯 FOUND ERROR in {lib_name}: {e}")
            else:
                print(f"   ⚠️  {lib_name} - error: {e}")


def main():
    """Main debug function"""
    print("🚀 Starting chunking error debug session...")
    print("=" * 60)
    
    # First, try to reproduce the error with a research task
    research_result = trace_chunking_error()
    
    # Then check individual text processing libraries
    check_text_processing_libraries()
    
    print("\n" + "=" * 60)
    print("🏁 Debug session completed")
    
    if research_result and research_result.get("error_identified"):
        print("✅ Successfully identified the chunking error source!")
    else:
        print("⚠️  Could not reproduce the chunking error in this session")
        print("   The error may be intermittent or context-dependent")


if __name__ == "__main__":
    main()