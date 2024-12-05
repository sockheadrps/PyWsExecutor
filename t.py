import base64
import time
import cv2
import numpy as np
import pyautogui
import asyncio
from asyncio import sleep, Queue

queue = Queue()
def capture_screen():
    screenshot = pyautogui.screenshot()
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return frame


def compress_frame(frame, quality=70):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    result, encoded_frame = cv2.imencode('.jpg', frame, encode_param)
    return encoded_frame.tobytes()


async def capture_and_compress():
    for i in range(100):
        loop = asyncio.get_event_loop()
        frame = await loop.run_in_executor(None, capture_screen)
        compressed_frame = await loop.run_in_executor(None, compress_frame, frame)
        frame_base64 = base64.b64encode(compressed_frame).decode("utf-8")
        await queue.put(frame_base64)
        await asyncio.sleep(0.1)  # Add small delay between captures


# read from queue and decompress
async def read_from_queue():
    while True:  # Keep checking for new items
        try:
            frame_base64 = await queue.get()
            print(len(frame_base64))
        except asyncio.QueueEmpty:
            break


async def main():
            # Create a thread for screen capture and compression
    # Run both coroutines concurrently
    await asyncio.gather(
        capture_and_compress(),
        read_from_queue()
    )

asyncio.run(main())
