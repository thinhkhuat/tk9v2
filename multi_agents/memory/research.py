import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class ResearchState(TypedDict, total=False):
    task: Dict[str, Any]
    initial_research: str
    sections: List[str]
    research_data: List[Dict[str, Any]]
    human_feedback: Optional[str]
    # Report layout
    title: str
    headers: Dict[str, str]
    date: str
    table_of_contents: str
    introduction: str
    conclusion: str
    sources: List[str]
    report: str
    # Additional fields for workflow state
    draft: Optional[str]
    revision_notes: Optional[str]
    review: Optional[str]
    translation_result: Optional[Dict[str, Any]]
    revision_count: Annotated[int, operator.add]  # Initialize to 0, increment on each revision
