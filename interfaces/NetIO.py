from typing import Callable, Union
from interfaces.magic_io import RichText
import uuid
import asyncio

# use of create_task is abusive but justified for brevity

class NetIO():
    def __init__(self, input_stream : Callable[[str, uuid.UUID], None], output_stream : Callable[[str,Union[list, RichText, str]], None]):
        # join object ID to username
        self.id_to_user : dict[uuid.UUID, str] = dict()
        self.user_to_id : dict[str, uuid.UUID] = dict()
        # send out to server instance
        self.output_stream = output_stream
        # call parse on these
        self.input_stream = input_stream

    def send_to(self, id, msg):
        if id not in self.id_to_user:
            return        
        username = self.id_to_user.get(id)
        asyncio.create_task(self.output_stream(username, msg))

    def broadcast(self, msg):
        for user in set(self.id_to_user.values()):
            # prevents same user being called twice
            asyncio.create_task(self.output_stream(user, msg))
    
    def add_user(self, user, id):
        self.id_to_user[id] = user
        self.user_to_id[user] = id

    def remove_user(self, user):
        id = self.user_to_id[user]
        del self.id_to_user[id]
        del self.user_to_id[user]
    
    def remove_id(self, id):
        user = self.id_to_user[id]
        del self.user_to_id[user]
        del self.id_to_user[id]

    async def parse(self, input, user):
        if user not in self.user_to_id:
            return

        self.input_stream(input, self.user_to_id.get(user))