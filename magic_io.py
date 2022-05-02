import curses
from curses import ascii
import time


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

    def add_output(self, output):
        self.output_buffer.append(output)
        self.can_refresh_output = True

    def refresh_output(self):
        self.output_scr.clear()
        buf_len = len(self.output_buffer)
        start = (buf_len + 1 - self.cursor_location) - curses.LINES
        if start < 0: start = 0
        to_print = self.output_buffer[ start : buf_len - self.cursor_location ]
        self.output_scr.addstr("\n".join(to_print))
        self.output_scr.refresh()
        self.can_refresh_output = False
        self.input_scr.refresh()

    def poll(self):
        if self.can_refresh_output:
            self.refresh_output()
        key_ascii = self.stdscr.getch()
        key_str = ascii.unctrl(key_ascii)
        
        if (key_ascii != -1):
            if key_ascii in self.key_presses:
                self.key_presses.get(key_ascii)(self)
            elif not self.scrolling:
                self.input_buffer += key_str
            self.input_scr.clear()
            input_str = self.input_prefix
            if (self.scrolling):
                input_str = "[SCROLL]"
            self.input_scr.addstr(input_str + self.input_buffer)
            self.input_scr.refresh()