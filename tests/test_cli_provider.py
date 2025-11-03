#!/usr/bin/env python3
"""
Test script to check what provider message appears when starting the interactive CLI
"""

import subprocess
import sys
import time


def test_cli_provider_message():
    print("🧪 Testing Interactive CLI Provider Message")
    print("=" * 50)

    # Start the interactive CLI
    proc = subprocess.Popen(
        ["uv", "run", "python", "-m", "main"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    try:
        # Send a simple test query
        proc.stdin.write("Test provider configuration\n")
        proc.stdin.flush()

        # Wait a bit for output
        time.sleep(3)

        # Send quit command
        proc.stdin.write("/quit\n")
        proc.stdin.flush()

        # Get output
        stdout, _ = proc.communicate(timeout=10)

        # Look for the PROVIDERS line
        lines = stdout.split("\n")
        for line in lines:
            if "PROVIDERS:" in line:
                print(f"🎯 Found provider line: {line.strip()}")

                if "google_gemini" in line and "google" in line:
                    print("✅ SUCCESS: Correct providers detected!")
                    return True
                elif "openai" in line and "tavily" in line:
                    print("❌ FAILURE: Still using old providers")
                    return False
                else:
                    print("⚠️  UNKNOWN: Unexpected provider configuration")
                    return False

        print("❓ No PROVIDERS line found in output")
        print("\nFirst 20 lines of output:")
        for i, line in enumerate(lines[:20]):
            if line.strip():
                print(f"  {i + 1}: {line}")

        return False

    except subprocess.TimeoutExpired:
        proc.kill()
        print("❌ Test timed out")
        return False
    except Exception as e:
        proc.kill()
        print(f"❌ Test error: {e}")
        return False


if __name__ == "__main__":
    success = test_cli_provider_message()
    sys.exit(0 if success else 1)
