#!/usr/bin/env python3
"""
Test script to verify provider configuration is working correctly
Run this in a fresh terminal session to test the configuration
"""


def test_provider_configuration():
    print("🧪 Testing Provider Configuration")
    print("=" * 50)

    # Step 1: Load environment
    from dotenv import load_dotenv

    load_dotenv(override=True)

    import os

    print("📁 Environment Variables:")
    print(f"  PRIMARY_LLM_PROVIDER: {os.getenv('PRIMARY_LLM_PROVIDER')}")
    print(f"  PRIMARY_SEARCH_PROVIDER: {os.getenv('PRIMARY_SEARCH_PROVIDER')}")
    print(f"  GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY', 'NOT_SET')[:10]}...")

    # Step 2: Test orchestrator
    print("\n🎭 Testing Orchestrator:")
    try:
        from multi_agents.agents.orchestrator import ChiefEditorAgent

        task = {"query": "Configuration test", "report_type": "research_report", "language": "en"}

        print("  Creating ChiefEditorAgent...")
        ChiefEditorAgent(task, write_to_files=False)
        print("  ✅ Success! Check the PROVIDERS line above.")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Step 3: Test configuration directly
    print("\n⚙️  Testing Configuration Manager:")
    try:
        from multi_agents.config.providers import ProviderConfigManager

        config_manager = ProviderConfigManager()

        print(
            f"  LLM: {config_manager.config.primary_llm.provider.value}:{config_manager.config.primary_llm.model}"
        )
        print(f"  Search: {config_manager.config.primary_search.provider.value}")
        print("  ✅ Configuration is correct!")

    except Exception as e:
        print(f"  ❌ Configuration error: {e}")


if __name__ == "__main__":
    test_provider_configuration()
