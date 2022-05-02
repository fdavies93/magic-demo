from magic_io import CursesIO
from time import sleep

def echo(interface : "CursesIO", input_ : str):
    interface.add_output(input_)

if __name__ == "__main__":
    with open("./log.txt", mode="a") as log:
        with CursesIO(logfile=log) as curse_io:
            tick_time = 0.0625
            while True:
                curse_io.poll()
                next_input = curse_io.pop_input()
                if next_input != None:
                    curse_io.add_output(next_input)
                sleep(tick_time)