import asyncio
import base64
import functools
import json
import tempfile
from threading import Thread
import threading
import uuid
import cv2
from gtts import gTTS
import keyboard
import mss
import pyautogui
import rpaudio
import websockets
from PIL import Image, ImageGrab
import io
import time
from multiprocessing import Process, Queue
import numpy as np
from asyncio import Queue as AsyncQueue


media_stream_flag = True
key_listener_flag = True
media_stream_manager = None


def tts(text, volume):
    tts = gTTS(text)
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        filename = temp_file.name
        tts.save(filename)
        sound = rpaudio.AudioSink().load_audio(filename)
        volume = float(volume)
        sound.set_volume(volume)
        sound.play()


class KeyListener:
    def __init__(self, keystroke_queue):
        self.listener_thread = None
        self.keystroke_queue = keystroke_queue

    def listen_for_keys(self, keystroke_queue):
        def on_key_press(event):
            global key_listener_flag
            if key_listener_flag:
                keystroke_queue.put_nowait(event.name)

        keyboard.on_press(on_key_press)

    def stop_listening(self):
        keyboard.unhook_all()

    def start_listening(self):
        self.listener_thread = Thread(
            target=self.listen_for_keys, args=(self.keystroke_queue,), daemon=True)
        self.listener_thread.start()

    async def keystroke_loop(self):
        while True:
            await asyncio.sleep(0.1)
            while not self.keystroke_queue.empty():
                key = await self.keystroke_queue.get()
                return key


def track_first_call(func):
    """Decorator to track if it's the first time the function has been called
       since global media_stream_flag was set to True.
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        global media_stream_flag

        if media_stream_flag and not self.first_call_since_flag_set:
            self.first_call_since_flag_set = True
            print("Sending stream_begin")
            screenshot = await func(self, *args, **kwargs)
            await self.websocket.send(json.dumps({
                "event": "stream_begin",
                "data": {"client_id": self.client_id,
                         "frame": screenshot}
            }))

            return await func(self, *args, **kwargs)

        elif media_stream_flag and self.first_call_since_flag_set:
            return await func(self, *args, **kwargs)

        elif not media_stream_flag:
            self.first_call_since_flag_set = False
            return None

    return wrapper


class WebSocketClient:
    def __init__(self, uri, websocket_rx_queue):
        self.uri = uri
        self.client_id = str("boo")
        self.websocket_rx_queue = websocket_rx_queue
        self.first_call_since_flag_set = False

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        await self.websocket.send(json.dumps({"event": "connect", "data": {"client_type": "client", "client_id": self.client_id}}))

    async def send_keystroke(self, key):
        await self.websocket.send(json.dumps({"event": "keystroke", "data": {"key": key}}))

    @track_first_call
    async def send_screenshot(self, screenshot):
        await self.websocket.send(json.dumps({"event": "stream_data", "data": {"frame": screenshot, "client_id": self.client_id}}))

    async def listen_loop(self):
        while True:
            await asyncio.sleep(0.1)
            message = await self.websocket.recv()
            self.websocket_rx_queue.put_nowait(json.loads(message))


class StreamManager:
    def __init__(self):
        self.run_stream = asyncio.Event()  # Controls whether to capture or not
        self.run_stream.set()  # Allow capturing by default

    async def capture_and_compress(self, queue: Queue, initial_interval=0.2):
        loop = asyncio.get_running_loop()  # Reuse the event loop
        while True:
            if not self.run_stream.is_set():  # Pause capturing if the event is cleared
                await asyncio.sleep(initial_interval)
                continue

            # Capture the screen in a thread-safe manner
            frame = await loop.run_in_executor(None, self.capture_screen)

            # Resize the frame immediately during capture if possible
            frame = cv2.resize(frame, (1920//2, 1080//2)
                               )  # Adjust size of image

            # Compress the frame to JPEG
            success, buffer = cv2.imencode(
                ".webp", frame, [int(cv2.IMWRITE_WEBP_QUALITY), 70])
            if not success:
                print("Error encoding image.")
                continue

            # Encode to Base64 for transmission
            base64_frame = base64.b64encode(buffer).decode("utf-8")

            # Put the encoded frame into the queue
            try:
                await queue.put(base64_frame)
            except asyncio.QueueFull:
                print("Queue is full, skipping frame.")

            await asyncio.sleep(initial_interval)

    def capture_screen(self):
        """Capture a single screenshot."""
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            # Remove alpha channel
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    async def start_capture(self, queue: Queue, initial_interval=0.2):
        """Start the capture loop."""
        await self.capture_and_compress(queue, initial_interval)

    # Method to control when to start or stop capturing
    def set_media_stream_flag(self, flag):
        if flag:
            self.run_stream.set()  # Allow screenshot capture
        else:
            self.run_stream.clear()  # Stop screenshot capture


async def process_queues(key_listener, websocket_rx_queue, screenshot_queue, websocket_client):
    global key_listener_flag
    global media_stream_flag
    global media_stream_manager

    while True:
        if not key_listener.keystroke_queue.empty():
            key = await key_listener.keystroke_queue.get()
            await websocket_client.send_keystroke(key)
        if not screenshot_queue.empty():
            if not media_stream_flag:
                while not screenshot_queue.empty():
                    screenshot_queue.get_nowait()
            else:
                screenshot = screenshot_queue.get_nowait()
                if screenshot is not None:
                    await websocket_client.send_screenshot(screenshot)

        if not websocket_rx_queue.empty():
            ws_rx_message = await websocket_rx_queue.get()
            if ws_rx_message.get("event") == "tts":
                tts(ws_rx_message.get("data").get("text"),
                    ws_rx_message.get("data").get("volume"))
            elif ws_rx_message.get("event") == "media_stream":
                media_stream_flag = ws_rx_message.get(
                    "data").get("media_stream")
                media_stream_manager.set_media_stream_flag(media_stream_flag)
            elif ws_rx_message.get("event") == "key_listener":
                key_listener_flag = ws_rx_message.get(
                    "data").get("key_listener")
            print(f"Received WebSocket message: {ws_rx_message}")

        await asyncio.sleep(0.1)


async def main():
    global media_stream_manager
    key_queue = AsyncQueue()
    key_listener = KeyListener(key_queue)
    key_listener.start_listening()

    websocket_rx_queue = AsyncQueue()
    websocket_client = WebSocketClient(
        "ws://localhost:8122/ws", websocket_rx_queue)
    await websocket_client.connect()
    asyncio.create_task(websocket_client.listen_loop())

    media_stream_manager = StreamManager()
    media_stream_manager.set_media_stream_flag(True)
    screenshot_queue = AsyncQueue()
    capture_task = asyncio.create_task(media_stream_manager.capture_and_compress(
        screenshot_queue))

    queue_task = asyncio.create_task(process_queues(
        key_listener, websocket_rx_queue, screenshot_queue, websocket_client))

    await asyncio.gather(capture_task, queue_task)
    capture_task.cancel()
    queue_task.cancel()
    key_listener.stop_listening()
    await websocket_client.close()
    await asyncio.gather(capture_task, queue_task, return_exceptions=True)


if __name__ == '__main__':
    asyncio.run(main())
    loop = asyncio.get_event_loop()
    for task in asyncio.all_tasks(loop):
        task.cancel()
    loop.close()
