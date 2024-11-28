from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from fastapi import Request
from pydantic import BaseModel
import json
import uvicorn


app = FastAPI()

# Store connections
active_connections = []

# Static file serving
app.mount("/static", StaticFiles(directory="static"), name="static")

# Template rendering
templates = Jinja2Templates(directory="templates")


# Pydantic Model for event request
class EventRequest(BaseModel):
    event: str  # Event name
    data: dict  # Associated data for the event


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from client: {data}")

            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_message("Error: Received invalid JSON", websocket)
                continue

            # Handle incoming event (general structure now)
            event = data.get("event")
            if event:
                event_data = data.get("data", {})
                print(f"Event: {event}, Data: {event_data}")

                # Broadcast the event and its data to all connected clients
                await manager.broadcast(json.dumps({"event": event, "data": event_data}))

            else:
                await manager.send_message(f"Error: Invalid event format", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")


@app.get("/tts", response_class=HTMLResponse)
async def get_html_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/send-event")
async def send_event(request: EventRequest):
    try:
        event = request.event
        data = request.data
        
        print(f"Event: {event}, Data: {data}")

        # Broadcast the event to all connected clients
        await manager.broadcast(json.dumps({"event": event, "data": data}))

        return JSONResponse(content={"status": "Event sent successfully"})
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send event")


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8123, reload=True)