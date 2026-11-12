import os

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..agents.orchestrator import create_graph
from ..agents.state import initial_state

app = FastAPI(title="MARA - Multi-Agent Research Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = create_graph()

class ResearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/research")
async def research(request: ResearchRequest):
    try:
        return await graph.ainvoke(initial_state(request.query.strip()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/research")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        query = str(data.get('query', '')).strip()
        if len(query) < 3:
            await websocket.send_json({'error': 'Query must be at least 3 characters.'})
            return

        state = initial_state(query)
        await websocket.send_json({'node': 'start', **state})
        # each update is {node_name: new_state}; forward the merged state so the UI always has a flat view
        async for update in graph.astream(state, stream_mode="updates"):
            for node, node_state in update.items():
                state = {**state, **node_state}
                await websocket.send_json({'node': node, **state})
        await websocket.send_json({**state, 'node': 'done', 'status': 'completed'})
    except WebSocketDisconnect:
        return
    except Exception as e:
        await websocket.send_json({'error': str(e)})
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass
