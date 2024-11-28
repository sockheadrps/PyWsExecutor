import asyncio
import websockets
import json
from gtts import gTTS
import rpaudio

async def send_and_receive_messages(uri):
    """
    Connects to the WebSocket server, sends a message, and listens for responses.
    If the connection is lost, it will attempt to reconnect indefinitely.
    """
    while True:
        try:
            # Attempt to connect to the WebSocket server
            async with websockets.connect(uri) as websocket:
                print("Connected to WebSocket server.")
                while True:
                    try:
                        response = await websocket.recv()
                        print("Received from server:", response)

                        # Check if the message contains a "message" field
                        data = json.loads(response)
                        if "message" in data:
                            text = data["message"]
                            save_audio_file(text)

                    except websockets.ConnectionClosed:
                        print("Connection closed. Reconnecting...")
                        break  
            
        except (websockets.ConnectionClosedError, websockets.InvalidStatusCode):
            print("Connection failed. Retrying in 15 seconds...")
            await asyncio.sleep(15)

def save_audio_file(text):
    """
    Converts the provided text to speech and saves it as an MP3 file.
    """
    try:
        tts = gTTS(text)
        filename = f"tts_output.mp3" 
        tts.save(filename)
        sound = rpaudio.AudioSink().load_audio(filename)
        sound.play()
        print(f"Audio saved as {filename}")
    except Exception as e:
        print(f"Error generating audio: {e}")

async def main():
    uri = "ws://tts.socksthoughtshop.lol/ws"  
    await send_and_receive_messages(uri)

asyncio.run(main())
