import asyncio
from websockets import client as ws
import time
import json

import websockets
from magic_io import *


async def help(client : "Client", args):
    client.io.add_output("HELP")
    for cmd in Client._default_commands:
        client.io.add_output(f"{cmd} | {Client._default_commands[cmd][0]}")

async def exit_game(client : "Client", args):
    client.exit = True

async def connect(client : "Client", args):
    if len(args) < 3:
        client.io.add_output("Usage: connect URI USERNAME")
        return

    if client.connection != None:
        client.io.add_output("You're already connected to a server. Disconnect before doing anything else.")
        return

    client.io.add_output(f"Attempting connection to {args[1]}")
    await asyncio.sleep(0.5)
    try:
        connection = await ws.connect(args[1])
        client.connection = connection
        client.cur_user = args[2]
        await client.connection.send(json.dumps({ "type": "connect", "user": args[2] }))
        client.io.add_output(f"Connected to {args[1]} successfully.")
    except:
        client.io.add_output("Couldn't connect to remote server.")
        client.connection = None

async def disconnect(client: "Client"):
    if client.connection != None:
        await client.connection.send(json.dumps({"type": "disconnect", "user": client.cur_user}))
        await client.connection.close()
        client.cur_user = None
        client.connection = None

async def disconnect_parse(client: "Client", args):
    if client.connection != None:
        await disconnect(client)
        client.io.add_output("Disconnected from server.")

class Client:

    _default_commands = {"help": ("See this help message", help), "quit": ("Exit the game.", exit_game), "connect": ("Connect to a server.", connect), "disconnect": ("Disconnect from a server.", disconnect_parse)}

    def __init__(self, tick_time = 0.0625):
        self.exit : bool = False
        self.tick_time = tick_time
        self.connection = None
        self.cur_user = None

    @staticmethod
    def decode_json(message : str) -> Union[str, RichText, list]:
        obj = json.loads(message)


    @staticmethod
    def split_args(raw: str) -> list[str]:
        i = 0
        start = 0
        buffer = ""
        quoting = False
        arg_list = []
        while i < len(raw):
            buffer += raw[i]
            if raw[i] == " " and not quoting:
                arg_list.append(buffer[:-1])
                start = i+1
                buffer = ""
            if raw[i] in "\"\'" and not quoting:
                quoting = True
                start = i
                buffer = ""
            elif raw[i] in "\"\'" and quoting:
                quoting = False
                buffer = buffer[:-1]
            i += 1
        if len(buffer) > 0:
            arg_list.append(buffer)
        return arg_list


    async def parse(self, raw : str):
        split = Client.split_args(raw)
        if len(split) > 0 and split[0] in Client._default_commands:
            await Client._default_commands[split[0]][1](self, split)
        elif self.connection != None:
            await self.connection.send(json.dumps({"type":"message", "data": split}))
        

    async def start(self):
        # setup code
        parsing = set()
        with CursesIO() as self.io:
            while not self.exit:
                self.io.poll() # probably need an async option for sending / retrieving data from cursesIO
                next_input = self.io.pop_input()
                if next_input != None:
                    cur_parse = asyncio.create_task(self.parse(next_input))
                    parsing.add(cur_parse)
                    cur_parse.add_done_callback(parsing.discard)

                await asyncio.sleep(self.tick_time)
            
            await disconnect(self)
        return

if __name__ == "__main__":
    client = Client()
    asyncio.run(client.start())