from .utils.views import print_agent_output
from .utils.llms import call_model
import json

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
        Review a draft article
        :param draft_state:
        :return:
        """
        review = draft_state.get("review")
        task = draft_state.get("task")
        draft_report = draft_state.get("draft")
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

        response = await call_model(
            prompt,
            model=task.get("model"),
            response_format="json",
        )
        return response

    async def run(self, draft_state: dict):
        print_agent_output(f"Rewriting draft based on feedback...", agent="REVISOR")
        revision = await self.revise_draft(draft_state)

        # Handle case where revision might be a string instead of dict due to JSON parsing failure
        if isinstance(revision, str):
            print_agent_output(f"JSON parsing failed, applying intelligent content extraction", agent="REVISOR")
            
            # Enhanced content extraction with multiple strategies
            extracted_result = self._extract_content_intelligently(revision, draft_state)
            
            result = {
                **draft_state,  # Preserve all state fields
                "draft": extracted_result["draft"],
                "revision_notes": extracted_result["revision_notes"],
                "revision_count": draft_state.get("revision_count", 0) + 1,
                "extraction_method": extracted_result["method"]
            }
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
                "revision_count": draft_state.get("revision_count", 0) + 1,  # Increment revision count
            }
        
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
                    "draft_length": len(result.get("draft", ""))
                }
            )
            
            # Save revision history if we have both original and revised drafts
            if result.get("draft") and draft_state.get("draft"):
                self.draft_manager.save_revision_history(
                    original=draft_state.get("draft"),
                    revised=result.get("draft"),
                    changes=result.get("revision_notes", ""),
                    agent="reviser"
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
        import re
        import json
        
        original_draft = draft_state.get("draft", "")
        
        # Strategy 1: Try to find JSON embedded in the response
        json_matches = re.findall(r'\{[\s\S]*?\}', raw_response)
        for json_str in json_matches:
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict) and ("draft" in parsed or "revision" in parsed):
                    draft_content = parsed.get("draft") or parsed.get("revision", "")
                    if draft_content and len(draft_content) > 50:
                        return {
                            "draft": draft_content,
                            "revision_notes": parsed.get("revision_notes", "Extracted from embedded JSON"),
                            "method": "embedded_json"
                        }
            except json.JSONDecodeError:
                continue
        
        # Strategy 2: Enhanced pattern-based extraction with markdown preservation
        enhanced_patterns = [
            # Translation-specific patterns
            r'(?:translated\s+(?:draft|version|text)[\s:]*)([\s\S]+?)(?:\n\n(?:revision|notes|feedback)|$)',
            r'(?:revised\s+(?:draft|version|text)[\s:]*)([\s\S]+?)(?:\n\n(?:revision|notes|feedback)|$)',
            
            # General content patterns with improved boundaries
            r'(?:draft[\s:]+)([\s\S]+?)(?:\n\n(?:revision|notes|feedback|changes)|$)',
            r'(?:here(?:\'s|\s+is)\s+the\s+(?:revised|updated|new)\s+(?:draft|version)[\s:]*)([\s\S]+?)(?:\n\n|$)',
            
            # Vietnamese-specific patterns
            r'(?:bài\s+viết\s+(?:được\s+)?(?:chỉnh\s+sửa|dịch)[\s:]*)([\s\S]+?)(?:\n\n|$)',
            r'(?:báo\s+cáo\s+(?:được\s+)?(?:chỉnh\s+sửa|dịch)[\s:]*)([\s\S]+?)(?:\n\n|$)',
            
            # Markdown document patterns (look for complete documents)
            r'(^#\s+.+[\s\S]*?)(?:\n\n(?:revision|notes|feedback)|$)',  # Documents starting with headers
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
                    extraction_method = f"pattern_{i+1}"
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
            formatting_score = self._calculate_formatting_preservation_score(original_draft, extracted_content)
            
            return {
                "draft": extracted_content,
                "revision_notes": f"Intelligent extraction successful (method: {extraction_method}, formatting score: {formatting_score:.2f})",
                "method": extraction_method
            }
        else:
            # Ultimate fallback: return original with minimal changes
            return {
                "draft": original_draft,
                "revision_notes": f"Content extraction failed, preserved original draft. Raw response length: {len(raw_response)}",
                "method": "fallback_original"
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
        has_structure = any(marker in content for marker in ['#', '-', '*', '|', '```', '**'])
        
        # Check for academic/research content indicators
        has_academic_content = any(term in content.lower() for term in [
            'research', 'study', 'analysis', 'findings', 'conclusion', 'methodology',
            'nghiên cứu', 'phân tích', 'kết quả', 'kết luận'  # Vietnamese terms
        ])
        
        return has_structure or has_academic_content
    
    def _extract_by_similarity(self, raw_response: str, original_draft: str) -> str:
        """Extract content based on similarity to original structure"""
        import re
        
        # Split response into chunks and find the most similar to original
        chunks = re.split(r'\n\n+', raw_response)
        
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
        cleaned = re.sub(r'^(?:here\s+is|here\'s|i\s+have|i\'ve)\s+(?:the\s+)?(?:revised|updated|new|translated)?\s*(?:draft|version|text)?[\s:]*', '', raw_response, flags=re.IGNORECASE)
        cleaned = re.sub(r'(?:revision\s+notes?|feedback|changes\s+made)[\s:]*.*$', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Find the longest coherent section that looks like a document
        sections = re.split(r'\n\n+', cleaned)
        
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
        if any(marker in raw_response for marker in ['#', '##', '-', '*', '|', '```']):
            # Clean up the response but preserve markdown
            cleaned = re.sub(r'^[^\#\-\*\|]*?(?=[\#\-\*\|])', '', raw_response, flags=re.MULTILINE)
            if len(cleaned) > 50:
                return cleaned
        
        # Last resort: return the raw response with basic cleanup
        cleaned = raw_response.strip()
        
        # Remove obvious LLM artifacts
        cleaned = re.sub(r'^(?:I\s+have|Here\s+is|Here\'s).*?:\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\n\n+', '\n\n', cleaned)
        
        return cleaned if len(cleaned) > 50 else original_draft
    
    def _looks_like_document_content(self, content: str) -> bool:
        """Check if content looks like a coherent document"""
        if len(content) < 100:
            return False
        
        # Check for document-like characteristics
        has_sentences = len(content.split('.')) > 3
        has_structure = any(marker in content for marker in ['#', '-', '*', '1.', '2.'])
        reasonable_length = 100 < len(content) < 50000
        
        return has_sentences and reasonable_length
    
    def _calculate_formatting_preservation_score(self, original: str, revised: str) -> float:
        """Calculate how well formatting is preserved (0.0 to 1.0)"""
        import re
        
        if not original or not revised:
            return 0.0
        
        # Count various formatting elements
        elements = ['#', '##', '###', '-', '*', '```', '|', '**', '*', '[', ']', '(', ')']
        
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
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        # Remove trailing whitespace from lines
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        # Remove empty lines at the beginning and end
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
