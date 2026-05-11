from langgraph import StateGraph
from .state import AgentState
from .specialist_agents import search_agent, critic_agent, synthesis_agent, writer_agent, hypothesis_agent

async def reflection_agent(state: AgentState) -> AgentState:
    if state['confidence_score'] < 0.65 and state['iteration'] < 3:
        return {**state, 'iteration': state['iteration'] + 1, 'status': 'Reflecting, low confidence'}
    else:
        return {**state, 'status': 'Confidence sufficient'}

def create_graph():
    graph = StateGraph(AgentState)
    graph.add_node("search", search_agent)
    graph.add_node("critic", critic_agent)
    graph.add_node("synthesis", synthesis_agent)
    graph.add_node("writer", writer_agent)
    graph.add_node("hypothesis", hypothesis_agent)
    graph.add_node("reflection", reflection_agent)

    graph.set_entry_point("search")
    graph.add_edge("search", "critic")
    graph.add_edge("critic", "synthesis")
    graph.add_edge("synthesis", "reflection")
    graph.add_conditional_edges("reflection", lambda s: "search" if s['iteration'] < 3 and s['confidence_score'] < 0.65 else "writer", {"search": "search", "writer": "writer"})
    graph.add_edge("writer", "hypothesis")
    graph.set_finish_point("hypothesis")

    return graph.compile()