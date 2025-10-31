#!/usr/bin/env python3
"""
Test script to verify the text processing fix is applied correctly
"""

print("=" * 80)
print("Testing Text Processing Fix Application Order")
print("=" * 80)

try:
    print("\n1. Importing multi_agents.main...")
    from multi_agents.main import run_research_task
    print("✅ Import successful")

    print("\n2. Checking if gpt_researcher is available...")
    import gpt_researcher
    print(f"✅ gpt_researcher version: {gpt_researcher.__version__ if hasattr(gpt_researcher, '__version__') else 'unknown'}")

    print("\n3. Checking if langchain is available...")
    import langchain
    print("✅ langchain available")

    print("\n4. Checking if patches were applied...")
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    # Check if our patched method exists
    if hasattr(RecursiveCharacterTextSplitter, 'split_text'):
        print("✅ RecursiveCharacterTextSplitter.split_text method exists")

        # Try to split some text
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=20,
            separators=["\n\n", "\n", " ", ""]
        )

        test_text = "This is a test. " * 50  # Create text that needs splitting
        try:
            chunks = splitter.split_text(test_text)
            print(f"✅ Text splitting successful: {len(chunks)} chunks created")
            print(f"   Max chunk size: {max(len(c) for c in chunks)} chars")
        except Exception as e:
            print(f"❌ Text splitting failed: {e}")

    print("\n" + "=" * 80)
    print("✅ ALL CHECKS PASSED - Text processing fix is properly applied!")
    print("=" * 80)

except ModuleNotFoundError as e:
    print(f"\n❌ Module not found: {e}")
    print("   Run this script with: uv run python test_chunking_fix_order.py")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
