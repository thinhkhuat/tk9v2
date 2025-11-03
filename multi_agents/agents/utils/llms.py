import json5 as json
import json_repair
from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion
from langchain_community.adapters.openai import convert_openai_messages
from loguru import logger

from .date_context import format_system_prompt_with_date, get_current_date_context


async def call_model(
    prompt: list,
    model: str,
    response_format: str = None,
):
    # Ensure provider configuration is applied before creating Config

    from ...providers.factory import enhanced_config

    # Re-apply configuration to ensure environment variables are set
    if enhanced_config:
        enhanced_config.apply_to_environment()

    # Language configuration removed - research agents should work in English for best source quality
    # Only the final translation step will convert to target language

    cfg = Config()

    # Log provider info for debugging (can be commented out in production)
    # print(f"DEBUG: SMART_LLM from env: {os.getenv('SMART_LLM')}")
    # print(f"DEBUG: smart_llm_provider: {cfg.smart_llm_provider}")

    # Inject date context into system prompts for temporal awareness
    enhanced_prompt = prompt.copy()
    get_current_date_context()

    # Find and enhance system messages with date context
    for i, msg in enumerate(enhanced_prompt):
        if msg.get("role") == "system":
            original_content = msg["content"]
            # Add date context if not already present
            if (
                "current year" not in original_content.lower()
                and "today's date" not in original_content.lower()
            ):
                enhanced_prompt[i]["content"] = format_system_prompt_with_date(original_content)

    lc_messages = convert_openai_messages(enhanced_prompt)

    # Set up optional parameters for JSON responses
    llm_kwargs = cfg.llm_kwargs.copy() if cfg.llm_kwargs else {}
    if response_format == "json":
        # For Google Gemini models, we need to use the proper JSON schema format
        if cfg.smart_llm_provider == "google_genai":
            # Add JSON generation config for Google Gemini
            llm_kwargs.update({"generation_config": {"response_mime_type": "application/json"}})
        else:
            # For OpenAI-compatible models
            llm_kwargs.update({"response_format": {"type": "json_object"}})

    try:
        # For Google Gemini, we need to ensure the model name doesn't include provider prefix
        if cfg.smart_llm_provider == "google_genai" and model.startswith("google_genai:"):
            model = model.replace("google_genai:", "")

        response = await create_chat_completion(
            model=model,
            messages=lc_messages,
            temperature=0,
            llm_provider=cfg.smart_llm_provider,
            llm_kwargs=llm_kwargs,
            # cost_callback=cost_callback,
        )

        if response_format == "json":
            # Check if response is already a dictionary (pre-parsed JSON)
            if isinstance(response, dict):
                return response

            # Convert response to string if it's not already
            if not isinstance(response, str):
                response = str(response)

            # Robust JSON parsing that works with both OpenAI and Gemini responses
            def extract_json_from_response(text):
                """Extract JSON from various response formats"""
                import re

                # First, try the response as-is (for properly formatted responses)
                try:
                    return json.loads(text.strip())
                except:
                    pass

                # Clean markdown code blocks (common in Gemini responses)
                cleaned = text.strip()

                # Remove markdown code blocks - handle various patterns
                patterns_to_remove = [
                    r"```json\s*",  # ```json at start
                    r"```javascript\s*",  # ```javascript at start
                    r"```JSON\s*",  # ```JSON at start (uppercase)
                    r"```\s*",  # ``` at start
                    r"\s*```$",  # ``` at end
                    r"^JSON:\s*",  # JSON: at start
                    r"^json:\s*",  # json: at start
                    r"^Here\'s the JSON:\s*",  # Common Gemini pattern
                    r"^Here is the JSON:\s*",  # Common Gemini pattern
                ]

                for pattern in patterns_to_remove:
                    cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE | re.IGNORECASE)

                # Try parsing after markdown removal
                try:
                    return json.loads(cleaned.strip())
                except:
                    pass

                # Extract JSON object from text (find first { to last })
                try:
                    start_idx = cleaned.find("{")
                    if start_idx != -1:
                        # Find matching closing brace
                        brace_count = 0
                        end_idx = start_idx
                        for i, char in enumerate(cleaned[start_idx:], start_idx):
                            if char == "{":
                                brace_count += 1
                            elif char == "}":
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i
                                    break

                        if brace_count == 0:  # Found complete JSON object
                            json_str = cleaned[start_idx : end_idx + 1]
                            return json.loads(json_str)
                except:
                    pass

                # Try JSON array extraction [...]
                try:
                    start_idx = cleaned.find("[")
                    if start_idx != -1:
                        bracket_count = 0
                        end_idx = start_idx
                        for i, char in enumerate(cleaned[start_idx:], start_idx):
                            if char == "[":
                                bracket_count += 1
                            elif char == "]":
                                bracket_count -= 1
                                if bracket_count == 0:
                                    end_idx = i
                                    break

                        if bracket_count == 0:  # Found complete JSON array
                            json_str = cleaned[start_idx : end_idx + 1]
                            return json.loads(json_str)
                except:
                    pass

                # Try json_repair on the cleaned text first
                try:
                    return json_repair.loads(cleaned)
                except:
                    pass

                # Last resort: try json_repair on original text
                try:
                    return json_repair.loads(text)
                except:
                    pass

                # Final attempt: try to fix common JSON issues manually
                # Remove trailing commas, fix quotes, etc.
                try:
                    fixed = re.sub(r",\s*}", "}", cleaned)  # Remove trailing commas before }
                    fixed = re.sub(r",\s*]", "]", fixed)  # Remove trailing commas before ]
                    fixed = re.sub(
                        r"([{,]\s*)(\w+):", r'\1"\2":', fixed
                    )  # Add quotes to unquoted keys
                    return json.loads(fixed)
                except:
                    pass

                raise ValueError(f"Could not parse JSON from response: {text[:200]}...")

            try:
                return extract_json_from_response(response)
            except Exception as e:
                print("⚠️ Error in reading JSON, attempting to repair JSON")
                print(f"Response that failed to parse: {response[:1000] if response else 'None'}")
                logger.error(
                    f"JSON parsing failed for response preview: {response[:500] if response else 'None'}..."
                )
                logger.error(f"Error details: {str(e)}")
                logger.error(f"Response type: {type(response)}, Provider: {cfg.smart_llm_provider}")
                # Return the original response as string if all parsing fails
                return response
        else:
            return response

    except Exception as e:
        print("⚠️ Error in calling model")
        logger.error(f"Error in calling model: {e}")


# REMOVED: Language constraints function that was severely limiting research quality
# by forcing agents to search in non-English languages with poor, outdated sources.
# Research agents now work in English for best source quality, with translation only at the end.

# def _apply_language_to_prompt(prompt: list) -> list:
#     """Apply language configuration to prompts - DISABLED FOR RESEARCH QUALITY"""
#     return prompt  # No language constraints for research agents
