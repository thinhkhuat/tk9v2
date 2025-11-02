from .utils.file_formats import write_md_to_pdf, write_md_to_word, write_text_to_md
from .utils.views import print_agent_output


class PublisherAgent:
    def __init__(
        self, output_dir: str, websocket=None, stream_output=None, headers=None, draft_manager=None
    ):
        self.websocket = websocket
        self.stream_output = stream_output
        self.output_dir = output_dir
        self.headers = headers or {}
        self.draft_manager = draft_manager

    async def publish_research_report(self, research_state: dict, publish_formats: dict):
        layout = self.generate_layout(research_state)
        if self.output_dir:
            await self.write_report_by_formats(layout, publish_formats)

        return layout

    def generate_layout(self, research_state: dict):
        # Safely handle potentially None values
        research_data = research_state.get("research_data", [])
        sections = "\n\n".join(
            f"{value}"
            for subheader in research_data
            for key, value in subheader.items()
            if subheader
        )

        sources = research_state.get("sources", [])
        references = "\n".join(f"{reference}" for reference in sources) if sources else ""

        headers = research_state.get("headers", {})

        # Provide safe defaults for all required fields
        title = headers.get("title", "Research Report")
        date_header = headers.get("date", "Date")
        date_value = research_state.get("date", "")
        intro_header = headers.get("introduction", "Introduction")
        intro_content = research_state.get("introduction", "")
        toc_header = headers.get("table_of_contents", "Table of Contents")
        toc_content = research_state.get("table_of_contents", "")
        conclusion_header = headers.get("conclusion", "Conclusion")
        conclusion_content = research_state.get("conclusion", "")
        references_header = headers.get("references", "References")

        layout = f"""# {title}
#### {date_header}: {date_value}

## {intro_header}
{intro_content}

## {toc_header}
{toc_content}

{sections}

## {conclusion_header}
{conclusion_content}

## {references_header}
{references}
"""

        # Save layout draft
        if self.draft_manager:
            self.draft_manager.save_intermediate_draft(
                content=layout, phase="publishing", section="generated_layout", agent="publisher"
            )

        return layout

    async def write_report_by_formats(self, layout: str, publish_formats: dict):
        if publish_formats.get("pdf"):
            await write_md_to_pdf(layout, self.output_dir)
        if publish_formats.get("docx"):
            await write_md_to_word(layout, self.output_dir)
        if publish_formats.get("markdown"):
            await write_text_to_md(layout, self.output_dir)

    async def run(self, research_state: dict):
        task = research_state.get("task")
        publish_formats = task.get("publish_formats")
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "publishing",
                "Publishing final research report based on retrieved data...",
                self.websocket,
            )
        else:
            print_agent_output(
                output="Publishing final research report based on retrieved data...",
                agent="PUBLISHER",
            )

        final_research_report = await self.publish_research_report(research_state, publish_formats)

        # Save publishing output
        if self.draft_manager:
            self.draft_manager.save_agent_output(
                agent_name="publisher",
                phase="publishing",
                output=final_research_report,
                step="final_report",
                metadata={
                    "publish_formats": publish_formats,
                    "output_dir": self.output_dir,
                    "report_length": len(final_research_report),
                },
            )

            # Save final research state
            final_state = {**research_state, "report": final_research_report}
            self.draft_manager.save_research_state("publishing", final_state)

            # Create phase summary for completion
            self.draft_manager.create_phase_summary("publishing")

        return {"report": final_research_report}
