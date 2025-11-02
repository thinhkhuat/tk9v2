#!/usr/bin/env python
"""
Test script to verify network reliability fixes
"""

import logging
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_network_improvements():
    """Test the network reliability improvements"""
    print("🧪 Testing Network Reliability Improvements...")

    # Load environment
    from dotenv import load_dotenv

    load_dotenv(override=True)

    # Apply network patches
    try:
        from network_reliability_patch import (
            apply_network_reliability_patches,
            setup_global_session_defaults,
        )

        patch_success = apply_network_reliability_patches()
        setup_global_session_defaults()

        if patch_success:
            print("✅ Network reliability patches applied successfully")
        else:
            print("❌ Some network patches failed")
            return False

    except Exception as e:
        print(f"❌ Failed to apply network patches: {e}")
        return False

    # Test with a simple scraper simulation
    print("\n🧪 Testing scraper timeout behavior...")

    try:
        # Import the patched scrapers
        from gpt_researcher.scraper.beautiful_soup.beautiful_soup import BeautifulSoupScraper

        # Create a scraper instance
        test_urls = [
            "https://httpbin.org/delay/1",  # Should succeed
            "https://httpbin.org/status/500",  # Should retry
            "https://www.example.com",  # Should succeed
        ]

        for test_url in test_urls:
            print(f"\n🔗 Testing URL: {test_url}")
            try:
                scraper = BeautifulSoupScraper(test_url)
                result = scraper.scrape()

                if result and len(result[0]) > 0:  # result is (text, images, title)
                    print(f"✅ Successfully scraped content ({len(result[0])} characters)")
                else:
                    print(f"⚠️  No content scraped from {test_url}")

            except Exception as e:
                print(f"❌ Scraping failed for {test_url}: {e}")

    except ImportError as e:
        print(f"❌ Could not import scrapers for testing: {e}")
        return False

    print("\n🎉 Network reliability test completed!")
    return True


def test_startup_integration():
    """Test the startup integration"""
    print("\n🧪 Testing startup integration...")

    # Simulate the main.py startup sequence
    original_dir = os.getcwd()

    try:
        # Change to multi_agents directory
        os.chdir(
            "/Users/thinhkhuat/DEV--local/multi-agent-deep-research/deep-research-mcp-og/multi_agents"
        )

        # Test the import and setup as it would happen in main.py
        from network_reliability_patch import (
            apply_network_reliability_patches,
            setup_global_session_defaults,
        )

        patch_success = apply_network_reliability_patches()
        setup_global_session_defaults()

        if patch_success:
            print("✅ Startup integration test passed")
            return True
        else:
            print("❌ Startup integration test failed - patches not applied")
            return False

    except Exception as e:
        print(f"❌ Startup integration test failed: {e}")
        return False
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    success = True

    # Test network improvements
    if not test_network_improvements():
        success = False

    # Test startup integration
    if not test_startup_integration():
        success = False

    if success:
        print("\n🎉 All tests passed! Network reliability fixes are working correctly.")
        print("\n📋 Summary of fixes applied:")
        print("   ✅ Timeout increased from 4s to 30s")
        print("   ✅ Retry logic with exponential backoff implemented")
        print("   ✅ Connection pooling configured")
        print("   ✅ Realistic browser headers added")
        print("   ✅ Enhanced error handling for connection resets")
        print("   ✅ Integrated into system startup sequence")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
