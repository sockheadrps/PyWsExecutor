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
from models import PressAction, ComboAction, WordAction, DelayAction, WsEvent


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
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    ws_data = WsEvent(**data)

                    match ws_data.event:
                        case "tts":
                            tts(ws_data.data.message, ws_data.data.volume)
                        case "keypress":
                            handle_keys(ws_data.data.keys)

            
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

asyncio.run(main())
