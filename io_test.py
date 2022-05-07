from magic_io import CursesIO, RichText, COLOR
from time import sleep

def echo(interface : "CursesIO", input_ : str):
    interface.add_output(input_)



if __name__ == "__main__":
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    rich_lorem = RichText(lorem, color = COLOR.RED, bold=True)

    lorem_list = [lorem, rich_lorem, lorem]

    fake_buffer = [ ["a1", "a2", "a3"], ["b1", "b2", "b3", "b4"], ["c1", "c2"] ]

    # print(CursesIO.get_lines_between(fake_buffer, 0, 7))

    with open("./log.txt", mode="w") as log:
        with CursesIO(logfile=log) as curse_io:
            # log.write(str(CursesIO.split_to_lines_simple(lorem)))
            # log.write(str(CursesIO.split_to_lines_simple(rich_lorem)))
            # curse_io.add_output(lorem_list)
            # curse_io.add_output(lorem)
            # curse_io.add_output( str(len(curse_io.output_buffer[0])) )
            # curse_io.add_output(f"\n{curse_io.output_buffer[0][5]}")
            for i in range(4):
                curse_io.add_output(lorem_list)
                # curse_io.add_output(lorem)
                # curse_io.add_output(rich_lorem)
                # for ln in CursesIO.split_to_lines_simple(lorem).lines:
                #     curse_io.add_output(ln)
                # for ln in CursesIO.split_to_lines_simple(rich_lorem).lines:
                #     curse_io.add_output(ln)

            tick_time = 0.0625
            while True:
                curse_io.poll()
                next_input = curse_io.pop_input()
                if next_input != None:
                    curse_io.add_output(next_input)
                sleep(tick_time)