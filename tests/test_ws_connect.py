
import asyncio
import websockets
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from config import settings

async def test_websocket():
    uri = f"ws://localhost:{settings.PORT}/api/ws/stream"
    print(f"Attempting to connect to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connection successful!")
            
            # Send dummy data
            await websocket.send(b"test_image_data")
            print("Sent test data")
            
            # Receive response
            response = await websocket.recv()
            print(f"Received response: {response}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
