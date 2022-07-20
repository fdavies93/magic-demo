import asyncio
from dataclasses import asdict, fields
from dis import disco
from multiprocessing.dummy import Array
from websockets import client as ws
from types import NoneType
from typing import Union
import time
import json

import websockets
from magic_io import *

@dataclass
class RichTextData:
    text: str
    color : int = 0
    standout : bool = False
    bold : bool = False
    blink : bool = False
    dim : bool = False
    reverse : bool = False
    underline : bool = False

@dataclass
class Output:
    type : str
    content : Union[RichTextData, str, list, NoneType]

@dataclass
class SendData:
    type: str
    data : Union[NoneType, Output]

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
        asyncio.create_task(client.receive_message())
    except:
        client.io.add_output("Couldn't connect to remote server.")
        client.connection = None

async def disconnect(client: "Client", send_header: bool = True):
    if client.connection != None:
        client.disconnecting.set() # stop receiving in the receive loop
        if send_header:
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

    async def receive_loop():
        pass

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
            await self.connection.send(json.dumps({"type":"message", "data": raw}))
    
    # example_message = {
    #     "type": "output",
    #     "output": {
    #         "type": "RichText",
    #         "content": {
    #             "text": "some_text",
    #             "color": 0,
    #             "standout": False,
    #             "bold": False,
    #             "blink": False,
    #             "dim": False,
    #             "reverse": False,
    #             "underline": False
    #         }
    #     }
    # }

    @staticmethod
    def parse_disconnect(client : "Client", message : dict):
        disconnect(client, False)

    @staticmethod
    def format_rich_text(body:dict):
        if not "text" in body or not isinstance(body["text"], str):
            return None

        # check fields and remove fields not in the spec programatically, exploiting dataclass functions

        rt_fields = dict( (f.name, f.type) for f in fields(RichText))
        new_body = dict()

        for key in body:
            if key in rt_fields and isinstance(body[key], rt_fields[key]) :
                new_body[key] = body[key]

        out = RichText(**new_body)
        return out

    @staticmethod
    def format_plain_text(body:dict):
        if not isinstance(body, str):
            return None
        return body

    @staticmethod
    def parse_rich_text(client : "Client", body : dict):
        out = Client.format_rich_text(body)
        if out != None:
            client.io.add_output(out)

    @staticmethod
    def parse_plain_text(client : "Client", body : str):
        out = Client.format_plain_text(body)        
        if out != None:
            client.io.add_output(out)

    @staticmethod
    def parse_list(client : "Client", body : list):
        out = []
        for msg in body:
            content_type = msg.get("type")
            if content_type == None:
                continue

            content_body = msg.get("content")
            if content_body == None:
                continue
            
            if content_type == "PlainText":
                out.append(Client.format_plain_text(content_body))
            elif content_type == "RichText":
                out.append(Client.format_rich_text(content_body))
            
        client.io.add_output(out)
            


    @staticmethod
    def parse_output(client : "Client", output : dict):
        content_type = output.get("type")
        if content_type == None:
            return

        content_body = output.get("content")
        if content_body == None:
            return
        
        if content_type in Client.output_strategies:
            Client.output_strategies[content_type](client, content_body)

    @staticmethod
    def parse_output_message(client : "Client", message : dict):
        print(message)
        output = message.get("data")
        print (output)
        if output == None:
            return

        Client.parse_output(client, output)
            

    strategies = { "output" : parse_output_message, "disconnect": parse_disconnect }
    output_strategies = { "RichText" : parse_rich_text, "PlainText" : parse_plain_text, "List": parse_list }

    @staticmethod
    def parse_message(client: "Client", message : str):
        obj = json.loads(message)
        obj_type = obj.get("type")
        if obj_type == None:
            return
        elif obj_type in Client.strategies:
            Client.strategies[obj_type](client, obj)

    async def receive_message(self):
        self.disconnecting = asyncio.Event()
        while self.connection != None:
            # self.io.add_output("Loop in receive_message.")
            recv_task = asyncio.create_task(self.connection.recv())
            wait_task = asyncio.create_task(self.disconnecting.wait())
            done, pending = await asyncio.wait({recv_task, wait_task}, return_when=asyncio.FIRST_COMPLETED)

            if recv_task in done:
                Client.parse_message(self, recv_task.result())
            else:
                recv_task.cancel()
                break

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