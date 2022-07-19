import asyncio
from dataclasses import dataclass, asdict
from types import NoneType
import websockets
import json
from typing import Any, Union
from magic_io import RichText

JOIN : dict[str, Any] = dict()
disconnecting = set()
connected = set()
shutdown = False
to_send : asyncio.Queue["SendWrapper"] = asyncio.Queue()

@dataclass
class Output:
    type : str
    content : Union[RichText, str, list, NoneType]

@dataclass
class SendData:
    type: str
    data : Union[NoneType, Output]

@dataclass
class SendWrapper:
    user : str
    data : SendData

async def parse(event, user):
    if event.get("type") == None:
        return
    if event["type"] == "disconnect":
        disconnecting.add(user)
    elif event["type"] == "message" and event.get("data") != None:
        print(str(event["data"]))

# async def receive_loop():
#     receive_events = set()
#     while not shutdown:
#         done, pending = await asyncio.wait(receive_events, return_when=asyncio.FIRST_COMPLETED)

async def send_message_to(user, msg):
    if isinstance(msg, RichText):
        send_type = "RichText"
    elif isinstance(msg, str):
        send_type = "PlainText"
    elif isinstance(msg, list):
        send_type = "List"
    
    output = Output(send_type, msg)

    await to_send.put(SendWrapper(user, SendData("output", output)))

async def send_loop():
    while not shutdown:
        next_message = await to_send.get()
        print(next_message)
        await JOIN[next_message.user].send(json.dumps(asdict(next_message.data)))
        print("Successfully sent.")

async def handler(websocket):
    connected.add(websocket)
    try:
        message = await websocket.recv()
        event = json.loads(message)

        assert event["type"] == "connect"

        user = event["user"]
        JOIN[event["user"]] = websocket

        print ( f"User {event.get('user')} connected to server." )

        await send_message_to(user, RichText(f"Welcome to the server, {user}.", color=1, bold=True))

        # while user not in disconnecting:
        #     await asyncio.gather( [websocket.recv(), websocket.send()] )

        while not (user in disconnecting):
            message = await websocket.recv()
            event = json.loads(message)
            await parse(event, user)

    finally:
        print (f"User {user} disconnecting from server.")
        await websocket.close()
        disconnecting.remove(user)
        connected.remove(websocket)
        del JOIN[user]
    
async def main():
    port = 8001
    async with websockets.serve(handler, "", port):
        print(f"Opening server on port {port}.")
        asyncio.create_task(send_loop())
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())