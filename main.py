from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Union
from pydantic import BaseModel, Field, ValidationError
from fastapi import Request
import json
import uvicorn
from models import PressAction, ComboAction, WordAction, DelayAction, WsEvent, TTSData, EventData

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

active_connections = []

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_json(json.loads(message))

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
                try:
                    event = WsEvent(**data)
                    await manager.broadcast(event.model_dump_json())
                except ValidationError as e:
                    await manager.send_message(f"Validation error: {e.json()}", websocket)
            except json.JSONDecodeError:
                await manager.send_message("Error: Received invalid JSON", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def validate_ws_event(request: WsEvent):
    event = request.event
    data = request.data

    match event:
        case "keypress":
            if not isinstance(data, EventData):
                raise HTTPException(status_code=422, detail="Invalid data for event 'keypress'. Expected EventData.")
        case "tts":
            if not isinstance(data, TTSData):
                raise HTTPException(status_code=422, detail="Invalid data for event 'tts'. Expected TTSData.")
        case _:
            raise HTTPException(status_code=422, detail=f"Invalid event: {event}. Allowed events are ['keypress', 'tts'].")

    return request

@app.get("/tts", response_class=HTMLResponse)
async def get_html_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/send-event")
async def send_event(request: WsEvent = Depends(validate_ws_event)):
    try:
        await manager.broadcast(request.model_dump_json())  
        return {"status": "Event sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send event: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8123)
