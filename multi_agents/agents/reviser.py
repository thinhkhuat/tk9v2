# from .utils.fact_checker import get_fact_checker, VerificationStatus, FeedbackCategory  # DISABLED - fact-checking removed
import json

from .utils.llms import call_model
from .utils.type_safety import safe_dict_get
from .utils.views import print_agent_output

sample_revision_notes = """
{
  "draft": { 
    draft title: The revised draft that you are submitting for review 
  },
  "revision_notes": Your message to the reviewer about the changes you made to the draft based on their feedback
}
"""


class ReviserAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None, draft_manager=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.draft_manager = draft_manager

    async def revise_draft(self, draft_state: dict):
        """
        Review a draft article with fact-checking protocol
        :param draft_state:
        :return: Dictionary with revised draft and notes
        """
        review = draft_state.get("review")
        task = draft_state.get("task")
        draft_report = draft_state.get("draft")
        revision_count = draft_state.get("revision_count", 0)

        # Handle case where no review feedback is provided
        if not review:
            return {
                **draft_state,
                "draft": draft_report,
                "revision_notes": "No review feedback provided, keeping original draft",
                "revision_count": revision_count,
            }

        # Handle case where no draft is provided
        if not draft_report:
            return {
                **draft_state,
                "draft": "",
                "revision_notes": "No draft content provided for revision",
                "revision_count": revision_count,
            }

        # FEEDBACK VERIFICATION PROTOCOL: Check categorization and apply appropriate processing
        print_agent_output(
            "🔍 Verifying review feedback categorization and content...", agent="REVISOR"
        )

        # Get fact checker instance - DISABLED
        # fact_checker = get_fact_checker()

        # Get categorization from reviewer if available, otherwise re-categorize
        feedback_category_str = draft_state.get("feedback_category")
        draft_state.get("feedback_analysis")

        if feedback_category_str:
            try:
                # feedback_category = FeedbackCategory(feedback_category_str)  # DISABLED
                feedback_category = None
                print_agent_output("📋 Fact-checking disabled", agent="REVISOR")
            except ValueError:
                # Fallback to re-categorization with error handling
                try:
                    # feedback_category, feedback_analysis = fact_checker.categorize_feedback(review)  # DISABLED
                    feedback_category, _feedback_analysis = None, {"disabled": True}
                    print_agent_output("🔄 Fact-checking disabled", agent="REVISOR")
                except Exception as e:
                    print_agent_output(
                        f"⚠️ Error categorizing feedback: {e}. Using CONTENT category as default.",
                        agent="REVISOR",
                    )
                    feedback_category = None
                    {"error": str(e), "fallback": True}
        else:
            # Categorize the feedback with error handling
            try:
                # feedback_category, feedback_analysis = fact_checker.categorize_feedback(review)  # DISABLED
                feedback_category, _feedback_analysis = None, {"disabled": True}
                print_agent_output("📊 Fact-checking disabled", agent="REVISOR")
            except Exception as e:
                print_agent_output(
                    f"⚠️ Error categorizing feedback: {e}. Using CONTENT category as default.",
                    agent="REVISOR",
                )
                feedback_category = None
                {"error": str(e), "fallback": True}

        # Apply appropriate processing based on category - DISABLED
        if False:  # feedback_category == FeedbackCategory.FORMATTING:
            print_agent_output(
                "✅ FORMATTING feedback - applying changes without fact-checking", agent="REVISOR"
            )
            # Skip fact-checking for pure formatting feedback

        elif False:  # feedback_category == FeedbackCategory.HYBRID:
            print_agent_output(
                "🔍 HYBRID feedback - double-checking for disguised content changes",
                agent="REVISOR",
            )
            # For hybrid, do a more careful analysis
            factual_claims = fact_checker.extract_factual_claims(review)
            if factual_claims:
                print_agent_output(
                    f"⚠️ Found {len(factual_claims)} potential factual claims in hybrid feedback",
                    agent="REVISOR",
                )
            else:
                print_agent_output(
                    "✅ Hybrid feedback contains no extractable factual claims", agent="REVISOR"
                )

        elif False:  # feedback_category == FeedbackCategory.CONTENT:
            print_agent_output(
                "🔍 CONTENT feedback requires full fact-checking verification", agent="REVISOR"
            )

        # Check if we need to fact-check based on category - DISABLED
        if False:  # fact_checker.should_fact_check(feedback_category):
            # Extract factual claims for verification
            factual_claims = fact_checker.extract_factual_claims(review)

            if factual_claims:
                print_agent_output(
                    f"📊 Found {len(factual_claims)} factual claims in review feedback",
                    agent="REVISOR",
                )

                # Verify each claim before accepting it
                verified_claims = []
                rejected_claims = []

                for claim in factual_claims:
                    result = await fact_checker.verify_claim(claim, context=draft_report)

                    if (
                        result.status == VerificationStatus.VERIFIED_FALSE
                        and result.confidence > 0.8
                    ):
                        # This is a valid correction we should apply
                        verified_claims.append(claim)
                        print_agent_output(
                            f"✅ Accepting verified correction: {claim[:100]}...", agent="REVISOR"
                        )
                    elif result.status == VerificationStatus.INCONCLUSIVE:
                        # Cannot verify - apply burden of proof
                        rejected_claims.append(claim)
                        print_agent_output(
                            f"❓ Rejecting inconclusive claim: {claim[:100]}...", agent="REVISOR"
                        )
                    elif result.status == VerificationStatus.VERIFIED_TRUE:
                        # The original was correct, reviewer was wrong
                        rejected_claims.append(claim)
                        print_agent_output(
                            f"❌ Rejecting false correction (original was correct): {claim[:100]}...",
                            agent="REVISOR",
                        )

            # Filter review to only include verified corrections
            if rejected_claims and not verified_claims:
                print_agent_output(
                    "⚠️ All factual claims in review were rejected - keeping original draft",
                    agent="REVISOR",
                )
                return {
                    **draft_state,
                    "draft": draft_report,
                    "revision_notes": f"Fact-checking rejected all {len(rejected_claims)} factual claims. Original content verified as correct.",
                    "revision_count": revision_count,
                }
            elif rejected_claims:
                # Some claims were rejected - filter the review
                print_agent_output(
                    f"📝 Filtering review: keeping {len(verified_claims)} verified claims, rejecting {len(rejected_claims)}",
                    agent="REVISOR",
                )
                # Create filtered review with only verified claims
                filtered_review = self._filter_review_feedback(
                    review, verified_claims, rejected_claims
                )
                review = filtered_review
            else:
                print_agent_output(
                    f"📝 {feedback_category.value.upper()} feedback contains no factual claims to verify",
                    agent="REVISOR",
                )
        else:
            print_agent_output(
                f"✅ {feedback_category.value.upper()} feedback - no fact-checking required",
                agent="REVISOR",
            )
        prompt = [
            {
                "role": "system",
                "content": "You are an expert writer. Your goal is to revise drafts based on reviewer notes.",
            },
            {
                "role": "user",
                "content": f"""Draft:\n{draft_report}\n\nReviewer's notes:\n{review}\n\n
You have been tasked by your reviewer with revising the following draft, which was written by a non-expert.
If you decide to follow the reviewer's notes, please write a new draft and make sure to address all of the points they raised.
Please keep all other aspects of the draft the same.

You MUST return ONLY a valid JSON object in the following format (no markdown code blocks, no additional text):
{sample_revision_notes}

Return only valid JSON, nothing else.
""",
            },
        ]

        try:
            response = await call_model(
                prompt,
                model=task.get("model"),
                response_format="json",
            )

            # Ensure response is a dictionary
            if isinstance(response, str):
                # Try to parse as JSON
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    # If parsing fails, create a proper dictionary
                    return {
                        **draft_state,
                        "draft": draft_report,  # Keep original draft
                        "revision_notes": f"JSON parsing failed. Raw response: {response[:200]}...",
                        "revision_count": revision_count,
                    }

            # Ensure the response has required fields
            if not isinstance(response, dict):
                response = {
                    **draft_state,
                    "draft": draft_report,
                    "revision_notes": "Invalid response format from LLM",
                    "revision_count": revision_count,
                }
            elif "draft" not in response:
                response["draft"] = draft_report
            if "revision_notes" not in response:
                response["revision_notes"] = "Revision completed"

            # Merge with draft_state to preserve all fields
            result = {
                **draft_state,
                **response,
                "revision_count": revision_count,  # Ensure revision count is preserved
            }

            # Ensure draft field is never empty
            if not result.get("draft"):
                result["draft"] = draft_report
                print_agent_output(
                    "WARNING: Preserving original draft to prevent empty draft field",
                    agent="REVISOR",
                )

            return result

        except Exception as e:
            print_agent_output(f"Error in revise_draft: {str(e)}", agent="REVISOR")
            return {
                **draft_state,
                "draft": draft_report,
                "revision_notes": f"Error during revision: {str(e)}",
                "revision_count": revision_count,
            }

    async def run(self, draft_state: dict):
        print_agent_output("Rewriting draft based on feedback...", agent="REVISOR")
        revision = await self.revise_draft(draft_state)

        # Handle case where revision might be a string instead of dict due to JSON parsing failure
        if isinstance(revision, str):
            print_agent_output(
                "JSON parsing failed, applying intelligent content extraction", agent="REVISOR"
            )

            # Enhanced content extraction with multiple strategies
            extracted_result = self._extract_content_intelligently(revision, draft_state)

            result = {
                **draft_state,  # Preserve all state fields
                "draft": extracted_result["draft"],
                "revision_notes": extracted_result["revision_notes"],
                "revision_count": draft_state.get("revision_count", 0) + 1,
                "extraction_method": extracted_result["method"],
            }

            # If this is a translation revision, save the revised translation to files
            if draft_state.get("translation_result"):
                await self._save_revised_translation(extracted_result["draft"], draft_state)
        else:
            if draft_state.get("task").get("verbose"):
                if self.websocket and self.stream_output:
                    await self.stream_output(
                        "logs",
                        "revision_notes",
                        f"Revision notes: {revision.get('revision_notes')}",
                        self.websocket,
                    )
                else:
                    print_agent_output(
                        f"Revision notes: {revision.get('revision_notes')}", agent="REVISOR"
                    )

            result = {
                **draft_state,  # Preserve all state fields
                "draft": revision.get("draft"),
                "revision_notes": revision.get("revision_notes"),
                "revision_count": draft_state.get("revision_count", 0)
                + 1,  # Increment revision count
            }

            # If this is a translation revision, save the revised translation to files
            if draft_state.get("translation_result"):
                await self._save_revised_translation(revision.get("draft"), draft_state)

        # Save revision history if draft_manager is available
        if self.draft_manager:
            # Save the revision output
            self.draft_manager.save_agent_output(
                agent_name="reviser",
                phase="parallel_research",
                output=result,
                step="revision_result",
                metadata={
                    "review_feedback": draft_state.get("review"),
                    "json_parsed": isinstance(revision, dict),
                    "draft_length": len(result.get("draft", "")),
                },
            )

            # Save revision history if we have both original and revised drafts
            if result.get("draft") and draft_state.get("draft"):
                self.draft_manager.save_revision_history(
                    original=draft_state.get("draft"),
                    revised=result.get("draft"),
                    changes=result.get("revision_notes", ""),
                    agent="reviser",
                )

        return result

    def _extract_content_intelligently(self, raw_response: str, draft_state: dict) -> dict:
        """
        Intelligently extract revised content from raw LLM response using multiple strategies

        Args:
            raw_response: Raw string response from LLM
            draft_state: Current draft state for fallback

        Returns:
            Dictionary with extracted draft, revision notes, and extraction method used
        """
        import json
        import re

        original_draft = draft_state.get("draft", "")

        # Strategy 1: Try to find JSON embedded in the response
        json_matches = re.findall(r"\{[\s\S]*?\}", raw_response)
        for json_str in json_matches:
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict) and ("draft" in parsed or "revision" in parsed):
                    draft_content = safe_dict_get(parsed, "draft") or safe_dict_get(
                        parsed, "revision", ""
                    )
                    if draft_content and len(draft_content) > 50:
                        return {
                            "draft": draft_content,
                            "revision_notes": safe_dict_get(
                                parsed, "revision_notes", "Extracted from embedded JSON", str
                            ),
                            "method": "embedded_json",
                        }
            except json.JSONDecodeError:
                continue

        # Strategy 2: Enhanced pattern-based extraction with markdown preservation
        enhanced_patterns = [
            # Translation-specific patterns
            r"(?:translated\s+(?:draft|version|text)[\s:]*)([\s\S]+?)(?:\n\n(?:revision|notes|feedback)|$)",
            r"(?:revised\s+(?:draft|version|text)[\s:]*)([\s\S]+?)(?:\n\n(?:revision|notes|feedback)|$)",
            # General content patterns with improved boundaries
            r"(?:draft[\s:]+)([\s\S]+?)(?:\n\n(?:revision|notes|feedback|changes)|$)",
            r"(?:here(?:\'s|\s+is)\s+the\s+(?:revised|updated|new)\s+(?:draft|version)[\s:]*)([\s\S]+?)(?:\n\n|$)",
            # Vietnamese-specific patterns
            r"(?:bài\s+viết\s+(?:được\s+)?(?:chỉnh\s+sửa|dịch)[\s:]*)([\s\S]+?)(?:\n\n|$)",
            r"(?:báo\s+cáo\s+(?:được\s+)?(?:chỉnh\s+sửa|dịch)[\s:]*)([\s\S]+?)(?:\n\n|$)",
            # Markdown document patterns (look for complete documents)
            r"(^#\s+.+[\s\S]*?)(?:\n\n(?:revision|notes|feedback)|$)",  # Documents starting with headers
        ]

        extracted_content = None
        extraction_method = "pattern_matching"

        for i, pattern in enumerate(enhanced_patterns):
            matches = re.finditer(pattern, raw_response, re.DOTALL | re.IGNORECASE | re.MULTILINE)
            for match in matches:
                candidate = match.group(1).strip()

                # Quality checks for extracted content
                if self._is_valid_extracted_content(candidate, original_draft):
                    extracted_content = candidate
                    extraction_method = f"pattern_{i + 1}"
                    break

            if extracted_content:
                break

        # Strategy 3: Content similarity-based extraction
        if not extracted_content:
            extracted_content = self._extract_by_similarity(raw_response, original_draft)
            if extracted_content:
                extraction_method = "similarity_based"

        # Strategy 4: Smart content splitting
        if not extracted_content:
            extracted_content = self._extract_by_content_splitting(raw_response, original_draft)
            if extracted_content:
                extraction_method = "content_splitting"

        # Strategy 5: Formatting preservation fallback
        if not extracted_content:
            extracted_content = self._preserve_formatting_fallback(raw_response, original_draft)
            extraction_method = "formatting_preservation"

        # Final validation and cleanup
        if extracted_content:
            extracted_content = self._clean_extracted_content(extracted_content)

            # Validate that we preserved essential formatting
            formatting_score = self._calculate_formatting_preservation_score(
                original_draft, extracted_content
            )

            return {
                "draft": extracted_content,
                "revision_notes": f"Intelligent extraction successful (method: {extraction_method}, formatting score: {formatting_score:.2f})",
                "method": extraction_method,
            }
        else:
            # Ultimate fallback: return original with minimal changes
            return {
                "draft": original_draft,
                "revision_notes": f"Content extraction failed, preserved original draft. Raw response length: {len(raw_response)}",
                "method": "fallback_original",
            }

    def _is_valid_extracted_content(self, content: str, original: str) -> bool:
        """Check if extracted content is valid based on multiple criteria"""
        if not content or len(content) < 50:
            return False

        # Check minimum length relative to original
        if len(content) < len(original) * 0.3:
            return False

        # Check for meaningful content (not just repetitive text)
        words = content.split()
        if len(set(words)) < len(words) * 0.3:  # Too much repetition
            return False

        # Check for markdown structure elements
        has_structure = any(marker in content for marker in ["#", "-", "*", "|", "```", "**"])

        # Check for academic/research content indicators
        content_lower = (
            content.lower() if isinstance(content, str) else str(content).lower() if content else ""
        )
        has_academic_content = any(
            term in content_lower
            for term in [
                "research",
                "study",
                "analysis",
                "findings",
                "conclusion",
                "methodology",
                "nghiên cứu",
                "phân tích",
                "kết quả",
                "kết luận",  # Vietnamese terms
            ]
        )

        return has_structure or has_academic_content

    def _extract_by_similarity(self, raw_response: str, original_draft: str) -> str:
        """Extract content based on similarity to original structure"""
        import re

        # Split response into chunks and find the most similar to original
        chunks = re.split(r"\n\n+", raw_response)

        best_chunk = ""
        best_score = 0

        for chunk in chunks:
            if len(chunk) < 100:  # Skip very short chunks
                continue

            # Calculate similarity score based on structure preservation
            score = self._calculate_formatting_preservation_score(original_draft, chunk)

            if score > best_score and score > 0.3:  # Minimum similarity threshold
                best_score = score
                best_chunk = chunk

        return best_chunk if best_score > 0.3 else ""

    def _extract_by_content_splitting(self, raw_response: str, original_draft: str) -> str:
        """Extract content by intelligent splitting and filtering"""
        import re

        # Remove common LLM response prefixes/suffixes
        cleaned = re.sub(
            r"^(?:here\s+is|here\'s|i\s+have|i\'ve)\s+(?:the\s+)?(?:revised|updated|new|translated)?\s*(?:draft|version|text)?[\s:]*",
            "",
            raw_response,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"(?:revision\s+notes?|feedback|changes\s+made)[\s:]*.*$",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Find the longest coherent section that looks like a document
        sections = re.split(r"\n\n+", cleaned)

        best_section = ""
        for section in sections:
            section = section.strip()
            if len(section) > len(best_section) and self._looks_like_document_content(section):
                best_section = section

        return best_section

    def _preserve_formatting_fallback(self, raw_response: str, original_draft: str) -> str:
        """Fallback that tries to preserve original formatting while updating content"""
        import re

        # If response contains markdown elements, prefer it over plain text
        if any(marker in raw_response for marker in ["#", "##", "-", "*", "|", "```"]):
            # Clean up the response but preserve markdown
            cleaned = re.sub(r"^[^\#\-\*\|]*?(?=[\#\-\*\|])", "", raw_response, flags=re.MULTILINE)
            if len(cleaned) > 50:
                return cleaned

        # Last resort: return the raw response with basic cleanup
        cleaned = raw_response.strip()

        # Remove obvious LLM artifacts
        cleaned = re.sub(
            r"^(?:I\s+have|Here\s+is|Here\'s).*?:\s*", "", cleaned, flags=re.IGNORECASE
        )
        cleaned = re.sub(r"\n\n+", "\n\n", cleaned)

        return cleaned if len(cleaned) > 50 else original_draft

    def _looks_like_document_content(self, content: str) -> bool:
        """Check if content looks like a coherent document"""
        if len(content) < 100:
            return False

        # Check for document-like characteristics
        has_sentences = len(content.split(".")) > 3
        any(marker in content for marker in ["#", "-", "*", "1.", "2."])
        reasonable_length = 100 < len(content) < 50000

        return has_sentences and reasonable_length

    def _calculate_formatting_preservation_score(self, original: str, revised: str) -> float:
        """Calculate how well formatting is preserved (0.0 to 1.0)"""
        import re

        if not original or not revised:
            return 0.0

        # Count various formatting elements
        elements = ["#", "##", "###", "-", "*", "```", "|", "**", "*", "[", "]", "(", ")"]

        orig_counts = {elem: len(re.findall(re.escape(elem), original)) for elem in elements}
        rev_counts = {elem: len(re.findall(re.escape(elem), revised)) for elem in elements}

        # Calculate preservation score
        total_elements = sum(orig_counts.values())
        if total_elements == 0:
            return 1.0  # No formatting to preserve

        preserved_elements = 0
        for elem in elements:
            orig_count = orig_counts[elem]
            rev_count = rev_counts[elem]

            if orig_count == 0:
                preserved_elements += 1  # No elements to preserve
            else:
                # Calculate preservation ratio with tolerance
                preservation_ratio = min(rev_count, orig_count) / orig_count
                preserved_elements += preservation_ratio

        return preserved_elements / len(elements)

    def _clean_extracted_content(self, content: str) -> str:
        """Clean up extracted content while preserving formatting"""
        import re

        # Remove multiple consecutive blank lines
        content = re.sub(r"\n\n\n+", "\n\n", content)

        # Remove trailing whitespace from lines
        lines = content.split("\n")
        cleaned_lines = [line.rstrip() for line in lines]

        # Remove empty lines at the beginning and end
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()

        return "\n".join(cleaned_lines)

    def _filter_review_feedback(
        self, review: str, verified_claims: list, rejected_claims: list
    ) -> str:
        """
        Filter review feedback to only include verified claims.

        Args:
            review: Original review feedback
            verified_claims: List of verified factual claims to keep
            rejected_claims: List of rejected claims to remove

        Returns:
            Filtered review feedback
        """
        import re

        filtered_lines = []
        filtered_lines.append("FACT-CHECKED REVIEW FEEDBACK:")
        filtered_lines.append(
            f"(Verified {len(verified_claims)} claims, rejected {len(rejected_claims)} unverified claims)\n"
        )

        # Split review into sentences
        sentences = re.split(r"(?<=[.!?])\s+", review)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if this sentence contains a rejected claim
            is_rejected = False
            for claim in rejected_claims:
                if claim[:50] in sentence or sentence[:50] in claim:
                    is_rejected = True
                    break

            if is_rejected:
                continue  # Skip rejected claims

            # Check if this sentence contains a verified claim or is non-factual
            is_verified = False
            for claim in verified_claims:
                if claim[:50] in sentence or sentence[:50] in claim:
                    is_verified = True
                    break

            # Also keep non-factual feedback (style, structure, etc.)
            style_keywords = [
                "formatting",
                "structure",
                "clarity",
                "grammar",
                "spelling",
                "readability",
                "flow",
                "organization",
                "style",
                "tone",
            ]

            sentence_lower = (
                sentence.lower()
                if isinstance(sentence, str)
                else str(sentence).lower()
                if sentence
                else ""
            )
            is_style_feedback = any(keyword in sentence_lower for keyword in style_keywords)

            if is_verified or is_style_feedback:
                filtered_lines.append(sentence)

        if len(filtered_lines) <= 2:  # Only header lines
            # No valid feedback remains
            return ""

        return " ".join(filtered_lines)

    async def _save_revised_translation(self, revised_content: str, draft_state: dict):
        """Save the revised translation to files"""
        import os
        import uuid

        from .utils.file_formats import write_md_to_pdf, write_md_to_word

        # Get the output directory from translation_result
        translation_result = draft_state.get("translation_result", {})

        # Find the output directory from any of the translated file paths
        output_dir = None
        for file_path in translation_result.values():
            if file_path and isinstance(file_path, str):
                output_dir = os.path.dirname(file_path)
                break

        if not output_dir:
            print_agent_output(
                "No output directory found for saving revised translation", agent="REVISOR"
            )
            return

        # Generate unique filename for revised translation
        task_id = str(uuid.uuid4().hex)

        try:
            # Save as markdown
            md_path = os.path.join(output_dir, f"{task_id}_vi_revised.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(revised_content)
            print_agent_output(f"Saved revised translation to: {md_path}", agent="REVISOR")

            # Also generate PDF and DOCX
            pdf_path = await write_md_to_pdf(revised_content, output_dir)
            if pdf_path:
                pdf_path = os.path.join(output_dir, f"{task_id}_vi_revised.pdf")
                print_agent_output(f"Saved revised PDF to: {pdf_path}", agent="REVISOR")

            docx_path = await write_md_to_word(revised_content, output_dir)
            if docx_path:
                docx_path = os.path.join(output_dir, f"{task_id}_vi_revised.docx")
                print_agent_output(f"Saved revised DOCX to: {docx_path}", agent="REVISOR")

        except Exception as e:
            print_agent_output(f"Error saving revised translation files: {e}", agent="REVISOR")
