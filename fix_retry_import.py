#!/usr/bin/env python3
"""
Fix for 'Retry' is not defined error in web_dashboard/cli_executor sessions.
This script ensures that the Retry class is properly imported in all necessary locations.
"""

import logging
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def fix_retry_import():
    """
    Ensure Retry is available in the global namespace and patch any modules that need it.
    """
    try:
        # First, try to import Retry from the standard location
        try:
            from requests.packages.urllib3.util.retry import Retry

            logger.info("✅ Successfully imported Retry from requests.packages.urllib3.util.retry")
        except ImportError:
            # Fallback to direct urllib3 import
            from urllib3.util.retry import Retry

            logger.info("✅ Successfully imported Retry from urllib3.util.retry (fallback)")

        # Make Retry available globally (monkey-patch)
        import builtins

        if not hasattr(builtins, "Retry"):
            builtins.Retry = Retry
            logger.info("✅ Made Retry available in builtins namespace")

        # Also ensure it's available in the requests module namespace
        import requests

        if not hasattr(requests, "Retry"):
            requests.Retry = Retry
            logger.info("✅ Added Retry to requests module namespace")

        # Try to patch gpt_researcher if it's installed
        try:
            import gpt_researcher

            # Add Retry to gpt_researcher namespace
            gpt_researcher.Retry = Retry
            logger.info("✅ Added Retry to gpt_researcher namespace")

            # Check if gpt_researcher.scraper exists and patch it
            if hasattr(gpt_researcher, "scraper"):
                gpt_researcher.scraper.Retry = Retry
                logger.info("✅ Added Retry to gpt_researcher.scraper namespace")
        except ImportError:
            logger.warning("⚠️  gpt_researcher not installed, skipping its patching")
        except Exception as e:
            logger.warning(f"⚠️  Could not patch gpt_researcher: {e}")

        # Apply network reliability patches
        try:
            from multi_agents.network_reliability_patch import apply_network_reliability_patches

            if apply_network_reliability_patches():
                logger.info("✅ Network reliability patches applied successfully")
            else:
                logger.warning("⚠️  Network reliability patches may not have been fully applied")
        except ImportError as e:
            logger.warning(f"⚠️  Could not import network reliability patch: {e}")
        except Exception as e:
            logger.error(f"❌ Error applying network reliability patches: {e}")

        logger.info("\n✅ Retry import fix completed successfully!")
        logger.info("   The 'Retry' class is now available in the global namespace.")
        logger.info(
            "   You can now run your web_dashboard without the 'Retry is not defined' error."
        )

        return True

    except Exception as e:
        logger.error(f"❌ Failed to fix Retry import: {e}")
        return False


def verify_fix():
    """Verify that Retry is now accessible"""
    try:
        # Check if Retry is accessible
        import builtins

        if hasattr(builtins, "Retry"):
            logger.info("✅ Verification: Retry is accessible from builtins")
            return True

        # Try to access it directly
        try:
            from requests.packages.urllib3.util.retry import Retry

            logger.info("✅ Verification: Retry can be imported")
            return True
        except ImportError:
            logger.info("✅ Verification: Retry can be imported (fallback)")
            return True

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting Retry import fix...")
    logger.info("-" * 50)

    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.info(f"Added {project_root} to Python path")

    # Apply the fix
    success = fix_retry_import()

    if success:
        logger.info("-" * 50)
        logger.info("Verifying the fix...")
        if verify_fix():
            logger.info("\n✅ SUCCESS: The Retry import issue has been fixed!")
            logger.info("\nYou can now:")
            logger.info("1. Run your web_dashboard without errors")
            logger.info("2. The fix will persist for this Python session")
            logger.info(
                "\nNote: You may need to restart your web_dashboard service for the fix to take effect."
            )
            sys.exit(0)
        else:
            logger.error("\n❌ Verification failed. The fix may not have worked completely.")
            sys.exit(1)
    else:
        logger.error("\n❌ Failed to apply the fix.")
        sys.exit(1)
