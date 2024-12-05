import asyncio
import base64
import websockets
import json

# WebSocket server to test with
async def handle_connection(websocket):
    print(f"Client connected: {websocket.remote_address}")

    # Send a welcome message when a client connects
    connect_event = {
        "event": "connect",
        "data": {
            "message": "Welcome to the WebSocket server!",
        }
    }
    tts_event = {
        "event": "tts",
        "data": {
            "text": "Hello, how are you?",
            "volume": 0.5,
        }
    }
    media_stream_event = {
        "event": "media_stream",
        "data": {
            "media_stream": True,
        }
    }
    key_listener_event = {
        "event": "key_listener",
        "data": {
            "key_listener": True,
        }
    }
    await websocket.send(json.dumps(connect_event))
    # await websocket.send(json.dumps(tts_event))
    await websocket.send(json.dumps(media_stream_event))    
    await websocket.send(json.dumps(key_listener_event))
    first_screenshot_sent = False
    try:
        # Listen for messages from the client
        async for message in websocket:
            print(f"Received message from client: {message}")

            # Respond with an acknowledgment message
            response = {
                "event": "acknowledgment",
                "data": {
                    "message": "Message received",
                    "client_message": "message",
                }
            }
            message = json.loads(message)
            if message["event"] == "stream_data":
                await websocket.send(json.dumps(response))

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print(f"Client disconnected: {websocket.remote_address}")

# Start the server
async def main():
    # Start the WebSocket server on ws://localhost:8765
    server = await websockets.serve(handle_connection, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
