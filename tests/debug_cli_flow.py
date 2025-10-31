#!/usr/bin/env python3
"""
Debug script that exactly mimics the interactive CLI flow
"""

import asyncio
from datetime import datetime
from gpt_researcher.utils.enum import Tone

def debug_cli_flow():
    print("🔍 DEBUGGING EXACT CLI FLOW")
    print("=" * 50)
    
    # Step 1: Import main (this is what happens when CLI starts)
    print("Step 1: Importing main.py...")
    from multi_agents.main import run_research_task
    
    # Step 2: Import interactive CLI  
    print("Step 2: Importing interactive CLI...")
    from cli.interactive import InteractiveCLI
    
    # Step 3: Create CLI instance
    print("Step 3: Creating InteractiveCLI instance...")
    cli = InteractiveCLI(verbose=False, save_files=True)
    
    # Step 4: Simulate the exact flow when user types a query
    print("Step 4: Simulating research query...")
    query = "Test debug flow"
    
    print(f"\n{'═══ STARTING RESEARCH ═══'}")
    print(f"Query: {query}")
    print(f"Save Files: Yes")
    print(f"Assembling research team...")
    
    # Step 5: This is the exact call that happens in handle_research_query
    print("Step 5: About to call run_research_task...")
    
    async def run_test():
        # Stream output handler like in interactive CLI
        async def cli_stream_output(type_: str, key: str, value, websocket=None):
            if type_ == "agent_output":
                agent_name = key.upper()
                print(f"🎯 CAPTURED: [{agent_name}] {value}")
                
                # Look specifically for provider messages
                if "PROVIDERS" in agent_name or "Using LLM" in str(value):
                    print(f"🚨 PROVIDER MESSAGE DETECTED: {value}")
            elif type_ == "logs":
                print(f"📝 LOG: [{key}] {value}")
            else:
                print(f"🔍 OTHER: {type_}:{key} = {value}")
        
        # This is the EXACT call from interactive.py line 149-155
        try:
            result = await run_research_task(
                query=query,
                websocket=None,
                stream_output=cli_stream_output,
                tone=Tone.Objective,
                write_to_files=True
            )
            print("✅ run_research_task completed")
            return result
        except KeyboardInterrupt:
            print("⚠️ Interrupted by user")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    # Run the async function
    return asyncio.run(run_test())

if __name__ == "__main__":
    debug_cli_flow()