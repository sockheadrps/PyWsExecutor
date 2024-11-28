from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from fastapi import Request
from pydantic import BaseModel
import json

app = FastAPI()

# Store connections
active_connections = []

# Static file serving
app.mount("/static", StaticFiles(directory="static"), name="static")

# Template rendering
templates = Jinja2Templates(directory="templates")


# Pydantic Model for message request
class MessageRequest(BaseModel):
    message: str  # Only message, no voice anymore


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

            # Handle incoming message type (without voice now)
            if data.get("type") == "send_message":
                message = data.get("message")
                print(f"Message: {message}")

                # Broadcast the received message to all connected clients
                await manager.broadcast(f'{{"message": "{message}"}}')

            else:
                await manager.send_message(f"Server received message: {data}", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")


@app.get("/tts", response_class=HTMLResponse)
async def get_html_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/send-message")
async def send_message(request: MessageRequest):
    try:
        message = request.message  # Only the message now
        print(f"Message: {message}")

        # Broadcast the message to all connected clients
        await manager.broadcast(f'{{"message": "{message}"}}')

        return JSONResponse(content={"status": "Message sent successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send message")
