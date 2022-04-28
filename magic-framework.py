from rich import print
from rich.table import Table
import uuid
from typing import Callable, Union

class GameObject:
    def __init__(self):
        self.id : str = uuid.uuid4()
        self.states : dict = dict() # keys strings to some other data, usually attached / managed by skills
        self.skills : set = set() # set of *ids* of available skills
        self.reactions : set = set() # set of *ids* of reactions

class Skill:
    def __init__(self, name : str, synonyms : list[str] = [], on_parsed : Callable[["Game", list[str], str]] = None):
        self.id : str = uuid.uuid4()
        self.name : str = name
        self.synonyms : str = synonyms
        self.on_parsed = on_parsed

class Reaction:
    def __init__(self, reaction_to : str, handle):
        self.id : str = uuid.uuid4()
        self.reacting_to : str = reaction_to
        self.callback = handle


def help(game : "Game"):
    tbl = Table(title="Commands")
    tbl.add_column("Command", justify="center", style="bright_cyan")
    tbl.add_column("Description", justify="center")
    for cmd in Game._default_commands:
        tbl.add_row(cmd, Game._default_commands[cmd][0])
    print(tbl)

def exit_game(game : "Game"):
    game.exit = True

def skill_look(game : "Game", args, parsed_id): # that info can kind of be bundled to an InvocationContext or similar
    game.get_by_state()

class Game:

    _default_commands = {"help": ("See this help message", help), "quit": ("Exit the game.", exit_game)}

    def __init__(self):
        self.game_objects : dict[GameObject] = []
        self.skills : dict[Skill] = []
        self._skill_parse_dict : dict[str, str] = []
        self.exit : bool = False

    def parse(self, raw : str):
        split = raw.split()
        if len(split) > 0 and split[0] in Game._default_commands:
            Game._default_commands[split[0]][1](self)
        elif len(split) > 0 and split[0] in self._skill_parse_dict:
            # this is STILL wrong because we need the player object to be set up as a receiver for inputs
            skill_id = self._skill_parse_dict.get(split[0])
            self.skills.get(skill_id).on_parsed(self, split, self.player_id)

    def get_by_state(self, state_id, eval_fn):
        # this builds a pretty strong case for having a state manager rather than having GameObjects handle their own state
        # because we want to be able to index, update, and search for state (location is a state) independently of whatever
        # a given GameObject thinks it ought to be doing
        return [y for y in self.game_objects if (state_id in y.states and eval_fn(y.states[state_id]))] # noice


    def start(self):
        room = GameObject()
        room.states["name"] = "A room"
        room.states["description"] = "A small room."
        player = GameObject()
        player.states["name"] = "Hero"
        player.states["description"] = "You look very handsome."
        player.states["location"] = room.id
        look_skill = Skill("look", on_parsed=skill_look)
        self.game_objects[room.id] = room
        self.game_objects[player.id] = player
        self.skills[look_skill.id] = look_skill
        player.skills.add(look_skill.id)
        while not self.exit:
            print("[bright_cyan]Try help if you need help.[/bright_cyan]")
            raw = input("> ")
            self.parse(raw)

if __name__ == "__main__":
    gm = Game()
    gm.start()