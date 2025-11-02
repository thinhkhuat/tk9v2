"""
Fact-Checking Utility for Reviewer and Reviser Agents

This module implements a comprehensive fact-checking protocol that prevents agents
from blocking the workflow based on unverified claims. It enforces mandatory 
verification through BRAVE search before any factual corrections can be made.

Key Features:
- Mandatory verification via BRAVE search for factual claims
- Burden of proof principle: if can't verify as false, assume valid
- Contemporary event awareness (2024-2025)
- Transparent logging of all verification attempts
- Safeguards against workflow blocking
"""

import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple, Union

import requests

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Status of fact verification attempt"""

    VERIFIED_TRUE = "verified_true"
    VERIFIED_FALSE = "verified_false"
    INCONCLUSIVE = "inconclusive"
    SEARCH_FAILED = "search_failed"
    NO_VERIFICATION_NEEDED = "no_verification_needed"


class FeedbackCategory(Enum):
    """Category of feedback for appropriate processing"""

    FORMATTING = "formatting"  # Grammar, spelling, structure - no fact-check needed
    CONTENT = "content"  # Facts, dates, claims - mandatory fact-check
    HYBRID = "hybrid"  # Formatting that affects content - double-check


class FactCheckResult:
    """Result of a fact-checking operation"""

    def __init__(
        self,
        claim: str,
        status: VerificationStatus,
        evidence: List[Dict[str, str]] = None,
        confidence: float = 0.0,
        search_query: str = None,
        error_message: str = None,
    ):
        self.claim = claim
        self.status = status
        self.evidence = evidence or []
        self.confidence = confidence
        self.search_query = search_query
        self.error_message = error_message
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "claim": self.claim,
            "status": self.status.value,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "search_query": self.search_query,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }

    def can_block_workflow(self) -> bool:
        """
        Determine if this result can block the workflow.
        Only VERIFIED_FALSE claims with high confidence can block.
        """
        return self.status == VerificationStatus.VERIFIED_FALSE and self.confidence > 0.8

    def __str__(self) -> str:
        """String representation for logging"""
        return (
            f"FactCheckResult(claim='{self.claim[:50]}...', "
            f"status={self.status.value}, confidence={self.confidence:.2f})"
        )


class FactChecker:
    """
    Comprehensive fact-checking utility using BRAVE search.
    Implements burden of proof principle and contemporary awareness.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the fact checker with BRAVE API credentials.

        Args:
            api_key: BRAVE API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        if not self.api_key:
            logger.warning("BRAVE_API_KEY not found. Fact-checking will be limited.")

        self.endpoint = "https://api.search.brave.com/res/v1/web/search"
        self.current_year = datetime.now().year
        self.verification_log = []

        # Contemporary event awareness
        self.contemporary_years = [self.current_year - 1, self.current_year, self.current_year + 1]

        # Keywords that indicate factual claims needing verification
        self.factual_claim_indicators = [
            "incorrect",
            "wrong",
            "false",
            "inaccurate",
            "mistaken",
            "error",
            "not true",
            "actually",
            "in fact",
            "really",
            "should be",
            "must be",
            "is not",
            "was not",
            "will not",
        ]

        # Keywords that indicate style/structure issues (not factual)
        self.style_indicators = [
            "formatting",
            "structure",
            "clarity",
            "grammar",
            "spelling",
            "readability",
            "flow",
            "organization",
            "style",
            "tone",
            "coherence",
            "consistency",
            "redundant",
            "verbose",
        ]

        # Enhanced categorization patterns
        self.formatting_patterns = {
            "grammar": ["grammar", "grammatical", "sentence structure", "syntax", "tense", "voice"],
            "spelling": ["spelling", "typo", "misspelled", "typos", "misspell"],
            "punctuation": ["punctuation", "comma", "period", "semicolon", "colon", "apostrophe"],
            "structure": [
                "structure",
                "organization",
                "flow",
                "transition",
                "paragraph",
                "section",
            ],
            "style": ["style", "tone", "clarity", "readability", "concise", "verbose", "redundant"],
            "formatting": [
                "formatting",
                "bold",
                "italic",
                "bullet",
                "numbering",
                "heading",
                "markdown",
            ],
        }

        self.content_patterns = {
            "dates": [
                "year",
                "date",
                "january",
                "february",
                "march",
                "april",
                "may",
                "june",
                "july",
                "august",
                "september",
                "october",
                "november",
                "december",
                "2020",
                "2021",
                "2022",
                "2023",
                "2024",
                "2025",
            ],
            "numbers": ["percent", "%", "million", "billion", "thousand", "statistics", "data"],
            "names": ["president", "ceo", "founder", "director", "minister", "secretary"],
            "events": [
                "announced",
                "launched",
                "founded",
                "established",
                "created",
                "died",
                "born",
            ],
            "facts": [
                "actually",
                "in fact",
                "really",
                "truth",
                "false",
                "true",
                "correct",
                "incorrect",
            ],
        }

        self.hybrid_indicators = {
            # Patterns that could be both formatting AND content issues
            "date_formatting": ["date format", "year format", "time format"],
            "numerical_formatting": ["number format", "percentage format", "currency format"],
            "citation_formatting": ["citation", "reference", "source", "bibliography"],
            "name_formatting": ["name format", "title format", "capitalization of names"],
        }

    def _safe_string(self, value: Any) -> str:
        """Safely convert any value to string."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            # Handle dictionary inputs by extracting text content
            try:
                # Try to find text content in common keys
                text_keys = ["text", "content", "message", "feedback", "review", "response"]
                for key in text_keys:
                    if key in value and isinstance(value[key], str) and value[key].strip():
                        return value[key]
                # If no text found in common keys, try to join all string values
                text_parts = []
                for v in value.values():
                    if isinstance(v, str) and v.strip():
                        text_parts.append(v)
                if text_parts:
                    return " ".join(text_parts)
                # Fallback to string representation
                return str(value)
            except Exception as e:
                logger.warning(f"Failed to convert dict to string: {e}")
                return str(value) if value else ""
        try:
            return str(value)
        except Exception as e:
            logger.warning(f"Failed to convert value to string: {e}")
            return ""

    def _safe_lower(self, text: Any) -> str:
        """Safely convert text to lowercase."""
        try:
            # First convert to safe string
            safe_text = self._safe_string(text)
            # Double-check that we have a string before calling .lower()
            if not isinstance(safe_text, str):
                logger.warning(
                    f"_safe_string returned non-string type {type(safe_text)}, converting again"
                )
                safe_text = str(safe_text) if safe_text is not None else ""
            # Now safe to call .lower()
            return safe_text.lower() if safe_text else ""
        except Exception as e:
            logger.error(f"Error in _safe_lower with input type {type(text)}: {e}")
            # Ultimate fallback - try to convert input directly to string and lowercase
            try:
                fallback_str = str(text) if text is not None else ""
                return fallback_str.lower() if fallback_str else ""
            except Exception as e2:
                logger.error(f"Ultimate fallback failed in _safe_lower: {e2}")
                return ""

    def _safe_dict_get(self, data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
        """Safely access nested dictionary values."""
        if not isinstance(data, dict):
            return default

        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current if current is not None else default

    def _validate_string_input(self, text: Any, param_name: str) -> str:
        """Validate and convert input to safe string."""
        if text is None:
            logger.warning(f"None value provided for {param_name}")
            return ""

        safe_text = self._safe_string(text).strip()
        if not safe_text:
            logger.warning(f"Empty or invalid text provided for {param_name}")
            return ""

        return safe_text

    def extract_factual_claims(self, text: Union[str, Any]) -> List[str]:
        """
        Extract potential factual claims from review text that need verification.

        Args:
            text: Review or revision text (any type will be safely converted)

        Returns:
            List of extracted factual claims
        """
        import re

        # Validate and convert input to safe string
        safe_text = self._validate_string_input(text, "text")
        if not safe_text:
            logger.warning("No valid text provided for factual claim extraction")
            return []

        claims = []

        try:
            sentences = re.split(r"[.!?]+", safe_text)
        except Exception as e:
            logger.error(f"Failed to split text into sentences: {e}")
            return []

        for sentence in sentences:
            # Safe string processing
            sentence = self._safe_string(sentence).strip()
            if not sentence:
                continue

            sentence_lower = self._safe_lower(sentence)
            if not sentence_lower:
                continue

            # Skip style/structure feedback
            try:
                if any(indicator in sentence_lower for indicator in self.style_indicators):
                    continue
            except (TypeError, AttributeError) as e:
                logger.warning(f"Error checking style indicators: {e}")
                continue

            # Check if sentence contains factual claim indicators
            try:
                if any(indicator in sentence_lower for indicator in self.factual_claim_indicators):
                    claims.append(sentence)
            except (TypeError, AttributeError) as e:
                logger.warning(f"Error checking factual indicators: {e}")
                continue

            # Also extract specific date/event claims
            # Pattern for dates (years, specific dates)
            date_patterns = [
                r"\b(19|20)\d{2}\b",  # Years
                r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",  # Dates
                r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
            ]

            try:
                for pattern in date_patterns:
                    if re.search(pattern, sentence):
                        claims.append(sentence)
                        break
            except Exception as e:
                logger.warning(f"Error matching date patterns: {e}")
                continue

            # Extract claims about specific people/events
            try:
                if re.search(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", sentence):  # Proper names
                    event_words = ["president", "ceo", "founded", "died", "born", "elected"]
                    if any(word in sentence_lower for word in event_words):
                        claims.append(sentence)
            except Exception as e:
                logger.warning(f"Error matching name patterns: {e}")
                continue

        # Remove duplicates safely
        try:
            return list(set(claims))
        except Exception as e:
            logger.error(f"Error removing duplicates from claims: {e}")
            return claims

    def categorize_feedback(self, feedback_input: Any) -> Tuple[FeedbackCategory, Dict[str, Any]]:
        """
        Categorize feedback into FORMATTING, CONTENT, or HYBRID based on analysis.

        Args:
            feedback_input: The feedback text to categorize (any type will be safely handled)

        Returns:
            Tuple of (category, analysis_details)
        """
        import re

        # Handle both string and dictionary inputs with defensive programming
        feedback_text = ""

        try:
            if isinstance(feedback_input, dict):
                # Extract text content from dictionary - try common keys
                possible_text_keys = [
                    "feedback",
                    "review",
                    "content",
                    "text",
                    "message",
                    "comments",
                    "notes",
                    "analysis",
                    "response",
                ]

                # Try to find text content in common keys
                for key in possible_text_keys:
                    try:
                        if key in feedback_input:
                            value = feedback_input[key]
                            if isinstance(value, str) and value.strip():
                                feedback_text = value
                                break
                    except (TypeError, KeyError) as e:
                        logger.warning(f"Error accessing key '{key}': {e}")
                        continue

                # If no text found in common keys, try to stringify dict values
                if not feedback_text:
                    try:
                        text_parts = []
                        for value in feedback_input.values():
                            if isinstance(value, (str, int, float)) and str(value).strip():
                                text_parts.append(str(value))
                        feedback_text = " ".join(text_parts) if text_parts else ""
                    except Exception as e:
                        logger.warning(f"Error extracting text from dict values: {e}")

                # Final fallback - use string representation of the entire dict
                if not feedback_text:
                    try:
                        feedback_text = str(feedback_input)
                    except Exception as e:
                        logger.error(f"Failed to stringify feedback dict: {e}")
                        feedback_text = "Unable to process feedback content"

            elif isinstance(feedback_input, str):
                feedback_text = feedback_input
            else:
                # Handle other types by converting to string
                try:
                    feedback_text = str(feedback_input)
                except Exception as e:
                    logger.error(f"Failed to convert feedback to string: {e}")
                    feedback_text = "Unable to process feedback content"

        except Exception as e:
            logger.error(f"Error processing feedback input: {e}")
            feedback_text = "Error processing feedback content"

        # Ensure we have a non-empty string
        feedback_text = self._safe_string(feedback_text).strip()
        if not feedback_text:
            feedback_text = "No feedback content available"

        feedback_lower = self._safe_lower(feedback_text)
        analysis = {
            "formatting_score": 0.0,
            "content_score": 0.0,
            "hybrid_score": 0.0,
            "detected_patterns": {"formatting": [], "content": [], "hybrid": []},
            "reasoning": [],
        }

        # Pre-analysis: Check for strong formatting signals that should override content signals
        strong_formatting_phrases = [
            "grammar",
            "spelling",
            "punctuation",
            "formatting",
            "style",
            "structure",
            "organization",
            "flow",
            "readability",
            "clarity",
            "bullet points",
            "headings",
            "capitalization",
        ]

        try:
            formatting_phrase_count = sum(
                1
                for phrase in strong_formatting_phrases
                if phrase and feedback_lower and phrase in feedback_lower
            )
        except (TypeError, AttributeError) as e:
            logger.warning(f"Error counting formatting phrases: {e}")
            formatting_phrase_count = 0

        # If feedback is dominated by formatting terminology, bias towards formatting
        if formatting_phrase_count >= 2:
            analysis["formatting_bias"] = True
            analysis["reasoning"].append(
                f"Strong formatting terminology detected ({formatting_phrase_count} phrases)"
            )
        else:
            analysis["formatting_bias"] = False

        # Analyze formatting patterns
        try:
            for category, patterns in self.formatting_patterns.items():
                if not isinstance(patterns, (list, tuple)):
                    continue
                for pattern in patterns:
                    try:
                        pattern_str = self._safe_string(pattern)
                        if pattern_str and feedback_lower and pattern_str in feedback_lower:
                            analysis["formatting_score"] += 1.0
                            analysis["detected_patterns"]["formatting"].append(
                                f"{category}: {pattern_str}"
                            )
                    except Exception as e:
                        logger.warning(f"Error checking formatting pattern {pattern}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error analyzing formatting patterns: {e}")

        # Analyze content patterns
        try:
            for category, patterns in self.content_patterns.items():
                if not isinstance(patterns, (list, tuple)):
                    continue
                for pattern in patterns:
                    try:
                        pattern_str = self._safe_string(pattern)
                        if pattern_str and feedback_lower and pattern_str in feedback_lower:
                            analysis["content_score"] += 2.0  # Content patterns weighted higher
                            analysis["detected_patterns"]["content"].append(
                                f"{category}: {pattern_str}"
                            )
                    except Exception as e:
                        logger.warning(f"Error checking content pattern {pattern}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error analyzing content patterns: {e}")

        # Analyze hybrid patterns
        try:
            for category, patterns in self.hybrid_indicators.items():
                if not isinstance(patterns, (list, tuple)):
                    continue
                for pattern in patterns:
                    try:
                        pattern_str = self._safe_string(pattern)
                        if pattern_str and feedback_lower and pattern_str in feedback_lower:
                            analysis["hybrid_score"] += 1.5
                            analysis["detected_patterns"]["hybrid"].append(
                                f"{category}: {pattern_str}"
                            )
                    except Exception as e:
                        logger.warning(f"Error checking hybrid pattern {pattern}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error analyzing hybrid patterns: {e}")

        # Check for factual claim indicators (strong content signal)
        factual_matches = 0
        try:
            for indicator in self.factual_claim_indicators:
                indicator_str = self._safe_string(indicator)
                if not indicator_str or not feedback_lower:
                    continue

                try:
                    if indicator_str in feedback_lower:
                        factual_matches += 1
                        # Only add high score if not in a formatting context
                        try:
                            context_words = feedback_lower.split()
                            context_around = (
                                " ".join(context_words) if context_words else feedback_lower
                            )

                            # Check if the factual indicator is in a formatting context
                            formatting_context_phrases = [
                                "formatting error",
                                "format issue",
                                "grammar",
                                "spelling",
                                "style",
                                "structure",
                                "punctuation",
                                "capitalization",
                            ]

                            in_formatting_context = any(
                                phrase in context_around
                                for phrase in formatting_context_phrases
                                if phrase and context_around
                            )

                            if in_formatting_context:
                                analysis["hybrid_score"] += 2.0  # Likely hybrid
                                analysis["detected_patterns"]["hybrid"].append(
                                    f"factual_in_format_context: {indicator_str}"
                                )
                            else:
                                analysis["content_score"] += 3.0  # Strong content indicator
                                analysis["detected_patterns"]["content"].append(
                                    f"factual_claim: {indicator_str}"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Error analyzing context for indicator '{indicator_str}': {e}"
                            )
                            # Default to content if context analysis fails
                            analysis["content_score"] += 3.0
                            analysis["detected_patterns"]["content"].append(
                                f"factual_claim: {indicator_str}"
                            )
                except Exception as e:
                    logger.warning(f"Error checking factual indicator '{indicator_str}': {e}")
                    continue
        except Exception as e:
            logger.error(f"Error analyzing factual claim indicators: {e}")

        # Check for semantic patterns that indicate content changes
        # But first check if they're in formatting contexts
        content_change_patterns = [
            (r'\b(?:should be|must be|actually is)\s+(["\']?[^"\']+["\']?)', "specific_change"),
            (
                r"\b(?:date|year|time|when)\s+(?:should be|is actually|was really)\s+([^.,]+)",
                "date_change",
            ),
            (
                r"\b(?:name|person|president|ceo|founder)\s+(?:should be|is actually)\s+([^.,]+)",
                "name_change",
            ),
            (
                r"\b(?:number|amount|percentage|statistics?)\s+(?:should be|is actually)\s+([^.,]+)",
                "number_change",
            ),
            (r"\b(?:not|isn\'t|wasn\'t|weren\'t)\s+([^.,]+)", "negation"),
        ]

        formatting_exclusions = [
            "grammar",
            "spelling",
            "format",
            "formatting",
            "style",
            "structure",
            "capitalization",
            "punctuation",
            "organization",
            "flow",
            "readability",
        ]

        try:
            for pattern, change_type in content_change_patterns:
                try:
                    matches = re.findall(pattern, feedback_text, re.IGNORECASE)
                    for match in matches:
                        try:
                            # Check if the match is about formatting rather than content
                            match_lower = self._safe_lower(match)
                            if not match_lower:
                                continue

                            is_formatting_related = any(
                                exclusion in match_lower
                                for exclusion in formatting_exclusions
                                if exclusion and match_lower
                            )

                            if is_formatting_related:
                                analysis["hybrid_score"] += 1.0
                                analysis["detected_patterns"]["hybrid"].append(
                                    f"format_related_{change_type}: {match}"
                                )
                            else:
                                analysis["content_score"] += 2.0
                                analysis["detected_patterns"]["content"].append(
                                    f"semantic_change: {match}"
                                )
                        except Exception as e:
                            logger.warning(f"Error processing match '{match}': {e}")
                            continue
                except Exception as e:
                    logger.warning(f"Error matching pattern '{pattern}': {e}")
                    continue
        except Exception as e:
            logger.error(f"Error analyzing semantic patterns: {e}")

        # Check for formatting-disguised content changes (hybrid detection)
        disguised_content_patterns = [
            r"(?:grammar|spelling|format)\s+(?:error|mistake|issue)\s+(?:with|in)\s+(?:date|year|name|number)",
            r"(?:capitalization|punctuation)\s+(?:of|for)\s+(?:president|ceo|company|organization)",
            r"(?:format|style)\s+(?:of|for)\s+(?:citation|reference|source|quote)",
        ]

        try:
            for pattern in disguised_content_patterns:
                try:
                    if feedback_lower and re.search(pattern, feedback_lower):
                        analysis["hybrid_score"] += 2.0
                        analysis["detected_patterns"]["hybrid"].append(
                            f"disguised_content: {pattern}"
                        )
                except Exception as e:
                    logger.warning(f"Error checking disguised pattern '{pattern}': {e}")
                    continue
        except Exception as e:
            logger.error(f"Error analyzing disguised content patterns: {e}")

        # Decision logic with reasoning
        # Calculate ratios to make better decisions with safe division
        try:
            total_score = float(
                analysis["formatting_score"] + analysis["content_score"] + analysis["hybrid_score"]
            )

            if total_score == 0:
                # No patterns detected - default to content for safety
                analysis["reasoning"].append(
                    "No categorization patterns detected - defaulting to CONTENT for safety"
                )
                return FeedbackCategory.CONTENT, analysis

            format_ratio = analysis["formatting_score"] / total_score
            content_ratio = analysis["content_score"] / total_score
            hybrid_ratio = analysis["hybrid_score"] / total_score

        except (TypeError, ZeroDivisionError, ValueError) as e:
            logger.error(f"Error calculating ratios: {e}")
            analysis["reasoning"].append(
                f"Error in ratio calculation - defaulting to CONTENT for safety: {e}"
            )
            return FeedbackCategory.CONTENT, analysis

        # Improved decision logic with formatting bias consideration
        if analysis.get("formatting_bias", False):
            # Strong formatting terminology detected - bias towards formatting
            if format_ratio >= 0.4 and content_ratio < 0.6:
                analysis["reasoning"].append(
                    f"Strong formatting bias overrides content signals (F:{format_ratio:.2f}, C:{content_ratio:.2f})"
                )
                return FeedbackCategory.FORMATTING, analysis
            elif content_ratio >= 0.6:
                # Still predominantly content despite formatting terms
                analysis["reasoning"].append(
                    f"Content ratio dominates despite formatting bias: {content_ratio:.2f}"
                )
                return FeedbackCategory.HYBRID, analysis

        if format_ratio >= 0.6 and content_ratio < 0.3:
            # Predominantly formatting feedback
            analysis["reasoning"].append(
                f"Predominantly formatting feedback (ratio: {format_ratio:.2f})"
            )
            analysis["reasoning"].append("Low content signal - safe for fast-track processing")
            return FeedbackCategory.FORMATTING, analysis

        elif content_ratio >= 0.5 and format_ratio < 0.3:
            # Predominantly content feedback
            analysis["reasoning"].append(
                f"Predominantly content feedback (ratio: {content_ratio:.2f})"
            )
            analysis["reasoning"].append("Requires full fact-checking verification")
            return FeedbackCategory.CONTENT, analysis

        elif hybrid_ratio >= 0.4 or (content_ratio > 0.3 and format_ratio > 0.3):
            # Mixed signals or explicit hybrid patterns
            analysis["reasoning"].append(
                f"Mixed or hybrid patterns (H:{hybrid_ratio:.2f}, C:{content_ratio:.2f}, F:{format_ratio:.2f})"
            )
            analysis["reasoning"].append("Formatting changes that could affect content meaning")
            return FeedbackCategory.HYBRID, analysis

        elif analysis["content_score"] >= 5.0 and not analysis.get("formatting_bias", False):
            # High absolute content score without formatting bias
            analysis["reasoning"].append(
                f"High absolute content score: {analysis['content_score']}"
            )
            analysis["reasoning"].append("Strong content signal requiring verification")
            return FeedbackCategory.CONTENT, analysis

        elif analysis["formatting_score"] > analysis["content_score"]:
            # Formatting wins in comparison
            analysis["reasoning"].append(
                f"Formatting score dominates: {analysis['formatting_score']} vs {analysis['content_score']}"
            )
            return FeedbackCategory.FORMATTING, analysis

        else:
            # Default based on context
            if analysis.get("formatting_bias", False):
                analysis["reasoning"].append(
                    "Formatting bias detected - defaulting to HYBRID for careful processing"
                )
                return FeedbackCategory.HYBRID, analysis
            else:
                analysis["reasoning"].append(
                    "Ambiguous categorization - defaulting to CONTENT for safety"
                )
                analysis["reasoning"].append(
                    f"Scores: F={analysis['formatting_score']}, C={analysis['content_score']}, H={analysis['hybrid_score']}"
                )
                return FeedbackCategory.CONTENT, analysis

    def should_fact_check(self, category: FeedbackCategory) -> bool:
        """
        Determine if feedback category requires fact-checking.

        Args:
            category: The feedback category

        Returns:
            Whether fact-checking is required
        """
        return category in [FeedbackCategory.CONTENT, FeedbackCategory.HYBRID]

    async def verify_claim(self, claim: str, context: str = None) -> FactCheckResult:
        """
        Verify a single factual claim using BRAVE search with comprehensive error handling.

        Args:
            claim: The factual claim to verify
            context: Additional context for the claim

        Returns:
            FactCheckResult with verification status and evidence
        """
        # Input validation
        safe_claim = self._validate_string_input(claim, "claim")
        if not safe_claim:
            error_msg = f"Invalid claim provided: {claim}"
            logger.error(error_msg)
            result = FactCheckResult(
                claim=str(claim) if claim is not None else "None",
                status=VerificationStatus.SEARCH_FAILED,
                error_message=error_msg,
            )
            try:
                self.verification_log.append(result.to_dict())
            except Exception as e:
                logger.warning(f"Error logging failed claim verification: {e}")
            return result

        if not self.api_key:
            logger.warning(f"Cannot verify claim without API key: {safe_claim[:50]}...")
            result = FactCheckResult(
                claim=safe_claim,
                status=VerificationStatus.SEARCH_FAILED,
                error_message="No BRAVE API key available",
            )
            try:
                self.verification_log.append(result.to_dict())
            except Exception as e:
                logger.warning(f"Error logging verification without API key: {e}")
            return result

        # Formulate search query with error handling
        try:
            search_query = self._formulate_search_query(safe_claim, context)
        except Exception as e:
            logger.error(f"Error formulating search query: {e}")
            search_query = f"{safe_claim} fact check verify"

        try:
            # Perform BRAVE search
            search_results = self._brave_search(search_query)

            if not search_results:
                # Search failed or no results
                result = FactCheckResult(
                    claim=safe_claim,
                    status=VerificationStatus.INCONCLUSIVE,
                    search_query=search_query,
                    error_message="No search results found",
                )
            else:
                # Analyze search results
                try:
                    result = self._analyze_search_results(safe_claim, search_results, search_query)
                except Exception as e:
                    logger.error(f"Error analyzing search results: {e}")
                    result = FactCheckResult(
                        claim=safe_claim,
                        status=VerificationStatus.SEARCH_FAILED,
                        search_query=search_query,
                        error_message=f"Error analyzing search results: {str(e)}",
                    )

            # Log the verification attempt safely
            try:
                self.verification_log.append(result.to_dict())
                logger.info(f"Fact check result: {result}")
            except Exception as e:
                logger.warning(f"Error logging verification result: {e}")

            return result

        except Exception as e:
            logger.error(f"Fact verification error: {e}")
            result = FactCheckResult(
                claim=safe_claim,
                status=VerificationStatus.SEARCH_FAILED,
                search_query=search_query,
                error_message=str(e),
            )
            try:
                self.verification_log.append(result.to_dict())
            except Exception as log_error:
                logger.warning(f"Error logging failed verification: {log_error}")
            return result

    def _formulate_search_query(self, claim: str, context: str = None) -> str:
        """
        Formulate an effective search query for fact verification with input validation.

        Args:
            claim: The claim to verify
            context: Additional context

        Returns:
            Optimized search query
        """
        import re

        # Input validation
        safe_claim = self._validate_string_input(claim, "claim")
        if not safe_claim:
            return "fact check verify"  # Fallback query

        safe_context = self._safe_string(context).strip() if context else ""

        try:
            # Extract key entities and dates from the claim
            query_parts = []

            # Extract proper names safely
            try:
                names = re.findall(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", safe_claim)
                if names:
                    query_parts.extend([name for name in names if name and len(name.strip()) > 0])
            except Exception as e:
                logger.warning(f"Error extracting names from claim: {e}")

            # Extract dates safely
            try:
                dates = re.findall(r"\b(19|20)\d{2}\b", safe_claim)
                if dates:
                    query_parts.extend([date for date in dates if date])
            except Exception as e:
                logger.warning(f"Error extracting dates from claim: {e}")

            # Extract key factual terms
            factual_terms = ["president", "ceo", "founded", "launched", "announced", "died", "born"]
            try:
                claim_lower = self._safe_lower(safe_claim)
                for term in factual_terms:
                    if term and claim_lower and term in claim_lower:
                        query_parts.append(term)
            except Exception as e:
                logger.warning(f"Error extracting factual terms: {e}")

            # Build the query safely
            try:
                if query_parts:
                    # Remove duplicates and empty parts
                    unique_parts = list(
                        set(part.strip() for part in query_parts if part and part.strip())
                    )
                    if unique_parts:
                        query = " ".join(unique_parts) + " fact check verify"
                    else:
                        query = safe_claim + " fact check verify"
                else:
                    # Use the full claim with fact-check suffix
                    query = safe_claim + " fact check true false verify"

                # Add contemporary context for recent events
                try:
                    if any(str(year) in safe_claim for year in self.contemporary_years if year):
                        query += f" {self.current_year} recent news"
                except Exception as e:
                    logger.warning(f"Error adding contemporary context: {e}")

                return query.strip()

            except Exception as e:
                logger.error(f"Error building search query: {e}")
                # Fallback to basic query
                return f"{safe_claim} fact check verify"

        except Exception as e:
            logger.error(f"Error formulating search query: {e}")
            # Final fallback
            return f"{safe_claim} verify" if safe_claim else "fact check verify"

    def _brave_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform BRAVE search for fact verification with comprehensive error handling.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        # Input validation
        safe_query = self._validate_string_input(query, "search query")
        if not safe_query:
            logger.error("No valid search query provided")
            return []

        # Validate max_results
        try:
            max_results = int(max_results)
            max_results = max(1, min(max_results, 20))  # BRAVE max is 20
        except (TypeError, ValueError):
            logger.warning(f"Invalid max_results value: {max_results}, using default 10")
            max_results = 10

        if not self.api_key:
            logger.error("No BRAVE API key available for search")
            return []

        # Retry logic for API calls
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                params = {
                    "q": safe_query,
                    "count": max_results,
                    "country": "US",
                    "search_lang": "en",
                    "freshness": "pw",  # Prefer recent results for contemporary claims
                }

                # Make request with comprehensive error handling
                response = requests.get(
                    self.endpoint,
                    headers={"X-Subscription-Token": self.api_key},
                    params=params,
                    timeout=15,  # Increased timeout
                    allow_redirects=True,
                )

                # Handle HTTP status codes
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return []

                    # Safe extraction of web results
                    web_results = self._safe_dict_get(data, "web", "results", default=[])
                    if not isinstance(web_results, list):
                        logger.warning("Web results is not a list, converting")
                        web_results = []

                    # Format results for analysis with safe access
                    formatted_results = []
                    for item in web_results:
                        if not isinstance(item, dict):
                            logger.warning(f"Skipping non-dict search result: {type(item)}")
                            continue

                        try:
                            # Safe extraction with defaults
                            result_item = {
                                "title": self._safe_string(
                                    self._safe_dict_get(item, "title", default="")
                                ),
                                "url": self._safe_string(
                                    self._safe_dict_get(item, "url", default="")
                                ),
                                "description": self._safe_string(
                                    self._safe_dict_get(item, "description", default="")
                                ),
                                "age": self._safe_string(
                                    self._safe_dict_get(item, "age", default="")
                                ),
                                "domain": self._safe_string(
                                    self._safe_dict_get(item, "meta_url", "hostname", default="")
                                ),
                            }
                            formatted_results.append(result_item)
                        except Exception as e:
                            logger.warning(f"Error formatting search result: {e}")
                            continue

                    logger.info(
                        f"BRAVE search successful: {len(formatted_results)} results for query '{safe_query[:50]}...'"
                    )
                    return formatted_results

                elif response.status_code == 429:  # Rate limited
                    logger.warning(f"Rate limited by BRAVE API (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * 2)  # Longer delay for rate limiting
                        continue
                    else:
                        logger.error("Max retries exceeded for rate limiting")
                        return []

                elif response.status_code in [401, 403]:  # Auth errors
                    logger.error(f"Authentication error with BRAVE API: {response.status_code}")
                    return []

                else:
                    logger.error(
                        f"BRAVE API HTTP error: {response.status_code} - {response.text[:200]}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return []

            except requests.exceptions.Timeout:
                logger.warning(f"BRAVE API timeout (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                logger.error("Max retries exceeded for timeouts")
                return []

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error to BRAVE API (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                logger.error("Max retries exceeded for connection errors")
                return []

            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception during BRAVE search: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return []

            except Exception as e:
                logger.error(f"Unexpected error during BRAVE search: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return []

            finally:
                retry_delay *= 2  # Exponential backoff

        logger.error(f"All retry attempts failed for BRAVE search query: {safe_query[:50]}...")
        return []

    def _analyze_search_results(
        self, claim: str, search_results: List[Dict[str, Any]], search_query: str
    ) -> FactCheckResult:
        """
        Analyze search results to determine claim veracity with safe processing.

        Args:
            claim: The original claim
            search_results: Search results from BRAVE
            search_query: The query used

        Returns:
            FactCheckResult with analysis
        """
        supporting_evidence = []
        contradicting_evidence = []

        # Input validation
        safe_claim = self._validate_string_input(claim, "claim")
        if not safe_claim:
            return FactCheckResult(
                claim=str(claim),
                status=VerificationStatus.SEARCH_FAILED,
                search_query=str(search_query),
                error_message="Invalid claim provided for analysis",
            )

        # Validate search results
        if not isinstance(search_results, list):
            logger.error(f"Search results must be a list, got {type(search_results)}")
            return FactCheckResult(
                claim=safe_claim,
                status=VerificationStatus.SEARCH_FAILED,
                search_query=str(search_query),
                error_message="Invalid search results format",
            )

        claim_lower = self._safe_lower(safe_claim)

        for result in search_results:
            if not isinstance(result, dict):
                logger.warning(f"Skipping non-dict search result: {type(result)}")
                continue

            try:
                # Safe extraction of title and description
                title = self._safe_string(self._safe_dict_get(result, "title", default=""))
                description = self._safe_string(
                    self._safe_dict_get(result, "description", default="")
                )
                title_desc = self._safe_lower(f"{title} {description}")

                if not title_desc.strip():
                    continue  # Skip if no meaningful content

                # Look for direct contradictions
                contradiction_terms = ["false", "incorrect", "myth", "debunked", "not true", "hoax"]
                support_terms = ["true", "confirmed", "verify", "correct", "accurate", "fact"]

                # Check if result contradicts or supports the claim
                try:
                    is_contradiction = any(
                        term in title_desc for term in contradiction_terms if term
                    )
                    is_support = any(term in title_desc for term in support_terms if term)
                except Exception as e:
                    logger.warning(f"Error checking support/contradiction terms: {e}")
                    continue

                # Build evidence entry with safe access
                try:
                    evidence_entry = {
                        "source": self._safe_string(
                            self._safe_dict_get(result, "domain", default="")
                        ),
                        "title": title,
                        "description": description,
                        "url": self._safe_string(self._safe_dict_get(result, "url", default="")),
                    }
                except Exception as e:
                    logger.warning(f"Error building evidence entry: {e}")
                    continue

                # Categorize evidence
                if is_contradiction and not is_support:
                    contradicting_evidence.append(evidence_entry)
                elif is_support and not is_contradiction:
                    supporting_evidence.append(evidence_entry)

            except Exception as e:
                logger.warning(f"Error processing search result: {e}")
                continue

        # Determine verification status based on evidence
        if len(contradicting_evidence) >= 3:
            # Strong evidence against the claim
            return FactCheckResult(
                claim=claim,
                status=VerificationStatus.VERIFIED_FALSE,
                evidence=contradicting_evidence[:3],  # Top 3 contradicting sources
                confidence=min(0.9, len(contradicting_evidence) / 10),
                search_query=search_query,
            )
        elif len(supporting_evidence) >= 3:
            # Strong evidence supporting the claim
            return FactCheckResult(
                claim=claim,
                status=VerificationStatus.VERIFIED_TRUE,
                evidence=supporting_evidence[:3],  # Top 3 supporting sources
                confidence=min(0.9, len(supporting_evidence) / 10),
                search_query=search_query,
            )
        else:
            # Inconclusive - apply burden of proof principle
            # Cannot block workflow without clear evidence
            return FactCheckResult(
                claim=claim,
                status=VerificationStatus.INCONCLUSIVE,
                evidence=supporting_evidence + contradicting_evidence,
                confidence=0.3,  # Low confidence
                search_query=search_query,
            )

    async def verify_review_feedback(
        self, review_text: str, original_content: str = None
    ) -> Tuple[List[FactCheckResult], bool]:
        """
        Verify all factual claims in review feedback with comprehensive error handling.

        Args:
            review_text: The review feedback text
            original_content: The original content being reviewed

        Returns:
            Tuple of (list of fact check results, whether workflow can proceed)
        """
        # Input validation
        safe_review_text = self._validate_string_input(review_text, "review_text")
        if not safe_review_text:
            logger.warning("No valid review text provided for fact checking")
            return [], True  # No valid review to check, workflow can proceed

        safe_original_content = self._safe_string(original_content) if original_content else None

        try:
            # Extract factual claims from review
            claims = self.extract_factual_claims(safe_review_text)

            if not claims:
                logger.info("No factual claims found in review feedback")
                return [], True  # No claims to verify, workflow can proceed

            logger.info(f"Found {len(claims)} factual claims to verify")

            # Verify each claim with error handling
            results = []
            for claim in claims:
                try:
                    result = await self.verify_claim(claim, context=safe_original_content)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error verifying claim '{claim[:50]}...': {e}")
                    # Create error result for this claim
                    error_result = FactCheckResult(
                        claim=claim,
                        status=VerificationStatus.SEARCH_FAILED,
                        error_message=f"Verification failed: {str(e)}",
                    )
                    results.append(error_result)

            # Determine if workflow can proceed
            try:
                blocking_results = [r for r in results if r and r.can_block_workflow()]
                can_proceed = len(blocking_results) == 0

                if not can_proceed:
                    logger.warning(f"{len(blocking_results)} verified false claims found")
                else:
                    logger.info("No blocking factual errors found - workflow can proceed")

                return results, can_proceed

            except Exception as e:
                logger.error(f"Error determining workflow blocking status: {e}")
                # Default to allowing workflow to proceed on error
                return results, True

        except Exception as e:
            logger.error(f"Error in verify_review_feedback: {e}")
            # Return empty results and allow workflow to proceed on critical error
            return [], True

    def generate_verification_report(self) -> str:
        """
        Generate a human-readable verification report.

        Returns:
            Formatted verification report
        """
        if not self.verification_log:
            return "No verification attempts recorded."

        report = ["# Fact Verification Report\n"]
        report.append(f"Generated: {datetime.now().isoformat()}\n")
        report.append(f"Total verifications: {len(self.verification_log)}\n\n")

        # Group by status
        by_status = {}
        for entry in self.verification_log:
            status = entry["status"]
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(entry)

        # Report by status
        for status, entries in by_status.items():
            report.append(f"## {status} ({len(entries)} claims)\n")
            for entry in entries:
                report.append(f"- **Claim**: {entry['claim'][:100]}...\n")
                report.append(f"  - Confidence: {entry['confidence']:.2f}\n")
                if entry.get("evidence"):
                    report.append(f"  - Evidence sources: {len(entry['evidence'])}\n")
                if entry.get("error_message"):
                    report.append(f"  - Error: {entry['error_message']}\n")
                report.append("\n")

        return "".join(report)

    def reset_verification_log(self):
        """Reset the verification log for a new session"""
        self.verification_log = []


# Singleton instance for easy access
_fact_checker_instance = None


def get_fact_checker() -> FactChecker:
    """
    Get or create the singleton FactChecker instance.

    Returns:
        FactChecker instance
    """
    global _fact_checker_instance
    if _fact_checker_instance is None:
        _fact_checker_instance = FactChecker()
    return _fact_checker_instance


async def verify_factual_claim(claim: str, context: str = None) -> FactCheckResult:
    """
    Convenience function to verify a single claim with error handling.

    Args:
        claim: The claim to verify
        context: Additional context

    Returns:
        FactCheckResult
    """
    try:
        checker = get_fact_checker()
        return await checker.verify_claim(claim, context)
    except Exception as e:
        logger.error(f"Error in convenience function verify_factual_claim: {e}")
        return FactCheckResult(
            claim=str(claim) if claim is not None else "None",
            status=VerificationStatus.SEARCH_FAILED,
            error_message=f"Convenience function error: {str(e)}",
        )


async def can_block_workflow(review_text: str, original_content: str = None) -> bool:
    """
    Determine if review feedback can block the workflow with error handling.

    Args:
        review_text: Review feedback
        original_content: Original content

    Returns:
        Whether the workflow can proceed (defaults to True on error)
    """
    try:
        checker = get_fact_checker()
        _, can_proceed = await checker.verify_review_feedback(review_text, original_content)
        return can_proceed
    except Exception as e:
        logger.error(f"Error in convenience function can_block_workflow: {e}")
        # Default to allowing workflow to proceed on error
        return True
