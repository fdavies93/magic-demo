import asyncio
from dataclasses import dataclass, asdict
from multiprocessing.sharedctypes import Value
from types import NoneType
import websockets
import json
from typing import Any, Union
from client import connect
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
        # print(str(event["data"]))
        await send_message_all([RichText(f"{user}: ", 1), event["data"]])

# async def receive_loop():
#     receive_events = set()
#     while not shutdown:
#         done, pending = await asyncio.wait(receive_events, return_when=asyncio.FIRST_COMPLETED)

def format_message(msg):
    if isinstance(msg, RichText):
        return Output("RichText", msg)
    elif isinstance(msg, str):
        return Output("PlainText", msg)
    elif isinstance(msg, list):
        return Output("List", [ format_message(item) for item in msg ])

async def send_message_websocket(socket, msg):
    out = format_message(msg)
    await socket.send(json.dumps(asdict(SendData("output",out))))

async def send_message_to(user, msg):
    output = format_message(msg)

    await to_send.put(SendWrapper(user, SendData("output", output)))

async def send_message_all(msg):
    output = format_message(msg)

    for user in JOIN:
        await to_send.put(SendWrapper(user, SendData("output", output)))

async def send_loop():
    while not shutdown:
        next_message = await to_send.get()
        print(next_message)
        await JOIN[next_message.user].send(json.dumps(asdict(next_message.data)))
        print("Successfully sent.")

async def handler(websocket):
    try:
        message = await websocket.recv()
        event = json.loads(message)

        assert event["type"] == "connect"

        user = event["user"]

        if user in JOIN:
            await send_message_websocket(websocket, f"Username {user} already exists on this server, please try logging on again with a different username.")
            await websocket.send(json.dumps(asdict(SendData("disconnect", None))))
            raise ValueError

        connected.add(websocket)
        JOIN[event["user"]] = websocket
        print ( f"User {event.get('user')} connected to server." )

        await send_message_all(RichText(f"Welcome to the server, {user}.", color=1, bold=True))

        while not (user in disconnecting):
            message = await websocket.recv()
            event = json.loads(message)
            await parse(event, user)

    finally:
        print (f"User {user} disconnecting from server.")
        await websocket.close()
        if user in disconnecting:
            # don't do any if not true, because this is an error
            disconnecting.remove(user)
            del JOIN[user]
        if websocket in connected:
            connected.remove(websocket)        
    
async def main():
    port = 8001
    async with websockets.serve(handler, "", port):
        print(f"Opening server on port {port}.")
        asyncio.create_task(send_loop())
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())