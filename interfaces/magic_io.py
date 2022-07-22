import curses
from curses import ascii, curs_set
from os import stat
import time
from typing import Callable, Union
from dataclasses import dataclass
from enum import IntEnum
from math import ceil
import uuid

# from magic_rpg import Game
# from server import send_message_to

class COLOR(IntEnum):
    BLACK = 0,
    RED = 1,
    GREEN = 2,
    YELLOW = 3,
    BLUE = 4,
    MAGENTA = 5,
    CYAN = 6,
    WHITE = 7

@dataclass
class RichText():
    text : str
    color : int = 7 # curses.color_pair(7), i.e. white
    standout : bool = False
    bold : bool = False
    blink : bool = False
    dim : bool = False
    reverse : bool = False
    underline : bool = False

    def __len__(self):
        return len(self.text)

@dataclass
class LineSplitData:
    lines : list[str]
    offset : int 

