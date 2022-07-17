import curses
from curses import ascii, curs_set
from os import stat
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

    def __len__(self):
        return len(self.text)

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
        if io_.scrolling and io_.cursor_location < (CursesIO.get_buffer_length(io_.output_buffer) - (curses.LINES - 1)):
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
        curs_set(False)
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
        # lines = CursesIO.split_to_lines(output)
        self.output_buffer.append(output)
        self.can_refresh_output = True

    def clear_output(self):
        self.output_buffer = []
        self.cursor_location = 0
        self.can_refresh_output = True

    @staticmethod
    def get_string_repr(output : Union[str, list, RichText]) -> str:
        if isinstance(output, str):
            return output
        if isinstance(output, RichText):
            return output.text
        if isinstance(output, list):
            return ''.join([ CursesIO.get_string_repr(o) for o in output ])

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
            if chars_no_line_break >= curses.COLS-1 or char == "\n":
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

        offset = chars_no_line_break

        return LineSplitData(out,offset)

    # @staticmethod
    def split_to_lines(self, output: Union[str, RichText, list]):
        if isinstance(output, RichText) or isinstance(output, str):
            return [ line for line in CursesIO.split_to_lines_simple(output).lines ]
            # array of either rich text or strs
        elif isinstance(output, list):
            out = []
            current_line = []
            offset = 0
            cur_chars = 0
            for o in output:
                cur_split = CursesIO.split_to_lines_simple(o, offset=offset)
                for el in cur_split.lines:
                    cur_chars += len(el)
                    current_line.append(el)
                    if cur_chars >= curses.COLS - 1:
                        out.append(current_line)
                        cur_chars = 0
                        current_line = []
                offset = cur_split.offset
            if cur_chars > 0:
                out.append(current_line)
            return out

    @staticmethod
    def get_buffer_length(buf):
        return sum( [len(o) for o in buf] )

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

    def process_output_line(self, output : Union[str, list, RichText]):
        if isinstance(output, str) or isinstance(output, RichText):
            self.process_output(output)
        elif isinstance(output, list):
            for o in output:
                self.process_output(o)

    def render_from(self, offset : int, limit: int):
        pos = 0
        cur_ln = 0
        # self.log(str(start))
        render_buffer = []
        breaks : set[int] = set() # which lines should end in breaks?
        # push everything into the render buffer, but don't output it yet
        for i, output in enumerate(self.output_buffer):
            cur_output = self.split_to_lines(output) # always an array with length being number of on-screen lines
            render_buffer.extend(cur_output)
            breaks.add( len(render_buffer) - 1 )

        start = 0 # calculate from offset and buffer length
        start = len(render_buffer) - (curses.LINES - 2) - offset
        if start < 0:
            start = 0

        line_i = start
        while line_i < len(render_buffer) and line_i < start+limit:
            line = render_buffer[line_i]
            self.process_output_line(line)
            if line_i in breaks:
                self.output_scr.addstr("\n")
            line_i += 1

    def refresh_output(self):
        self.output_scr.clear()
        self.render_from(self.cursor_location, curses.LINES-2)

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