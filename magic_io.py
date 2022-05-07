import curses
from curses import ascii
import time
from typing import Union
from dataclasses import dataclass
from enum import IntEnum
from math import ceil

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

@dataclass
class LineSplitData:
    lines : list[str]
    offset : int 

class CursesIO():

    @staticmethod
    def push_to_input_queue(io_ : "CursesIO", input_ : str):
        io_.input_queue.append(input_)

    @staticmethod
    def on_enter(io_):
        io_.input_history.append(io_.input_buffer)
        if io_.on_input != None:
            io_.on_input(io_, io_.input_buffer)
        io_.input_buffer = ""
    
    @staticmethod
    def on_backspace(io_):
        io_.input_buffer = io_.input_buffer[:-1]

    @staticmethod
    def on_tab(io_):
        if not io_.scrolling:
            io_.scrolling = True
        else:
            io_.can_refresh_output = True
            io_.scrolling = False
            io_.cursor_location = 0

    @staticmethod
    def on_up(io_):
        if io_.scrolling and io_.cursor_location < (len(io_.output_buffer) - (curses.LINES - 1)):
            io_.cursor_location += 1
            io_.can_refresh_output = True
    
    @staticmethod
    def on_down(io_):
        if io_.scrolling and io_.cursor_location > 0:
            io_.cursor_location -= 1
            io_.can_refresh_output = True

    def __init__(self, input_prefix = "> ", on_input = None, logfile = None): # i.e. 1/32 of a second
        if on_input == None:
            self.on_input = CursesIO.push_to_input_queue
        else:
            self.on_input = on_input
        
        self.stdscr = None
        self.msg_buffer = []
        self.quit = False
        self.output_scr = None
        self.input_scr = None
        self.input_buffer = ""
        self.input_prefix = "> "
        self.input_queue = [] # for things you want other components to read
        self.output_buffer = []
        self.input_history = []
        self.history_pos = -1
        self.can_refresh_output = False
        self.logfile = logfile
        self.cursor_location = 0
        self.scrolling = False
        self.key_presses = {
            curses.KEY_ENTER : CursesIO.on_enter,
            ord('\n') : CursesIO.on_enter,
            ord('\r') : CursesIO.on_enter,
            curses.KEY_BACKSPACE : CursesIO.on_backspace,
            ord('\b') : CursesIO.on_backspace,
            ord('\x7f'): CursesIO.on_backspace,
            ord('\t') : CursesIO.on_tab,
            curses.KEY_UP : CursesIO.on_up,
            curses.KEY_DOWN : CursesIO.on_down
        }

    def __enter__(self):
        self.init_windows()
        return self
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def log(self, str_):
        if (self.logfile != None):
            self.logfile.write(str_ + "\n")

    def init_windows(self):
        # general curses setup
        self.stdscr = curses.initscr()
        curses.start_color()

        for color in range(1,9):
            curses.init_pair(color, color, curses.COLOR_BLACK)

        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        
        self.stdscr.nodelay(True) # non-blocking

        # setup / refresh subscreens
        self.output_scr = curses.newwin(curses.LINES-1, curses.COLS-1, 0, 0)
        self.input_scr = curses.newwin(1, curses.COLS-1, curses.LINES-1, 0)
        self.input_scr.addstr(self.input_prefix)
        self.stdscr.refresh()
        self.output_scr.refresh()
        self.input_scr.refresh()
        
    def pop_input(self):
        if len(self.input_queue) > 0:
            return self.input_queue.pop(0)
        return None

    def add_output(self, output : Union[str, list, RichText]):
        self.output_buffer.append(output)
        self.can_refresh_output = True

    def clear_output(self):
        self.output_buffer = []
        self.cursor_location = 0
        self.can_refresh_output = True

    def process_output(self, output : Union[str, RichText]):
        if isinstance(output, str):
            self.output_scr.addstr(output)
        elif isinstance(output, RichText):
            modifier = curses.color_pair(int(output.color))
            if output.bold:
                modifier = modifier | curses.A_BOLD
            if output.standout:
                modifier = modifier | curses.A_STANDOUT
            if output.dim:
                modifier = modifier | curses.A_DIM
            if output.reverse:
                modifier = modifier | curses.A_REVERSE
            if output.blink:
                modifier = modifier | curses.A_BLINK
            if output.underline:
                modifier = modifier | curses.A_UNDERLINE
            self.output_scr.addstr(output.text, modifier)

    def get_string_repr(self, output : Union[str, list, RichText]) -> str:
        if isinstance(output, str):
            return output
        if isinstance(output, RichText):
            return output.text
        if isinstance(output, list):
            return ''.join([ self.get_string_repr(o) for o in output ])

    def get_output_lines(self, output : Union[str, list, RichText]) -> int:
        # get the lines used by a given output
        lines = 1
        str_ : str = get_string_repr(output)
        lines += str_.count("\n")
        str_ : str = str_.replace("\n","")
        total_len = len(str_)
        lines += math.ceil(float(total_len) / float(curses.COLS))
        return lines

    @staticmethod
    def split_to_lines_simple(output : Union[str, RichText], offset: int = 0) -> LineSplitData:
        # offset enables this working in lists
        if isinstance(output, RichText):
            raw_text : str = output.text
        elif isinstance(output, str):
            raw_text : str = output
        
        out = []
        chars_no_line_break = offset
        last_break = 0
        for i, char in enumerate(raw_text):
            chars_no_line_break += 1
            if chars_no_line_break >= curses.COLS-2 or char == "\n":
                split_text = raw_text[last_break:i+1]
                last_break = i+1
                chars_no_line_break = 0
                if isinstance(output, RichText):
                    out.append(RichText(split_text, color=output.color, standout=output.standout, bold=output.bold, blink=output.blink, dim=output.dim, reverse=output.reverse, underline=output.underline))
                elif isinstance(output, str):
                    out.append(split_text)
        
        split_text = raw_text[last_break:]
        
        if isinstance(output, RichText):
            out.append(RichText(split_text, color=output.color, standout=output.standout, bold=output.bold, blink=output.blink, dim=output.dim, reverse=output.reverse, underline=output.underline))
        elif isinstance(output, str):
            out.append(split_text)

        return LineSplitData(out,offset)
    
    @staticmethod
    def split_to_lines(output: Union[str, RichText, list]):
        if isinstance(output, RichText) or isinstance(output, str):
            return [ line for line in CursesIO.split_to_lines_simple(output).lines ]
        elif isinstance(output, list):
            current = []
            offset = 0
            for o in output:
                cur_split = CursesIO.split_to_lines_simple(o, offset=offset)
                current.extend(cur_split.lines)
                offset = cur_split.offset
            return current

    def process_output_line(self, output : Union[str, list, RichText], line_index):
        if line_index != 0:
            self.output_scr.addstr('\n')
        if isinstance(output, str) or isinstance(output, RichText):
            self.process_output(output)
        elif isinstance(output, list):
            for o in output:
                self.process_output(o)

    def refresh_output(self):
        self.output_scr.clear()
        buf_len = len(self.output_buffer)
        start = (buf_len + 1 - self.cursor_location) - curses.LINES
        if start < 0: start = 0
        to_print = self.output_buffer[ start : buf_len - self.cursor_location ]

        for (i, output) in enumerate(to_print):
            self.process_output_line(output, i)

        self.output_scr.refresh()
        self.can_refresh_output = False
        self.input_scr.refresh()

    def poll(self):
        if self.can_refresh_output:
            self.refresh_output()
        
        key_buffer = []
        while (cur_key := self.stdscr.getch()) != -1:
            key_buffer.append(cur_key)


        for key_ascii in key_buffer:
            key_str = ascii.unctrl(key_ascii)
            if key_ascii in self.key_presses:
                self.key_presses.get(key_ascii)(self)
            elif not self.scrolling and (len(self.input_prefix) + len(self.input_buffer) + len(key_str) < curses.COLS - 1):
                self.input_buffer += key_str
            self.input_scr.clear()
            input_str = self.input_prefix
            if (self.scrolling):
                input_str = "[SCROLL]"
            self.input_scr.addstr(input_str + self.input_buffer)
            self.input_scr.refresh()