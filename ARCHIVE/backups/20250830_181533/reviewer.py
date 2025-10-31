from .utils.views import print_agent_output
from .utils.llms import call_model

TEMPLATE = """You are an expert research article reviewer. \
Your goal is to review research drafts and provide feedback to the reviser only based on specific guidelines. \
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
        :return:
        """
        task = draft_state.get("task")
        guidelines = "- ".join(guideline for guideline in task.get("guidelines"))
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
            formatting_analysis = self._analyze_formatting_preservation(original_draft, draft_state.get("draft", ""))
            
            review_prompt = f"""You are reviewing a TRANSLATED research report from English to {task.get('language', 'target language')}.

COMPREHENSIVE TRANSLATION QUALITY EVALUATION:

1. **Content Accuracy**: 
   - Is the meaning correctly conveyed?
   - Are all sections and paragraphs translated?
   - No content omissions or additions?

2. **Formatting Preservation** (CRITICAL):
   - Headings (# ## ### ####): {formatting_analysis['headings_preserved']}
   - Lists (bullet points, numbered): {formatting_analysis['lists_preserved']} 
   - Tables structure: {formatting_analysis['tables_preserved']}
   - Code blocks and inline code: {formatting_analysis['code_preserved']}
   - Links and references: {formatting_analysis['links_preserved']}
   - Bold/italic emphasis: {formatting_analysis['emphasis_preserved']}
   - Line breaks and paragraphs: {formatting_analysis['structure_preserved']}

3. **Language Quality**:
   - Natural fluency in target language
   - Appropriate academic/research tone
   - Correct technical terminology
   - Cultural adaptation where needed

4. **Structural Integrity**:
   - Document hierarchy maintained
   - Cross-references intact
   - Citations and footnotes preserved

FORMATTING ISSUES DETECTED: {formatting_analysis['issues']}

Original Guidelines: {guidelines}

REVIEW DECISION:
- If formatting is BROKEN or content is MISSING: Provide specific revision notes
- If translation quality is good: return None
- Focus on CRITICAL formatting issues that affect readability

{revise_prompt if revision_notes else ""}

Translated Draft: {draft_state.get("draft")}\n
"""
        else:
            review_prompt = f"""You have been tasked with reviewing the draft which was written by a non-expert based on specific guidelines.
Please accept the draft if it is good enough to publish, or send it for revision, along with your notes to guide the revision.
If not all of the guideline criteria are met, you should send appropriate revision notes.
If the draft meets all the guidelines, please return None.
{revise_prompt if revision_notes else ""}

Guidelines: {guidelines}\nDraft: {draft_state.get("draft")}\n
"""
        prompt = [
            {"role": "system", "content": TEMPLATE},
            {"role": "user", "content": review_prompt},
        ]

        response = await call_model(prompt, model=task.get("model"))

        if task.get("verbose"):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "review_feedback",
                    f"Review feedback is: {response}...",
                    self.websocket,
                )
            else:
                print_agent_output(
                    f"Review feedback is: {response}...", agent="REVIEWER"
                )

        if "None" in response:
            return None
        return response

    async def run(self, draft_state: dict):
        task = draft_state.get("task")
        guidelines = task.get("guidelines")
        to_follow_guidelines = task.get("follow_guidelines")
        review = None
        if to_follow_guidelines:
            print_agent_output(f"Reviewing draft...", agent="REVIEWER")

            if task.get("verbose"):
                print_agent_output(
                    f"Following guidelines {guidelines}...", agent="REVIEWER"
                )

            review = await self.review_draft(draft_state)
        else:
            print_agent_output(f"Ignoring guidelines...", agent="REVIEWER")
        
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
                    "guidelines_followed": to_follow_guidelines
                }
            )
        
        return {"review": review}

    def _analyze_formatting_preservation(self, original_content: str, translated_content: str) -> dict:
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
                'headings_preserved': '❌ Cannot analyze - missing content',
                'lists_preserved': '❌ Cannot analyze - missing content',
                'tables_preserved': '❌ Cannot analyze - missing content',
                'code_preserved': '❌ Cannot analyze - missing content',
                'links_preserved': '❌ Cannot analyze - missing content',
                'emphasis_preserved': '❌ Cannot analyze - missing content',
                'structure_preserved': '❌ Cannot analyze - missing content',
                'issues': ['Missing original or translated content']
            }
        
        analysis = {
            'headings_preserved': '✅ Good',
            'lists_preserved': '✅ Good',
            'tables_preserved': '✅ Good',
            'code_preserved': '✅ Good',
            'links_preserved': '✅ Good',
            'emphasis_preserved': '✅ Good',
            'structure_preserved': '✅ Good',
            'issues': []
        }
        
        # Analyze headings (# ## ### ####)
        original_headings = re.findall(r'^(#{1,6})\s+(.+)$', original_content, re.MULTILINE)
        translated_headings = re.findall(r'^(#{1,6})\s+(.+)$', translated_content, re.MULTILINE)
        
        # Check for problematic long headings (paragraphs marked as headings)
        problematic_headings = []
        for level, text in translated_headings:
            # Flag headings that are too long (likely full paragraphs)
            if len(text.split()) > 15 or len(text) > 100:
                problematic_headings.append(f"'{text[:50]}...'" if len(text) > 50 else f"'{text}'")
            # Flag headings that end with periods (usually paragraphs)
            elif text.endswith('.') and not text.endswith('...'):
                problematic_headings.append(f"'{text[:50]}...'" if len(text) > 50 else f"'{text}'")
        
        if problematic_headings:
            analysis['headings_preserved'] = f'❌ {len(problematic_headings)} problematic headings detected'
            analysis['issues'].append(f'Long paragraphs incorrectly marked as headings: {", ".join(problematic_headings[:3])}{"..." if len(problematic_headings) > 3 else ""}')
        elif len(original_headings) != len(translated_headings):
            analysis['headings_preserved'] = f'❌ Count mismatch: {len(original_headings)} → {len(translated_headings)}'
            analysis['issues'].append(f'Heading count changed: {len(original_headings)} → {len(translated_headings)}')
        elif original_headings:
            # Check heading levels are preserved
            orig_levels = [len(h[0]) for h in original_headings]
            trans_levels = [len(h[0]) for h in translated_headings]
            if orig_levels != trans_levels:
                analysis['headings_preserved'] = '⚠️ Level structure changed'
                analysis['issues'].append('Heading level hierarchy altered')
        
        # Analyze lists (bullet points and numbered)
        original_bullets = re.findall(r'^[\s]*[-*+]\s+', original_content, re.MULTILINE)
        translated_bullets = re.findall(r'^[\s]*[-*+]\s+', translated_content, re.MULTILINE)
        original_numbered = re.findall(r'^[\s]*\d+\.\s+', original_content, re.MULTILINE)
        translated_numbered = re.findall(r'^[\s]*\d+\.\s+', translated_content, re.MULTILINE)
        
        if len(original_bullets) != len(translated_bullets):
            analysis['lists_preserved'] = f'❌ Bullet lists: {len(original_bullets)} → {len(translated_bullets)}'
            analysis['issues'].append(f'Bullet list count changed: {len(original_bullets)} → {len(translated_bullets)}')
        
        if len(original_numbered) != len(translated_numbered):
            if analysis['lists_preserved'] == '✅ Good':
                analysis['lists_preserved'] = f'❌ Numbered lists: {len(original_numbered)} → {len(translated_numbered)}'
            analysis['issues'].append(f'Numbered list count changed: {len(original_numbered)} → {len(translated_numbered)}')
        
        # Analyze tables
        original_tables = re.findall(r'\|(.+)\|', original_content)
        translated_tables = re.findall(r'\|(.+)\|', translated_content)
        
        if len(original_tables) != len(translated_tables):
            analysis['tables_preserved'] = f'❌ Table rows: {len(original_tables)} → {len(translated_tables)}'
            analysis['issues'].append(f'Table structure changed: {len(original_tables)} → {len(translated_tables)} rows')
        elif original_tables:
            # Check table structure integrity
            orig_cols = [len(row.split('|')) for row in original_tables[:3]]  # Sample first 3 rows
            trans_cols = [len(row.split('|')) for row in translated_tables[:3]]
            if orig_cols != trans_cols:
                analysis['tables_preserved'] = '⚠️ Column structure may be altered'
                analysis['issues'].append('Table column structure possibly changed')
        
        # Analyze code blocks
        original_code_blocks = re.findall(r'```[\s\S]*?```', original_content)
        translated_code_blocks = re.findall(r'```[\s\S]*?```', translated_content)
        original_inline_code = re.findall(r'`[^`]+`', original_content)
        translated_inline_code = re.findall(r'`[^`]+`', translated_content)
        
        if len(original_code_blocks) != len(translated_code_blocks):
            analysis['code_preserved'] = f'❌ Code blocks: {len(original_code_blocks)} → {len(translated_code_blocks)}'
            analysis['issues'].append(f'Code block count changed: {len(original_code_blocks)} → {len(translated_code_blocks)}')
        
        if len(original_inline_code) != len(translated_inline_code):
            if analysis['code_preserved'] == '✅ Good':
                analysis['code_preserved'] = f'❌ Inline code: {len(original_inline_code)} → {len(translated_inline_code)}'
            analysis['issues'].append(f'Inline code count changed: {len(original_inline_code)} → {len(translated_inline_code)}')
        
        # Analyze links
        original_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', original_content)
        translated_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', translated_content)
        
        if len(original_links) != len(translated_links):
            analysis['links_preserved'] = f'❌ Links: {len(original_links)} → {len(translated_links)}'
            analysis['issues'].append(f'Link count changed: {len(original_links)} → {len(translated_links)}')
        elif original_links:
            # Check if URLs are preserved
            orig_urls = set(link[1] for link in original_links)
            trans_urls = set(link[1] for link in translated_links)
            if orig_urls != trans_urls:
                analysis['links_preserved'] = '⚠️ Link URLs may have changed'
                analysis['issues'].append('Some link URLs were altered during translation')
        
        # Analyze emphasis (bold/italic)
        original_bold = re.findall(r'\*\*([^*]+)\*\*', original_content)
        translated_bold = re.findall(r'\*\*([^*]+)\*\*', translated_content)
        original_italic = re.findall(r'\*([^*]+)\*', original_content)
        translated_italic = re.findall(r'\*([^*]+)\*', translated_content)
        
        bold_diff = abs(len(original_bold) - len(translated_bold))
        italic_diff = abs(len(original_italic) - len(translated_italic))
        
        if bold_diff > 2 or italic_diff > 2:  # Allow some variation for natural translation
            analysis['emphasis_preserved'] = f'⚠️ Bold: {len(original_bold)}→{len(translated_bold)}, Italic: {len(original_italic)}→{len(translated_italic)}'
            analysis['issues'].append('Significant emphasis formatting changes detected')
        
        # Analyze overall structure (paragraph count, line breaks)
        original_paragraphs = len([p for p in original_content.split('\n\n') if p.strip()])
        translated_paragraphs = len([p for p in translated_content.split('\n\n') if p.strip()])
        
        if abs(original_paragraphs - translated_paragraphs) > 2:  # Allow some variation
            analysis['structure_preserved'] = f'⚠️ Paragraphs: {original_paragraphs} → {translated_paragraphs}'
            analysis['issues'].append(f'Paragraph structure significantly changed: {original_paragraphs} → {translated_paragraphs}')
        
        # Overall assessment
        if not analysis['issues']:
            analysis['issues'] = ['No significant formatting issues detected']
        
        return analysis
