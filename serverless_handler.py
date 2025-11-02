"""
AWS Lambda handlers for Deep Research MCP serverless deployment.
This module provides the necessary handlers to run the MCP server in AWS Lambda.
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO if os.getenv("LOG_LEVEL", "INFO") == "INFO" else logging.DEBUG)

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import MCP server components
try:
    from gpt_researcher.utils.enum import Tone

    from mcp_server import deep_research, health_check, mcp, system_info
    from multi_agents.main import run_research_task
except ImportError as e:
    logger.error(f"Failed to import MCP components: {e}")
    raise


def lambda_response(
    status_code: int, body: Dict[str, Any], headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standard Lambda response object.

    Args:
        status_code: HTTP status code
        body: Response body dictionary
        headers: Optional HTTP headers

    Returns:
        Lambda response dictionary
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS,PUT,DELETE",
    }

    if headers:
        default_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body, default=str, ensure_ascii=False),
    }


def extract_request_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract request data from Lambda event.

    Args:
        event: Lambda event dictionary

    Returns:
        Extracted request data
    """
    try:
        # Handle different event sources
        if "body" in event:
            body = event.get("body", "{}")
            if isinstance(body, str):
                body = json.loads(body) if body else {}
        else:
            body = event

        query_params = event.get("queryStringParameters", {}) or {}
        path_params = event.get("pathParameters", {}) or {}
        headers = event.get("headers", {})

        return {
            "body": body,
            "query": query_params,
            "path": path_params,
            "headers": headers,
            "method": event.get("httpMethod", "GET"),
            "path": event.get("path", "/"),
            "source": event.get("source", "api-gateway"),
        }
    except Exception as e:
        logger.error(f"Error extracting request data: {e}")
        return {
            "body": {},
            "query": {},
            "path": {},
            "headers": {},
            "method": "GET",
            "path": "/",
            "source": "unknown",
        }


async def handle_mcp_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle MCP protocol requests.

    Args:
        request_data: Extracted request data

    Returns:
        MCP response
    """
    try:
        method = request_data["method"]
        path = request_data["path"]
        body = request_data["body"]

        # Route MCP requests
        if path == "/health" or path.endswith("/health"):
            result = await health_check()
            return lambda_response(200, result)

        elif path == "/system-info" or path.endswith("/system-info"):
            result = await system_info()
            return lambda_response(200, result)

        elif path == "/research" or path.endswith("/research"):
            if method != "POST":
                return lambda_response(
                    405, {"error": "Method not allowed. Use POST for research requests."}
                )

            # Extract research parameters
            query = body.get("query")
            if not query:
                return lambda_response(400, {"error": "Query parameter is required"})

            tone = body.get("tone", "objective")
            language = body.get("language", os.getenv("RESEARCH_LANGUAGE", "en"))

            # Set language environment if provided
            if language:
                os.environ["RESEARCH_LANGUAGE"] = language

            # Perform research
            result = await deep_research(query, tone)
            return lambda_response(200, result)

        else:
            # Default MCP server behavior for other paths
            return lambda_response(
                404,
                {
                    "error": "Endpoint not found",
                    "available_endpoints": ["/health", "/system-info", "/research"],
                },
            )

    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        logger.error(traceback.format_exc())
        return lambda_response(
            500,
            {
                "error": "Internal server error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


def mcp_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for MCP server requests.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Lambda response
    """
    try:
        logger.info(
            f"Processing MCP request: {event.get('httpMethod', 'UNKNOWN')} {event.get('path', 'UNKNOWN')}"
        )

        # Handle preflight CORS requests
        if event.get("httpMethod") == "OPTIONS":
            return lambda_response(200, {"message": "CORS preflight"})

        # Extract request data
        request_data = extract_request_data(event)

        # Handle the request asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(handle_mcp_request(request_data))
            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Unhandled error in mcp_handler: {e}")
        logger.error(traceback.format_exc())
        return lambda_response(
            500,
            {
                "error": "Unhandled server error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


def health_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lightweight health check handler.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Health check response
    """
    try:
        # Quick health check without heavy dependencies
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "lambda_request_id": context.aws_request_id if context else "unknown",
            "remaining_time_ms": context.get_remaining_time_in_millis() if context else 0,
            "environment": {
                "stage": os.getenv("STAGE", "unknown"),
                "region": os.getenv("AWS_REGION", "unknown"),
                "service": os.getenv("SERVICE_NAME", "deep-research-mcp"),
            },
        }

        return lambda_response(200, health_data)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return lambda_response(
            503,
            {"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow().isoformat()},
        )


def research_processor(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Background research task processor for SQS messages.

    Args:
        event: SQS event
        context: Lambda context

    Returns:
        Processing result
    """
    try:
        results = []

        # Process each SQS record
        for record in event.get("Records", []):
            try:
                # Parse message body
                message_body = json.loads(record.get("body", "{}"))

                logger.info(
                    f"Processing research task: {message_body.get('research_id', 'unknown')}"
                )

                # Extract research parameters
                query = message_body.get("query")
                tone = message_body.get("tone", "objective")
                language = message_body.get("language", "en")
                research_id = message_body.get("research_id")

                if not query:
                    logger.error(f"No query provided in message: {record}")
                    results.append({"status": "error", "error": "No query provided"})
                    continue

                # Set language environment if provided
                if language:
                    os.environ["RESEARCH_LANGUAGE"] = language

                # Run research task
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    tone_enum = getattr(Tone, tone.capitalize(), Tone.Objective)

                    research_result = loop.run_until_complete(
                        run_research_task(
                            query=query,
                            websocket=None,
                            stream_output=None,
                            tone=tone_enum,
                            write_to_files=False,  # Don't write files in Lambda
                        )
                    )

                    # Store result (could be in S3 or DynamoDB)
                    # TODO: Implement storage logic based on your needs

                    results.append(
                        {
                            "status": "success",
                            "research_id": research_id,
                            "query": query,
                            "result_summary": f"Research completed: {len(research_result)} characters",
                        }
                    )

                    logger.info(f"Successfully processed research task: {research_id}")

                finally:
                    loop.close()

            except Exception as e:
                logger.error(f"Error processing SQS record: {e}")
                logger.error(traceback.format_exc())
                results.append(
                    {
                        "status": "error",
                        "error": str(e),
                        "record": record.get("messageId", "unknown"),
                    }
                )

        return {
            "processed_count": len(results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Fatal error in research_processor: {e}")
        logger.error(traceback.format_exc())
        raise  # Re-raise to trigger Lambda retry/DLQ


def cloudwatch_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler for CloudWatch scheduled events (health checks, maintenance, etc.).

    Args:
        event: CloudWatch event
        context: Lambda context

    Returns:
        Processing result
    """
    try:
        source = event.get("source", "unknown")
        detail_type = event.get("detail-type", "unknown")

        logger.info(f"Processing CloudWatch event: {detail_type} from {source}")

        if "ScheduledEvent" in detail_type:
            # Periodic health check or maintenance task
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                health_result = loop.run_until_complete(health_check())

                # Log health status
                logger.info(
                    f"Scheduled health check result: {health_result.get('status', 'unknown')}"
                )

                return {
                    "status": "completed",
                    "event_type": detail_type,
                    "health_check": health_result,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            finally:
                loop.close()

        else:
            logger.warning(f"Unknown CloudWatch event type: {detail_type}")
            return {
                "status": "ignored",
                "event_type": detail_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"Error in cloudwatch_handler: {e}")
        logger.error(traceback.format_exc())
        raise


# ============================================================================
# Lambda Cold Start Optimization
# ============================================================================

# Pre-import heavy dependencies to reduce cold start time
try:
    logger.info("Pre-loading MCP components for cold start optimization")
    # This helps with subsequent invocations
except Exception as e:
    logger.warning(f"Cold start optimization warning: {e}")


# ============================================================================
# Handler Registration
# ============================================================================

# Export handlers for Serverless Framework
__all__ = ["mcp_handler", "health_handler", "research_processor", "cloudwatch_handler"]
