#!/usr/bin/env python3
"""
Fix for the translator concurrent processing issue.
This script replaces the problematic _translate_chunk_concurrent method.
"""

NEW_CONCURRENT_METHOD = '''
    async def _translate_chunk_concurrent(self, content: str, language_name: str, target_language: str, task: Dict[str, Any]) -> Optional[str]:
        """
        Translate content by sending concurrent requests to all endpoints.
        Simplified version that works correctly without as_completed issues.
        """
        import asyncio
        import aiohttp
        import json
        
        # Translation endpoints with priority order (1=highest priority)
        endpoints = [
            {"url": "https://n8n.thinhkhuat.com/webhook/agent/translate", "priority": 1, "name": "Primary"},
            {"url": "https://n8n.thinhkhuat.work/webhook/agent/translate", "priority": 2, "name": "Backup-1"},  
            {"url": "https://srv.saola-great.ts.net/webhook/agent/translate", "priority": 3, "name": "Backup-2"}
        ]
        
        # Prepare payload matching your endpoint schema
        payload = {
            "transcript": content,
            "sessionId": f"translator-{int(datetime.now().timestamp())}"
        }
        
        print_agent_output(f"Sending concurrent requests to {len(endpoints)} translation endpoints...", agent="TRANSLATOR")
        
        # Create concurrent tasks for all endpoints
        tasks = []
        for i, endpoint in enumerate(endpoints):
            task = asyncio.create_task(
                self._translate_single_endpoint(endpoint, payload)
            )
            tasks.append((task, endpoint))
        
        # Wait for all tasks to complete with gather
        completed_results = []
        try:
            # Run all tasks concurrently
            results = await asyncio.gather(*[t[0] for t in tasks], return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                endpoint_info = endpoints[i]
                if isinstance(result, Exception):
                    print_agent_output(f"Endpoint {endpoint_info['name']} failed with exception: {result}", agent="TRANSLATOR")
                elif result and isinstance(result, dict) and result.get("success"):
                    completed_results.append({
                        **result,
                        "endpoint": endpoint_info,
                        "priority": endpoint_info["priority"]
                    })
                    print_agent_output(f"Endpoint {endpoint_info['name']} completed successfully: {result.get('length', 0)} chars", agent="TRANSLATOR")
                else:
                    print_agent_output(f"Endpoint {endpoint_info['name']} returned no valid result", agent="TRANSLATOR")
        
        except Exception as e:
            print_agent_output(f"Error during concurrent translation: {e}", agent="TRANSLATOR")
        
        # Select the best result using priority and length criteria
        if completed_results:
            selected_result = self._select_best_translation_result(completed_results)
            if selected_result:
                endpoint_name = selected_result["endpoint"]["name"]
                text_length = selected_result.get("length", 0)
                print_agent_output(f"Selected result from {endpoint_name}: {text_length} chars", agent="TRANSLATOR")
                return selected_result.get("text")
        
        print_agent_output("No valid translation results from any endpoint", agent="TRANSLATOR")
        return None
'''

print("New _translate_chunk_concurrent method ready to replace the problematic version.")
print("\nThis fixes:")
print("1. Removes problematic asyncio.as_completed usage")
print("2. Uses simpler asyncio.gather approach")
print("3. Properly processes all results")
print("4. Maintains concurrent execution")