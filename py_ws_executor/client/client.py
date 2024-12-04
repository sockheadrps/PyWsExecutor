import asyncio
import websockets
import json
from gtts import gTTS
import rpaudio
import pydirectinput
from time import sleep
import pyautogui
from dotenv import load_dotenv
import os
from py_ws_executor.models import PressAction, ComboAction, WordAction, DelayAction, WsEvent
from datetime import datetime
import tempfile
import os
import requests
import aiohttp

load_dotenv() 
uri = os.getenv("WEBSOCKET_URIS", "ws://localhost:8123/ws")


async def screen_shot():
    global uri
    http_uri = uri.replace('ws:', 'http:')
    http_uri = http_uri.replace('/ws', "")
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    screenshot = pyautogui.screenshot()
    
    temp_fd, temp_path = tempfile.mkstemp(suffix='.webp', prefix=f'screenshot_{date}_')
    
    try:
        screenshot.save(temp_path, format='webp')
        print(f"Taking screenshot at {date}, saved to {temp_path}")
        
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            with open(temp_path, 'rb') as f:
                data.add_field('file', f)
                data.add_field('pin', '1234')
            
                async with session.post(http_uri + '/upload', data=data) as response:
                    if response.status == 200:
                        print("Screenshot uploaded successfully")
                    else:
                        print(f"Failed to upload screenshot: {await response.text()}")
                    
    finally:
        os.close(temp_fd)
        try:
            os.remove(temp_path)
        except PermissionError:
            print(f"Could not remove temporary file {temp_path}")



def handle_keys(keys):
    for key_entry in keys:
        match key_entry:
            case PressAction(press=key):
                pydirectinput.press(key.lower())
            case ComboAction(hold=hold_keys, press=press_keys):
                for hold_key in hold_keys:
                    pydirectinput.keyDown(hold_key.lower())
                for press_key in press_keys:
                    pydirectinput.press(press_key.lower())
                for hold_key in hold_keys:
                    pydirectinput.keyUp(hold_key.lower())
            case WordAction(word=word):
                pyautogui.write(word)
            case DelayAction(delay=delay_time):
                sleep(float(delay_time))
            case _:
                print(f"Unknown key entry format in handle_keys: {key_entry}")


async def send_and_receive_messages(uri):
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to WebSocket server.")
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    ws_data = WsEvent(**data)

                    match ws_data.event:
                        case "tts":
                            tts(ws_data.data.message, ws_data.data.volume)
                        case "keypress":
                            handle_keys(ws_data.data.keys)
                        case "screenshot":
                            await screen_shot()

            
        except (websockets.ConnectionClosedError, websockets.InvalidStatusCode):
            print("Connection failed. Retrying in 15 seconds...")
            await asyncio.sleep(15)


def tts(text, volume):
    try:
        tts = gTTS(text)
        filename = f"tts_output.mp3" 
        tts.save(filename)
        sound = rpaudio.AudioSink().load_audio(filename)
        volume = float(volume)
        sound.set_volume(volume)
        sound.play()
    except Exception as e:
        print(f"Error generating audio: {e}")

async def main():
    load_dotenv() 
    uri = os.getenv("WEBSOCKET_URIS", "ws://localhost:8123/ws")
    await send_and_receive_messages(uri)

# asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())