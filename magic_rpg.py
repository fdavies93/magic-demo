import uuid
from typing import Callable, Union, Any
from curses import wrapper
from interfaces.CursesIO import CursesIO
from interfaces.magic_io import RichText, COLOR
import time
import asyncio

class GameObject:
    def __init__(self):
        self.id : str = uuid.uuid4()
        self.states : dict = dict() # keys strings to some other data, usually attached / managed by skills
        self.skills : set = set() # set of *ids* of available skills
        self.reactions : set = set() # set of *ids* of reactions
        self.on_tick = None

class Skill:
    def __init__(self, name : str, description : str = "Some skill.", synonyms : list[str] = [], on_parsed : Callable[["Game", list[str], str], Any] = None):
        self.id : str = uuid.uuid4()
        self.name : str = name
        self.description : str = description
        self.synonyms : str = synonyms
        self.on_parsed = on_parsed

class Reaction:
    def __init__(self, name : str, reaction_to : str, handle):
        self.name : str = name
        self.id : str = uuid.uuid4()
        self.reacting_to : str = reaction_to # id, not name
        self.callback = handle


def help(game : "Game"):
    game.io.add_output("HELP")
    for cmd in Game._default_commands:
        game.io.add_output(f"{cmd} | {Game._default_commands[cmd][0]}")
    # tbl = Table(title="Commands")
    # tbl.add_column("Command", justify="center", style="bright_cyan")
    # tbl.add_column("Description", justify="center")
    # for cmd in Game._default_commands:
    #     tbl.add_row(cmd, Game._default_commands[cmd][0])
    # print(tbl)

def exit_game(game : "Game"):
    game.exit = True

def show_skills(game : "Game"):
    player : GameObject = game.game_objects[game.player_id]
    # tbl = Table(title="Skills")
    # tbl.add_column("Skill", justify="center", style="bright_cyan")
    # tbl.add_column("Description", justify="center")
    game.io.add_output("SKILLS")
    for skill_id in player.skills:
        skill : Skill = game.skills.get(skill_id)
        game.io.add_output(f"{skill.name} | {skill.description}")
    # print(tbl)
    
def do_nothing(game: "Game"):
    pass


class Game:

    _default_commands = {"help": ("See this help message", help), "quit": ("Exit the game.", exit_game), "skills": ("Show your available skills (things you can do).", show_skills)}

    def __init__(self, tick_time = 0.0625):
        self.game_objects : dict[uuid.UUID, GameObject] = dict()
        self.skills : dict[str, Skill] = dict()
        self.reactions : dict[str, Reaction] = dict()
        self.before_start : Callable[["Game"], None] = do_nothing
        self._skill_parse_dict : dict[str, str] = dict()
        self._reaction_parse_dict : dict[str, list[str]] = dict()
        self.on_tick_listeners : set[uuid.UUID] = set()
        self.exit : bool = False
        self.tick_time = tick_time
        self.interface = None
        self.game_time = 0.0

    def set_interface(self, interface):
        self.interface = interface

    def split_args(raw: str) -> list[str]:
        i = 0
        start = 0
        buffer = ""
        quoting = False
        arg_list = []
        while i < len(raw):
            buffer += raw[i]
            if raw[i] == " " and not quoting:
                arg_list.append(buffer[:-1])
                start = i+1
                buffer = ""
            if raw[i] in "\"\'" and not quoting:
                quoting = True
                start = i
                buffer = ""
            elif raw[i] in "\"\'" and quoting:
                quoting = False
                buffer = buffer[:-1]
            i += 1
        if len(buffer) > 0:
            arg_list.append(buffer)
        return arg_list


    def parse(self, raw : str, user):
        split = Game.split_args(raw)
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
    
    def use_skill(self, raw, caller_id):
        split = Game.split_args(raw)
        skill_id = self._skill_parse_dict.get(split[0])
        self.skills.get(skill_id).on_parsed(self, split, skill_id, caller_id)

    def get_by_id(self, id_ : str):
        return self.game_objects.get(id_)

    def add_skill(self, skill : Skill):
        self.skills[skill.id] = skill
        self._skill_parse_dict[skill.name.lower()] = skill.id
        for synonym in skill.synonyms:
            self._skill_parse_dict[synonym.lower()] = skill.id

    def add_object(self, obj : GameObject):
        self.game_objects[obj.id] = obj

    def register_on_tick(self, obj_id : uuid.UUID):
        self.on_tick_listeners.add(obj_id)

    def add_reaction(self, reaction : Reaction):
        self.reactions[reaction.id] = reaction
        reaction_list = self._reaction_parse_dict.get(reaction.reacting_to)
        if reaction_list != None:
            reaction_list.append(reaction.id)
        else:
            reaction_list = [reaction.id]
        self._reaction_parse_dict[reaction.reacting_to] = reaction_list

    def get_reactions(self, reacts_to : str):
        skill_id = self._skill_parse_dict.get(reacts_to)
        if skill_id == None:
            return []
        reaction_ids = self._reaction_parse_dict.get(skill_id)
        if reaction_ids == None:
            return []
        return reaction_ids

    def get_reactions_by_name(self, name : str):
        return list([reaction for reaction in self.reactions.values() if reaction.name == name])

    def react_to(self, actor_id, skill_id, target_id, params = {}):
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
            self.io.add_output(f"Warning: more than one reaction to {skill_id} in {actor_id}. Only executing the first one.")
        if len(final_targets) > 0:
            return final_targets[0].callback(self, actor_id, target_id, params)
        return None

    def get_skill_id(self, skill_name):
        return self._skill_parse_dict.get(skill_name)

    # def use_skill(self, caller_id, skill_name, args = []):
    #     skill_id = self._skill_parse_dict.get(skill_name)
    #     self.skills.get(skill_id).on_parsed(self, [skill_name] + args, skill_id, caller_id)

    async def tick(self):
        self.game_time += self.tick_time
        for id in self.on_tick_listeners:
            self.game_objects.get(id).on_tick(self, self.game_time, id)
        # raw = input("> ")
        # self.io.poll()
        # next_input = self.io.pop_input()
        # if next_input != None:
        # # print(Game.split_args(raw))
        #     self.parse(next_input, "")
        await asyncio.sleep(self.tick_time)
    
    def tick_sync(self):
        self.game_time += self.tick_time
        for id in self.on_tick_listeners:
            self.game_objects.get(id).on_tick(self, self.game_time, id)
        # raw = input("> ")
        self.io.poll()
        next_input = self.io.pop_input()
        if next_input != None:
        # print(Game.split_args(raw))
            self.parse(next_input, "")

    def start(self):
        # setup code
        with CursesIO() as self.io:
            self.before_start(self)
            self.io.add_output(["Try ", RichText("help", color=int(COLOR.CYAN), bold=True), " if you need help."])
            while not self.exit:
                self.tick_sync()
                time.sleep(self.tick_time)