import asyncio
import websockets
import json
from gtts import gTTS
import rpaudio
import pydirectinput
from time import sleep
import pyautogui

def handle_keys(keys):
    """
    Processes the `keys` array, handling both single key presses and combos.
    """
    for key_entry in keys:
        if "press" in key_entry:
            key = key_entry["press"].lower()
            pydirectinput.press(key, _pause=False)

        elif "combo" in key_entry:
            combo = key_entry["combo"]
            hold_keys = combo.get("hold", [])
            press_keys = combo.get("press", [])

            for hold_key in hold_keys:
                pydirectinput.keyDown(hold_key.lower(), _pause=False)

            for press_key in press_keys:
                pydirectinput.press(press_key.lower(), _pause=False)

            for hold_key in hold_keys:
                pydirectinput.keyUp(hold_key.lower(), _pause=False)

        elif "word" in key_entry:
            word = key_entry["word"]
            pyautogui.write(word)
        
        elif "delay" in key_entry:
            delay_time = float(key_entry["delay"])  
            sleep(delay_time)
                

async def send_and_receive_messages(uri):
    """
    Connects to the WebSocket server, sends a message, and listens for responses.
    If the connection is lost, it will attempt to reconnect indefinitely.
    """
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to WebSocket server.")
                while True:
                    response = await websocket.recv()
                    print("Received from server:", response)

                    # Parse the incoming JSON message
                    data = json.loads(response)

                    if data.get('event') == "tts":
                        text = data['data'].get("message")
                        volume = data['data'].get("volume")
                        if text is not None and volume is not None:
                            tts(text, volume)

                    # Handle keypress events
                    elif data.get('event') == "keypress":
                        keys = data['data'].get("keys", [])
                        if keys:
                            handle_keys(keys)
            
        except (websockets.ConnectionClosedError, websockets.InvalidStatusCode):
            print("Connection failed. Retrying in 15 seconds...")
            await asyncio.sleep(15)

def tts(text, volume):
    """
    Converts the provided text to speech and saves it as an MP3 file.
    """
    try:
        tts = gTTS(text)
        filename = f"tts_output.mp3" 
        tts.save(filename)
        print(f"Audio saved as {filename}")
        sound = rpaudio.AudioSink().load_audio(filename)
        volume = float(volume)
        sound.set_volume(volume)
        sound.play()
    except Exception as e:
        print(f"Error generating audio: {e}")

async def main():
    uri = "ws://tts.socksthoughtshop.lol/ws"  
    # uri = "ws://localhost:8123/ws"  
    await send_and_receive_messages(uri)

asyncio.run(main())
