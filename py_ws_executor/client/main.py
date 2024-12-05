import asyncio
from PIL import Image, ImageGrab
import io
import time
from collections import deque
from multiprocessing import Process, Queue
import websockets
import uuid
import json
import base64
import json
from gtts import gTTS
import rpaudio
import pydirectinput
import pyautogui
from dotenv import load_dotenv
import os
from py_ws_executor.models import PressAction, ComboAction, WordAction, DelayAction, WsEvent
from datetime import datetime
import tempfile
import aiohttp
from threading import Thread
import keyboard
from queue import Queue
import uuid
import cv2
import numpy as np
from asyncio import Queue as AsyncQueue, QueueEmpty
from time import sleep
import mss

class StreamManager:
    def __init__(self):
        self.run_stream = asyncio.Event()  # Controls whether to capture or not
        self.run_stream.set()  # Allow capturing by default

    async def capture_and_compress(self, queue: Queue, initial_interval=0.2):
        while True:
            if not self.run_stream.is_set():  # Pause capturing if the event is cleared
                await asyncio.sleep(initial_interval)
                continue
            
            # Capture the screen in a thread-safe manner
            loop = asyncio.get_event_loop()
            frame = await loop.run_in_executor(None, self.capture_screen)
            
            # Compress the frame to JPEG
            _, buffer = cv2.imencode(".jpg", frame)
            
            # Encode to Base64 for transmission
            base64_frame = base64.b64encode(buffer).decode("utf-8")
            
            # Put the encoded frame into the queue
            await queue.put(base64_frame)

            # Display the frame (for debugging purposes)
            cv2.imshow("Desktop Capture", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.run_stream.clear()  # Stop capturing if 'q' is pressed
            
            await asyncio.sleep(initial_interval)

    def capture_screen(self):
        """Capture a single screenshot."""
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            # Convert screenshot to NumPy array (BGR format for OpenCV)
            frame = np.array(screenshot)
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # Remove alpha channel

    async def start_capture(self, queue: Queue, initial_interval=0.2):
        """Start the capture loop."""
        await self.capture_and_compress(queue, initial_interval)



class Client:
    def __init__(self):
        self.websocket_client = ClientWebSocket("ws://localhost:8123/ws")
        self.queue = AsyncQueue()  # Use AsyncQueue instead of Queue
        self.stream_manager = StreamManager()
        self.stream_process = None
        self.keystroke_queue = Queue()
        self.key_listener = KeyListener()
        self.loop = asyncio.get_event_loop()
        self.active_tasks = []

    async def start_stream(self):
        self.stream_process = Process(target=self.stream_manager.capture_screen, args=())
        self.stream_process.start()

    async def stop_stream(self):
        self.stream_manager.run_stream = False
        if self.stream_process:
            self.stream_process.terminate()
            self.stream_process.join()

    async def start_key_listener(self):
        self.key_listener.start_listening(self.keystroke_queue)

    async def stop_key_listener(self):
        self.key_listener.stop_listening()

    async def yield_frame(self):
        while True:
            # Wait for a frame to be put in the queue
            print(f"Queue size: {self.queue.qsize()}")
            frame = await self.queue.get()  # Use await with AsyncQueue.get()

            if frame is None:
                print("End of stream reached.")
                break

            print(f"Yielding frame, frame size: {len(frame.getvalue())} bytes")
            yield frame  # Yield the frame for processing

    async def process_frames(self):
        async for frame in self.yield_frame():  # Use async for to iterate over async generator
            base64_frame = base64.b64encode(frame.getvalue()).decode('utf-8')
            await self.websocket_client.send_frame(base64_frame)
            print(f"Sent frame of size: {len(base64_frame)} bytes")
    
    async def start_services(self):
        """
        Start all services: streaming, key listener, and WebSocket handling.
        """
        # Start the stream process
        # await client.start_stream()

        # Start the key listener
        # key_listener_task = self.loop.create_task(self.start_key_listener())
        # self.active_tasks.append(key_listener_task)

        # Connect to WebSocket
        await self.websocket_client.connect()

        while True:
            try:
                key = await asyncio.get_event_loop().run_in_executor(None, self.keystroke_queue.get_nowait)
                print(f"Key pressed: {key}")
            except QueueEmpty:
                pass
            async for frame in client.yield_frame():
                print(f"Processing frame of size: {len(frame.getvalue())} bytes")
                base64_frame = base64.b64encode(frame.getvalue()).decode('utf-8')
                await self.websocket_client.send_frame(base64_frame)
            await asyncio.sleep(1)

    async def stop_services(self):
        """
        Stop all services and clean up resources.
        """
        await self.stop_stream()
        await self.stop_key_listener()
        await self.websocket_client.close()

        # Cancel any remaining tasks
        for task in self.active_tasks:
            task.cancel()

    def run(self):
        self.loop.run_until_complete(self.start_services())
        self.loop.run_until_complete(self.stop_services())
        print("Services stopped. Exiting...")
        self.loop.close()


class ClientWebSocket:
    def __init__(self, uri):
        self.id = str(uuid.uuid4())
        self.uri = uri
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        
        connect_event = {
            "event": "connect",
            "data": {
                "client_type": "client",
                "client_id": self.id,
            }
        }
        await self.websocket.send(json.dumps(connect_event))

    async def send_frame(self, frame_data):
        if self.websocket:
            message = {
                "event": "frame",
                "data": {
                    "frame": frame_data,
                    "timestamp": time.time()
                }
            }
            await self.websocket.send(json.dumps(message))

    async def close(self):
        if self.websocket:
            await self.websocket.close()


class KeyListener:
    def __init__(self):
        self.listener_thread = None
        self.keystroke_queue = None

    def listen_for_keys(self, keystroke_queue):
        def on_key_press(event):
            keystroke_queue.put_nowait(event.name)

        keyboard.on_press(on_key_press)

    def stop_listening(self):
        keyboard.unhook_all()

    def start_listening(self, keystroke_queue):
        self.keystroke_queue = keystroke_queue
        self.listener_thread = Thread(target=self.listen_for_keys, args=(keystroke_queue,), daemon=True)
        self.listener_thread.start()

    async def keystroke_loop(self):
        while True:
            await asyncio.sleep(0.1)
            while not self.keystroke_queue.empty():
                key = await self.keystroke_queue.get()
                return key


async def main():
    client = Client()
    client.websocket_client.uri = "ws://localhost:8122/ws"
    await client.start_stream()
    await client.start_key_listener()
    await client.websocket_client.connect()
    await client.process_frames()

    if client.stream_process and client.stream_process.is_alive():
        client.stream_process.terminate()
        client.stream_process.join()


if __name__ == "__main__":
    asyncio.run(main())
