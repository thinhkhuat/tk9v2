import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from ..utils.language_config import LanguageConfig
from .utils.file_formats import write_md_to_pdf, write_md_to_word, write_text_to_md
from .utils.type_safety import (
    ensure_dict,
    safe_dict_get,
    safe_string_operation,
)
from .utils.views import print_agent_output


class TranslatorAgent:
    """Agent responsible for professional translation of final research reports"""

    def __init__(
        self, websocket=None, stream_output=None, headers=None, draft_manager=None, output_dir=None
    ):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers
        self.draft_manager = draft_manager
        self.output_dir = output_dir
        # Endpoint health tracking - simple failure count per session
        self._endpoint_failures = {}

    def reset_endpoint_health(self) -> None:
        """Reset endpoint health tracking - useful for testing or long-running sessions"""
        self._endpoint_failures.clear()
        print_agent_output("Endpoint health tracking reset", agent="TRANSLATOR")

    def get_endpoint_health_status(self) -> Dict[str, int]:
        """Get current endpoint failure counts for debugging"""
        return self._endpoint_failures.copy()

    async def translate_report_file(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate the final research report by reading the markdown file created by the publisher.
        This is much simpler and more reliable than managing complex state transfers.

        Args:
            research_state: Dictionary containing the task information

        Returns:
            Dictionary with translation results
        """
        task = ensure_dict(research_state.get("task"), {"language": "vi"})
        target_language = safe_dict_get(task, "language", "vi", str)
        language_name = LanguageConfig.get_language_name(target_language)

        # Skip translation if target language is English
        target_lang_str = str(target_language) if target_language else "en"
        if target_lang_str.lower() == "en":
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "translation_skipped",
                    "Target language is English, skipping translation...",
                    self.websocket,
                )
            else:
                print_agent_output(
                    "Target language is English, skipping translation...", agent="TRANSLATOR"
                )
            return {"status": "skipped", "reason": "target_language_is_english"}

        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "translating_report",
                f"Translating final report files (.md, .pdf, .docx) to {language_name}...",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Translating final report files (.md, .pdf, .docx) to {language_name}...",
                agent="TRANSLATOR",
            )

        # Find the markdown file created by the publisher using the known output directory
        if not self.output_dir:
            error_msg = "No output directory provided to translator"
            print_agent_output(error_msg, agent="TRANSLATOR")
            return {"status": "error", "message": error_msg}

        # Look for markdown files in the output directory with type safety
        try:
            all_files = os.listdir(self.output_dir)
            markdown_files = []
            for f in all_files:
                if safe_string_operation(f, "endswith", ".md") and not safe_string_operation(
                    f, "startswith", "WORKFLOW"
                ):
                    markdown_files.append(f)
        except OSError as e:
            error_msg = f"Failed to list directory {self.output_dir}: {e}"
            print_agent_output(error_msg, agent="TRANSLATOR")
            return {"status": "error", "message": error_msg}

        if not markdown_files:
            error_msg = f"No markdown files found in output directory: {self.output_dir}"
            print_agent_output(error_msg, agent="TRANSLATOR")
            return {"status": "error", "message": error_msg}

        # Use the first (and typically only) markdown file
        markdown_file_path = os.path.join(self.output_dir, markdown_files[0])
        print_agent_output(
            f"Found markdown file to translate: {markdown_file_path}", agent="TRANSLATOR"
        )

        # Read the entire markdown file content
        try:
            with open(markdown_file_path, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception as e:
            error_msg = f"Failed to read markdown file: {e}"
            print_agent_output(error_msg, agent="TRANSLATOR")
            return {"status": "error", "message": error_msg}

        if not original_content.strip():
            error_msg = "Markdown file is empty"
            print_agent_output(error_msg, agent="TRANSLATOR")
            return {"status": "error", "message": error_msg}

        # Translate the entire file content
        translated_content = await self._translate_markdown_content(
            original_content, language_name, target_language, task
        )

        if not translated_content:
            error_msg = "Translation failed - empty result"
            print_agent_output(error_msg, agent="TRANSLATOR")
            return {"status": "error", "message": error_msg}

        # Generate translated files in all formats
        original_files = self._find_all_format_files(markdown_file_path)
        translated_files = await self._create_translated_files(
            translated_content, original_files, target_language, language_name
        )

        if not translated_files:
            error_msg = "Failed to create translated files"
            print_agent_output(error_msg, agent="TRANSLATOR")
            return {"status": "error", "message": error_msg}

        success_msg = f"Translation completed for {len(translated_files)} files: {', '.join(translated_files)}"
        print_agent_output(success_msg, agent="TRANSLATOR")

        # Save translation metadata
        if self.draft_manager:
            self.draft_manager.save_agent_output(
                agent_name="translator",
                phase="translation",
                output={
                    "original_files": original_files,
                    "translated_files": translated_files,
                    "target_language": target_language,
                    "status": "success",
                },
                step="translate_all_formats",
                metadata={
                    "language": target_language,
                    "language_name": language_name,
                    "original_size": len(original_content),
                    "translated_size": len(translated_content),
                    "formats_created": len(translated_files),
                },
            )

        return {
            "status": "success",
            "original_files": original_files,
            "translated_files": translated_files,
            "target_language": target_language,
            "language_name": language_name,
        }

    async def run(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for the Translator Agent.
        This is the FINAL agent in the workflow - it translates and saves files, then ends.

        Args:
            research_state: Current research state

        Returns:
            Updated research state with translation completion status
        """
        translation_result = await self.translate_report_file(research_state)

        # Save translation state
        if self.draft_manager:
            self.draft_manager.save_research_state(
                "translation", {**research_state, "translation_result": translation_result}
            )

        # Log translation completion
        if translation_result and isinstance(translation_result, dict):
            status = translation_result.get("status", "unknown")
            if status == "success":
                translated_files = translation_result.get("translated_files", [])
                print_agent_output(
                    f"Translation completed successfully. Created {len(translated_files)} files.",
                    agent="TRANSLATOR",
                )
                print_agent_output(
                    "Workflow complete - all files saved in both English and translated versions.",
                    agent="TRANSLATOR",
                )
            elif status == "skipped":
                print_agent_output(
                    "Translation skipped (English target). Workflow complete.", agent="TRANSLATOR"
                )
            else:
                print_agent_output(
                    f"Translation status: {status}. Workflow complete.", agent="TRANSLATOR"
                )

        # Return the state to end the workflow
        # DO NOT populate draft field - translator is the final agent
        return {
            **research_state,
            "translation_result": translation_result,
            "workflow_complete": True,  # Signal that workflow is complete
        }

    def _find_all_format_files(self, markdown_file_path: str) -> Dict[str, str]:
        """Find all format files (.md, .pdf, .docx) in the directory (UUIDs may differ)"""
        directory = os.path.dirname(markdown_file_path)

        format_files = {}

        # Find all files in directory by extension (since publisher creates different UUIDs)
        try:
            for filename in os.listdir(directory):
                # Use type-safe string operations
                if (
                    safe_string_operation(filename, "startswith", "WORKFLOW")
                    or safe_string_operation(filename, "startswith", ".")
                    or safe_string_operation(filename, "startswith", "~$")
                ):
                    continue  # Skip workflow files, hidden files, and temp files

                full_path = os.path.join(directory, filename)
                if os.path.isfile(full_path):
                    # Type-safe file extension checks
                    if safe_string_operation(
                        filename, "endswith", ".md"
                    ) and not safe_string_operation(filename, "endswith", "_vi.md"):
                        format_files["md"] = full_path
                    elif safe_string_operation(
                        filename, "endswith", ".pdf"
                    ) and not safe_string_operation(filename, "endswith", "_vi.pdf"):
                        format_files["pdf"] = full_path
                    elif safe_string_operation(
                        filename, "endswith", ".docx"
                    ) and not safe_string_operation(filename, "endswith", "_vi.docx"):
                        format_files["docx"] = full_path
        except OSError as e:
            print_agent_output(f"Error listing directory {directory}: {e}", agent="TRANSLATOR")

        print_agent_output(f"Found original files: {format_files}", agent="TRANSLATOR")
        return format_files

    async def _create_translated_files(
        self,
        translated_content: str,
        original_files: Dict[str, str],
        target_language: str,
        language_name: str,
    ) -> List[str]:
        """Create translated versions of all format files"""
        translated_files = []

        # Get the directory from any of the original files
        if not original_files:
            return translated_files

        directory = os.path.dirname(next(iter(original_files.values())))

        try:
            # Create markdown file first
            if "md" in original_files:
                md_path = await write_text_to_md(translated_content, directory)
                if md_path:
                    # Rename to include language suffix
                    translated_md_path = self._add_language_suffix(md_path, target_language)
                    os.rename(md_path, translated_md_path)
                    translated_files.append(translated_md_path)

                    # Create PDF if original had PDF
                    if "pdf" in original_files:
                        print_agent_output("Creating translated PDF...", agent="TRANSLATOR")
                        pdf_path = await write_md_to_pdf(translated_content, directory)
                        if pdf_path:
                            # Decode URL encoding and rename with language suffix
                            import urllib.parse

                            pdf_path = urllib.parse.unquote(pdf_path)
                            print_agent_output(f"PDF created at: {pdf_path}", agent="TRANSLATOR")

                            if os.path.exists(pdf_path):
                                translated_pdf_path = self._add_language_suffix(
                                    pdf_path, target_language
                                )
                                os.rename(pdf_path, translated_pdf_path)
                                translated_files.append(translated_pdf_path)
                                print_agent_output(
                                    f"PDF renamed to: {translated_pdf_path}", agent="TRANSLATOR"
                                )
                            else:
                                print_agent_output(
                                    f"PDF file not found at path: {pdf_path}", agent="TRANSLATOR"
                                )
                        else:
                            print_agent_output(
                                "PDF creation failed - no path returned", agent="TRANSLATOR"
                            )

                    # Create DOCX if original had DOCX
                    if "docx" in original_files:
                        print_agent_output("Creating translated DOCX...", agent="TRANSLATOR")
                        docx_path = await write_md_to_word(translated_content, directory)
                        if docx_path:
                            # Decode URL encoding and rename with language suffix
                            import urllib.parse

                            docx_path = urllib.parse.unquote(docx_path)
                            print_agent_output(
                                f"DOCX path returned: {docx_path}", agent="TRANSLATOR"
                            )

                            if os.path.exists(docx_path):
                                translated_docx_path = self._add_language_suffix(
                                    docx_path, target_language
                                )
                                os.rename(docx_path, translated_docx_path)
                                translated_files.append(translated_docx_path)
                                print_agent_output(
                                    f"DOCX renamed to: {translated_docx_path}", agent="TRANSLATOR"
                                )
                            else:
                                print_agent_output(
                                    f"DOCX file not found at path: {docx_path}", agent="TRANSLATOR"
                                )
                        else:
                            print_agent_output(
                                "DOCX creation failed - no path returned", agent="TRANSLATOR"
                            )

        except Exception as e:
            print_agent_output(f"Error creating translated files: {e}", agent="TRANSLATOR")

        return translated_files

    def _add_language_suffix(self, file_path: str, target_language: str) -> str:
        """Add language suffix to filename"""
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)

        # Create translated filename with language suffix
        translated_filename = f"{name}_{target_language}{ext}"
        return os.path.join(directory, translated_filename)

    async def _translate_markdown_content(
        self, content: str, language_name: str, target_language: str, task: Dict[str, Any]
    ) -> Optional[str]:
        """
        Translate the entire markdown content using dedicated translation endpoint

        Args:
            content: Original markdown content
            language_name: Full name of target language (e.g., "Vietnamese")
            target_language: Language code (e.g., "vi")
            task: Task configuration

        Returns:
            Translated markdown content
        """
        # Send entire content in one request to your endpoint
        print_agent_output(
            f"Translating complete document ({len(content)} chars) to {language_name}...",
            agent="TRANSLATOR",
        )

        translated_content = await self._translate_chunk_with_retry(
            content, language_name, target_language, task
        )

        if translated_content:
            print_agent_output(
                f"Translation successful: {len(translated_content)} chars", agent="TRANSLATOR"
            )

            # Return translated content as-is (markdown formatting is now preserved by endpoint)
            print_agent_output(
                f"Translation returned with preserved formatting: {len(translated_content)} chars",
                agent="TRANSLATOR",
            )

            return translated_content
        else:
            print_agent_output(
                "Translation failed - returning original content", agent="TRANSLATOR"
            )
            return content  # Fallback to original if translation fails

    async def _translate_chunk_with_retry(
        self,
        content: str,
        language_name: str,
        target_language: str,
        task: Dict[str, Any],
        max_retries: int = 2,
    ) -> Optional[str]:
        """Translate using concurrent requests to all endpoints with intelligent result selection"""

        print_agent_output(
            f"Starting concurrent translation to all endpoints ({len(content)} chars)...",
            agent="TRANSLATOR",
        )

        for attempt in range(max_retries):
            try:
                print_agent_output(
                    f"Concurrent translation attempt {attempt + 1}/{max_retries}",
                    agent="TRANSLATOR",
                )

                result = await self._translate_chunk_concurrent(
                    content, language_name, target_language, task
                )
                if result:
                    print_agent_output(
                        f"Concurrent translation successful on attempt {attempt + 1}",
                        agent="TRANSLATOR",
                    )
                    return result
                else:
                    print_agent_output(
                        f"Concurrent translation attempt {attempt + 1} failed (no valid results)",
                        agent="TRANSLATOR",
                    )
            except Exception as e:
                print_agent_output(
                    f"Concurrent translation attempt {attempt + 1} failed with error: {e}",
                    agent="TRANSLATOR",
                )

            if attempt < max_retries - 1:
                print_agent_output(
                    f"Retrying concurrent translation... (attempt {attempt + 2}/{max_retries})",
                    agent="TRANSLATOR",
                )

        print_agent_output(
            f"All {max_retries} concurrent translation attempts failed", agent="TRANSLATOR"
        )
        return None

    async def _translate_chunk_concurrent(
        self, content: str, language_name: str, target_language: str, task: dict
    ) -> str:
        """
        Translate content by sending concurrent requests to all endpoints.
        Simplified version that works correctly without as_completed issues.
        """
        import asyncio


        # Translation endpoints with priority order (1=highest priority)
        endpoints = [
            {
                "url": "https://n8n.thinhkhuat.com/webhook/agent/translate",
                "priority": 1,
                "name": "Primary",
            },
            {
                "url": "https://n8n.thinhkhuat.work/webhook/agent/translate",
                "priority": 2,
                "name": "Backup-1",
            },
            {
                "url": "https://srv.saola-great.ts.net/webhook/agent/translate",
                "priority": 3,
                "name": "Backup-2",
            },
        ]

        # Filter out endpoints that have failed too many times this session (but always try at least primary)
        healthy_endpoints = []
        for endpoint in endpoints:
            failure_count = self._endpoint_failures.get(endpoint["name"], 0)
            if failure_count < 3 or endpoint["priority"] == 1:  # Always include primary endpoint
                healthy_endpoints.append(endpoint)
            else:
                print_agent_output(
                    f"Skipping {endpoint['name']} - too many failures this session ({failure_count})",
                    agent="TRANSLATOR",
                )

        endpoints = healthy_endpoints

        # Prepare payload matching your endpoint schema
        payload = {
            "transcript": content,
            "sessionId": f"translator-{int(datetime.now().timestamp())}",
        }

        original_length = len(content)
        print_agent_output(
            f"Sending concurrent requests to {len(endpoints)} translation endpoints...",
            agent="TRANSLATOR",
        )
        print_agent_output(f"Original content: {original_length} chars", agent="TRANSLATOR")

        # Create concurrent tasks for all endpoints
        tasks = []
        for endpoint in endpoints:
            task = asyncio.create_task(self._translate_single_endpoint(endpoint, payload))
            tasks.append(task)

        # Wait for all tasks to complete with gather
        completed_results = []
        try:
            # Run all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(results):
                endpoint_info = endpoints[i]
                if isinstance(result, Exception):
                    print_agent_output(
                        f"Endpoint {endpoint_info['name']} failed with exception: {result}",
                        agent="TRANSLATOR",
                    )
                elif result and isinstance(result, dict) and result.get("success"):
                    completed_results.append(
                        {**result, "endpoint": endpoint_info, "priority": endpoint_info["priority"]}
                    )
                    print_agent_output(
                        f"Endpoint {endpoint_info['name']} completed successfully: {result.get('length', 0)} chars",
                        agent="TRANSLATOR",
                    )
                else:
                    print_agent_output(
                        f"Endpoint {endpoint_info['name']} returned no valid result",
                        agent="TRANSLATOR",
                    )

        except Exception as e:
            print_agent_output(f"Error during concurrent translation: {e}", agent="TRANSLATOR")

        # Select the best result using priority-based selection with validation
        if completed_results:
            selected_result = self._select_best_translation_result(
                completed_results, original_length
            )
            if selected_result:
                endpoint_name = selected_result["endpoint"]["name"]
                text_length = selected_result.get("length", 0)
                percentage = (
                    int((text_length / original_length) * 100) if original_length > 0 else 0
                )
                print_agent_output(
                    f"Final selection: {endpoint_name} with {text_length} chars ({percentage}% of original)",
                    agent="TRANSLATOR",
                )
                return selected_result.get("text")

        print_agent_output("No valid translation results from any endpoint", agent="TRANSLATOR")
        return None

    async def _wait_for_higher_priority(
        self, pending_tasks, task_to_endpoint, current_priority, completed_results, min_valid_length
    ):
        """
        Wait for higher priority endpoints to complete.
        Returns True if a higher priority valid result is found.
        """
        import asyncio

        # Filter for tasks with higher priority
        higher_priority_tasks = [
            task for task in pending_tasks if task_to_endpoint[task]["priority"] < current_priority
        ]

        if not higher_priority_tasks:
            return False

        # Wait for any of the higher priority tasks to complete
        done, pending = await asyncio.wait(
            higher_priority_tasks, return_when=asyncio.FIRST_COMPLETED, timeout=5.0
        )

        for task in done:
            try:
                result = await task
                endpoint_info = task_to_endpoint[task]

                if result and result.get("success") and result["length"] >= min_valid_length:
                    # Found a valid higher priority result
                    print_agent_output(
                        f"Higher priority endpoint {endpoint_info['name']} completed with valid result",
                        agent="TRANSLATOR",
                    )
                    completed_results.append(
                        {**result, "endpoint": endpoint_info, "priority": endpoint_info["priority"]}
                    )
                    return True
            except Exception:
                pass

        return False

    async def _translate_single_endpoint(
        self, endpoint: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send translation request to a single endpoint with configurable timeout"""
        import json


        endpoint_url = endpoint["url"]
        endpoint_name = endpoint["name"]

        # Get timeout from environment variable, default to 300 seconds (5 minutes)
        translation_timeout = int(os.getenv("TRANSLATION_TIMEOUT", "300"))

        try:
            # Only log start for primary endpoints to reduce noise
            if endpoint["priority"] <= 2:  # Only log for Primary and Backup-1
                print_agent_output(
                    f"Starting translation request to {endpoint_name}: {endpoint_url} (timeout: {translation_timeout}s)",
                    agent="TRANSLATOR",
                )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(
                        total=translation_timeout
                    ),  # Configurable timeout
                ) as response:

                    if response.status == 200:
                        result = await response.json()

                        # Log raw response structure for debugging (first 500 chars of response)
                        import json

                        try:
                            # Try to pretty print JSON for better debugging
                            result_preview = (
                                json.dumps(result, indent=2)[:1000] if result else "None"
                            )
                        except:
                            result_preview = str(result)[:1000] if result else "None"
                        print_agent_output(
                            f"Raw response from {endpoint_name}: {result_preview}",
                            agent="TRANSLATOR_DEBUG",
                        )

                        # Try multiple possible field structures
                        # 1. Direct fields at root level
                        translated_text = (
                            result.get("response") or result.get("output") or result.get("text")
                        )

                        # 2. Check for nested structures (common in webhook responses)
                        if not translated_text and isinstance(result, dict):
                            # Check for data.output or data.response structure
                            if "data" in result and isinstance(result["data"], dict):
                                translated_text = (
                                    result["data"].get("output")
                                    or result["data"].get("response")
                                    or result["data"].get("text")
                                )
                            # Check for result.output or result.response structure
                            elif "result" in result and isinstance(result["result"], dict):
                                translated_text = (
                                    result["result"].get("output")
                                    or result["result"].get("response")
                                    or result["result"].get("text")
                                )
                            # Check for body.output structure (common in webhook responses)
                            elif "body" in result and isinstance(result["body"], dict):
                                translated_text = (
                                    result["body"].get("output")
                                    or result["body"].get("response")
                                    or result["body"].get("text")
                                )

                        # 3. If still no text, check if the entire result is a string (direct response)
                        if not translated_text and isinstance(result, str):
                            translated_text = result

                        # 4. Last resort: check for any large text field in the response
                        if not translated_text and isinstance(result, dict):
                            # Find the largest string value in the response
                            for key, value in result.items():
                                if (
                                    isinstance(value, str) and len(value) > 1000
                                ):  # Likely to be the translation if > 1000 chars
                                    print_agent_output(
                                        f"Found potential translation in field '{key}' with {len(value)} chars",
                                        agent="TRANSLATOR_DEBUG",
                                    )
                                    translated_text = value
                                    break

                        if translated_text and isinstance(translated_text, str):
                            cleaned_response = translated_text.strip()

                            # Enhanced validation: check if it's actually translated (not English)
                            # Simple heuristic: Vietnamese text should have Vietnamese characters or be significantly different
                            if cleaned_response and cleaned_response not in [
                                "",
                                "...",
                                "…",
                                "N/A",
                                "None",
                            ]:
                                # Log first 200 chars of translation for verification
                                preview = (
                                    cleaned_response[:200] + "..."
                                    if len(cleaned_response) > 200
                                    else cleaned_response
                                )
                                print_agent_output(
                                    f"Translation preview from {endpoint_name}: {preview}",
                                    agent="TRANSLATOR",
                                )

                                # Check if response looks like it's still in English (basic heuristic)
                                # This helps detect when the endpoint returns the original text unchanged
                                english_indicators = [
                                    "the",
                                    "and",
                                    "of",
                                    "to",
                                    "in",
                                    "a",
                                    "is",
                                    "that",
                                    "for",
                                    "with",
                                ]
                                first_500_chars = cleaned_response[:500].lower()
                                english_word_count = sum(
                                    1
                                    for word in english_indicators
                                    if f" {word} " in first_500_chars
                                )

                                if english_word_count > 10:  # If too many English words found
                                    print_agent_output(
                                        f"WARNING: Response from {endpoint_name} appears to still be in English (found {english_word_count} common English words). The endpoint may have returned the original text unchanged.",
                                        agent="TRANSLATOR",
                                    )
                                    # Still return it but mark as potentially untranslated
                                    return {
                                        "success": True,
                                        "text": cleaned_response,
                                        "length": len(cleaned_response),
                                        "endpoint_name": endpoint_name,
                                        "warning": "possibly_untranslated",
                                    }

                                print_agent_output(
                                    f"Translation successful from {endpoint_name}: {len(cleaned_response)} chars",
                                    agent="TRANSLATOR",
                                )

                                return {
                                    "success": True,
                                    "text": cleaned_response,
                                    "length": len(cleaned_response),
                                    "endpoint_name": endpoint_name,
                                }
                            else:
                                print_agent_output(
                                    f"Endpoint {endpoint_name} returned empty/placeholder: '{cleaned_response}'",
                                    agent="TRANSLATOR",
                                )
                                return {
                                    "success": False,
                                    "endpoint_name": endpoint_name,
                                    "reason": "empty_response",
                                }
                        else:
                            # Log the actual structure for debugging
                            print_agent_output(
                                f"Endpoint {endpoint_name} returned unexpected structure. Type: {type(translated_text)}, Keys: {result.keys() if isinstance(result, dict) else 'N/A'}",
                                agent="TRANSLATOR",
                            )
                            return {
                                "success": False,
                                "endpoint_name": endpoint_name,
                                "reason": "invalid_structure",
                            }
                    else:
                        # Intelligent error handling based on status code and endpoint
                        error_text = await response.text()
                        self._handle_http_error(
                            endpoint_name, response.status, error_text, endpoint_url
                        )

        except asyncio.TimeoutError:
            # Count timeouts as failures for non-Backup-2 endpoints
            if not ("saola-great.ts.net" in endpoint_url or "Backup-2" in endpoint_name):
                self._endpoint_failures[endpoint_name] = (
                    self._endpoint_failures.get(endpoint_name, 0) + 1
                )
            print_agent_output(
                f"Endpoint {endpoint_name} timed out after {translation_timeout} seconds. Consider increasing TRANSLATION_TIMEOUT env var if translations are completing but timing out.",
                agent="TRANSLATOR",
            )
        except aiohttp.ClientError as e:
            # Count connection errors as failures for non-Backup-2 endpoints
            if not ("saola-great.ts.net" in endpoint_url or "Backup-2" in endpoint_name):
                self._endpoint_failures[endpoint_name] = (
                    self._endpoint_failures.get(endpoint_name, 0) + 1
                )
            print_agent_output(
                f"Endpoint {endpoint_name} connection error: {e}", agent="TRANSLATOR"
            )
        except json.JSONDecodeError as e:
            # JSON decode errors are always counted as failures
            self._endpoint_failures[endpoint_name] = (
                self._endpoint_failures.get(endpoint_name, 0) + 1
            )
            print_agent_output(
                f"Endpoint {endpoint_name} JSON decode error: {e}", agent="TRANSLATOR"
            )
        except Exception as e:
            # Other unexpected errors are always counted as failures
            self._endpoint_failures[endpoint_name] = (
                self._endpoint_failures.get(endpoint_name, 0) + 1
            )
            print_agent_output(
                f"Endpoint {endpoint_name} unexpected error: {e}", agent="TRANSLATOR"
            )

        return {"success": False, "endpoint_name": endpoint_name}

    def _handle_http_error(
        self, endpoint_name: str, status_code: int, error_text: str, endpoint_url: str
    ) -> None:
        """Handle HTTP errors with appropriate logging levels based on error type and endpoint"""

        # Track failures for health monitoring (but don't count expected 502s as failures)
        if not (
            status_code == 502
            and ("saola-great.ts.net" in endpoint_url or "Backup-2" in endpoint_name)
        ):
            self._endpoint_failures[endpoint_name] = (
                self._endpoint_failures.get(endpoint_name, 0) + 1
            )

        # Expected service unavailability (especially for Backup-2 which is known to be offline)
        if status_code == 502:
            # 502 Bad Gateway - service is down/unavailable (expected for some endpoints)
            if "saola-great.ts.net" in endpoint_url or "Backup-2" in endpoint_name:
                # This is expected for the Tailscale endpoint - no logging to reduce noise
                pass
            else:
                # Unexpected 502 from primary services - log as warning
                print_agent_output(
                    f"Endpoint {endpoint_name} service unavailable (502) - may be temporarily down",
                    agent="TRANSLATOR",
                )

        elif status_code in [503, 504]:
            # 503 Service Unavailable, 504 Gateway Timeout - temporary issues
            print_agent_output(
                f"Endpoint {endpoint_name} temporarily unavailable ({status_code})",
                agent="TRANSLATOR",
            )

        elif status_code == 429:
            # Rate limiting
            print_agent_output(
                f"Endpoint {endpoint_name} rate limited (429) - backing off", agent="TRANSLATOR"
            )

        elif status_code in [400, 401, 403]:
            # Client errors that indicate configuration issues
            print_agent_output(
                f"Endpoint {endpoint_name} client error ({status_code}): {error_text[:100]}",
                agent="TRANSLATOR",
            )

        elif status_code in [500, 501, 505]:
            # Server errors that are unexpected
            print_agent_output(
                f"Endpoint {endpoint_name} server error ({status_code}): {error_text[:100]}",
                agent="TRANSLATOR",
            )

        else:
            # Other HTTP errors
            print_agent_output(
                f"Endpoint {endpoint_name} HTTP error ({status_code}): {error_text[:100]}",
                agent="TRANSLATOR",
            )

    def _select_best_translation_result(
        self, results: List[Dict[str, Any]], original_length: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Select translation result based on priority order with character count validation:
        1. Priority 1: n8n.thinhkhuat.com (Primary)
        2. Priority 2: n8n.thinhkhuat.work (Backup-1)
        3. Priority 3: srv.saola-great.ts.net (Backup-2)

        Validation rules:
        - Must have ≥90% of original character count to be preferred
        - Must have ≥70% of original character count to be valid
        - Must have ≤150% of original character count to be valid
        - Prefer results without translation warnings
        """
        if not results:
            return None

        print_agent_output(
            f"Selecting from {len(results)} translations using priority-based selection:",
            agent="TRANSLATOR",
        )

        # Separate results with warnings from clean results
        clean_results = [r for r in results if not r.get("warning")]
        warned_results = [r for r in results if r.get("warning")]

        # Prefer clean results over warned results
        sorted_results = sorted(clean_results, key=lambda x: x["priority"]) + sorted(
            warned_results, key=lambda x: x["priority"]
        )

        # Log all results for comparison
        for result in sorted_results:
            endpoint_name = result["endpoint"]["name"]
            priority = result["priority"]
            length = result.get("length", 0)
            warning = " [WARNING: possibly untranslated]" if result.get("warning") else ""
            print_agent_output(
                f"  Priority {priority} - {endpoint_name}: {length} chars{warning}",
                agent="TRANSLATOR",
            )

        # Try to get original length from the first result's context if not provided
        if original_length is None and sorted_results:
            # Estimate from average - translations are usually similar to original
            original_length = int(
                sum(r.get("length", 0) for r in sorted_results) / len(sorted_results)
            )
            print_agent_output(
                f"Estimated original length: {original_length} chars", agent="TRANSLATOR"
            )

        # Define validation thresholds
        min_preferred = int(original_length * 0.9) if original_length else 0  # 90% for preferred
        min_valid = int(original_length * 0.7) if original_length else 0  # 70% minimum
        max_valid = int(original_length * 1.5) if original_length else float("inf")  # 150% maximum

        print_agent_output(
            f"Validation thresholds - Min preferred: {min_preferred}, Min valid: {min_valid}, Max valid: {max_valid}",
            agent="TRANSLATOR",
        )

        # Check each result in priority order
        for result in sorted_results:
            length = result.get("length", 0)
            endpoint_name = result["endpoint"]["name"]
            priority = result["priority"]

            # Check if within valid range (70% - 150%)
            if min_valid <= length <= max_valid:
                # Check if meets preferred threshold (≥90%)
                if length >= min_preferred:
                    print_agent_output(
                        f"Selected Priority {priority} ({endpoint_name}): {length} chars - meets preferred threshold",
                        agent="TRANSLATOR",
                    )
                    return result
                else:
                    # Valid but not preferred (70-89%), continue checking higher priority
                    print_agent_output(
                        f"Priority {priority} ({endpoint_name}): {length} chars - valid but below preferred (continuing)",
                        agent="TRANSLATOR",
                    )
            else:
                # Outside valid range
                if length < min_valid:
                    print_agent_output(
                        f"Priority {priority} ({endpoint_name}): {length} chars - too short (<70%)",
                        agent="TRANSLATOR",
                    )
                else:
                    print_agent_output(
                        f"Priority {priority} ({endpoint_name}): {length} chars - too long (>150%)",
                        agent="TRANSLATOR",
                    )

        # If no result meets preferred threshold, select first valid result
        for result in sorted_results:
            length = result.get("length", 0)
            if min_valid <= length <= max_valid:
                endpoint_name = result["endpoint"]["name"]
                priority = result["priority"]
                print_agent_output(
                    f"Selected Priority {priority} ({endpoint_name}): {length} chars - first valid result",
                    agent="TRANSLATOR",
                )
                return result

        # No valid results found
        print_agent_output(
            "No translation results within valid range (70%-150% of original)", agent="TRANSLATOR"
        )
        return None
