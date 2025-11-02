import logging
import os
import platform
import sys
import time
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP

# Suppress the non-critical MCPRetriever import warning from gpt_researcher
logging.getLogger("gpt_researcher.retrievers.mcp").setLevel(logging.ERROR)

from gpt_researcher.utils.enum import Tone

from multi_agents.main import run_research_task

# Load environment variables
load_dotenv(override=True)

# Validate configuration at startup (non-blocking)
try:
    from multi_agents.config.validation import validate_startup_configuration

    # Run validation but don't block server startup
    config_valid = validate_startup_configuration(verbose=False)

    if not config_valid:
        print("⚠️  MCP Server: Configuration issues detected but server will start.")
        print("   Use the health_check tool to see detailed validation results.")

except Exception as e:
    print(f"⚠️  MCP Server: Configuration validation failed: {str(e)}")
    print("   Server will start but may encounter runtime errors.")

# Create an MCP server named "Deep Research"
mcp = FastMCP("Deep Research")


@mcp.tool()
async def deep_research(query: str, tone: str = "objective", ctx: Context = None) -> Dict[Any, Any]:
    """
    Perform deep research on a given query using multiple AI agents.

    Args:
        query: The research question or topic to investigate
        tone: Research tone (objective, critical, optimistic, balanced, skeptical)
        ctx: MCP context for progress reporting

    Returns:
        A dictionary containing the research results and analysis
    """
    try:
        # Convert tone string to enum
        tone_enum = getattr(Tone, tone.capitalize(), Tone.Objective)

        # Define a stream output handler that reports progress via MCP
        async def stream_output(type: str, key: str, value: Any, _):
            if ctx:
                if type == "logs":
                    ctx.info(f"stream_output logs:{key}: {value}")
                elif type == "progress":
                    await ctx.report_progress(value, 100)

        # Run the research task
        research_report = await run_research_task(
            query=query,
            websocket=None,  # We're not using websockets in MCP
            stream_output=stream_output,
            tone=tone_enum,
        )

        return {"status": "success", "query": query, "tone": tone, "report": research_report}

    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============================================================================
# Health Check and System Info Tools
# ============================================================================


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Perform a comprehensive health check of the system.

    Returns:
        A dictionary containing system health status and metrics
    """
    try:
        start_time = time.time()

        # Basic system info
        system_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "python_version": sys.version,
            "platform": platform.platform(),
            "uptime": time.time() - start_time,
        }

        # Run comprehensive configuration validation
        validation_status = {}
        try:
            from multi_agents.config.validation import get_validation_summary

            validation_status = get_validation_summary()
        except Exception as e:
            validation_status = {
                "valid": False,
                "error_count": 1,
                "warning_count": 0,
                "errors": [
                    {"component": "Validation", "message": f"Validation system failed: {str(e)}"}
                ],
                "configuration": {},
            }

        # Check environment variables
        required_env_vars = ["PRIMARY_LLM_PROVIDER", "PRIMARY_SEARCH_PROVIDER"]

        env_status = {}
        for var in required_env_vars:
            env_status[var] = "configured" if os.getenv(var) else "missing"

        # Check API keys (without exposing them)
        api_keys_status = {}
        api_key_vars = [
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY",
            "ANTHROPIC_API_KEY",
            "TAVILY_API_KEY",
            "BRAVE_API_KEY",
        ]

        for var in api_key_vars:
            value = os.getenv(var)
            if value and value != f"your_{var.lower()}_here":
                api_keys_status[var] = "configured"
            else:
                api_keys_status[var] = "not_configured"

        # Memory usage (basic)
        memory_info = {
            "available": True,  # Basic check
        }

        # Check disk space for outputs
        output_dir = "./outputs"
        disk_info = {
            "output_dir_exists": os.path.exists(output_dir),
            "output_dir_writable": (
                os.access(output_dir, os.W_OK) if os.path.exists(output_dir) else False
            ),
        }

        health_data = {
            "status": "healthy",
            "timestamp": system_info["timestamp"],
            "system": system_info,
            "environment": env_status,
            "api_keys": api_keys_status,
            "validation": validation_status,
            "memory": memory_info,
            "disk": disk_info,
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }

        # Determine overall health status based on validation results
        if not validation_status.get("valid", False):
            health_data["status"] = "degraded"
            health_data["warnings"] = [
                f"Configuration validation failed with {validation_status.get('error_count', 0)} errors"
            ]

            # Add specific configuration guidance
            if validation_status.get("error_count", 0) > 0:
                health_data["configuration_guidance"] = [
                    "1. Check .env file exists and has valid configuration",
                    "2. Ensure API keys are properly configured",
                    "3. Set PRIMARY_LLM_PROVIDER and PRIMARY_SEARCH_PROVIDER",
                    "4. Run CLI command: python main.py --config",
                ]

        # Legacy checks for backward compatibility
        missing_env = [k for k, v in env_status.items() if v == "missing"]
        if missing_env:
            health_data["status"] = "degraded"
            health_data.setdefault("warnings", []).append(
                f"Missing environment variables: {', '.join(missing_env)}"
            )

        if not disk_info["output_dir_writable"]:
            health_data["status"] = "degraded"
            health_data.setdefault("warnings", []).append("Output directory not writable")

        return health_data

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "response_time_ms": (
                round((time.time() - start_time) * 1000, 2) if "start_time" in locals() else 0
            ),
        }


@mcp.tool()
async def system_info() -> Dict[str, Any]:
    """
    Get detailed system information and configuration.

    Returns:
        A dictionary containing system configuration and status
    """
    try:
        return {
            "version": "1.0.0",
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "node": platform.node(),
            "system": platform.system(),
            "release": platform.release(),
            "providers": {
                "llm_primary": os.getenv("PRIMARY_LLM_PROVIDER", "not_configured"),
                "llm_model": os.getenv("PRIMARY_LLM_MODEL", "not_configured"),
                "search_primary": os.getenv("PRIMARY_SEARCH_PROVIDER", "not_configured"),
                "research_language": os.getenv("RESEARCH_LANGUAGE", "en"),
            },
            "directories": {
                "current": os.getcwd(),
                "outputs": (
                    os.path.abspath("./outputs") if os.path.exists("./outputs") else "not_created"
                ),
                "logs": os.path.abspath("./logs") if os.path.exists("./logs") else "not_created",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    # Run the server
    mcp.run()
