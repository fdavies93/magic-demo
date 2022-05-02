import curses
from curses import ascii
import time


class CursesIO():
    def __init__(self, input_prefix = "> ", on_input = None, logfile = None): # i.e. 1/32 of a second
        self.stdscr = None
        self.msg_buffer = []
        self.quit = False
        self.output_scr = None
        self.input_scr = None
        self.input_buffer = ""
        self.input_prefix = "> "
        self.output_buffer = []
        self.input_history = []
        self.history_pos = -1
        self.refresh_output = False
        self.on_input = on_input
        self.logfile = logfile

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
        

    def add_output(self, output):
        self.output_buffer.append(output)
        self.refresh_output = True

    def poll(self):
        self.log("polling")

        if self.refresh_output:
            self.output_scr.clear()
            to_print = self.output_buffer[1-curses.LINES:]
            self.output_scr.addstr("\n".join(to_print))
            self.output_scr.refresh()
            self.refresh_output = False
            self.input_scr.refresh()
            self.log("Refreshed output")

        key_ascii = self.stdscr.getch()
        key_str = ascii.unctrl(key_ascii)
        
        if (key_ascii != -1):
            if key_ascii == curses.KEY_ENTER or key_ascii == 10 or key_ascii == 13:
                # if it will move cursor outside the edge of the window
                self.input_history.append(self.input_buffer)
                if self.on_input != None:
                    self.on_input(self, self.input_buffer)
                self.input_buffer = ""
            elif key_ascii == curses.KEY_BACKSPACE:
                self.input_buffer = self.input_buffer[:-1]
            else:
                self.input_buffer += key_str
            self.input_scr.clear()
            self.input_scr.addstr(self.input_prefix + self.input_buffer)
            self.input_scr.refresh()
            self.log("keypress detected")

    # def main_loop(self):
    #     cur_key = None
    #     while not self.quit:

    #         if self.refresh_output:
    #             self.output_scr.clear()
    #             to_print = self.output_buffer[1-curses.LINES:]
    #             self.output_scr.addstr("\n".join(to_print))
    #             self.output_scr.refresh()
    #             self.refresh_output = False
    #             self.input_scr.refresh()

    #         key_ascii = self.stdscr.getch()
    #         key_str = ascii.unctrl(key_ascii)
    #         if (key_ascii != -1):
    #             if key_ascii == curses.KEY_ENTER or key_ascii == 10 or key_ascii == 13:
    #                 # if it will move cursor outside the edge of the window
    #                 self.input_history.append(self.input_buffer)
    #                 if self.on_input != None:
    #                     self.on_input(self, self.input_buffer)
    #                 self.input_buffer = ""
    #             elif key_ascii == curses.KEY_BACKSPACE:
    #                 self.input_buffer = self.input_buffer[:-1]
    #             else:
    #                 self.input_buffer += key_str
    #             self.input_scr.clear()
    #             self.input_scr.addstr(self.input_prefix + self.input_buffer)
    #             self.input_scr.refresh()
    #         time.sleep(self.tick_time)

    # def start(self):
    #     self.init_windows(stdscr)