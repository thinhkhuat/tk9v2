import json


class HumanAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None, draft_manager=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.draft_manager = draft_manager

    async def review_plan(self, research_state: dict):
        print(f"HumanAgent websocket: {self.websocket}")
        print(f"HumanAgent stream_output: {self.stream_output}")
        task = research_state.get("task")
        layout = research_state.get("sections")

        user_feedback = None

        if task.get("include_human_feedback"):
            # Stream response to the user if a websocket is provided (such as from web app)
            if self.websocket and self.stream_output:
                try:
                    await self.stream_output(
                        "human_feedback",
                        "request",
                        f"Any feedback on this plan of topics to research? {layout}? If not, please reply with 'no'.",
                        self.websocket,
                    )
                    # because websocket is wrapped inside a CustomLogsHandler in websocket_manager
                    response = await self.websocket.websocket.receive_text()
                    print(f"Received response: {response}", flush=True)
                    response_data = json.loads(response)
                    if response_data.get("type") == "human_feedback":
                        user_feedback = response_data.get("content")
                    else:
                        print(
                            f"Unexpected response type: {response_data.get('type')}",
                            flush=True,
                        )
                except Exception as e:
                    print(f"Error receiving human feedback: {e}", flush=True)
            # Otherwise, prompt the user for feedback in the console
            else:
                import asyncio
                import sys
                
                # Use async-compatible input alternative
                try:
                    user_feedback = await self._async_input(
                        f"Any feedback on this plan? {layout}? If not, please reply with 'no'.\n>> "
                    )
                except Exception as e:
                    print(f"Error getting async input: {e}", flush=True)
                    # Fallback to synchronous input if async fails
                    user_feedback = input(
                        f"Any feedback on this plan? {layout}? If not, please reply with 'no'.\n>> "
                    )

        user_feedback_str = str(user_feedback).strip() if user_feedback else ""
        if user_feedback_str and "no" in user_feedback_str.lower():
            user_feedback = None

        print(f"User feedback before return: {user_feedback}")

        # Save human feedback if provided
        if self.draft_manager and user_feedback:
            self.draft_manager.save_human_feedback(
                feedback=user_feedback,
                context={
                    "layout": layout,
                    "task": task,
                    "feedback_method": "websocket" if self.websocket else "console"
                }
            )

        return {"human_feedback": user_feedback}

    async def _async_input(self, prompt: str) -> str:
        """
        Async-compatible input method that doesn't block the event loop
        """
        import asyncio
        import sys
        
        # Write the prompt
        sys.stdout.write(prompt)
        sys.stdout.flush()
        
        # Read input asynchronously using a thread executor
        loop = asyncio.get_event_loop()
        input_text = await loop.run_in_executor(None, sys.stdin.readline)
        
        return input_text.strip()
