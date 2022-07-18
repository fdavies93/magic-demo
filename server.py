import asyncio
import websockets
import json
from magic_io import RichText

JOIN = dict()
disconnecting = set()
connected = set()

async def parse(event, user):
    if event.get("type") == None:
        return
    if event["type"] == "disconnect":
        disconnecting.add(user)
    elif event["type"] == "message" and event.get("data") != None:
        print(str(event["data"]))

async def handler(websocket):
    connected.add(websocket)
    try:
        message = await websocket.recv()
        event = json.loads(message)

        assert event["type"] == "connect"

        user = event["user"]
        JOIN[event["user"]] = websocket

        print ( f"User {event.get('user')} connected to server." )

        while not (user in disconnecting):
            message = await websocket.recv()
            event = json.loads(message)
            await parse(event, user)

    finally:
        print (f"User {user} disconnecting from server.")
        await websocket.close()
        disconnecting.remove(user)
        connected.remove(websocket)
        del JOIN[event["user"]]
    
async def main():
    port = 8001
    async with websockets.serve(handler, "", port):
        print(f"Opening server on port {port}.")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())