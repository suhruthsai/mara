from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    query: str
    search_query: str
    papers: List[Dict[str, Any]]
    critiques: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    synthesis: str
    report: str
    confidence_score: float
    iteration: int
    status: str

MAX_ITERATIONS = 3
CONFIDENCE_THRESHOLD = 0.65

def initial_state(query: str) -> AgentState:
    return {
        'query': query,
        'search_query': query,
        'papers': [],
        'critiques': [],
        'hypotheses': [],
        'synthesis': '',
        'report': '',
        'confidence_score': 0.0,
        'iteration': 0,
        'status': 'Starting'
    }
