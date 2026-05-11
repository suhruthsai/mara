from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    query: str
    papers: List[Dict[str, Any]]
    critiques: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    synthesis: str
    report: str
    confidence_score: float
    iteration: int
    status: str