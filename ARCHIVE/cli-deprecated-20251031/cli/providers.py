"""
Provider Management CLI Commands
Manage LLM and search providers configuration
"""

import os
from typing import Dict, Any
from multi_agents.providers.factory import config_manager, enhanced_config


class ProviderCLI:
    """CLI commands for provider management"""
    
    @staticmethod
    def show_provider_status():
        """Show current provider configuration and status"""
        from .utils import CLIColors
        colors = CLIColors()
        
        print(f"\n{colors.BLUE}═══ PROVIDER STATUS ═══{colors.RESET}")
        
        # Get provider information
        provider_info = config_manager.get_provider_info()
        validation = enhanced_config.validate_current_config()
        
        # Primary providers
        print(f"\n{colors.YELLOW}Primary Providers:{colors.RESET}")
        llm_info = provider_info["primary_llm"]
        search_info = provider_info["primary_search"]
        
        # LLM status
        llm_status = colors.GREEN + "✓" if llm_info["has_api_key"] else colors.RED + "✗"
        print(f"  LLM: {llm_status}{colors.RESET} {llm_info['provider']}:{llm_info['model']}")
        
        # Search status
        search_status = colors.GREEN + "✓" if search_info["has_api_key"] else colors.RED + "✗"
        print(f"  Search: {search_status}{colors.RESET} {search_info['provider']} (max: {search_info['max_results']})")
        
        # Fallback providers
        if provider_info.get("fallback_llm"):
            print(f"\n{colors.YELLOW}Fallback Providers:{colors.RESET}")
            fallback_llm = provider_info["fallback_llm"]
            fallback_search = provider_info.get("fallback_search")
            
            llm_status = colors.GREEN + "✓" if fallback_llm["has_api_key"] else colors.RED + "✗"
            print(f"  LLM: {llm_status}{colors.RESET} {fallback_llm['provider']}:{fallback_llm['model']}")
            
            if fallback_search:
                search_status = colors.GREEN + "✓" if fallback_search["has_api_key"] else colors.RED + "✗"
                print(f"  Search: {search_status}{colors.RESET} {fallback_search['provider']}")
        
        # Strategies
        strategies = provider_info["strategies"]
        print(f"\n{colors.YELLOW}Strategies:{colors.RESET}")
        print(f"  LLM: {strategies['llm']}")
        print(f"  Search: {strategies['search']}")
        
        # Validation status
        print(f"\n{colors.YELLOW}Configuration Status:{colors.RESET}")
        if validation["valid"]:
            print(f"  {colors.GREEN}✓ Valid configuration{colors.RESET}")
        else:
            print(f"  {colors.RED}✗ Configuration issues:{colors.RESET}")
            for issue in validation["issues"]:
                print(f"    - {colors.RED}{issue}{colors.RESET}")
    
    @staticmethod
    def list_available_providers():
        """List all available providers"""
        from .utils import CLIColors
        colors = CLIColors()
        
        print(f"\n{colors.BLUE}═══ AVAILABLE PROVIDERS ═══{colors.RESET}")
        
        print(f"\n{colors.YELLOW}LLM Providers:{colors.RESET}")
        llm_providers = [
            ("openai", "OpenAI GPT models", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]),
            ("google_gemini", "Google Gemini models", ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]),
            ("anthropic", "Anthropic Claude models", ["claude-3-sonnet", "claude-3-haiku"]),
            ("azure_openai", "Azure OpenAI", ["gpt-4", "gpt-35-turbo"])
        ]
        
        for provider, description, models in llm_providers:
            env_key = {
                "openai": "OPENAI_API_KEY",
                "google_gemini": "GOOGLE_API_KEY", 
                "anthropic": "ANTHROPIC_API_KEY",
                "azure_openai": "AZURE_OPENAI_API_KEY"
            }.get(provider)
            
            has_key = bool(os.getenv(env_key))
            status = colors.GREEN + "✓" if has_key else colors.GRAY + "○"
            
            print(f"  {status}{colors.RESET} {colors.CYAN}{provider}{colors.RESET}")
            print(f"    {description}")
            print(f"    Models: {', '.join(models)}")
            print(f"    Env: {env_key}")
            print()
        
        print(f"{colors.YELLOW}Search Providers:{colors.RESET}")
        search_providers = [
            ("tavily", "Tavily Search API", "TAVILY_API_KEY", "Advanced AI search"),
            ("brave", "Brave Search API", "BRAVE_API_KEY", "Independent search engine"),
            ("google", "Google Custom Search", "GOOGLE_API_KEY", "Google search results"),
            ("serpapi", "SerpAPI", "SERPAPI_API_KEY", "Google search scraping"),
            ("duckduckgo", "DuckDuckGo", None, "Privacy-focused search (no API key)")
        ]
        
        for provider, description, env_key, details in search_providers:
            if env_key:
                has_key = bool(os.getenv(env_key))
                status = colors.GREEN + "✓" if has_key else colors.GRAY + "○"
            else:
                status = colors.GREEN + "✓"
            
            print(f"  {status}{colors.RESET} {colors.CYAN}{provider}{colors.RESET}")
            print(f"    {description}")
            print(f"    {details}")
            if env_key:
                print(f"    Env: {env_key}")
            print()
    
    @staticmethod
    def test_providers():
        """Test connectivity to configured providers"""
        from .utils import CLIColors
        colors = CLIColors()
        
        print(f"\n{colors.BLUE}═══ TESTING PROVIDERS ═══{colors.RESET}")
        
        # Test current configuration
        validation = enhanced_config.validate_current_config()
        
        if not validation["valid"]:
            print(f"{colors.RED}Configuration is invalid. Fix issues first:{colors.RESET}")
            for issue in validation["issues"]:
                print(f"  - {colors.RED}{issue}{colors.RESET}")
            return
        
        print(f"{colors.CYAN}Testing provider connectivity...{colors.RESET}")
        
        # This would require implementing test methods in the provider classes
        # For now, just show configuration validation
        current_providers = enhanced_config.get_current_providers()
        
        print(f"\n{colors.YELLOW}Current Configuration:{colors.RESET}")
        print(f"  LLM: {current_providers['llm_provider']}:{current_providers['llm_model']}")
        print(f"  Search: {current_providers['search_provider']}")
        
        print(f"\n{colors.GREEN}Configuration appears valid.{colors.RESET}")
        print(f"{colors.GRAY}Note: Run a research task to fully test provider connectivity.{colors.RESET}")
    
    @staticmethod
    def switch_provider(provider_type: str, provider_name: str, fallback: bool = False):
        """Switch to a different provider"""
        from .utils import CLIColors
        colors = CLIColors()
        
        print(f"\n{colors.BLUE}═══ SWITCHING PROVIDER ═══{colors.RESET}")
        
        if provider_type not in ["llm", "search"]:
            print(f"{colors.RED}Invalid provider type. Use 'llm' or 'search'.{colors.RESET}")
            return
        
        try:
            if provider_type == "llm":
                enhanced_config.switch_llm_provider(use_fallback=fallback)
            else:
                enhanced_config.switch_search_provider(use_fallback=fallback)
            
            current_providers = enhanced_config.get_current_providers()
            print(f"{colors.GREEN}Successfully switched providers:{colors.RESET}")
            print(f"  LLM: {current_providers['llm_provider']}:{current_providers['llm_model']}")
            print(f"  Search: {current_providers['search_provider']}")
            
        except Exception as e:
            print(f"{colors.RED}Error switching provider: {e}{colors.RESET}")
    
    @staticmethod
    def show_usage_stats():
        """Show provider usage statistics"""
        from .utils import CLIColors
        from multi_agents.providers.factory import provider_manager
        colors = CLIColors()
        
        print(f"\n{colors.BLUE}═══ USAGE STATISTICS ═══{colors.RESET}")
        
        try:
            stats = provider_manager.get_usage_stats()
            
            if stats["llm"]:
                print(f"\n{colors.YELLOW}LLM Usage:{colors.RESET}")
                for provider, data in stats["llm"].items():
                    print(f"  {colors.CYAN}{provider}{colors.RESET}")
                    print(f"    Requests: {data['requests']}")
                    print(f"    Tokens: {data['tokens']:,}")
                    print(f"    Cost: ${data['cost']:.4f}")
                    print(f"    Errors: {data['errors']}")
            
            if stats["search"]:
                print(f"\n{colors.YELLOW}Search Usage:{colors.RESET}")
                for provider, data in stats["search"].items():
                    print(f"  {colors.CYAN}{provider}{colors.RESET}")
                    print(f"    Requests: {data['requests']}")
                    print(f"    Results: {data['results']}")
                    print(f"    Errors: {data['errors']}")
            
            if not stats["llm"] and not stats["search"]:
                print(f"{colors.GRAY}No usage statistics available yet.{colors.RESET}")
                print(f"{colors.GRAY}Run some research tasks to see statistics.{colors.RESET}")
        
        except Exception as e:
            print(f"{colors.RED}Error retrieving usage stats: {e}{colors.RESET}")
    
    @staticmethod
    def show_configuration_examples():
        """Show configuration examples"""
        from .utils import CLIColors
        colors = CLIColors()
        
        print(f"\n{colors.BLUE}═══ CONFIGURATION EXAMPLES ═══{colors.RESET}")
        
        examples = [
            {
                "name": "OpenAI + Tavily (Default)",
                "description": "Standard configuration with OpenAI and Tavily",
                "config": {
                    "PRIMARY_LLM_PROVIDER": "openai",
                    "PRIMARY_LLM_MODEL": "gpt-4o",
                    "PRIMARY_SEARCH_PROVIDER": "tavily",
                    "OPENAI_API_KEY": "sk-...",
                    "TAVILY_API_KEY": "tvly-..."
                }
            },
            {
                "name": "Google Gemini + Brave",
                "description": "Google Gemini with Brave Search",
                "config": {
                    "PRIMARY_LLM_PROVIDER": "google_gemini",
                    "PRIMARY_LLM_MODEL": "gemini-1.5-pro",
                    "PRIMARY_SEARCH_PROVIDER": "brave",
                    "GOOGLE_API_KEY": "...",
                    "BRAVE_API_KEY": "..."
                }
            },
            {
                "name": "Mixed with Fallbacks",
                "description": "Primary providers with fallback alternatives",
                "config": {
                    "PRIMARY_LLM_PROVIDER": "openai",
                    "FALLBACK_LLM_PROVIDER": "google_gemini",
                    "PRIMARY_SEARCH_PROVIDER": "tavily",
                    "FALLBACK_SEARCH_PROVIDER": "brave",
                    "LLM_STRATEGY": "fallback_on_error",
                    "SEARCH_STRATEGY": "fallback_on_error"
                }
            }
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"\n{colors.YELLOW}{i}. {example['name']}{colors.RESET}")
            print(f"   {example['description']}")
            print(f"   {colors.GRAY}Configuration:{colors.RESET}")
            for key, value in example['config'].items():
                print(f"     {key}={value}")
        
        print(f"\n{colors.CYAN}To apply a configuration:{colors.RESET}")
        print(f"1. Edit your .env file with the desired settings")
        print(f"2. Restart the application")
        print(f"3. Run 'python main.py --config' to verify")


def add_provider_commands(parser):
    """Add provider management commands to CLI parser"""
    provider_parser = parser.add_parser('providers', help='Manage LLM and search providers')
    provider_subparsers = provider_parser.add_subparsers(dest='provider_command', help='Provider commands')
    
    # Status command
    status_parser = provider_subparsers.add_parser('status', help='Show provider status')
    status_parser.set_defaults(func=lambda args: ProviderCLI.show_provider_status())
    
    # List command
    list_parser = provider_subparsers.add_parser('list', help='List available providers')
    list_parser.set_defaults(func=lambda args: ProviderCLI.list_available_providers())
    
    # Test command
    test_parser = provider_subparsers.add_parser('test', help='Test provider connectivity')
    test_parser.set_defaults(func=lambda args: ProviderCLI.test_providers())
    
    # Switch command
    switch_parser = provider_subparsers.add_parser('switch', help='Switch providers')
    switch_parser.add_argument('type', choices=['llm', 'search'], help='Provider type')
    switch_parser.add_argument('--fallback', action='store_true', help='Switch to fallback provider')
    switch_parser.set_defaults(func=lambda args: ProviderCLI.switch_provider(args.type, "", args.fallback))
    
    # Stats command
    stats_parser = provider_subparsers.add_parser('stats', help='Show usage statistics')
    stats_parser.set_defaults(func=lambda args: ProviderCLI.show_usage_stats())
    
    # Examples command
    examples_parser = provider_subparsers.add_parser('examples', help='Show configuration examples')
    examples_parser.set_defaults(func=lambda args: ProviderCLI.show_configuration_examples())
    
    return provider_parser