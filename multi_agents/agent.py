import asyncio

from multi_agents.agents import ChiefEditorAgent


async def main():
    chief_editor = ChiefEditorAgent(
        {
            "query": "US-Vietnam Trade Agreement 2025 - Impacts and Strategic Responses, with the interest of the Vietnamese",
            "max_sections": 7,
            "follow_guidelines": True,
            "model": "gemini-2.5-flash-preview-05-20",
            "guidelines": ["The report MUST be written in VIETNAMESE"],
            "verbose": True,
        },
        websocket=None,
        stream_output=print,
        write_to_files=True,
    )

    graph = chief_editor.init_research_team()
    graph = graph.compile()

    # Run the research task
    result = await graph.ainvoke({"task": chief_editor.task})
    print("Research completed successfully!")
    return result


if __name__ == "__main__":
    asyncio.run(main())
