from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from fastapi import Request
from pydantic import BaseModel
import json
import uvicorn
import os


app = FastAPI()

active_connections = []

app.mount("/static", StaticFiles(directory="py_ws_executor/server/static"), name="static")

templates = Jinja2Templates(directory="py_ws_executor/server/templates")

# Security configuration
UPLOAD_PIN = "1234"  # In production, use environment variables for this


class EventRequest(BaseModel):
    event: str  
    data: dict  


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
            try:
                data = await websocket.receive_json()
                event = data.get("event")
                if event:
                    event_data = data.get("data", {})

                    await manager.broadcast(json.dumps({"event": event, "data": event_data}))
                else:
                    await manager.send_message("Error: Invalid event format", websocket)
            except json.JSONDecodeError:
                await manager.send_message("Error: Received invalid JSON", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)



@app.get("/tts", response_class=HTMLResponse)
async def get_html_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/send-event")
async def send_event(request: EventRequest):
    try:
        event = request.event
        data = request.data
        
        await manager.broadcast(json.dumps({"event": event, "data": data}))

        return JSONResponse(content={"status": "Event sent successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send event")


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    pin: str = Form(...),
):
    if pin != UPLOAD_PIN:
        raise HTTPException(status_code=403, detail="Invalid PIN")
        
    try:
        upload_dir = "py_ws_executor/server/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return JSONResponse(content={
            "status": "success",
            "message": "File uploaded successfully",
            "filename": file.filename
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8123)