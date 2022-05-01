from magic_io import CursesIO

def echo(interface : "CursesIO", input_ : str):
    interface.add_output(input_)

if __name__ == "__main__":
    io = CursesIO(on_input=echo)
    io.start()