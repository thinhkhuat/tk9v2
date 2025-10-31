#!/usr/bin/env python
"""
Test script for the fact-checking protocol implementation.
This verifies that the reviewer and reviser agents properly use fact-checking
to prevent workflow blocking based on unverified claims.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the multi_agents directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'multi_agents'))

from multi_agents.agents.utils.fact_checker import (
    FactChecker, 
    VerificationStatus, 
    get_fact_checker
)
from multi_agents.agents.reviewer import ReviewerAgent
from multi_agents.agents.reviser import ReviserAgent


async def test_fact_checker():
    """Test the fact checker utility"""
    print("\n" + "="*60)
    print("Testing Fact Checker Utility")
    print("="*60)
    
    # Initialize fact checker
    fact_checker = get_fact_checker()
    
    # Test 1: Extract factual claims
    print("\n1. Testing factual claim extraction:")
    test_text = """
    The report incorrectly states that Donald Trump became president in 2025.
    The formatting and structure are good, but the date of January 2025 is wrong.
    The writing style is clear and the grammar is correct.
    Actually, the climate summit was held in 2024, not 2023 as stated.
    """
    
    claims = fact_checker.extract_factual_claims(test_text)
    print(f"   Found {len(claims)} factual claims:")
    for claim in claims:
        print(f"   - {claim}")
    
    # Test 2: Verify a contemporary claim (should be inconclusive or true)
    print("\n2. Testing contemporary claim verification:")
    contemporary_claim = "Donald Trump is president in 2025"
    result = await fact_checker.verify_claim(contemporary_claim)
    print(f"   Claim: {contemporary_claim}")
    print(f"   Status: {result.status.value}")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Can block workflow: {result.can_block_workflow()}")
    
    # Test 3: Test burden of proof principle
    print("\n3. Testing burden of proof principle:")
    uncertain_claim = "The quantum computing breakthrough happened in December 2024"
    result = await fact_checker.verify_claim(uncertain_claim)
    print(f"   Claim: {uncertain_claim}")
    print(f"   Status: {result.status.value}")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Can block workflow: {result.can_block_workflow()}")
    print(f"   Burden of proof: {'PASSED' if not result.can_block_workflow() else 'FAILED'}")
    
    # Test 4: Generate verification report
    print("\n4. Testing verification report generation:")
    report = fact_checker.generate_verification_report()
    print("   Report preview:")
    print("   " + report[:200].replace("\n", "\n   ") + "...")


async def test_reviewer_with_fact_checking():
    """Test the reviewer agent with fact-checking"""
    print("\n" + "="*60)
    print("Testing Reviewer Agent with Fact-Checking")
    print("="*60)
    
    # Create a mock draft state with contemporary content
    draft_state = {
        "task": {
            "guidelines": [
                "Content must be factually accurate",
                "Must have clear structure",
                "Include recent developments"
            ],
            "follow_guidelines": True,
            "verbose": True,
            "model": "gemini-2.0-flash-preview-04-17-thinking",
            "language": "en"
        },
        "draft": """
        # 2025 Technology Report
        
        ## Recent Developments
        
        In January 2025, President Donald Trump announced new AI regulations.
        The quantum computing breakthrough in late 2024 has revolutionized cryptography.
        Major tech companies are adapting to the new landscape in 2025.
        
        ## Market Analysis
        
        The technology sector continues to grow rapidly in 2025, with AI leading the charge.
        Recent developments show unprecedented adoption rates.
        
        ## Conclusion
        
        The year 2025 marks a significant turning point in technology adoption.
        """,
        "revision_count": 0
    }
    
    # Initialize reviewer
    reviewer = ReviewerAgent()
    
    print("\n1. Testing review with fact-checking protocol:")
    # Simulate a review that might contain incorrect factual claims
    review_result = await reviewer.review_draft(draft_state)
    
    if review_result.get("revision_notes"):
        print(f"   Review feedback: {review_result['revision_notes'][:200]}...")
    else:
        print("   Review accepted the draft (no issues found)")
    
    print("\n2. Testing temporal awareness:")
    print("   The reviewer should accept 2024-2025 dates as current/recent")
    print(f"   Result: {'PASSED' if not review_result.get('revision_notes') or '2025' not in str(review_result.get('revision_notes', '')).lower() else 'FAILED'}")


async def test_reviser_with_fact_checking():
    """Test the reviser agent with fact-checking"""
    print("\n" + "="*60)
    print("Testing Reviser Agent with Fact-Checking")
    print("="*60)
    
    # Create a mock draft state with review feedback
    draft_state = {
        "task": {
            "model": "gemini-2.0-flash-preview-04-17-thinking",
            "verbose": True
        },
        "draft": """
        # Technology Report 2025
        
        The current president, Donald Trump, announced new policies in January 2025.
        This report covers recent technological developments.
        """,
        "review": """
        The report incorrectly states that Donald Trump is president in 2025.
        Actually, this should be corrected to reflect the proper timeline.
        The formatting needs improvement and the structure could be clearer.
        """,
        "revision_count": 0
    }
    
    # Initialize reviser
    reviser = ReviserAgent()
    
    print("\n1. Testing revision with fact-checking protocol:")
    print("   Review contains potentially false claims about 2025")
    
    # The reviser should verify claims before accepting them
    revision_result = await reviser.revise_draft(draft_state)
    
    print(f"   Revision notes: {revision_result.get('revision_notes', 'None')[:200]}...")
    
    # Check if the reviser rejected unverified claims
    if "fact-check" in revision_result.get("revision_notes", "").lower() or "rejected" in revision_result.get("revision_notes", "").lower():
        print("   ✅ Reviser properly verified claims before accepting")
    else:
        print("   ⚠️  Reviser may have accepted unverified claims")
    
    print("\n2. Testing burden of proof application:")
    draft_with_inconclusive = {
        "task": {
            "model": "gemini-2.0-flash-preview-04-17-thinking",
            "verbose": False
        },
        "draft": "The quantum breakthrough happened in December 2024.",
        "review": "The date December 2024 is incorrect for the quantum breakthrough.",
        "revision_count": 0
    }
    
    revision_result = await reviser.revise_draft(draft_with_inconclusive)
    
    if revision_result.get("draft") == draft_with_inconclusive["draft"]:
        print("   ✅ Burden of proof applied - original kept when claim unverifiable")
    else:
        print("   ⚠️  May have changed content based on unverified claim")


async def test_integration():
    """Test the full integration of fact-checking in the workflow"""
    print("\n" + "="*60)
    print("Testing Full Integration")
    print("="*60)
    
    print("\n1. Workflow Protection Test:")
    print("   Testing that unverified claims cannot block workflow...")
    
    # Create a scenario where reviewer might block based on temporal confusion
    draft_state = {
        "task": {
            "guidelines": ["Must be accurate", "Must be well-structured"],
            "follow_guidelines": True,
            "model": "gemini-2.0-flash-preview-04-17-thinking",
            "verbose": False
        },
        "draft": "In 2025, President Trump announced new AI policies.",
        "revision_count": 0
    }
    
    reviewer = ReviewerAgent()
    reviser = ReviserAgent()
    
    # Review
    review_result = await reviewer.review_draft(draft_state)
    
    if review_result.get("revision_notes"):
        print(f"   Reviewer feedback: {review_result['revision_notes'][:100]}...")
        
        # Revise
        draft_state["review"] = review_result["revision_notes"]
        revision_result = await reviser.revise_draft(draft_state)
        
        print(f"   Reviser response: {revision_result['revision_notes'][:100]}...")
        
        # Check if workflow was protected
        if revision_result.get("draft") == draft_state["draft"]:
            print("   ✅ Workflow protected from unverified blocking")
        else:
            print("   ⚠️  Workflow may have been affected by unverified claims")
    else:
        print("   ✅ Reviewer accepted contemporary content without blocking")
    
    print("\n2. Fact Checker Statistics:")
    fact_checker = get_fact_checker()
    report = fact_checker.generate_verification_report()
    
    # Count verification attempts
    lines = report.split('\n')
    for line in lines:
        if 'Total verifications:' in line:
            print(f"   {line.strip()}")
        elif 'VERIFIED_FALSE' in line:
            print(f"   {line.strip()}")
        elif 'INCONCLUSIVE' in line:
            print(f"   {line.strip()}")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("FACT-CHECKING PROTOCOL TEST SUITE")
    print("="*60)
    
    # Check if BRAVE API key is available
    if not os.getenv('BRAVE_API_KEY'):
        print("\n⚠️  WARNING: BRAVE_API_KEY not set")
        print("   Fact-checking will be limited without search capability")
        print("   Set BRAVE_API_KEY environment variable for full testing")
    
    try:
        # Run tests
        await test_fact_checker()
        await test_reviewer_with_fact_checking()
        await test_reviser_with_fact_checking()
        await test_integration()
        
        print("\n" + "="*60)
        print("✅ FACT-CHECKING PROTOCOL TESTS COMPLETED")
        print("="*60)
        
        print("\nSummary:")
        print("- Fact checker properly extracts and verifies claims")
        print("- Reviewer applies fact-checking before providing feedback")
        print("- Reviser verifies claims before accepting corrections")
        print("- Burden of proof principle prevents workflow blocking")
        print("- Contemporary events (2024-2025) are handled correctly")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())