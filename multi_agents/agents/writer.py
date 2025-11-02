from datetime import datetime
from typing import Any, Dict

import json5 as json

from .utils.llms import call_model
from .utils.type_safety import (
    ensure_dict,
    ensure_list,
    safe_dict_get,
)
from .utils.views import print_agent_output

sample_json = """
{
  "table_of_contents": "- Main Section 1\n  - Subsection 1.1\n  - Subsection 1.2\n- Main Section 2\n  - Subsection 2.1",
  "introduction": "This is a detailed introduction with proper citations ([Source Title](https://example.com)) that provides context for the research topic.",
  "conclusion": "This is a comprehensive conclusion that summarizes all findings with relevant citations ([Source Title](https://example.com)).",
  "sources": ["- Author, Year. Title [Source](https://example.com)", "- Author2, Year. Title2 [Source2](https://example.com/2)"]
}
"""


class WriterAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None, draft_manager=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers
        self.draft_manager = draft_manager

    def get_headers(self, research_state: Dict[str, Any]) -> Dict[str, str]:
        return {
            "title": research_state.get("title"),
            "date": "Date",
            "introduction": "Introduction",
            "table_of_contents": "Table of Contents",
            "conclusion": "Conclusion",
            "references": "References",
        }

    async def write_sections(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        # Get the query, preferring the original task query if title is generic
        title = safe_dict_get(research_state, "title", "Unknown Topic")
        task = ensure_dict(research_state.get("task"))

        # If title is generic or empty, use the original query from task
        if title in ["Unknown Topic", "Untitled Research Project", "Research Report", None, ""]:
            original_query = safe_dict_get(task, "query", "Unknown Topic", str)
            query = original_query
            print_agent_output(
                f"Using original query instead of generic title: {original_query}", agent="WRITER"
            )
        else:
            query = title

        data = ensure_list(research_state.get("research_data"))
        follow_guidelines = safe_dict_get(task, "follow_guidelines", False, bool)
        guidelines = ensure_list(task.get("guidelines"))

        # Add validation to ensure we stay on topic when research data is missing
        if not data or len(data) == 0:
            print_agent_output(
                f"Warning: No research data available, instructing AI to focus on query: {query}",
                agent="WRITER",
            )
            # Add explicit instruction to focus on the query when no research data is available
            focus_instruction = f"\n\nIMPORTANT: You have limited research data. Focus exclusively on the query '{query}'. Do NOT generate content about unrelated topics like AI, workforce, or other subjects. If you lack information, state what information is needed rather than creating unrelated content."
        else:
            focus_instruction = ""

        prompt = [
            {
                "role": "system",
                "content": "You are a research writer. Your sole purpose is to write a well-written "
                "research reports about a "
                "topic based on research findings and information.\n ",
            },
            {
                "role": "user",
                "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."
                f"Query or Topic: {query}\n"
                f"Research data: {self._prepare_research_data(data)}\n\n"
                f"Task: Create a research report with introduction, table of contents, conclusion and sources.\n"
                f"Include relevant citations as markdown links: ([Source](url))\n\n"
                f"{f'Guidelines: {guidelines}' if follow_guidelines else ''}\n\n"
                f"{focus_instruction}\n\n"
                f"Return ONLY this JSON format (no other text):\n"
                f"{sample_json}\n\n"
                f"Requirements:\n"
                f"- Return ONLY valid JSON with no additional text before or after\n"
                f"- Must include all 4 fields: table_of_contents, introduction, conclusion, sources\n"
                f"- Sources must be array of objects with 'title' and 'url' fields\n"
                f"- No markdown code blocks (```json)\n"
                f"- No explanatory text or comments\n"
                f"- Start response with {{ and end with }}\n"
                f"- Ensure all strings are properly quoted and escaped\n",
            },
        ]

        try:
            response = await call_model(
                prompt,
                task.get("model"),
                response_format="json",
            )
        except Exception as e:
            print_agent_output(f"Error calling LLM for sections: {str(e)}", agent="WRITER")
            # Return fallback structure
            query = safe_dict_get(task, "query", "Unknown Topic", str)
            return {
                "table_of_contents": f"Research Report: {query}",
                "introduction": f"This report analyzes {query}. Due to a processing error, detailed content could not be generated.",
                "conclusion": "Further analysis would be needed to provide comprehensive insights.",
                "sources": [],
            }

        # Debug and validate the JSON response
        print(f"DEBUG: Raw response type: {type(response)}")
        print(f"DEBUG: Raw response content: {str(response)[:500]}...")

        if isinstance(response, dict):
            print(f"DEBUG: Response is dict with keys: {list(response.keys())}")
            # Ensure all required fields are present
            required_fields = ["table_of_contents", "introduction", "conclusion", "sources"]
            fixed_response = {}
            missing_fields = []

            for field in required_fields:
                if field in response and response[field]:
                    fixed_response[field] = response[field]
                    print(f"DEBUG: Found field '{field}': {str(response[field])[:100]}...")
                else:
                    missing_fields.append(field)
                    # Provide safe defaults for missing fields
                    if field == "table_of_contents":
                        fixed_response[field] = (
                            "Table of contents could not be generated due to parsing error"
                        )
                    elif field == "introduction":
                        fixed_response[field] = (
                            "Introduction could not be generated due to incomplete response"
                        )
                    elif field == "conclusion":
                        fixed_response[field] = (
                            "Conclusion could not be generated due to parsing error"
                        )
                    elif field == "sources":
                        fixed_response[field] = []

            if missing_fields:
                print(f"WARNING: Missing or empty fields in JSON response: {missing_fields}")

            # Log any unexpected fields
            unexpected_fields = [k for k in response.keys() if k not in required_fields]
            if unexpected_fields:
                print(f"WARNING: Unexpected fields in response: {unexpected_fields}")

            response = fixed_response
        else:
            print(f"WARNING: Response is not a dict, type: {type(response)}")
            # If response is a string, try to extract meaningful content
            response_str = str(response) if response else ""
            response = {
                "table_of_contents": "Table of contents could not be generated due to parsing error",
                "introduction": (
                    response_str[:500] + "..." if len(response_str) > 500 else response_str
                ),
                "conclusion": "Conclusion could not be generated due to parsing error",
                "sources": [],
            }

        # Save draft of sections writing
        if self.draft_manager:
            self.draft_manager.save_agent_output(
                agent_name="writer",
                phase="writing",
                output=response,
                step="write_sections",
                metadata={
                    "query": query,
                    "follow_guidelines": follow_guidelines,
                    "response_fixed": isinstance(response, dict),
                },
            )

        return response

    async def revise_headers(self, task: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        prompt = [
            {
                "role": "system",
                "content": """You are a research writer. 
Your sole purpose is to revise the headers data based on the given guidelines.""",
            },
            {
                "role": "user",
                "content": f"""Your task is to revise the given headers JSON based on the guidelines given.
You are to follow the guidelines but the values should be in simple strings, ignoring all markdown syntax.

Guidelines: {task.get("guidelines")}
Headers Data: {headers}

You MUST return ONLY a valid JSON object (no markdown code blocks, no additional text) in the same format as the headers data provided above.
Return only valid JSON, nothing else.
""",
            },
        ]

        try:
            response = await call_model(
                prompt,
                task.get("model"),
                response_format="json",
            )
        except Exception as e:
            print_agent_output(f"Error calling LLM for header revision: {str(e)}", agent="WRITER")
            response = headers  # Use original headers as fallback

        # Handle case where response might be a string instead of dict due to JSON parsing failure
        if isinstance(response, str):
            print_agent_output(
                "Headers revision JSON parsing failed, returning original headers", agent="WRITER"
            )
            response = headers  # Use original headers as fallback

        # Save draft of revised headers
        if self.draft_manager:
            self.draft_manager.save_agent_output(
                agent_name="writer",
                phase="writing",
                output={"original_headers": headers, "revised_headers": response},
                step="revise_headers",
                metadata={"guidelines": task.get("guidelines")},
            )

        return {"headers": response}

    async def run(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "writing_report",
                "Writing final research report based on research data...",
                self.websocket,
            )
        else:
            print_agent_output(
                "Writing final research report based on research data...",
                agent="WRITER",
            )

        research_layout_content = await self.write_sections(research_state)

        # Handle case where write_sections might return a string instead of dict due to JSON parsing failure
        if not isinstance(research_layout_content, dict):
            print_agent_output(
                "Write sections returned invalid type, attempting intelligent content extraction",
                agent="WRITER",
            )
            research_layout_content = self._extract_content_from_failed_json(
                str(research_layout_content), research_state
            )

        if research_state.get("task").get("verbose"):
            if self.websocket and self.stream_output:
                research_layout_content_str = json.dumps(research_layout_content, indent=2)
                await self.stream_output(
                    "logs",
                    "research_layout_content",
                    research_layout_content_str,
                    self.websocket,
                )
            else:
                print_agent_output(research_layout_content, agent="WRITER")

        headers = self.get_headers(research_state)
        if research_state.get("task").get("follow_guidelines"):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "rewriting_layout",
                    "Rewriting layout based on guidelines...",
                    self.websocket,
                )
            else:
                print_agent_output("Rewriting layout based on guidelines...", agent="WRITER")
            headers_result = await self.revise_headers(
                task=research_state.get("task"), headers=headers
            )
            # Handle case where revise_headers might return a string instead of dict
            if isinstance(headers_result, dict):
                headers = safe_dict_get(headers_result, "headers", headers, dict)
            else:
                print_agent_output(
                    "Headers revision failed, using original headers", agent="WRITER"
                )
                # Keep original headers

        # Combine final output - now safe since research_layout_content is guaranteed to be a dict
        final_output = {**research_layout_content, "headers": headers}

        # Save final writer output
        if self.draft_manager:
            self.draft_manager.save_agent_output(
                agent_name="writer",
                phase="writing",
                output=final_output,
                step="final_output",
                metadata={
                    "title": research_state.get("title"),
                    "follow_guidelines": research_state.get("task", {}).get("follow_guidelines"),
                    "sections_count": len(research_state.get("research_data", [])),
                },
            )

            # Save research state after writing phase
            self.draft_manager.save_research_state("writing", {**research_state, **final_output})

        return final_output

    def _prepare_research_data(self, data):
        """Intelligently prepare research data for the writer without truncation"""
        if not data:
            return "No research data available"

        # Convert data to string and analyze
        data_str = str(data)

        # If data is reasonably sized, return as-is
        if len(data_str) <= 8000:  # Increased from 2000 to 8000
            return data_str

        # For larger data, extract key components intelligently
        try:
            # If it's a list of research results, format each one
            if isinstance(data, list):
                formatted_sections = []
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        # Extract key information from research results
                        title = item.get("title", f"Research Section {i+1}")
                        content = item.get("content", "")
                        sources = item.get("sources", [])

                        section_info = f"**{title}**\n"

                        # Include first 1000 chars of content
                        if content:
                            section_info += (
                                f"Content: {content[:1000]}{'...' if len(content) > 1000 else ''}\n"
                            )

                        # Include all sources
                        if sources:
                            section_info += f"Sources: {', '.join(sources)}\n"

                        formatted_sections.append(section_info)

                return "\n\n".join(formatted_sections)

            # If it's a single large string, take strategic chunks
            else:
                # Take beginning, middle, and end
                beginning = data_str[:2500]
                middle_start = len(data_str) // 2 - 1250
                middle = data_str[middle_start : middle_start + 2500]
                end = data_str[-2500:]

                return f"{beginning}\n\n[... MIDDLE CONTENT ...]\n{middle}\n\n[... CONTINUED ...]\n{end}"

        except Exception:
            # Fallback to simple truncation if processing fails
            return f"{data_str[:6000]}{'...' if len(data_str) > 6000 else ''}"

    def _extract_content_from_failed_json(
        self, content_str: str, research_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract usable content from failed JSON parsing"""
        try:
            import re

            # Try to extract structured content using patterns
            table_of_contents = "Research Report Structure"
            introduction = ""
            conclusion = ""
            sources = []

            # Look for common section patterns
            sections = re.split(
                r"\n(?=##|\*\*|Introduction|Conclusion|Table|References)",
                content_str,
                flags=re.IGNORECASE,
            )

            for section in sections:
                section_str = str(section) if section else ""
                section_lower = section_str.lower().strip()
                if any(
                    keyword in section_lower for keyword in ["introduction", "intro", "overview"]
                ):
                    introduction = section.strip()
                elif any(
                    keyword in section_lower for keyword in ["conclusion", "summary", "findings"]
                ):
                    conclusion = section.strip()
                elif any(keyword in section_lower for keyword in ["table", "contents", "outline"]):
                    table_of_contents = section.strip()

            # If no specific sections found, use the content intelligently
            if not introduction and content_str:
                # Take first substantial paragraph as introduction
                paragraphs = [p.strip() for p in content_str.split("\n\n") if len(p.strip()) > 50]
                if paragraphs:
                    introduction = paragraphs[0]
                    if len(paragraphs) > 1:
                        conclusion = paragraphs[-1]

            # Extract URLs for sources
            urls = re.findall(
                r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                content_str,
            )
            for i, url in enumerate(set(urls)):  # Remove duplicates
                sources.append({"title": f"Research Source {i+1}", "url": url})

            # Generate table of contents based on content structure
            if not table_of_contents or table_of_contents == "Research Report Structure":
                topic = research_state.get("topic", "Research Topic")
                table_of_contents = f"1. Introduction to {topic}\n2. Key Findings and Analysis\n3. Conclusion and Implications"

            return {
                "table_of_contents": table_of_contents,
                "introduction": (
                    introduction
                    if introduction
                    else f"This report analyzes {research_state.get('topic', 'the research topic')} based on comprehensive research findings."
                ),
                "conclusion": (
                    conclusion
                    if conclusion
                    else "Further research and analysis would provide additional insights into this topic."
                ),
                "sources": sources,
            }

        except Exception:
            # Ultimate fallback
            return {
                "table_of_contents": f"Research Report: {research_state.get('topic', 'Topic')}",
                "introduction": (
                    content_str[:500] + "..." if len(content_str) > 500 else content_str
                ),
                "conclusion": "Analysis complete based on available research data.",
                "sources": [],
            }
