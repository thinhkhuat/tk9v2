from .utils.llms import call_model
from .utils.type_safety import safe_dict_get
from .utils.views import print_agent_output

# from .utils.fact_checker import get_fact_checker, VerificationStatus, FeedbackCategory  # DISABLED - fact-checking removed

TEMPLATE = """You are an expert research article reviewer. \
Your goal is to review research drafts and provide feedback to the reviser only based on specific guidelines. \

IMPORTANT CONTEXT:
- Today's date is: {current_date}
- You are operating in the year {current_year}
- Donald Trump is the current President of the United States (as of January 2025)
- Events from 2024-2025 are recent/current events, NOT future events
- You should accept contemporary references and dates as factually correct
- DO NOT reject content simply because it mentions dates in 2024-2025
- Focus on actual content quality, structure, and guideline compliance
"""


class ReviewerAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None, draft_manager=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.draft_manager = draft_manager

    async def review_draft(self, draft_state: dict):
        """
        Review a draft article or translated content
        :param draft_state:
        :return: Dictionary with review results
        """
        task = draft_state.get("task")

        # Get current date for temporal awareness
        import datetime

        current_date = datetime.datetime.now()
        current_year = current_date.year
        date_str = current_date.strftime("%B %d, %Y")

        # Check revision count to prevent infinite loops
        revision_count = draft_state.get("revision_count", 0)
        MAX_REVISIONS = 3

        if revision_count >= MAX_REVISIONS:
            print_agent_output(
                f"Maximum revisions ({MAX_REVISIONS}) reached. Accepting draft to prevent infinite loop.",
                agent="REVIEWER",
            )
            return {**draft_state, "revision_notes": None, "review": None}

        # Handle missing draft or guidelines gracefully
        draft_content = draft_state.get("draft", "")
        if not draft_content:
            error_msg = "The draft could not be reviewed as no content was provided in the 'Draft' field. Please submit the full research article draft for review."
            return {**draft_state, "revision_notes": error_msg, "review": None}

        guidelines_list = task.get("guidelines", [])
        if not guidelines_list:
            error_msg = "No specific guidelines were provided in the 'Guidelines' field. Please include the criteria against which the draft should be evaluated."
            return {**draft_state, "revision_notes": error_msg, "review": None}

        guidelines = "- ".join(guideline for guideline in guidelines_list)
        revision_notes = draft_state.get("revision_notes")

        # Check if we're reviewing a translation
        is_translation_review = draft_state.get("translation_result") is not None
        target_language = task.get("language", "en") if is_translation_review else None

        revise_prompt = f"""The reviser has already revised the draft based on your previous review notes with the following feedback:
{revision_notes}\n
Please provide additional feedback ONLY if critical since the reviser has already made changes based on your previous feedback.
If you think the article is sufficient or that non critical revisions are required, please aim to return None.
"""

        if is_translation_review:
            # Enhanced translation review with comprehensive formatting validation
            original_draft = draft_state.get("original_draft", "")
            formatting_analysis = self._analyze_formatting_preservation(
                original_draft, draft_state.get("draft", "")
            )

            review_prompt = f"""You are reviewing a TRANSLATED research report from English to {task.get("language", "target language")}.

CONTEXT: This is {current_year} content. References to 2024-2025 events are CURRENT, not future.

COMPREHENSIVE TRANSLATION QUALITY EVALUATION:

1. **Content Accuracy**: 
   - Is the meaning correctly conveyed?
   - Are all sections and paragraphs translated?
   - No content omissions or additions?

2. **Formatting Preservation** (CRITICAL):
   - Headings (# ## ### ####): {formatting_analysis["headings_preserved"]}
   - Lists (bullet points, numbered): {formatting_analysis["lists_preserved"]} 
   - Tables structure: {formatting_analysis["tables_preserved"]}
   - Code blocks and inline code: {formatting_analysis["code_preserved"]}
   - Links and references: {formatting_analysis["links_preserved"]}
   - Bold/italic emphasis: {formatting_analysis["emphasis_preserved"]}
   - Line breaks and paragraphs: {formatting_analysis["structure_preserved"]}

3. **Language Quality**:
   - Natural fluency in target language
   - Appropriate academic/research tone
   - Correct technical terminology
   - Cultural adaptation where needed

4. **Structural Integrity**:
   - Document hierarchy maintained
   - Cross-references intact
   - Citations and footnotes preserved

FORMATTING ISSUES DETECTED: {formatting_analysis["issues"]}

Original Guidelines: {guidelines}

REVIEW DECISION:
- If formatting is BROKEN or content is MISSING: Provide specific revision notes
- If translation quality is good: return None
- Focus on CRITICAL formatting issues that affect readability

{revise_prompt if revision_notes else ""}

Translated Draft: {safe_dict_get(draft_state, "draft", "")}\n
"""
        else:
            review_prompt = f"""You have been tasked with reviewing the draft which was written by a non-expert based on specific guidelines.

IMPORTANT: This research was conducted in {current_year}. Do NOT reject content for mentioning:
- Dates in 2024-2025 (these are current/recent)
- Current political figures (e.g., President Trump in 2025)
- Recent technological developments or events

Please accept the draft if it is good enough to publish, or send it for revision, along with your notes to guide the revision.
Focus on ACTUAL issues like:
- Content accuracy and completeness
- Guideline compliance
- Writing quality and structure
- Formatting and citations

If not all of the guideline criteria are met, you should send appropriate revision notes.
If the draft meets all the guidelines, please return None.
{revise_prompt if revision_notes else ""}

Guidelines: {guidelines}\nDraft: {safe_dict_get(draft_state, "draft", "")}\n
"""
        # Format template with current date context
        formatted_template = TEMPLATE.format(current_date=date_str, current_year=current_year)

        prompt = [
            {"role": "system", "content": formatted_template},
            {"role": "user", "content": review_prompt},
        ]

        response = await call_model(prompt, model=task.get("model"))

        # Initialize variables for all execution paths (CRITICAL: prevents UnboundLocalError)
        verified_false_claims = []
        inconclusive_claims = []

        # FEEDBACK CATEGORIZATION & FACT-CHECKING PROTOCOL
        if response and response != "None" and "None" not in response:
            print_agent_output(
                "🔍 Categorizing feedback and applying appropriate verification...",
                agent="REVIEWER",
            )

            # Get fact checker instance - DISABLED
            # fact_checker = get_fact_checker()

            # Categorize the feedback first - DISABLED
            # feedback_category, analysis = fact_checker.categorize_feedback(response)
            feedback_category = None
            analysis = {"disabled": True}

            print_agent_output("📊 Feedback processing: fact-checking disabled", agent="REVIEWER")

            if analysis.get("reasoning"):
                for reason in analysis["reasoning"][:2]:  # Show top 2 reasons
                    print_agent_output(f"   • {reason}", agent="REVIEWER")

            # Apply appropriate processing based on category - DISABLED
            if False:  # feedback_category == FeedbackCategory.FORMATTING:
                print_agent_output(
                    "✅ FORMATTING feedback - bypassing fact-checking (fast track)",
                    agent="REVIEWER",
                )
                # Skip fact-checking entirely for pure formatting feedback
                pass  # Allow response to proceed unchanged

            elif False:  # fact_checker.should_fact_check(feedback_category):
                print_agent_output("🔍 Fact-checking disabled", agent="REVIEWER")

                # Extract and verify factual claims - DISABLED
                # factual_claims = fact_checker.extract_factual_claims(response)
                factual_claims = []

                if factual_claims:
                    print_agent_output(
                        f"📊 Found {len(factual_claims)} potential factual claims to verify",
                        agent="REVIEWER",
                    )

                    # Verify each claim - variables already initialized above
                    for claim in factual_claims:
                        result = await fact_checker.verify_claim(
                            claim, context=draft_state.get("draft")
                        )

                        if (
                            result.status == VerificationStatus.VERIFIED_FALSE
                            and result.confidence > 0.8
                        ):
                            verified_false_claims.append((claim, result))
                            print_agent_output(
                                f"❌ VERIFIED FALSE: {claim[:100]}... (confidence: {result.confidence:.2f})",
                                agent="REVIEWER",
                            )
                        elif result.status == VerificationStatus.INCONCLUSIVE:
                            inconclusive_claims.append((claim, result))
                            print_agent_output(
                                f"❓ INCONCLUSIVE: {claim[:100]}... - cannot block workflow",
                                agent="REVIEWER",
                            )
                        elif result.status == VerificationStatus.VERIFIED_TRUE:
                            print_agent_output(
                                f"✅ VERIFIED TRUE: {claim[:100]}... (confidence: {result.confidence:.2f})",
                                agent="REVIEWER",
                            )

                # Apply burden of proof principle
                if verified_false_claims:
                    # Only keep feedback for verified false claims
                    filtered_feedback = []
                    filtered_feedback.append("FACT-CHECKED REVIEW FEEDBACK:\n")
                    filtered_feedback.append(
                        f"Found {len(verified_false_claims)} verified factual errors:\n\n"
                    )

                    for claim, result in verified_false_claims:
                        filtered_feedback.append(f"• {claim}\n")
                        if result.evidence:
                            filtered_feedback.append(
                                f"  Evidence: {result.evidence[0]['source']}\n"
                            )

                    response = "\n".join(filtered_feedback)
                    print_agent_output(
                        f"📝 Filtered feedback to {len(verified_false_claims)} verified issues",
                        agent="REVIEWER",
                    )

                elif inconclusive_claims:
                    # All claims are inconclusive - cannot block workflow
                    print_agent_output(
                        f"⚠️ All {len(inconclusive_claims)} factual claims are INCONCLUSIVE",
                        agent="REVIEWER",
                    )
                    print_agent_output(
                        "✅ Applying burden of proof: Cannot block workflow without verification",
                        agent="REVIEWER",
                    )

                    # Check if there are non-factual issues (style, structure, etc.)
                    non_factual_feedback = self._extract_non_factual_feedback(response)
                    if non_factual_feedback:
                        response = non_factual_feedback
                        print_agent_output(
                            "📝 Keeping non-factual feedback (style/structure issues)",
                            agent="REVIEWER",
                        )
                    else:
                        # No valid feedback remains - accept the draft
                        response = "None"
                        print_agent_output(
                            "✅ No verified issues found - accepting draft", agent="REVIEWER"
                        )
                else:
                    # No verified false claims found
                    print_agent_output(
                        "✅ No factual claims found or all claims verified as true",
                        agent="REVIEWER",
                    )
            else:
                # No factual claims in content/hybrid feedback - could be structural issues
                print_agent_output(
                    f"📝 {feedback_category.value.upper()} feedback contains no extractable factual claims",
                    agent="REVIEWER",
                )

        if task.get("verbose"):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "review_feedback",
                    f"Review feedback is: {response}...",
                    self.websocket,
                )
            else:
                print_agent_output(f"Review feedback is: {response}...", agent="REVIEWER")

        # Always return a dictionary with the review results
        if (
            response is None
            or response == "None"
            or (isinstance(response, str) and "None" in response)
        ):
            return {
                **draft_state,
                "revision_notes": None,
                "review": None,
                "revision_count": revision_count,  # Preserve revision count
            }

        # Check if the feedback is about temporal issues (should be ignored)
        temporal_keywords = [
            "future",
            "2025",
            "2024",
            "not yet",
            "hasn't happened",
            "will be",
            "upcoming",
        ]
        response_str = str(response) if response else ""
        if any(keyword in response_str.lower() for keyword in temporal_keywords):
            # Log but don't reject for temporal issues
            print_agent_output(
                f"Ignoring temporal concerns in review feedback: {str(response)[:100]}...",
                agent="REVIEWER",
            )
            # Check if there are other substantive issues
            has_other_issues = any(
                term in response_str.lower()
                for term in [
                    "format",
                    "structure",
                    "missing",
                    "incomplete",
                    "guideline",
                    "clarity",
                    "grammar",
                ]
            )
            if not has_other_issues:
                # Only temporal issues, accept the draft
                return {
                    **draft_state,
                    "revision_notes": None,
                    "review": None,
                    "revision_count": revision_count,
                }

        return {
            **draft_state,
            "revision_notes": response,
            "review": response,
            "revision_count": revision_count,  # Preserve revision count
            "feedback_category": (
                feedback_category.value if "feedback_category" in locals() else None
            ),
            "feedback_analysis": analysis if "analysis" in locals() else None,
        }

    async def run(self, draft_state: dict):
        task = draft_state.get("task")
        guidelines = task.get("guidelines")
        to_follow_guidelines = task.get("follow_guidelines")
        review = None
        if to_follow_guidelines:
            print_agent_output("Reviewing draft...", agent="REVIEWER")

            if task.get("verbose"):
                print_agent_output(f"Following guidelines {guidelines}...", agent="REVIEWER")

            review = await self.review_draft(draft_state)
        else:
            print_agent_output("Ignoring guidelines...", agent="REVIEWER")

        # Save review feedback if draft_manager is available
        if self.draft_manager and review:
            self.draft_manager.save_agent_output(
                agent_name="reviewer",
                phase="parallel_research",
                output=review,
                step="review_feedback",
                metadata={
                    "has_feedback": review is not None,
                    "revision_notes": draft_state.get("revision_notes"),
                    "guidelines_followed": to_follow_guidelines,
                },
            )

        return {"review": review}

    def _extract_non_factual_feedback(self, response: str) -> str:
        """
        Extract non-factual feedback (style, structure, formatting) from review response.

        Args:
            response: Full review response

        Returns:
            Non-factual feedback only, or empty string if none found
        """
        import re

        # Keywords that indicate style/structure feedback
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
            "coherence",
            "consistency",
            "redundant",
            "verbose",
            "concise",
            "paragraph",
            "section",
            "heading",
            "bullet",
            "list",
            "introduction",
            "conclusion",
            "transition",
        ]

        non_factual_feedback = []
        sentences = re.split(r"[.!?]+", response)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check if sentence contains style/structure keywords
            sentence_lower = str(sentence).lower() if sentence else ""
            if any(keyword in sentence_lower for keyword in style_keywords):
                # This is likely style/structure feedback
                non_factual_feedback.append(sentence + ".")

            # Also keep general improvement suggestions that don't make factual claims
            improvement_patterns = [
                r"could\s+be\s+(?:improved|enhanced|clarified)",
                r"would\s+benefit\s+from",
                r"consider\s+(?:adding|removing|revising)",
                r"(?:lacks?|needs?)\s+(?:clarity|detail|explanation)",
                r"(?:too|very)\s+(?:long|short|complex|simple)",
            ]

            for pattern in improvement_patterns:
                if re.search(pattern, sentence_lower):
                    if sentence not in non_factual_feedback:
                        non_factual_feedback.append(sentence + ".")
                    break

        if non_factual_feedback:
            return " ".join(non_factual_feedback)

        return ""

    def _analyze_formatting_preservation(
        self, original_content: str, translated_content: str
    ) -> dict:
        """
        Analyze how well formatting is preserved in the translation

        Args:
            original_content: Original markdown content
            translated_content: Translated markdown content

        Returns:
            Dictionary with preservation analysis results
        """
        import re

        if not original_content or not translated_content:
            return {
                "headings_preserved": "❌ Cannot analyze - missing content",
                "lists_preserved": "❌ Cannot analyze - missing content",
                "tables_preserved": "❌ Cannot analyze - missing content",
                "code_preserved": "❌ Cannot analyze - missing content",
                "links_preserved": "❌ Cannot analyze - missing content",
                "emphasis_preserved": "❌ Cannot analyze - missing content",
                "structure_preserved": "❌ Cannot analyze - missing content",
                "issues": ["Missing original or translated content"],
            }

        analysis = {
            "headings_preserved": "✅ Good",
            "lists_preserved": "✅ Good",
            "tables_preserved": "✅ Good",
            "code_preserved": "✅ Good",
            "links_preserved": "✅ Good",
            "emphasis_preserved": "✅ Good",
            "structure_preserved": "✅ Good",
            "issues": [],
        }

        # Analyze headings (# ## ### ####)
        original_headings = re.findall(r"^(#{1,6})\s+(.+)$", original_content, re.MULTILINE)
        translated_headings = re.findall(r"^(#{1,6})\s+(.+)$", translated_content, re.MULTILINE)

        # Check for problematic long headings (paragraphs marked as headings)
        problematic_headings = []
        for level, text in translated_headings:
            # Flag headings that are too long (likely full paragraphs)
            if len(text.split()) > 15 or len(text) > 100:
                problematic_headings.append(f"'{text[:50]}...'" if len(text) > 50 else f"'{text}'")
            # Flag headings that end with periods (usually paragraphs)
            elif text.endswith(".") and not text.endswith("..."):
                problematic_headings.append(f"'{text[:50]}...'" if len(text) > 50 else f"'{text}'")

        if problematic_headings:
            analysis["headings_preserved"] = (
                f"❌ {len(problematic_headings)} problematic headings detected"
            )
            analysis["issues"].append(
                f"Long paragraphs incorrectly marked as headings: {', '.join(problematic_headings[:3])}{'...' if len(problematic_headings) > 3 else ''}"
            )
        elif len(original_headings) != len(translated_headings):
            analysis["headings_preserved"] = (
                f"❌ Count mismatch: {len(original_headings)} → {len(translated_headings)}"
            )
            analysis["issues"].append(
                f"Heading count changed: {len(original_headings)} → {len(translated_headings)}"
            )
        elif original_headings:
            # Check heading levels are preserved
            orig_levels = [len(h[0]) for h in original_headings]
            trans_levels = [len(h[0]) for h in translated_headings]
            if orig_levels != trans_levels:
                analysis["headings_preserved"] = "⚠️ Level structure changed"
                analysis["issues"].append("Heading level hierarchy altered")

        # Analyze lists (bullet points and numbered)
        original_bullets = re.findall(r"^[\s]*[-*+]\s+", original_content, re.MULTILINE)
        translated_bullets = re.findall(r"^[\s]*[-*+]\s+", translated_content, re.MULTILINE)
        original_numbered = re.findall(r"^[\s]*\d+\.\s+", original_content, re.MULTILINE)
        translated_numbered = re.findall(r"^[\s]*\d+\.\s+", translated_content, re.MULTILINE)

        if len(original_bullets) != len(translated_bullets):
            analysis["lists_preserved"] = (
                f"❌ Bullet lists: {len(original_bullets)} → {len(translated_bullets)}"
            )
            analysis["issues"].append(
                f"Bullet list count changed: {len(original_bullets)} → {len(translated_bullets)}"
            )

        if len(original_numbered) != len(translated_numbered):
            if analysis["lists_preserved"] == "✅ Good":
                analysis["lists_preserved"] = (
                    f"❌ Numbered lists: {len(original_numbered)} → {len(translated_numbered)}"
                )
            analysis["issues"].append(
                f"Numbered list count changed: {len(original_numbered)} → {len(translated_numbered)}"
            )

        # Analyze tables
        original_tables = re.findall(r"\|(.+)\|", original_content)
        translated_tables = re.findall(r"\|(.+)\|", translated_content)

        if len(original_tables) != len(translated_tables):
            analysis["tables_preserved"] = (
                f"❌ Table rows: {len(original_tables)} → {len(translated_tables)}"
            )
            analysis["issues"].append(
                f"Table structure changed: {len(original_tables)} → {len(translated_tables)} rows"
            )
        elif original_tables:
            # Check table structure integrity
            orig_cols = [len(row.split("|")) for row in original_tables[:3]]  # Sample first 3 rows
            trans_cols = [len(row.split("|")) for row in translated_tables[:3]]
            if orig_cols != trans_cols:
                analysis["tables_preserved"] = "⚠️ Column structure may be altered"
                analysis["issues"].append("Table column structure possibly changed")

        # Analyze code blocks
        original_code_blocks = re.findall(r"```[\s\S]*?```", original_content)
        translated_code_blocks = re.findall(r"```[\s\S]*?```", translated_content)
        original_inline_code = re.findall(r"`[^`]+`", original_content)
        translated_inline_code = re.findall(r"`[^`]+`", translated_content)

        if len(original_code_blocks) != len(translated_code_blocks):
            analysis["code_preserved"] = (
                f"❌ Code blocks: {len(original_code_blocks)} → {len(translated_code_blocks)}"
            )
            analysis["issues"].append(
                f"Code block count changed: {len(original_code_blocks)} → {len(translated_code_blocks)}"
            )

        if len(original_inline_code) != len(translated_inline_code):
            if analysis["code_preserved"] == "✅ Good":
                analysis["code_preserved"] = (
                    f"❌ Inline code: {len(original_inline_code)} → {len(translated_inline_code)}"
                )
            analysis["issues"].append(
                f"Inline code count changed: {len(original_inline_code)} → {len(translated_inline_code)}"
            )

        # Analyze links
        original_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", original_content)
        translated_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", translated_content)

        if len(original_links) != len(translated_links):
            analysis["links_preserved"] = (
                f"❌ Links: {len(original_links)} → {len(translated_links)}"
            )
            analysis["issues"].append(
                f"Link count changed: {len(original_links)} → {len(translated_links)}"
            )
        elif original_links:
            # Check if URLs are preserved
            orig_urls = set(link[1] for link in original_links)
            trans_urls = set(link[1] for link in translated_links)
            if orig_urls != trans_urls:
                analysis["links_preserved"] = "⚠️ Link URLs may have changed"
                analysis["issues"].append("Some link URLs were altered during translation")

        # Analyze emphasis (bold/italic)
        original_bold = re.findall(r"\*\*([^*]+)\*\*", original_content)
        translated_bold = re.findall(r"\*\*([^*]+)\*\*", translated_content)
        original_italic = re.findall(r"\*([^*]+)\*", original_content)
        translated_italic = re.findall(r"\*([^*]+)\*", translated_content)

        bold_diff = abs(len(original_bold) - len(translated_bold))
        italic_diff = abs(len(original_italic) - len(translated_italic))

        if bold_diff > 2 or italic_diff > 2:  # Allow some variation for natural translation
            analysis["emphasis_preserved"] = (
                f"⚠️ Bold: {len(original_bold)}→{len(translated_bold)}, Italic: {len(original_italic)}→{len(translated_italic)}"
            )
            analysis["issues"].append("Significant emphasis formatting changes detected")

        # Analyze overall structure (paragraph count, line breaks)
        original_paragraphs = len([p for p in original_content.split("\n\n") if p.strip()])
        translated_paragraphs = len([p for p in translated_content.split("\n\n") if p.strip()])

        if abs(original_paragraphs - translated_paragraphs) > 2:  # Allow some variation
            analysis["structure_preserved"] = (
                f"⚠️ Paragraphs: {original_paragraphs} → {translated_paragraphs}"
            )
            analysis["issues"].append(
                f"Paragraph structure significantly changed: {original_paragraphs} → {translated_paragraphs}"
            )

        # Overall assessment
        if not analysis["issues"]:
            analysis["issues"] = ["No significant formatting issues detected"]

        return analysis
