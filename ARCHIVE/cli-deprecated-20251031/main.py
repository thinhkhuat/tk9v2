import asyncio
import argparse
import sys
import logging

# Suppress the non-critical MCPRetriever import warning from gpt_researcher
logging.getLogger('gpt_researcher.retrievers.mcp').setLevel(logging.ERROR)

from cli.interactive import InteractiveCLI
from cli.commands import CLICommands


def main():
    parser = argparse.ArgumentParser(
        description="Deep Research MCP - Multi-Agent Research CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Start interactive mode
  python main.py --research "AI trends"  # Run single research query
  python main.py --config                # Show current configuration
        """
    )
    
    parser.add_argument(
        "--research", "-r",
        help="Run a single research query and exit"
    )
    
    parser.add_argument(
        "--tone", "-t",
        choices=["objective", "critical", "optimistic", "balanced", "skeptical"],
        default="objective",
        help="Research tone (default: objective)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive chat mode (default if no other args)"
    )
    
    parser.add_argument(
        "--config", "-c",
        action="store_true",
        help="Show current configuration"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--save-files", "-s",
        action="store_true",
        default=True,
        help="Save research reports to files (default: True)"
    )
    
    parser.add_argument(
        "--no-save-files",
        action="store_false",
        dest="save_files",
        help="Don't save research reports to files"
    )
    
    parser.add_argument(
        "--provider-info",
        action="store_true",
        help="Show provider configuration information"
    )
    
    parser.add_argument(
        "--language", "-l",
        choices=["en", "vi", "es", "fr", "de", "zh", "ja", "ko", "pt", "it", "ru", "ar", "hi", "th"],
        help="Research language for entire process (en=English, vi=Vietnamese, es=Spanish, etc.)"
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, start interactive mode
    if len(sys.argv) == 1:
        args.interactive = True
    
    # Apply language configuration if provided
    if args.language:
        import os
        os.environ['RESEARCH_LANGUAGE'] = args.language
    
    try:
        if args.config:
            CLICommands.show_config()
        elif args.provider_info:
            from cli.providers import ProviderCLI
            ProviderCLI.show_provider_status()
        elif args.research:
            asyncio.run(CLICommands.run_single_research(args.research, args.tone, args.verbose, args.save_files, args.language))
        elif args.interactive:
            cli = InteractiveCLI(verbose=args.verbose, save_files=args.save_files, language=args.language)
            asyncio.run(cli.start())
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
