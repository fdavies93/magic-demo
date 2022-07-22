from ast import Call
from typing import Callable, Union
from magic_io import RichText
import uuid

class NetIO():
    def __init__(self, input_stream : Callable[[str, uuid.UUID]], output_stream : Callable[[str,Union[list, RichText, str]]]):
        # join object ID to username
        self.users : dict[uuid.UUID, str] = dict()
        # send out to server instance
        self.output_stream = output_stream
        # call parse on these
        self.input_stream = input_stream
    
    async def io_loop(self): 
        while True:
            self.game.tick()

    def send_to(self, id, msg):
        if id not in self.users:
            return        
        username = self.users.get(id)
        self.output_stream(username, msg)

    def broadcast(self, msg):
        for user in self.users.values():
            self.output_stream(user, msg)
    
    def parse(self, input, user):
        self.input_stream(input, user)