from langgraph.graph import StateGraph, END
from .state import AgentState
from .specialist_agents import (
    search_agent, critic_agent, synthesis_agent, reflection_agent, writer_agent, hypothesis_agent
)

def route_after_reflection(state: AgentState) -> str:
    # reflection_agent only changes the search query when it wants another pass
    return "search" if state['status'].startswith('Reflecting') else "writer"

def create_graph():
    graph = StateGraph(AgentState)
    graph.add_node("search", search_agent)
    graph.add_node("critic", critic_agent)
    graph.add_node("synthesis", synthesis_agent)
    graph.add_node("reflection", reflection_agent)
    graph.add_node("writer", writer_agent)
    graph.add_node("hypothesis", hypothesis_agent)

    graph.set_entry_point("search")
    graph.add_edge("search", "critic")
    graph.add_edge("critic", "synthesis")
    graph.add_edge("synthesis", "reflection")
    graph.add_conditional_edges("reflection", route_after_reflection, {"search": "search", "writer": "writer"})
    graph.add_edge("writer", "hypothesis")
    graph.add_edge("hypothesis", END)

    return graph.compile()
