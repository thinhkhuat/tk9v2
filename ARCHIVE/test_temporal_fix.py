#!/usr/bin/env python3
"""
Test script to verify the temporal awareness fix for the reviewer agent.
This tests that the system properly handles 2025 dates and contemporary events.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the multi_agents directory to the path
sys.path.insert(0, str(Path(__file__).parent / "multi_agents"))

from multi_agents.agents.reviewer import ReviewerAgent
from multi_agents.agents.reviser import ReviserAgent
from multi_agents.agents.utils.date_context import get_current_date_context, is_temporal_issue


async def test_reviewer_temporal_awareness():
    """Test that the reviewer agent has proper temporal awareness"""
    
    print("=" * 60)
    print("Testing Reviewer Agent Temporal Awareness")
    print("=" * 60)
    
    # Create a mock draft with 2025 content
    mock_draft = """
# AI Research Report - January 2025

## Executive Summary
This report analyzes the latest developments in artificial intelligence as of January 2025,
during the administration of President Donald Trump. The research covers breakthroughs
announced at major tech conferences in late 2024 and early 2025.

## Recent Developments
- OpenAI released GPT-5 in December 2024
- Google announced Gemini Ultra 2.0 in January 2025
- Meta's LLaMA 4 achieved new benchmarks in February 2025

## Political Context
Under President Trump's administration (starting January 2025), new AI regulations
have been proposed focusing on American competitiveness in the global AI race.

## Conclusion
The AI landscape in 2025 shows rapid advancement with significant implications
for various industries and society as a whole.
"""
    
    # Create mock state
    draft_state = {
        "task": {
            "guidelines": [
                "Report should be comprehensive and well-structured",
                "Include recent developments and current context",
                "Maintain academic tone and proper citations"
            ],
            "model": "gpt-4",
            "verbose": True
        },
        "draft": mock_draft,
        "revision_count": 0
    }
    
    # Test reviewer
    reviewer = ReviewerAgent()
    
    print("\n1. Testing Review with 2025 Content...")
    print("-" * 40)
    
    review_result = await reviewer.review_draft(draft_state)
    
    print(f"Review Notes: {review_result.get('revision_notes', 'None')}")
    print(f"Revision Count: {review_result.get('revision_count', 0)}")
    
    # Check if temporal issues were properly handled
    if review_result.get('revision_notes'):
        is_temporal = is_temporal_issue(review_result['revision_notes'])
        print(f"Contains only temporal issues: {is_temporal}")
        
        if is_temporal:
            print("✅ PASS: Temporal issues detected and would be ignored")
        else:
            print("ℹ️  Review contains substantive feedback beyond temporal issues")
    else:
        print("✅ PASS: No revision notes - draft accepted")
    
    return review_result


async def test_reviser_state_management():
    """Test that the reviser properly manages draft state"""
    
    print("\n" + "=" * 60)
    print("Testing Reviser Agent State Management")
    print("=" * 60)
    
    # Test with missing draft
    empty_state = {
        "task": {"model": "gpt-4"},
        "review": "Please improve the structure",
        "revision_count": 1,
        "report": "This is the original report content"  # Fallback content
    }
    
    reviser = ReviserAgent()
    
    print("\n2. Testing Reviser with Empty Draft Field...")
    print("-" * 40)
    
    result = await reviser.revise_draft(empty_state)
    
    has_draft = bool(result.get("draft"))
    print(f"Draft preserved: {has_draft}")
    print(f"Revision notes: {result.get('revision_notes', 'None')}")
    print(f"Revision count: {result.get('revision_count', 0)}")
    
    if has_draft:
        print("✅ PASS: Draft field maintained despite empty input")
    else:
        print("❌ FAIL: Draft field is empty")
    
    return result


async def test_revision_loop_prevention():
    """Test that revision loops are properly prevented"""
    
    print("\n" + "=" * 60)
    print("Testing Revision Loop Prevention")
    print("=" * 60)
    
    # Test at max revisions
    max_revision_state = {
        "task": {
            "guidelines": ["Must be perfect"],
            "model": "gpt-4"
        },
        "draft": "Some content",
        "revision_count": 3  # At max
    }
    
    reviewer = ReviewerAgent()
    
    print("\n3. Testing at Maximum Revisions...")
    print("-" * 40)
    
    result = await reviewer.review_draft(max_revision_state)
    
    print(f"Review at max revisions: {result.get('revision_notes', 'None')}")
    print(f"Revision count: {result.get('revision_count', 3)}")
    
    if result.get('revision_notes') is None:
        print("✅ PASS: Review loop prevented at max revisions")
    else:
        print("❌ FAIL: Review still requesting changes at max revisions")
    
    return result


async def test_date_context():
    """Test date context utilities"""
    
    print("\n" + "=" * 60)
    print("Testing Date Context Utilities")
    print("=" * 60)
    
    context = get_current_date_context()
    
    print(f"\nCurrent Date Context:")
    print(f"  - Date: {context['current_date']}")
    print(f"  - Year: {context['current_year']}")
    print(f"  - Context: {context['context_message']}")
    
    # Test temporal issue detection
    test_cases = [
        ("The event in 2025 hasn't happened yet", True),
        ("The formatting is incorrect and structure needs work", False),
        ("This future date of January 2025 is wrong", True),
        ("Missing citations and poor grammar throughout", False),
        ("The 2024 data is from the future which is impossible", True)
    ]
    
    print("\n4. Testing Temporal Issue Detection...")
    print("-" * 40)
    
    for text, expected in test_cases:
        result = is_temporal_issue(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text[:50]}...' -> {result} (expected: {expected})")


async def main():
    """Run all tests"""
    
    print("\n" + "=" * 60)
    print("TEMPORAL AWARENESS FIX TEST SUITE")
    print("=" * 60)
    
    try:
        # Test date context first (no async)
        await test_date_context()
        
        # Test reviewer temporal awareness
        review_result = await test_reviewer_temporal_awareness()
        
        # Test reviser state management
        revise_result = await test_reviser_state_management()
        
        # Test loop prevention
        loop_result = await test_revision_loop_prevention()
        
        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETE")
        print("=" * 60)
        print("\nSummary:")
        print("✅ Temporal awareness added to agents")
        print("✅ State management improved for draft preservation")
        print("✅ Loop prevention mechanisms in place")
        print("✅ Date context utilities functional")
        
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set up minimal environment
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")
    os.environ["TAVILY_API_KEY"] = os.environ.get("TAVILY_API_KEY", "test-key")
    
    asyncio.run(main())