import curses
from curses import ascii
import time

class CursesIO():
    def __init__(self, tick_time : float = 0.0625, input_prefix = "> "): # i.e. 1/32 of a second
        self.stdscr = None
        self.msg_buffer = []
        self.output_scr = None
        self.input_scr = None
        self.tick_time = tick_time
        self.input_buffer = ""
        self.input_prefix = "> "
        self.output_buffer = []
        self.input_history = []
        self.history_pos = -1

    def init_windows(self, stdscr):
        if stdscr != None:
            self.stdscr = stdscr
        self.stdscr.nodelay(True)
        self.output_scr = curses.newwin(curses.LINES-1, curses.COLS-1, 0, 0)
        self.input_scr = curses.newwin(1, curses.COLS-1, curses.LINES-1, 0)
        self.input_scr.addstr(self.input_prefix)
        self.stdscr.refresh()
        self.output_scr.refresh()
        self.input_scr.refresh()
        time.sleep(self.tick_time)
        

    def main_loop(self):
        cur_key = None
        while True:
            key_ascii = self.stdscr.getch()
            key_str = ascii.unctrl(key_ascii)
            if (key_ascii != -1):
                if key_ascii == curses.KEY_ENTER or key_ascii == 10 or key_ascii == 13:

                    # if it will move cursor outside the edge of the window

                    self.output_buffer.append(self.input_buffer)

                    self.output_scr.clear()
                    to_print = self.output_buffer[1-curses.LINES:]
                    self.output_scr.addstr("\n".join(to_print))

                    self.input_history.append(self.input_buffer)

                    self.output_scr.refresh()
                    self.input_buffer = ""
                elif key_ascii == curses.KEY_BACKSPACE:
                    self.input_buffer = self.input_buffer[:-1]
                else:
                    self.input_buffer += key_str
                self.input_scr.clear()
                self.input_scr.addstr(self.input_prefix + self.input_buffer)
                self.input_scr.refresh()

    @staticmethod
    def _start(stdscr, io : "CursesIO"):
        # instantiate 2 new panels
        io.init_windows(stdscr)
        io.main_loop()

    def start(self):
        curses.wrapper(CursesIO._start, self)