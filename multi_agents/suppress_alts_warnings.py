#!/usr/bin/env python
"""
Suppress ALTS credentials warnings from Google libraries.

These warnings appear when using Google Generative AI (Gemini) outside of GCP:
"ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled."

The warnings are harmless but create log noise. This module suppresses them.
"""

import logging
import os
import warnings


def suppress_alts_warnings():
    """
    Suppress ALTS-related warnings that appear when using Google libraries outside GCP.

    This function should be called early in the application startup, before importing
    any Google libraries.
    """

    # Method 1: Set environment variable to disable gRPC warnings
    os.environ["GRPC_VERBOSITY"] = "ERROR"

    # Method 2: Filter out the specific warning pattern
    warnings.filterwarnings("ignore", message=".*ALTS creds ignored.*")

    # Method 3: Suppress gRPC logging for ALTS-specific messages
    # gRPC uses its own logging system that outputs to stderr
    grpc_logger = logging.getLogger("grpc._cython.cygrpc")
    grpc_logger.setLevel(logging.ERROR)

    # Method 4: Suppress C++ gRPC logs by setting environment variable
    # This is the most effective for the E0000 ALTS messages
    os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "false"
    os.environ["GRPC_PYTHON_LOG_LEVEL"] = "error"

    # Method 5: Redirect stderr temporarily during Google library import
    # This is handled in the import wrapper below


def safe_import_google_genai():
    """
    Import Google Generative AI library with ALTS warnings suppressed.

    Returns:
        The google.generativeai module, or None if import fails
    """
    import io
    from contextlib import redirect_stderr

    # Suppress warnings before import
    suppress_alts_warnings()

    # Temporarily redirect stderr to suppress C++ ALTS warnings during import
    stderr_buffer = io.StringIO()

    try:
        with redirect_stderr(stderr_buffer):
            import google.generativeai as genai

        # Check if there were ALTS warnings and log them at debug level only
        stderr_content = stderr_buffer.getvalue()
        if "ALTS creds ignored" in stderr_content:
            logging.debug("Suppressed ALTS warning during google.generativeai import")

        return genai

    except ImportError as e:
        logging.error(f"Failed to import google.generativeai: {e}")
        return None
    finally:
        stderr_buffer.close()


# Apply suppressions immediately when this module is imported
suppress_alts_warnings()
