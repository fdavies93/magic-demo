import asyncio
from dataclasses import dataclass, asdict
from multiprocessing.sharedctypes import Value
from types import NoneType
import bcrypt
import websockets
import json
from typing import Any, Union
from client import connect
from interfaces.magic_io import RichText
from interfaces.NetIO import NetIO
from magic_rpg import Game, GameObject
from game.setup import game_setup, game_state_save, game_state_load
from game.utilities import create_object, get_first_with_name

JOIN : dict[str, Any] = dict()
disconnecting = set()
connected = set()
shutdown = False
to_send : asyncio.Queue["SendWrapper"] = asyncio.Queue()
gm = Game(0.5)
user_data : dict[str, "UserData"] = dict()

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

@dataclass
class UserData:
    name : str
    pass_hash : str
    data : dict

async def parse(event, user):
    if event.get("type") == None:
        return
    if event["type"] == "disconnect":
        disconnecting.add(user)
    elif event["type"] == "message" and event.get("data") != None:
        # print(str(event["data"]))
        await net_io.parse(event["data"], user)
        # await send_message_all([RichText(f"{user}: ", 1), event["data"]])

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

def load_user_data(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)    
        for user in data:
            username = user.get("name")
            
            if username == None:
                continue

            user_data[username] = UserData(username, user.get("pass_hash"), user.get("data"))

def update_user_data(name, new_data):
    # this is an update function; don't allow creation of arbitrary data
    user = user_data.get(name)
    if user == None:
        return
    user.data = new_data    

def save_user_data(filepath):
    users = []
    for user in user_data.values():
        users.append(asdict(user))
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(users, f)

async def game_loop():
    # net_io = NetIO(gm.parse, send_message_to)
    try:
        print(net_io)
        gm.set_interface(net_io)
        print("Loading game state.")
        load_user_data("users.json")
        game_state_load(gm, "last_quit.json")
        print("Starting main game loop.")
        # game_setup(gm) # should probably hook into game.before_first_tick
        while not shutdown:
            await gm.tick()
    finally:
        save_user_data("users.json")

net_io : NetIO = NetIO(gm.parse, send_message_to, update_user_data)
# on receive a message -> send to game to be parsed
# on output -> add message to send loop

async def send_loop():
    while not shutdown:
        try:
            next_message = await to_send.get()
            print(next_message)
            await JOIN[next_message.user].send(json.dumps(asdict(next_message.data)))
            print("Successfully sent.")
        except TypeError as e:
            print (e)

async def handler(websocket):
    try:
        avatar = None
        message = await websocket.recv()
        event = json.loads(message)

        assert event["type"] == "connect"

        user : str = event["user"]
        passwd : str = event["pass"]

        if user in JOIN:
            await send_message_websocket(websocket, f"Username {user} already exists on this server, please try logging on again with a different username.")
            await websocket.send(json.dumps(asdict(SendData("disconnect", None))))
            raise ValueError

        user_obj = user_data.get(user)

        if user_obj == None:
            room = get_first_with_name(gm, "Room")

            avatar = GameObject()
            gm.imbue_reactions(avatar, {"listen_can_hear", "look_visible"})
            gm.imbue_skills(avatar, {"look", "go", "say"})
            
            avatar.states = { "name": user, "description": f"Avatar for {user}.", "location": room[0].id }

            user_obj = UserData(user, bcrypt.hashpw(passwd.encode(), bcrypt.gensalt()).decode(), gm.obj_to_dict(avatar))

            # add user data
            user_data[user] = user_obj

        elif bcrypt.checkpw(passwd.encode(), user_obj.pass_hash.encode()):
            avatar = gm.obj_from_dict(user_obj.data)
        else:
            await send_message_websocket(websocket, f"Password incorrect, please try again.")
            await websocket.send(json.dumps(asdict(SendData("disconnect", None))))
            raise ValueError

        connected.add(websocket)
        JOIN[event["user"]] = websocket

        # ON USER CONNECT EVENT
        print ( f"User {event.get('user')} connected to server." )

        await send_message_all(RichText(f"Welcome to the server, {user}.", color=1, bold=True))

        # # create player object in server
        # room = get_first_with_name(gm, "Room")
        # avatar : GameObject = create_object(gm, user, f"Avatar for {user}.", room[0].id)

        # avatar.states["admin"] = True

        # gm.imbue_reactions(avatar, {"listen_can_hear","look_visible"})
        # gm.imbue_skills(avatar, {"look", "go", "say", "create", "destroy", "set", "list", "imbue", "inspect"})

        gm.add_object(avatar)

        net_io.add_user(user, avatar.id)
        # END ON USER CONNECT

        while not (user in disconnecting):
            message = await websocket.recv()
            event = json.loads(message)
            await parse(event, user)

    finally:
        if avatar != None:
            gm.remove_obj(avatar.id)
            net_io.remove_id(avatar.id)
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
    try:
        async with websockets.serve(handler, "", port):
            print(f"Opening server on port {port}.")
            send_task = asyncio.create_task(send_loop())
            game_task = asyncio.create_task(game_loop())
            await asyncio.Future()
    finally:
        game_state_save(gm, "last_quit.json")

if __name__ == "__main__":
    asyncio.run(main())