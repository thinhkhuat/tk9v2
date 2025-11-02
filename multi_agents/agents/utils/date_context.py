"""
Date context utilities for temporal awareness in agents.
Provides current date and contextual information to prevent temporal errors.
"""

import datetime
from typing import Any, Dict


def get_current_date_context() -> Dict[str, Any]:
    """
    Get current date context for agent awareness.

    Returns:
        Dictionary with current date, year, and contextual information
    """
    now = datetime.datetime.now()

    return {
        "current_date": now.strftime("%B %d, %Y"),
        "current_year": now.year,
        "current_month": now.month,
        "date_iso": now.isoformat(),
        "context_message": f"""You are operating in {now.year}. Events from 2024-2025 are current/recent events, not future events.""",
    }


def format_system_prompt_with_date(base_prompt: str) -> str:
    """
    Format a system prompt with current date context.

    Args:
        base_prompt: The base system prompt

    Returns:
        Formatted prompt with date awareness
    """
    context = get_current_date_context()

    date_awareness = f"""
TEMPORAL CONTEXT:
- Today's date: {context['current_date']}
- Current year: {context['current_year']}
- Important: Events from 2024-2025 are CURRENT events, not future events
- Do not reject content for mentioning recent dates or contemporary figures
"""

    return f"{base_prompt}\n{date_awareness}"


def is_temporal_issue(text: str) -> bool:
    """
    Check if text contains temporal concerns that should be ignored.

    Args:
        text: Text to check for temporal issues

    Returns:
        True if text primarily contains temporal concerns
    """
    if not text:
        return False

    text_lower = text.lower()

    # Temporal issue indicators
    temporal_indicators = [
        "future event",
        "hasn't happened",
        "not yet occurred",
        "will happen",
        "upcoming",
        "later this year",
        "next year",
        "factually incorrect date",
        "wrong year",
        "anachronistic",
    ]

    # Check for 2024-2025 dates being flagged
    date_issues = ("2024" in text or "2025" in text) and any(
        term in text_lower for term in ["future", "incorrect", "wrong", "error"]
    )

    # Substantive issue indicators
    substantive_indicators = [
        "format",
        "structure",
        "missing",
        "incomplete",
        "guideline",
        "clarity",
        "grammar",
        "citation",
        "evidence",
        "source",
        "organization",
        "flow",
        "coherence",
        "methodology",
    ]

    has_temporal = any(indicator in text_lower for indicator in temporal_indicators) or date_issues
    has_substantive = any(indicator in text_lower for indicator in substantive_indicators)

    # Return True only if temporal issues without substantive problems
    return has_temporal and not has_substantive


def get_contemporary_context() -> str:
    """
    Get a string describing the contemporary context for agents.

    Returns:
        String with current political, technological, and social context
    """
    context = get_current_date_context()

    return f"""
CONTEMPORARY CONTEXT (as of {context['current_date']}):
- Donald Trump is the current President of the United States (January 2025)
- AI and LLM technologies have advanced significantly in 2024-2025
- The COVID-19 pandemic is a recent historical event (2020-2023)
- Climate change and sustainability are major current global issues
- Social media and digital transformation continue to evolve rapidly

This context should be considered when reviewing content mentioning current events.
"""
