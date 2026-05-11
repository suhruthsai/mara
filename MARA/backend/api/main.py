from fastapi import FastAPI
from fastapi.websockets import WebSocket
from pydantic import BaseModel
from ..agents.orchestrator import create_graph
import json

app = FastAPI()

graph = create_graph()

class ResearchRequest(BaseModel):
    query: str

@app.post("/research")
async def research(request: ResearchRequest):
    initial_state = {
        'query': request.query,
        'papers': [],
        'critiques': [],
        'hypotheses': [],
        'synthesis': '',
        'report': '',
        'confidence_score': 0.0,
        'iteration': 0,
        'status': 'Starting'
    }
    result = await graph.ainvoke(initial_state)
    return result

@app.websocket("/ws/research")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        query = data['query']
        initial_state = {
            'query': query,
            'papers': [],
            'critiques': [],
            'hypotheses': [],
            'synthesis': '',
            'report': '',
            'confidence_score': 0.0,
            'iteration': 0,
            'status': 'Starting'
        }
        async for update in graph.astream(initial_state):
            await websocket.send_json(update)
        await websocket.send_json({'status': 'completed'})
    except Exception as e:
        await websocket.send_json({'error': str(e)})
    finally:
        await websocket.close()