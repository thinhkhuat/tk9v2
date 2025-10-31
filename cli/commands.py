import json
import os
import asyncio
from typing import Dict, Any
from datetime import datetime
from gpt_researcher.utils.enum import Tone
from multi_agents.main import run_research_task, open_task
from .utils import CLIColors, format_progress, create_progress_bar, ProgressTracker, print_box, format_duration


class CLICommands:
    """CLI command handlers"""
    
    @staticmethod
    def show_config():
        """Show current configuration"""
        colors = CLIColors()
        
        print(f"\n{colors.BLUE}═══ CURRENT CONFIGURATION ═══{colors.RESET}")
        
        # Force reload environment variables
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # Reload the provider configuration after env reload
        from multi_agents.providers.factory import config_manager
        config_manager.config = config_manager._load_config_from_env()
        
        # Load language configuration
        from multi_agents.utils.language_config import language_config
        
        try:
            # Load current task configuration
            task = open_task()
            
            print(f"\n{colors.YELLOW}Task Configuration:{colors.RESET}")
            print(f"  Query: {colors.CYAN}{task.get('query', 'Not set')}{colors.RESET}")
            print(f"  Model: {colors.CYAN}{task.get('model', 'Not set')}{colors.RESET}")
            print(f"  Max Sections: {colors.CYAN}{task.get('max_sections', 'Not set')}{colors.RESET}")
            print(f"  Include Human Feedback: {colors.CYAN}{task.get('include_human_feedback', False)}{colors.RESET}")
            print(f"  Follow Guidelines: {colors.CYAN}{task.get('follow_guidelines', False)}{colors.RESET}")
            print(f"  Verbose: {colors.CYAN}{task.get('verbose', False)}{colors.RESET}")
            
            # Show publish formats
            formats = task.get('publish_formats', {})
            print(f"\n{colors.YELLOW}Publish Formats:{colors.RESET}")
            for format_name, enabled in formats.items():
                status = colors.GREEN + "✓" if enabled else colors.RED + "✗"
                print(f"  {format_name}: {status}{colors.RESET}")
            
            # Show guidelines
            guidelines = task.get('guidelines', [])
            if guidelines:
                print(f"\n{colors.YELLOW}Guidelines:{colors.RESET}")
                for i, guideline in enumerate(guidelines, 1):
                    print(f"  {i}. {guideline}")
            
        except Exception as e:
            print(f"{colors.RED}Error loading configuration: {e}{colors.RESET}")
        
        # Show provider status
        from multi_agents.providers.factory import config_manager
        provider_info = config_manager.get_provider_info()
        
        print(f"\n{colors.YELLOW}Active Providers:{colors.RESET}")
        llm_info = provider_info["primary_llm"]
        search_info = provider_info["primary_search"]
        
        llm_status = colors.GREEN + "✓" if llm_info["has_api_key"] else colors.RED + "✗"
        search_status = colors.GREEN + "✓" if search_info["has_api_key"] else colors.RED + "✗"
        
        print(f"  LLM: {llm_status}{colors.RESET} {llm_info['provider']}:{llm_info['model']}")
        print(f"  Search: {search_status}{colors.RESET} {search_info['provider']} (max: {search_info['max_results']})")
        
        # Show language configuration
        print(f"\n{colors.YELLOW}Language Configuration:{colors.RESET}")
        lang_code = language_config.get_research_language()
        lang_name = language_config.get_language_name(lang_code)
        search_country = language_config.get_search_country(lang_code)
        
        print(f"  Research Language: {colors.CYAN}{lang_name} ({lang_code.upper()}){colors.RESET}")
        print(f"  Search Country: {colors.CYAN}{search_country}{colors.RESET}")
        print(f"  Brave UI Language: {colors.CYAN}{language_config.get_brave_ui_lang(lang_code)}{colors.RESET}")
        
        # Show translation configuration
        print(f"\n{colors.YELLOW}Translation Configuration:{colors.RESET}")
        translation_endpoints = [
            {"name": "Primary", "url": "n8n.thinhkhuat.com", "priority": 1},
            {"name": "Backup-1", "url": "n8n.thinhkhuat.work", "priority": 2},  
            {"name": "Backup-2", "url": "srv.saola-great.ts.net", "priority": 3}
        ]
        
        print(f"  Timeout per Endpoint: {colors.CYAN}300 seconds (5 minutes){colors.RESET}")
        print(f"  Max Retry Attempts: {colors.CYAN}2 attempts{colors.RESET}")
        print(f"  Execution Mode: {colors.CYAN}Concurrent with early return optimization{colors.RESET}")
        print(f"  Early Return Criteria: {colors.CYAN}≥90% of original text length{colors.RESET}")
        print(f"  Early Return Strategy:")
        print(f"    • {colors.GREEN}Priority 1 valid result → Return immediately{colors.RESET}")
        print(f"    • {colors.YELLOW}Priority 2/3 valid result → Wait 5s for higher priority{colors.RESET}")
        print(f"    • {colors.GRAY}Invalid results → Wait for all endpoints{colors.RESET}")
        print(f"  Final Selection: {colors.CYAN}Longest text → Highest priority{colors.RESET}")
        print(f"  Endpoints:")
        for endpoint in translation_endpoints:
            print(f"    {endpoint['priority']}. {colors.GREEN}{endpoint['name']}{colors.RESET}: {endpoint['url']}")
        
        # Show environment variables
        print(f"\n{colors.YELLOW}Environment:{colors.RESET}")
        env_vars = [
            'RESEARCH_LANGUAGE',
            'OPENAI_API_KEY',
            'GOOGLE_API_KEY',
            'ANTHROPIC_API_KEY',
            'LANGCHAIN_API_KEY',
            'LANGCHAIN_TRACING_V2',
            'TAVILY_API_KEY',
            'BRAVE_API_KEY',
            'GOOGLE_CSE_ID'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive keys
                if 'KEY' in var and len(value) > 8:
                    masked = value[:4] + '*' * (len(value) - 8) + value[-4:]
                    print(f"  {var}: {colors.GREEN}{masked}{colors.RESET}")
                else:
                    print(f"  {var}: {colors.GREEN}{value}{colors.RESET}")
            else:
                print(f"  {var}: {colors.RED}Not set{colors.RESET}")
    
    @staticmethod
    async def run_single_research(query: str, tone: str = "objective", verbose: bool = False, save_files: bool = True, language: str = None):
        """Run a single research query with enhanced progress tracking"""
        colors = CLIColors()
        progress_tracker = ProgressTracker(colors)
        
        # Apply language configuration if provided
        if language:
            import os
            os.environ['RESEARCH_LANGUAGE'] = language
            from multi_agents.utils.language_config import language_config
            language_config.apply_to_environment(language)
        
        # Get language status
        from multi_agents.utils.language_config import language_config
        lang_status = language_config.get_status_message()
        
        # Enhanced header with better formatting
        print(f"\n{colors.BLUE}{'═' * 60}{colors.RESET}")
        print_box(f"Deep Research MCP - Multi-Agent Research System", colors, "RESEARCH SESSION")
        
        # Research parameters in a structured format
        params = [
            f"Query: {colors.CYAN}{query}{colors.RESET}",
            f"Tone: {colors.CYAN}{tone.title()}{colors.RESET}",
            f"Language: {colors.CYAN}{lang_status}{colors.RESET}",
            f"Save Files: {colors.GREEN if save_files else colors.RED}{'Enabled' if save_files else 'Disabled'}{colors.RESET}",
            f"Verbose: {colors.GREEN if verbose else colors.GRAY}{'Enabled' if verbose else 'Disabled'}{colors.RESET}"
        ]
        
        for param in params:
            print(f"  {param}")
        
        print(f"{colors.BLUE}{'─' * 60}{colors.RESET}")
        print(f"{colors.CYAN}🚀 Initializing research workflow...{colors.RESET}")
        
        start_time = datetime.now()
        current_agent = None
        
        try:
            # Convert tone string to enum
            tone_enum = getattr(Tone, tone.capitalize(), Tone.Objective)
            
            # Enhanced progress handler with visual progress bars
            async def enhanced_progress_handler(type_: str, key: str, value: Any, websocket=None):
                nonlocal current_agent
                
                if type_ == "logs":
                    if verbose:
                        print(f"{colors.GRAY}  [LOG] {key}: {value}{colors.RESET}")
                elif type_ == "progress":
                    if isinstance(value, (int, float)):
                        if current_agent:
                            progress_tracker.update_progress(current_agent, value)
                            bar = create_progress_bar(value, width=30, colors=colors)
                            print(f"\r{colors.CYAN}  {current_agent}: {bar}{colors.RESET}", end='', flush=True)
                        else:
                            bar = create_progress_bar(value, width=30, colors=colors)
                            print(f"\r{colors.CYAN}  Overall Progress: {bar}{colors.RESET}", end='', flush=True)
                    else:
                        print(f"\n{colors.CYAN}  Status: {value}{colors.RESET}")
                elif type_ == "agent_start":
                    agent_name = key.replace('_', ' ').title()
                    current_agent = agent_name
                    progress_tracker.start_agent(agent_name, str(value))
                    print(f"\n{colors.GREEN}🤖 [{agent_name}] Starting: {value}{colors.RESET}")
                elif type_ == "agent_output":
                    agent_name = key.replace('_', ' ').title()
                    if current_agent:
                        progress_tracker.complete_agent(current_agent)
                    print(f"\n{colors.GREEN}✓ [{agent_name}] Completed{colors.RESET}")
                    if verbose and value:
                        # Show truncated output in verbose mode
                        preview = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                        print(f"{colors.GRAY}  Result: {preview}{colors.RESET}")
            
            # Run research with robust error handling for known issues
            max_retries = 2
            retry_count = 0
            result = None
            
            while retry_count <= max_retries:
                try:
                    result = await run_research_task(
                        query=query,
                        websocket=None,
                        stream_output=enhanced_progress_handler,
                        tone=tone_enum,
                        write_to_files=save_files,
                        language=language
                    )
                    break  # Success, exit retry loop
                    
                except Exception as research_error:
                    error_msg = str(research_error)
                    retry_count += 1
                    
                    # Check for known recoverable errors
                    if "Separator is not found" in error_msg and "chunk exceed" in error_msg:
                        print(f"\n{colors.YELLOW}⚠️  Text processing error detected (attempt {retry_count}/{max_retries + 1}){colors.RESET}")
                        print(f"{colors.GRAY}   This is usually due to large content chunks in search results{colors.RESET}")
                        
                        if retry_count <= max_retries:
                            print(f"{colors.CYAN}   Retrying with shorter query and reduced content limits...{colors.RESET}")
                            
                            # Modify query to be shorter for retry
                            if len(query) > 200:
                                shortened_query = query[:200].rsplit(' ', 1)[0] + "..."
                                print(f"{colors.GRAY}   Shortened query: {shortened_query}{colors.RESET}")
                                query = shortened_query
                            
                            # Add delay before retry
                            await asyncio.sleep(2)
                            continue
                        else:
                            print(f"{colors.RED}   Max retries exceeded. This may be a library-level issue.{colors.RESET}")
                            raise research_error
                    
                    elif "HTTP 422" in error_msg and "BRAVE" in error_msg:
                        print(f"\n{colors.YELLOW}⚠️  BRAVE API validation error (attempt {retry_count}/{max_retries + 1}){colors.RESET}")
                        
                        if retry_count <= max_retries:
                            print(f"{colors.CYAN}   Retrying with fallback search provider...{colors.RESET}")
                            
                            # Temporarily switch to fallback provider for this retry
                            original_provider = os.environ.get('PRIMARY_SEARCH_PROVIDER')
                            os.environ['PRIMARY_SEARCH_PROVIDER'] = 'tavily'  # Fallback to Tavily
                            
                            try:
                                await asyncio.sleep(1)
                                continue
                            finally:
                                # Restore original provider
                                if original_provider:
                                    os.environ['PRIMARY_SEARCH_PROVIDER'] = original_provider
                        else:
                            print(f"{colors.RED}   Max retries exceeded for BRAVE API errors{colors.RESET}")
                            raise research_error
                    
                    else:
                        # Unknown error, don't retry
                        print(f"\n{colors.RED}⚠️  Unknown research error: {error_msg}{colors.RESET}")
                        raise research_error
            
            if result is None:
                raise Exception("Research failed after all retry attempts")
            
            # Calculate duration
            duration = datetime.now() - start_time
            duration_str = format_duration(duration.total_seconds())
            
            # Success message with enhanced formatting
            print(f"\n\n{colors.GREEN}{'═' * 60}{colors.RESET}")
            print_box("Research Completed Successfully! 🎉", colors, "SUCCESS")
            
            completion_info = [
                f"Duration: {colors.CYAN}{duration_str}{colors.RESET}",
                f"Status: {colors.GREEN}✓ Complete{colors.RESET}",
                f"Agents Used: {colors.CYAN}{len(progress_tracker.agents)}{colors.RESET}"
            ]
            
            if save_files:
                completion_info.extend([
                    f"Output Location: {colors.CYAN}./outputs/{colors.RESET}",
                    f"Formats: {colors.GRAY}PDF • DOCX • Markdown{colors.RESET}"
                ])
            
            for info in completion_info:
                print(f"  {info}")
            
            # Show agent summary
            if progress_tracker.agents:
                print(f"\n{colors.YELLOW}Agent Summary:{colors.RESET}")
                print(progress_tracker.display_summary())
            
            # Format and display the result
            print(f"\n{colors.BLUE}{'─' * 60}{colors.RESET}")
            CLICommands._display_research_result(result, colors)
            
        except Exception as e:
            duration = datetime.now() - start_time
            duration_str = format_duration(duration.total_seconds())
            
            print(f"\n\n{colors.RED}{'═' * 60}{colors.RESET}")
            print_box(f"Research Failed After {duration_str}", colors, "ERROR")
            print(f"  {colors.RED}Error: {str(e)}{colors.RESET}")
            
            if progress_tracker.agents:
                print(f"\n{colors.YELLOW}Agent Status at Failure:{colors.RESET}")
                print(progress_tracker.display_summary())
            
            raise
    
    @staticmethod
    def _display_research_result(result: Any, colors: CLIColors):
        """Display research results in a formatted way"""
        print(f"\n{colors.GREEN}Research Results:{colors.RESET}")
        print(f"{colors.GRAY}{'=' * 80}{colors.RESET}")
        
        if isinstance(result, dict):
            # Try to find the main content
            content_keys = ['content', 'report', 'final_report', 'research_report']
            
            main_content = None
            for key in content_keys:
                if key in result:
                    main_content = result[key]
                    break
            
            if main_content:
                print(main_content)
            else:
                # Display the entire result as JSON if no main content found
                print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Display as string
            print(str(result))
        
        print(f"{colors.GRAY}{'=' * 80}{colors.RESET}")
    
    @staticmethod
    def show_agents_info():
        """Show information about available agents"""
        colors = CLIColors()
        
        print(f"\n{colors.BLUE}═══ MULTI-AGENT RESEARCH TEAM ═══{colors.RESET}")
        
        agents = [
            {
                "name": "Browser Agent",
                "role": "Initial Research",
                "description": "Conducts preliminary web research to gather basic information"
            },
            {
                "name": "Editor Agent", 
                "role": "Planning & Structure",
                "description": "Plans research outline and manages the overall structure"
            },
            {
                "name": "Researcher Agent",
                "role": "Deep Investigation", 
                "description": "Performs detailed research on specific topics and subtopics"
            },
            {
                "name": "Writer Agent",
                "role": "Content Creation",
                "description": "Compiles research into comprehensive reports with intro/conclusion"
            },
            {
                "name": "Publisher Agent",
                "role": "Output Generation",
                "description": "Formats and exports reports to multiple formats (PDF, DOCX, MD)"
            },
            {
                "name": "Reviewer Agent",
                "role": "Quality Control",
                "description": "Validates research quality and provides feedback"
            },
            {
                "name": "Revisor Agent",
                "role": "Revision & Improvement", 
                "description": "Revises content based on reviewer feedback"
            },
            {
                "name": "Human Agent",
                "role": "Human Oversight",
                "description": "Provides human-in-the-loop feedback and guidance"
            }
        ]
        
        for agent in agents:
            print(f"\n{colors.GREEN}{agent['name']}{colors.RESET}")
            print(f"  Role: {colors.CYAN}{agent['role']}{colors.RESET}")
            print(f"  Description: {colors.GRAY}{agent['description']}{colors.RESET}")
        
        print(f"\n{colors.YELLOW}Workflow:{colors.RESET}")
        print(f"  1. {colors.CYAN}Browse{colors.RESET} → Initial web research")
        print(f"  2. {colors.CYAN}Plan{colors.RESET} → Structure and outline")
        print(f"  3. {colors.CYAN}Research{colors.RESET} → Deep investigation (parallel)")
        print(f"  4. {colors.CYAN}Review{colors.RESET} → Quality validation")
        print(f"  5. {colors.CYAN}Revise{colors.RESET} → Content improvement")
        print(f"  6. {colors.CYAN}Write{colors.RESET} → Final report compilation")
        print(f"  7. {colors.CYAN}Publish{colors.RESET} → Multi-format output")