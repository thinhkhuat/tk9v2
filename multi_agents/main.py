from dotenv import load_dotenv
import sys
import os
import uuid
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Suppress ALTS credentials warnings from Google libraries (must be done early)
from multi_agents.suppress_alts_warnings import suppress_alts_warnings
suppress_alts_warnings()

# Suppress the non-critical MCPRetriever import warning from gpt_researcher
logging.getLogger('gpt_researcher.retrievers.mcp').setLevel(logging.ERROR)

# Load environment first
load_dotenv(override=True)

# Configuration validation before system startup
try:
    from multi_agents.config.validation import validate_startup_configuration
    
    # Run comprehensive configuration validation
    config_valid = validate_startup_configuration(verbose=False)  # Set to True for detailed output during debugging
    
    if not config_valid:
        print("⚠️  Configuration issues detected. Run with --config to see details.")
        print("   The system will attempt to continue but may encounter errors.")
        print("   Please check your .env file and API key configuration.\n")
        
except Exception as e:
    print(f"⚠️  Configuration validation failed: {str(e)}")
    print("   The system will continue without validation.\n")

# Early BRAVE integration setup before any GPT-researcher imports
if os.getenv('PRIMARY_SEARCH_PROVIDER') == 'brave':
    try:
        from simple_brave_retriever import setup_simple_brave_retriever
        setup_simple_brave_retriever()
        print("🔧 Early BRAVE integration setup completed")
    except ImportError:
        # Handle different import contexts
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        from simple_brave_retriever import setup_simple_brave_retriever
        setup_simple_brave_retriever()
        print("🔧 Early BRAVE integration setup completed (fallback path)")

# Ensure Retry is available globally to prevent NameError
try:
    from requests.packages.urllib3.util.retry import Retry
except ImportError:
    from urllib3.util.retry import Retry

# Make Retry available in builtins to prevent NameError
import builtins
if not hasattr(builtins, 'Retry'):
    builtins.Retry = Retry

# Apply network reliability patches before any GPT-researcher imports
try:
    from direct_timeout_patch import apply_direct_timeout_patches
    from network_reliability_patch import setup_global_session_defaults

    # Apply direct patches to gpt-researcher source files (one-time fix)
    direct_patch_success = apply_direct_timeout_patches()

    # Setup global session defaults for additional reliability
    setup_global_session_defaults()
    
    if direct_patch_success:
        print("🚀 Network reliability patches applied successfully")
        print("   • Timeout increased from 4s to 30s")
        print("   • Retry logic with exponential backoff")
        print("   • Enhanced connection handling")
    else:
        print("⚠️  Some network reliability patches had issues - check logs")
        
except ImportError:
    # Handle different import contexts
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from direct_timeout_patch import apply_direct_timeout_patches
    from network_reliability_patch import setup_global_session_defaults
    
    direct_patch_success = apply_direct_timeout_patches()
    setup_global_session_defaults()
    
    if direct_patch_success:
        print("🚀 Network reliability patches applied successfully (fallback path)")
    else:
        print("⚠️  Network reliability patch had issues - check logs for details")
        
except Exception as e:
    print(f"❌ Failed to apply network reliability patch: {e}")
    print("   Research may experience network timeout issues")
    print("   Run 'python direct_timeout_patch.py' manually to apply fixes")

# Apply text processing fixes to prevent chunking errors
try:
    from text_processing_fix import apply_text_processing_fixes
    
    # Apply patches to prevent "Separator is not found, and chunk exceed the limit" errors
    text_processing_success = apply_text_processing_fixes()
    
    if text_processing_success:
        print("🛡️  Text processing fixes applied successfully")
        print("   • Conservative chunk sizes (800 chars)")
        print("   • Defensive text validation and cleaning")
        print("   • Fallback splitting methods")
        print("   • Graceful degradation with automatic recovery")
    else:
        print("⚠️  Some text processing fixes had issues - check logs")
        
except ImportError:
    # Handle different import contexts
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from text_processing_fix import apply_text_processing_fixes
    
    text_processing_success = apply_text_processing_fixes()
    
    if text_processing_success:
        print("🛡️  Text processing fixes applied successfully (fallback path)")
    else:
        print("⚠️  Text processing fix had issues - check logs for details")
        
except Exception as e:
    print(f"❌ Failed to apply text processing fixes: {e}")
    print("   Research may experience chunking errors")
    print("   This is a critical fix for the 'Separator is not found' error")

from multi_agents.agents import ChiefEditorAgent
import asyncio
import json
from gpt_researcher.utils.enum import Tone

# Run with LangSmith if API key is set
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

def open_task():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to task.json
    task_json_path = os.path.join(current_dir, 'task.json')
    
    with open(task_json_path, 'r') as f:
        task = json.load(f)

    if not task:
        raise Exception("No task found. Please ensure a valid task.json file is present in the multi_agents directory and contains the necessary task information.")

    return task

async def run_research_task(query, websocket=None, stream_output=None, tone=Tone.Objective, headers=None, write_to_files=True, language=None):
    task = open_task()
    task["query"] = query
    
    # Apply language configuration if provided
    if language:
        task["language"] = language

    chief_editor = ChiefEditorAgent(task, websocket, stream_output, tone, headers, write_to_files)
    research_report = await chief_editor.run_research_task()

    if websocket and stream_output:
        await stream_output("logs", "research_report", research_report, websocket)

    return research_report

def handle_config_validation():
    """Handle configuration validation and diagnostics"""
    try:
        from multi_agents.config.validation import validate_startup_configuration, get_validation_summary
        
        print("🔍 Deep Research MCP - Configuration Validation")
        print("=" * 60)
        
        # Run comprehensive validation with verbose output
        is_valid = validate_startup_configuration(verbose=True)
        
        if not is_valid:
            print("\n🛠️  Configuration Fix Recommendations:")
            print("1. Copy .env.example to .env if not exists")
            print("2. Configure your API keys in the .env file")
            print("3. Set PRIMARY_LLM_PROVIDER and PRIMARY_SEARCH_PROVIDER")
            print("4. Ensure task.json has valid parameters")
            
        print("\n📊 Validation Summary:")
        summary = get_validation_summary()
        print(f"   Valid: {'✅ Yes' if summary['valid'] else '❌ No'}")
        print(f"   Errors: {summary['error_count']}")
        print(f"   Warnings: {summary['warning_count']}")
        print(f"   Info: {summary['info_count']}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {str(e)}")
        return False

def handle_provider_info():
    """Display provider information and status"""
    try:
        from multi_agents.config.providers import config_manager
        
        print("🔧 Provider Configuration Status")
        print("=" * 40)
        
        provider_info = config_manager.get_provider_info()
        
        # Primary LLM
        llm = provider_info["primary_llm"]
        print(f"LLM Provider:     {llm['provider']} ({llm['model']})")
        print(f"LLM API Key:      {'✅ Configured' if llm['has_api_key'] else '❌ Missing'}")
        
        # Primary Search
        search = provider_info["primary_search"]
        print(f"Search Provider:  {search['provider']}")
        print(f"Search API Key:   {'✅ Configured' if search['has_api_key'] else '❌ Missing'}")
        print(f"Max Results:      {search['max_results']}")
        
        # Strategies
        strategies = provider_info["strategies"]
        print(f"LLM Strategy:     {strategies['llm']}")
        print(f"Search Strategy:  {strategies['search']}")
        
        # Fallbacks
        if provider_info.get("fallback_llm"):
            fb_llm = provider_info["fallback_llm"]
            print(f"Fallback LLM:     {fb_llm['provider']} ({'✅' if fb_llm['has_api_key'] else '❌'})")
        
        if provider_info.get("fallback_search"):
            fb_search = provider_info["fallback_search"]
            print(f"Fallback Search:  {fb_search['provider']} ({'✅' if fb_search['has_api_key'] else '❌'})")
        
        # Validation status
        issues = config_manager.validate_configuration()
        print(f"\nValidation:       {'✅ Valid' if not issues else f'❌ {len(issues)} issues'}")
        
        if issues:
            print("\nIssues:")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"  • {issue}")
            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more issues")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Failed to get provider info: {str(e)}")
        return False

async def main():
    """Main entry point with CLI argument handling"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deep Research MCP - Multi-Agent Research System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Run research with default task.json
  python main.py --config                  # Validate configuration
  python main.py --provider-info           # Show provider status
  python main.py --research "AI trends"    # Run specific research query
        """
    )
    
    parser.add_argument('--config', action='store_true', 
                       help='Validate configuration and show detailed status')
    parser.add_argument('--provider-info', action='store_true',
                       help='Show current provider configuration and status')
    parser.add_argument('--research', type=str,
                       help='Run research on a specific query')
    parser.add_argument('--language', type=str, default=None,
                       help='Target language for research output')
    parser.add_argument('--tone', type=str, default='objective',
                       choices=['objective', 'critical', 'optimistic', 'balanced', 'skeptical'],
                       help='Research tone')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Handle configuration validation
    if args.config:
        is_valid = handle_config_validation()
        exit(0 if is_valid else 1)
    
    # Handle provider information
    if args.provider_info:
        is_valid = handle_provider_info()
        exit(0 if is_valid else 1)
    
    # Convert tone string to enum
    from gpt_researcher.utils.enum import Tone
    tone_enum = getattr(Tone, args.tone.capitalize(), Tone.Objective)
    
    # Run research task
    if args.research:
        # Custom research query
        research_report = await run_research_task(
            query=args.research,
            tone=tone_enum,
            language=args.language,
            write_to_files=True
        )
    else:
        # Default task from task.json
        task = open_task()
        if args.language:
            task["language"] = args.language
            
        chief_editor = ChiefEditorAgent(task, write_to_files=True, tone=tone_enum)
        research_report = await chief_editor.run_research_task(task_id=uuid.uuid4())
    
    return research_report

if __name__ == "__main__":
    asyncio.run(main())