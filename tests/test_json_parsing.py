#!/usr/bin/env python3

import asyncio
import sys

sys.path.append(".")

from multi_agents.agents.utils.llms import call_model


async def test_json_parsing():
    """Test JSON parsing with Google Gemini"""

    simple_prompt = [
        {"role": "system", "content": "You are a helpful assistant that returns JSON responses."},
        {
            "role": "user",
            "content": """Please return a simple JSON object with the following structure:
            {
              "title": "Test Title",
              "message": "This is a test message",
              "status": "success"
            }
            
            Return ONLY valid JSON, nothing else.""",
        },
    ]

    print("Testing JSON parsing with Google Gemini...")
    try:
        # Test with the configured Gemini model
        result = await call_model(
            prompt=simple_prompt, model="gemini-2.5-flash-preview-05-20", response_format="json"
        )

        print(f"Success! Result type: {type(result)}")
        print(f"Result: {result}")

        if isinstance(result, dict):
            print("✅ JSON parsing successful!")
        else:
            print("❌ JSON parsing failed - returned string")
            print(f"Raw response: {result}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_json_parsing())
