import websockets
import time
from magic_io import *


def help(client : "Client"):
    client.io.add_output("HELP")
    for cmd in Client._default_commands:
        client.io.add_output(f"{cmd} | {Client._default_commands[cmd][0]}")

def exit_game(client : "Client"):
    client.exit = True

class Client:

    _default_commands = {"help": ("See this help message", help), "quit": ("Exit the game.", exit_game)}

    def __init__(self, tick_time = 0.0625):
        self.exit : bool = False
        self.tick_time = tick_time

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


    def parse(self, raw : str):
        split = Client.split_args(raw)
        if len(split) > 0 and split[0] in Client._default_commands:
            Client._default_commands[split[0]][1](self)

    def start(self):
        # setup code
        with CursesIO() as self.io:
            while not self.exit:
                # raw = input("> ")
                self.io.poll()
                next_input = self.io.pop_input()
                if next_input != None:
                # print(Game.split_args(raw))
                    self.parse(next_input)
                time.sleep(self.tick_time)

if __name__ == "__main__":
    client = Client()
    client.start()