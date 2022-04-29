from rich import print
from rich.table import Table
import uuid
from typing import Callable, Union, Any

class GameObject:
    def __init__(self):
        self.id : str = uuid.uuid4()
        self.states : dict = dict() # keys strings to some other data, usually attached / managed by skills
        self.skills : set = set() # set of *ids* of available skills
        self.reactions : set = set() # set of *ids* of reactions

class Skill:
    def __init__(self, name : str, description : str = "Some skill.", synonyms : list[str] = [], on_parsed : Callable[["Game", list[str], str], Any] = None):
        self.id : str = uuid.uuid4()
        self.name : str = name
        self.description : str = description
        self.synonyms : str = synonyms
        self.on_parsed = on_parsed

class Reaction:
    def __init__(self, reaction_to : str, handle):
        self.id : str = uuid.uuid4()
        self.reacting_to : str = reaction_to # id, not name
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

def show_skills(game : "Game"):
    player : GameObject = game.game_objects[game.player_id]
    tbl = Table(title="Skills")
    tbl.add_column("Skill", justify="center", style="bright_cyan")
    tbl.add_column("Description", justify="center")
    for skill_id in player.skills:
        skill : Skill = game.skills.get(skill_id)
        tbl.add_row(skill.name, skill.description)
    print(tbl)
    
def do_nothing(game: "Game"):
    pass

class Game:

    _default_commands = {"help": ("See this help message", help), "quit": ("Exit the game.", exit_game), "skills": ("Show your available skills (things you can do).", show_skills)}

    def __init__(self):
        self.game_objects : dict[GameObject] = dict()
        self.skills : dict[str, Skill] = dict()
        self.reactions : dict[str, Reaction] = dict()
        self.before_start : Callable[["Game"], None] = do_nothing
        self._skill_parse_dict : dict[str, str] = dict()
        self._reaction_parse_dict : dict[str, list[str]] = dict()
        self.exit : bool = False

    def parse(self, raw : str):
        split = raw.split()
        if len(split) > 0 and split[0] in Game._default_commands:
            Game._default_commands[split[0]][1](self)
        elif len(split) > 0 and split[0] in self._skill_parse_dict:
            # this is STILL wrong because we need the player object to be set up as a receiver for inputs
            skill_id = self._skill_parse_dict.get(split[0])
            self.skills.get(skill_id).on_parsed(self, split, skill_id, self.player_id)

    def get_by_state(self, state_id, eval_fn):
        # this builds a pretty strong case for having a state manager rather than having GameObjects handle their own state
        # because we want to be able to index, update, and search for state (location is a state) independently of whatever
        # a given GameObject thinks it ought to be doing
        return [
            y
            for y in self.game_objects.values()
            if state_id in y.states
            if eval_fn(y.states[state_id])
        ]

    def get_by_id(self, id_ : str):
        return self.game_objects.get(id_)

    def add_skill(self, skill : Skill):
        self.skills[skill.id] = skill
        self._skill_parse_dict[skill.name.lower()] = skill.id
        for synonym in skill.synonyms:
            self._skill_parse_dict[synonym.lower()] = skill.id
    
    def add_reaction(self, reaction : Reaction):
        self.reactions[reaction.id] = reaction
        reaction_list = self._reaction_parse_dict.get(reaction.reacting_to)
        if reaction_list != None:
            reaction_list.append(reaction.id)
        else:
            reaction_list = [reaction.id]
        self._reaction_parse_dict[reaction.reacting_to] = reaction_list

    def react_to(self, actor_id, skill_id, target_id):
        target : GameObject = self.get_by_id(target_id)

        target_reactions = [ 
            self.reactions.get(reaction_id)
            for reaction_id in target.reactions
            if self._reaction_parse_dict.get(skill_id) != None
        ]

        final_targets = [
            reaction
            for reaction in target_reactions
            if reaction.id in self._reaction_parse_dict.get(skill_id)
        ]

        if len(final_targets) > 1:
            print(f"[red]Warning: more than one reaction to {skill_id} in {actor_id}. Only executing the first one.[/red]")
        if len(final_targets) > 0:
            return final_targets[0].callback(self, actor_id, target_id)
        return None

    def start(self):
        # setup code
        self.before_start(self)
        print("[bright_cyan]Try help if you need help.[/bright_cyan]")
        while not self.exit:
            raw = input("> ")
            self.parse(raw)