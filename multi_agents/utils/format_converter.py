"""
Format Converter for BRAVE Search Results
Converts between BRAVE search response format and GPT-researcher expected format
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BraveToGPTResearcherConverter:
    """
    Converts BRAVE search results to the format expected by GPT-researcher.

    GPT-researcher expects results in this format:
    [
        {
            "url": "http://example.com/page1",
            "raw_content": "Content of page 1"
        },
        ...
    ]

    BRAVE provides results in SearchResponse format with SearchResult objects.
    """

    @staticmethod
    def convert_search_response(brave_response, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Convert BRAVE SearchResponse to GPT-researcher format.

        Args:
            brave_response: BRAVE SearchResponse object
            max_results: Maximum number of results to return

        Returns:
            List of results in GPT-researcher format
        """
        try:
            if not brave_response or not hasattr(brave_response, "results"):
                logger.warning("Invalid BRAVE response format")
                return []

            gpt_results = []

            # Convert each BRAVE SearchResult to GPT-researcher format
            for idx, result in enumerate(brave_response.results[:max_results]):
                try:
                    # Ensure we have required fields
                    url = getattr(result, "url", "") or ""
                    content = getattr(result, "content", "") or ""
                    title = getattr(result, "title", "") or ""

                    # Create GPT-researcher compatible result
                    gpt_result = {
                        "href": url,  # GPT-researcher expects 'href'
                        "body": content,  # GPT-researcher expects 'body'
                        "raw_content": content,  # Also include for compatibility
                    }

                    # Add optional fields that GPT-researcher might use
                    if title:
                        gpt_result["title"] = title

                    # Add metadata if available
                    if hasattr(result, "published_date") and result.published_date:
                        gpt_result["published_date"] = result.published_date

                    if hasattr(result, "score") and result.score:
                        gpt_result["score"] = result.score

                    # Only add results with valid URL and content
                    if url and content:
                        gpt_results.append(gpt_result)
                        logger.debug(f"Converted result {idx + 1}: {url[:50]}...")
                    else:
                        logger.warning(f"Skipping result {idx + 1}: missing URL or content")

                except Exception as e:
                    logger.error(f"Error converting result {idx + 1}: {e}")
                    continue

            logger.info(f"Converted {len(gpt_results)} BRAVE results to GPT-researcher format")
            return gpt_results

        except Exception as e:
            logger.error(f"Error converting BRAVE response: {e}")
            return []

    @staticmethod
    def convert_search_results_list(
        brave_results: List, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Convert a list of BRAVE SearchResult objects to GPT-researcher format.

        Args:
            brave_results: List of BRAVE SearchResult objects
            max_results: Maximum number of results to return

        Returns:
            List of results in GPT-researcher format
        """
        try:
            if not brave_results:
                return []

            gpt_results = []

            for idx, result in enumerate(brave_results[:max_results]):
                try:
                    # Handle both object attributes and dict access
                    if hasattr(result, "url"):
                        # SearchResult object
                        url = result.url or ""
                        content = result.content or ""
                        title = result.title or ""
                    elif isinstance(result, dict):
                        # Dict format
                        url = result.get("url", "") or ""
                        content = result.get("content", "") or result.get("raw_content", "") or ""
                        title = result.get("title", "") or ""
                    else:
                        logger.warning(f"Unknown result format at index {idx}")
                        continue

                    # Create GPT-researcher result
                    gpt_result = {
                        "href": url,  # GPT-researcher expects 'href'
                        "body": content,  # GPT-researcher expects 'body'
                        "raw_content": content,  # Also include for compatibility
                    }

                    if title:
                        gpt_result["title"] = title

                    # Only add valid results
                    if url and content:
                        gpt_results.append(gpt_result)
                    else:
                        logger.warning(f"Skipping invalid result {idx + 1}")

                except Exception as e:
                    logger.error(f"Error processing result {idx + 1}: {e}")
                    continue

            return gpt_results

        except Exception as e:
            logger.error(f"Error converting BRAVE results list: {e}")
            return []

    @staticmethod
    def validate_gpt_researcher_format(results: List[Dict[str, Any]]) -> bool:
        """
        Validate that results are in the correct format for GPT-researcher.

        Args:
            results: List of result dictionaries

        Returns:
            True if format is valid, False otherwise
        """
        try:
            if not isinstance(results, list):
                logger.error("Results must be a list")
                return False

            for idx, result in enumerate(results):
                if not isinstance(result, dict):
                    logger.error(f"Result {idx} must be a dictionary")
                    return False

                # Check for GPT-researcher required fields
                if "href" not in result:
                    logger.error(f"Result {idx} missing required 'href' field")
                    return False

                if "body" not in result:
                    logger.error(f"Result {idx} missing required 'body' field")
                    return False

                if not isinstance(result["href"], str):
                    logger.error(f"Result {idx} 'href' must be a string")
                    return False

                if not isinstance(result["body"], str):
                    logger.error(f"Result {idx} 'body' must be a string")
                    return False

            logger.info(f"Validated {len(results)} results for GPT-researcher format")
            return True

        except Exception as e:
            logger.error(f"Error validating format: {e}")
            return False

    @staticmethod
    def add_content_summary(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add content summaries to results for better debugging.

        Args:
            results: List of GPT-researcher format results

        Returns:
            Results with added summary information
        """
        try:
            for idx, result in enumerate(results):
                content = result.get("raw_content", "")
                result["content_length"] = len(content)
                result["content_preview"] = content[:200] + "..." if len(content) > 200 else content

            return results

        except Exception as e:
            logger.error(f"Error adding content summaries: {e}")
            return results
