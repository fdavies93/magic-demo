from dataclasses import dataclass, asdict
import uuid
from typing import Callable, Iterable, Union, Any
from curses import wrapper
from interfaces.CursesIO import CursesIO
from interfaces.NetIO import NetIO
from interfaces.magic_io import RichText, COLOR
from copy import deepcopy
import time
import asyncio

class GameObject:
    def __init__(self, id = None):
        self.id : str = str(uuid.uuid4())
        if id != None:
            self.id = id
        self.states : dict = dict() # keys strings to some other data, usually attached / managed by skills
        self.skills : set = set() # set of *ids* of available skills
        self.reactions : set = set() # set of *ids* of reactions
        self.on_tick = None

class Skill:
    def __init__(self, name : str, description : str = "Some skill.", synonyms : list[str] = [], on_parsed : Callable[["Game", list[str], str], Any] = None):
        self.id : uuid.UUID = uuid.uuid4()
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

class Script:
    def __init__(self, name : str, callback : Callable[["Game", str, "EventData"], str]):
        self.name : str = name
        self.callback : Callable[[Game, str, "EventData"], str] = callback

@dataclass
class ListenerData:
    listener : str
    script : str

class EventData:
    pass

@dataclass
class EventDataOnTick(EventData):
    cur_time : float

def help(game : "Game", user : uuid.UUID):
    game.interface.send_to(user, "HELP")
    for cmd in Game._default_commands:
        game.interface.send_to(user, f"{cmd} | {Game._default_commands[cmd][0]}")
    # tbl = Table(title="Commands")
    # tbl.add_column("Command", justify="center", style="bright_cyan")
    # tbl.add_column("Description", justify="center")
    # for cmd in Game._default_commands:
    #     tbl.add_row(cmd, Game._default_commands[cmd][0])
    # print(tbl)

def exit_game(game : "Game"):
    game.exit = True

def show_skills(game : "Game", user):
    player : GameObject = game.game_objects[user]
    # tbl = Table(title="Skills")
    # tbl.add_column("Skill", justify="center", style="bright_cyan")
    # tbl.add_column("Description", justify="center")
    game.interface.send_to(user, "SKILLS")
    for skill_id in player.skills:
        skill : Skill = game.skills.get(skill_id)
        game.interface.send_to(user, f"{skill.name} | {skill.description}")
    # print(tbl)
    
def do_nothing(game: "Game"):
    pass


class Game:

    _default_commands = {"help": ("See this help message", help), "skills": ("Show your available skills (things you can do).", show_skills)}

    def __init__(self, tick_time = 0.0625):
        self.game_objects : dict[str, GameObject] = dict()
        self.skills : dict[str, Skill] = dict()
        self.reactions : dict[str, Reaction] = dict()
        self.scripts : dict[str, Script] = dict()
        self.listeners : dict[str, list[ListenerData]] = dict()
        self.before_start : Callable[["Game"], None] = do_nothing
        self._skill_parse_dict : dict[str, str] = dict()
        self._reaction_parse_dict : dict[str, list[str]] = dict()
        self.on_tick_listeners : set[str] = set()
        self.exit : bool = False
        self.tick_time = tick_time
        self.interface : NetIO = None
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

    def obj_to_dict(self, obj : GameObject):
        reaction_names = []
        for reaction in obj.reactions:
            reaction_names.append( self.reactions.get(reaction).name )
        skill_names = []
        for skill in obj.skills:
            skill_names.append( self.skills.get(skill).name )
        return {
            "id": obj.id,
            "state": deepcopy(obj.states),
            "reactions": reaction_names,
            "skills": skill_names
        }

    def listeners_to_dict(self):
        out = {}
        for ev, listeners in self.listeners.items():
            out[ev] = [x for x in map( lambda l : asdict(l), listeners )]
        return out

    def dump_state(self):
        return {
            "listeners": self.listeners_to_dict(),
            "objects": [x for x in map( lambda obj : self.obj_to_dict(obj), self.game_objects.values())]
        }

    def load_state(self, state_obj : dict):
        for obj in state_obj.get("objects"):
            new_obj = GameObject(obj.get("id"))
            new_obj.states = obj.get("state")
            self.imbue_reactions(new_obj, obj.get("reactions"))
            self.imbue_skills(new_obj, obj.get("skills"))
            self.add_object(new_obj)

        for ev, listeners in state_obj.get("listeners").items():
            for listener in listeners:
                self.register_event(ev, listener.get("listener"), listener.get("script"))

    def parse(self, raw : str, user):
        split = Game.split_args(raw)
        if len(split) > 0 and split[0] in Game._default_commands:
            Game._default_commands[split[0]][1](self, user)
        elif len(split) > 0 and split[0] in self._skill_parse_dict:
            # this is STILL wrong because we need the player object to be set up as a receiver for inputs
            skill_id = self._skill_parse_dict.get(split[0])
            self.skills.get(skill_id).on_parsed(self, split, skill_id, user)

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

    def add_script(self, script : Script):
        self.scripts[script.name] = script
    
    def add_scripts(self, scripts : Iterable[Script]):
        for script in scripts:
            self.add_script(script)

    def register_event(self, event_name : str, listener : str, script : str):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(ListenerData(listener, script))

    def call_event(self, event_name : str, data : EventData):
        listeners : list[ListenerData] = self.listeners.get(event_name)
        if listeners == None or not isinstance(listeners, list) or len(listeners) == 0:
            return
        for listener in listeners:
            self.scripts[listener.script].callback(self, listener.listener, data)
            
    def add_skill(self, skill : Skill):
        self.skills[skill.id] = skill
        self._skill_parse_dict[skill.name.lower()] = skill.id
        for synonym in skill.synonyms:
            self._skill_parse_dict[synonym.lower()] = skill.id

    def add_skills(self, skills : Iterable[Skill]):
        for skill in skills:
            self.add_skill(skill)

    def imbue_skill(self, obj : GameObject, skill : str):
        skill_id = self.get_skill_id(skill)
        obj.skills.add(skill_id)

    def imbue_skills(self, obj : GameObject, skills : Iterable[str]):
        for skill in skills:
            self.imbue_skill(obj, skill)

    def imbue_reaction(self, obj : GameObject, reaction : str):
        reaction_obj = self.get_reactions_by_name(reaction)[0]
        obj.reactions.add(reaction_obj.id)

    def imbue_reactions(self, obj : GameObject, reactions : Iterable[str]):
        for reaction in reactions:
            self.imbue_reaction(obj, reaction)

    def add_reactions(self, reactions : Iterable[Reaction]):
        for reaction in reactions:
            self.add_reaction(reaction)

    def add_object(self, obj : GameObject):
        self.game_objects[obj.id] = obj

    def remove_obj(self, id):
        del self.game_objects[id] # likely not very clean, but ok for now

    def register_on_tick(self, obj_id : uuid.UUID):
        self.on_tick_listeners.add(obj_id)

    def add_reaction(self, reaction : Reaction):
        self.reactions[reaction.id] = reaction
        skill_id = self.get_skill_id(reaction.reacting_to)
        reaction_list = self._reaction_parse_dict.get(skill_id)
        if reaction_list != None:
            reaction_list.append(reaction.id)
        else:
            reaction_list = [reaction.id]
        self._reaction_parse_dict[skill_id] = reaction_list

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
        self.call_event("tick", EventDataOnTick(self.game_time))
        # for id in self.on_tick_listeners:
        #     self.game_objects.get(id).on_tick(self, self.game_time, id)
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