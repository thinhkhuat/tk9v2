import asyncio
import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime
from gpt_researcher.utils.enum import Tone
from multi_agents.main import run_research_task
from .utils import CLIColors, format_progress, clear_screen, create_progress_bar, ProgressTracker, print_box, format_duration
from .commands import CLICommands


class InteractiveCLI:
    def __init__(self, verbose: bool = False, save_files: bool = True, language: str = None):
        self.verbose = verbose
        self.save_files = save_files
        self.language = language
        self.session_history = []
        self.current_research = None
        self.colors = CLIColors()
        self.session_start_time = datetime.now()
        self.session_id = self.session_start_time.strftime('%Y%m%d_%H%M%S')
        self.total_research_count = 0
        self.successful_research_count = 0
        
        # Apply language configuration if provided
        if language:
            import os
            os.environ['RESEARCH_LANGUAGE'] = language
            from multi_agents.utils.language_config import language_config
            language_config.apply_to_environment(language)
        
    async def start(self):
        """Start the interactive CLI session"""
        self.print_welcome()
        
        while True:
            try:
                user_input = input(f"\n{self.colors.CYAN}research> {self.colors.RESET}").strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                else:
                    # Treat as research query
                    await self.handle_research_query(user_input)
                    
            except KeyboardInterrupt:
                print(f"\n\n{self.colors.YELLOW}Use /quit to exit gracefully{self.colors.RESET}")
                continue
            except EOFError:
                break
                
        print(f"\n{self.colors.GREEN}Goodbye!{self.colors.RESET}")
    
    def print_welcome(self):
        """Print enhanced welcome message with session info"""
        clear_screen()
        
        # Enhanced header
        print(f"{self.colors.BLUE}{'═' * 70}{self.colors.RESET}")
        print_box("Deep Research MCP - Interactive Research Session", self.colors, "WELCOME")
        
        # Session information
        session_info = [
            f"Session ID: {self.colors.CYAN}{self.session_id}{self.colors.RESET}",
            f"Started: {self.colors.CYAN}{self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}{self.colors.RESET}",
            f"Multi-Agent Team: {self.colors.GREEN}8 Specialized AI Agents{self.colors.RESET}",
            f"Save Files: {self.colors.GREEN if self.save_files else self.colors.RED}{'Enabled' if self.save_files else 'Disabled'}{self.colors.RESET}",
            f"Verbose Mode: {self.colors.GREEN if self.verbose else self.colors.GRAY}{'Enabled' if self.verbose else 'Disabled'}{self.colors.RESET}"
        ]
        
        print(f"\n{self.colors.YELLOW}Session Information:{self.colors.RESET}")
        for info in session_info:
            print(f"  {info}")
        
        # Enhanced command list
        print(f"\n{self.colors.YELLOW}Available Commands:{self.colors.RESET}")
        commands = [
            ("/help", "Show detailed help and agent information"),
            ("/config", "Display current system configuration"),
            ("/history", "Show research session history"),
            ("/stats", "Display session statistics"),
            ("/clear", "Clear the terminal screen"),
            ("/quit or /exit", "Exit the interactive session")
        ]
        
        for cmd, desc in commands:
            print(f"  {self.colors.CYAN}{cmd:<15}{self.colors.RESET} - {desc}")
        
        # Research workflow info
        print(f"\n{self.colors.YELLOW}Research Workflow:{self.colors.RESET}")
        workflow_steps = [
            "🔍 Browse → Initial web research and source gathering",
            "📝 Plan → Structure research outline and sections", 
            "🔬 Research → Deep investigation with parallel agents",
            "📊 Review → Quality control and validation",
            "✍️ Write → Compile comprehensive final report",
            "📤 Publish → Export to multiple formats (PDF, DOCX, MD)"
        ]
        
        for step in workflow_steps:
            print(f"  {step}")
        
        print(f"\n{self.colors.YELLOW}Getting Started:{self.colors.RESET}")
        print(f"  Simply type your research question or topic to begin!")
        print(f"  {self.colors.GRAY}Example: \"What are the latest developments in quantum computing?\"{self.colors.RESET}")
        
        print(f"\n{self.colors.BLUE}{'─' * 70}{self.colors.RESET}")
        print(f"{self.colors.GREEN}🚀 Ready for research! Your AI agents are standing by...{self.colors.RESET}")
        
    async def handle_command(self, command: str):
        """Handle CLI commands"""
        cmd = command.lower().strip()
        
        if cmd == '/help':
            self.print_help()
        elif cmd == '/config':
            CLICommands.show_config()
        elif cmd == '/history':
            self.show_history()
        elif cmd == '/stats':
            self.show_session_stats()
        elif cmd == '/clear':
            clear_screen()
            print(f"{self.colors.GREEN}✨ Screen cleared!{self.colors.RESET}")
        elif cmd == '/quit' or cmd == '/exit':
            self.show_session_summary()
            print(f"\n{self.colors.GREEN}👋 Thank you for using Deep Research MCP!{self.colors.RESET}")
            print(f"{self.colors.CYAN}Session ended gracefully.{self.colors.RESET}")
            sys.exit(0)
        else:
            print(f"{self.colors.RED}❌ Unknown command: {command}{self.colors.RESET}")
            print(f"{self.colors.CYAN}Type /help for available commands{self.colors.RESET}")
    
    def print_help(self):
        """Print detailed help information"""
        print(f"\n{self.colors.BLUE}═══ HELP ═══{self.colors.RESET}")
        print(f"\n{self.colors.YELLOW}Commands:{self.colors.RESET}")
        print(f"  {self.colors.CYAN}/help{self.colors.RESET}     - Show this help message")
        print(f"  {self.colors.CYAN}/config{self.colors.RESET}   - Show current task configuration")
        print(f"  {self.colors.CYAN}/history{self.colors.RESET}  - Show research session history")
        print(f"  {self.colors.CYAN}/clear{self.colors.RESET}    - Clear the screen")
        print(f"  {self.colors.CYAN}/quit{self.colors.RESET}     - Exit the CLI")
        
        print(f"\n{self.colors.YELLOW}Research Usage:{self.colors.RESET}")
        print(f"  • Type any question or topic to start research")
        print(f"  • The system will automatically orchestrate 8 AI agents")
        print(f"  • Agents work in sequence: Browse → Plan → Research → Write → Publish")
        print(f"  • Progress will be displayed in real-time")
        
        print(f"\n{self.colors.YELLOW}Research Agents:{self.colors.RESET}")
        print(f"  • {self.colors.GREEN}Browser{self.colors.RESET}: Initial web research")
        print(f"  • {self.colors.GREEN}Editor{self.colors.RESET}: Plan research structure")
        print(f"  • {self.colors.GREEN}Researcher{self.colors.RESET}: Detailed investigation")
        print(f"  • {self.colors.GREEN}Writer{self.colors.RESET}: Compile final report")
        print(f"  • {self.colors.GREEN}Publisher{self.colors.RESET}: Format and output results")
        
    def show_history(self):
        """Show enhanced session history"""
        if not self.session_history:
            print_box("No research history in this session yet", self.colors, "HISTORY")
            print(f"{self.colors.CYAN}  Start researching to build your session history!{self.colors.RESET}")
            return
            
        print(f"\n{self.colors.BLUE}{'═' * 60}{self.colors.RESET}")
        print_box(f"Session History ({len(self.session_history)} entries)", self.colors, "HISTORY")
        
        for i, entry in enumerate(self.session_history, 1):
            timestamp = entry['timestamp']
            query = entry['query'][:60] + "..." if len(entry['query']) > 60 else entry['query']
            status = entry['status']
            duration = entry.get('duration', 'Unknown')
            
            # Status formatting
            status_icons = {
                'completed': f"{self.colors.GREEN}✓{self.colors.RESET}",
                'in_progress': f"{self.colors.YELLOW}⏳{self.colors.RESET}",
                'failed': f"{self.colors.RED}✗{self.colors.RESET}"
            }
            status_icon = status_icons.get(status, f"{self.colors.GRAY}•{self.colors.RESET}")
            
            print(f"\n{self.colors.CYAN}{i:2d}.{self.colors.RESET} {status_icon} {self.colors.GRAY}[{timestamp}]{self.colors.RESET}")
            print(f"     Query: {query}")
            if duration != 'Unknown':
                print(f"     Duration: {self.colors.CYAN}{duration}{self.colors.RESET}")
            if 'error' in entry:
                print(f"     {self.colors.RED}Error: {entry['error']}{self.colors.RESET}")
        
        print(f"\n{self.colors.BLUE}{'─' * 60}{self.colors.RESET}")

    def show_session_stats(self):
        """Show session statistics"""
        current_time = datetime.now()
        session_duration = current_time - self.session_start_time
        duration_str = format_duration(session_duration.total_seconds())
        
        success_rate = (self.successful_research_count / self.total_research_count * 100) if self.total_research_count > 0 else 0
        
        print(f"\n{self.colors.BLUE}{'═' * 50}{self.colors.RESET}")
        print_box("Session Statistics", self.colors, "STATS")
        
        stats = [
            f"Session ID: {self.colors.CYAN}{self.session_id}{self.colors.RESET}",
            f"Duration: {self.colors.CYAN}{duration_str}{self.colors.RESET}",
            f"Total Research Queries: {self.colors.CYAN}{self.total_research_count}{self.colors.RESET}",
            f"Successful Completions: {self.colors.GREEN}{self.successful_research_count}{self.colors.RESET}",
            f"Success Rate: {self.colors.GREEN if success_rate > 80 else self.colors.YELLOW if success_rate > 50 else self.colors.RED}{success_rate:.1f}%{self.colors.RESET}"
        ]
        
        for stat in stats:
            print(f"  {stat}")
        
        # Recent activity
        if self.session_history:
            recent_queries = self.session_history[-3:]
            print(f"\n{self.colors.YELLOW}Recent Activity:{self.colors.RESET}")
            for entry in recent_queries:
                status_icon = "✓" if entry['status'] == 'completed' else "✗" if entry['status'] == 'failed' else "⏳"
                query_preview = entry['query'][:40] + "..." if len(entry['query']) > 40 else entry['query']
                print(f"  {status_icon} {query_preview}")
        
        print(f"\n{self.colors.BLUE}{'─' * 50}{self.colors.RESET}")

    def show_session_summary(self):
        """Show session summary on exit"""
        current_time = datetime.now()
        session_duration = current_time - self.session_start_time
        duration_str = format_duration(session_duration.total_seconds())
        
        print(f"\n{self.colors.BLUE}{'═' * 60}{self.colors.RESET}")
        print_box("Session Summary", self.colors, "SESSION END")
        
        summary = [
            f"Session Duration: {self.colors.CYAN}{duration_str}{self.colors.RESET}",
            f"Research Queries: {self.colors.CYAN}{self.total_research_count}{self.colors.RESET}",
            f"Successful Completions: {self.colors.GREEN}{self.successful_research_count}{self.colors.RESET}"
        ]
        
        for item in summary:
            print(f"  {item}")
        
        if self.session_history and self.save_files:
            print(f"\n{self.colors.YELLOW}Your research outputs are saved in:{self.colors.RESET}")
            print(f"  {self.colors.CYAN}./outputs/{self.colors.RESET}")
        
        print(f"\n{self.colors.BLUE}{'─' * 60}{self.colors.RESET}")
    
    async def handle_research_query(self, query: str):
        """Handle research queries with enhanced tracking"""
        # Increment counters
        self.total_research_count += 1
        
        # Enhanced research header
        print(f"\n{self.colors.BLUE}{'═' * 70}{self.colors.RESET}")
        print_box(f"Research Query #{self.total_research_count}", self.colors, "RESEARCH SESSION")
        
        # Query information
        query_info = [
            f"Query: {self.colors.CYAN}{query}{self.colors.RESET}",
            f"Session: {self.colors.GRAY}{self.session_id}{self.colors.RESET}",
            f"Save Files: {self.colors.GREEN if self.save_files else self.colors.RED}{'Enabled' if self.save_files else 'Disabled'}{self.colors.RESET}",
            f"Verbose: {self.colors.GREEN if self.verbose else self.colors.GRAY}{'Enabled' if self.verbose else 'Disabled'}{self.colors.RESET}"
        ]
        
        for info in query_info:
            print(f"  {info}")
        
        print(f"{self.colors.BLUE}{'─' * 70}{self.colors.RESET}")
        print(f"{self.colors.CYAN}🚀 Assembling multi-agent research team...{self.colors.RESET}")
        
        # Add to history with more details
        start_time = datetime.now()
        research_entry = {
            'timestamp': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'query': query,
            'status': 'in_progress',
            'start_time': start_time
        }
        self.session_history.append(research_entry)
        
        # Progress tracking
        progress_tracker = ProgressTracker(self.colors)
        current_agent = None
        
        try:
            # Enhanced stream output handler
            async def interactive_stream_output(type_: str, key: str, value: Any, websocket=None):
                nonlocal current_agent
                
                if type_ == "logs":
                    if self.verbose:
                        print(f"{self.colors.GRAY}  [LOG] {key}: {value}{self.colors.RESET}")
                elif type_ == "progress":
                    if isinstance(value, (int, float)):
                        if current_agent:
                            progress_tracker.update_progress(current_agent, value)
                            bar = create_progress_bar(value, width=25, colors=self.colors)
                            print(f"\r{self.colors.CYAN}  {current_agent}: {bar}{self.colors.RESET}", end='', flush=True)
                        else:
                            bar = create_progress_bar(value, width=25, colors=self.colors)
                            print(f"\r{self.colors.CYAN}  Overall: {bar}{self.colors.RESET}", end='', flush=True)
                    else:
                        print(f"\n{self.colors.CYAN}  Status: {value}{self.colors.RESET}")
                elif type_ == "agent_start":
                    agent_name = key.replace('_', ' ').title()
                    current_agent = agent_name
                    progress_tracker.start_agent(agent_name, str(value))
                    print(f"\n{self.colors.GREEN}🤖 [{agent_name}] Starting: {value}{self.colors.RESET}")
                elif type_ == "agent_output":
                    agent_name = key.replace('_', ' ').title()
                    if current_agent:
                        progress_tracker.complete_agent(current_agent)
                    print(f"\n{self.colors.GREEN}✓ [{agent_name}] Completed{self.colors.RESET}")
                    if self.verbose and value:
                        preview = str(value)[:150] + "..." if len(str(value)) > 150 else str(value)
                        print(f"{self.colors.GRAY}  Result: {preview}{self.colors.RESET}")
            
            # Run research task
            result = await run_research_task(
                query=query,
                websocket=None,
                stream_output=interactive_stream_output,
                tone=Tone.Objective,
                write_to_files=self.save_files
            )
            
            # Calculate duration
            end_time = datetime.now()
            duration = end_time - start_time
            duration_str = format_duration(duration.total_seconds())
            
            # Update history and counters
            research_entry['status'] = 'completed'
            research_entry['duration'] = duration_str
            research_entry['result'] = result
            research_entry['end_time'] = end_time
            self.successful_research_count += 1
            
            # Display results
            self.display_research_results(query, result, duration_str, progress_tracker)
            
        except Exception as e:
            # Calculate duration for failed research
            end_time = datetime.now()
            duration = end_time - start_time
            duration_str = format_duration(duration.total_seconds())
            
            # Update history
            research_entry['status'] = 'failed'
            research_entry['duration'] = duration_str
            research_entry['error'] = str(e)
            research_entry['end_time'] = end_time
            
            # Display error
            print(f"\n\n{self.colors.RED}{'═' * 60}{self.colors.RESET}")
            print_box(f"Research Failed After {duration_str}", self.colors, "ERROR")
            print(f"  {self.colors.RED}Error: {str(e)}{self.colors.RESET}")
            
            if progress_tracker.agents:
                print(f"\n{self.colors.YELLOW}Agent Status at Failure:{self.colors.RESET}")
                print(progress_tracker.display_summary())
    
    def display_research_results(self, query: str, result: Dict[str, Any], duration: str, progress_tracker: ProgressTracker):
        """Display enhanced research results"""
        print(f"\n\n{self.colors.GREEN}{'═' * 70}{self.colors.RESET}")
        print_box("Research Completed Successfully! 🎉", self.colors, "SUCCESS")
        
        # Result summary
        summary_info = [
            f"Query: {self.colors.CYAN}{query[:50]}{'...' if len(query) > 50 else ''}{self.colors.RESET}",
            f"Duration: {self.colors.CYAN}{duration}{self.colors.RESET}",
            f"Agents Used: {self.colors.CYAN}{len(progress_tracker.agents)}{self.colors.RESET}",
            f"Status: {self.colors.GREEN}✓ Complete{self.colors.RESET}"
        ]
        
        if self.save_files:
            summary_info.extend([
                f"Output Location: {self.colors.CYAN}./outputs/{self.colors.RESET}",
                f"Formats: {self.colors.GRAY}PDF • DOCX • Markdown{self.colors.RESET}"
            ])
        
        for info in summary_info:
            print(f"  {info}")
        
        # Agent summary
        if progress_tracker.agents:
            print(f"\n{self.colors.YELLOW}Agent Workflow Summary:{self.colors.RESET}")
            print(progress_tracker.display_summary())
        
        # Result preview
        print(f"\n{self.colors.BLUE}{'─' * 70}{self.colors.RESET}")
        
        if isinstance(result, dict):
            # Extract content preview
            content = None
            if 'content' in result:
                content = result['content']
            elif 'report' in result:
                content = result['report']
            elif 'final_report' in result:
                content = result['final_report']
            
            if content:
                print(f"{self.colors.GREEN}📄 Research Report Preview:{self.colors.RESET}")
                # Show first few lines of the report
                lines = str(content).split('\n')
                preview_lines = lines[:10] if len(lines) > 10 else lines
                
                print(f"{self.colors.GRAY}{'─' * 60}{self.colors.RESET}")
                for line in preview_lines:
                    print(line)
                
                if len(lines) > 10:
                    remaining = len(lines) - 10
                    print(f"{self.colors.GRAY}... ({remaining} more lines in full report){self.colors.RESET}")
                
                print(f"{self.colors.GRAY}{'─' * 60}{self.colors.RESET}")
            else:
                # Fallback to JSON display
                print(f"{self.colors.GREEN}📊 Research Results:{self.colors.RESET}")
                print(f"{self.colors.GRAY}{'─' * 60}{self.colors.RESET}")
                print(json.dumps(result, indent=2, ensure_ascii=False)[:500] + "..." if len(str(result)) > 500 else json.dumps(result, indent=2, ensure_ascii=False))
                print(f"{self.colors.GRAY}{'─' * 60}{self.colors.RESET}")
        else:
            # Display as string with preview
            content_str = str(result)
            print(f"{self.colors.GREEN}📄 Research Results:{self.colors.RESET}")
            print(f"{self.colors.GRAY}{'─' * 60}{self.colors.RESET}")
            if len(content_str) > 1000:
                print(content_str[:1000] + f"\n{self.colors.GRAY}... (truncated, see full report in saved files){self.colors.RESET}")
            else:
                print(content_str)
            print(f"{self.colors.GRAY}{'─' * 60}{self.colors.RESET}")
        
        print(f"\n{self.colors.GREEN}✨ Ready for your next research query!{self.colors.RESET}")
        print(f"{self.colors.BLUE}{'═' * 70}{self.colors.RESET}")