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


def handle_keys(keys):
    for key_entry in keys:
        match key_entry:
            case {"press": key}:
                if key.lower() == "winleft":
                    pyautogui.press("super")
                else:
                    pydirectinput.press(key.lower(), _pause=False)

            case {"combo": {"hold": hold_keys, "press": press_keys}}:
                for hold_key in hold_keys:
                    pydirectinput.keyDown(hold_key.lower(), _pause=False)
                for press_key in press_keys:
                    pydirectinput.press(press_key.lower(), _pause=False)
                for hold_key in hold_keys:
                    pydirectinput.keyUp(hold_key.lower(), _pause=False)

            case {"word": word}:
                pyautogui.write(word)

            case {"delay": delay_time}:
                sleep(float(delay_time))

            case _:
                print(f"Unknown key entry format: {key_entry}")

                

async def send_and_receive_messages(uri):
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to WebSocket server.")
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)

                    if data.get('event') == "tts":
                        text = data['data'].get("message")
                        volume = data['data'].get("volume")
                        if text is not None and volume is not None:
                            tts(text, volume)

                    elif data.get('event') == "keypress":
                        keys = data['data'].get("keys", [])
                        if keys:
                            handle_keys(keys)
            
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
    uri = os.getenv("WEBSOCKET_URI", "ws://localhost:8123/ws")
    await send_and_receive_messages(uri)

asyncio.run(main())
