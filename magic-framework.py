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
    

def skill_look(game : "Game", args, skill_id, caller_id): # that info can kind of be bundled to an InvocationContext or similar
    caller : GameObject = game.get_by_id(caller_id)
    location = game.get_by_id(caller.states["location"])
    same_location = game.get_by_state("location",lambda loc : loc == caller.states["location"])
    location_data = game.react_to(caller.id, skill_id, location.id) # caller optional
    object_datas = [ game.react_to(caller.id, skill_id, y.id) for y in same_location ]
    
    if len(args) > 1:
        for obj in object_datas:
            if obj["name"].lower() == args[1].lower() or (obj["synonyms"] != None and args[1].lower() in obj["synonyms"]):
                print(f"[yellow]{obj['name']}[/]")
                print(f"{obj['description']}")
                return
    object_string = ', '.join([ obj["name"] for obj in object_datas ])
    print( f"[yellow]{location_data['name']}[/]")
    print( f"{location_data['description']} You can see {object_string} here.")

def reaction_look_visible(game : "Game", looker_id, self_id) -> dict:
    # print ( "Calling reaction_look_visible" )
    myself : GameObject = game.get_by_id(self_id)
    return { "name": myself.states.get("name"), "description": myself.states.get("description"), "synonyms": myself.states.get("synonyms") }

class Game:

    _default_commands = {"help": ("See this help message", help), "quit": ("Exit the game.", exit_game), "skills": ("Show your available skills (things you can do).", show_skills)}

    def __init__(self):
        self.game_objects : dict[GameObject] = dict()
        self.skills : dict[str, Skill] = dict()
        self.reactions : dict[str, Reaction] = dict()
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
        room = GameObject()
        room.states["name"] = "A room"
        room.states["description"] = "A small room."

        player = GameObject()
        player.states["name"] = "Hero"
        player.states["description"] = "You look very handsome."
        player.states["location"] = room.id

        box = GameObject()
        box.states["name"] = "Box"
        box.states["description"] = "It's a box."
        box.states["location"] = room.id

        look_skill = Skill("look", on_parsed=skill_look)
        look_reaction_visible = Reaction(look_skill.id, reaction_look_visible)
        self.game_objects[room.id] = room
        self.game_objects[player.id] = player
        self.game_objects[box.id] = box
        self.add_skill(look_skill)
        self.add_reaction(look_reaction_visible)
        player.skills.add(look_skill.id)
        player.reactions.add(look_reaction_visible.id)
        room.reactions.add(look_reaction_visible.id)
        box.reactions.add(look_reaction_visible.id)
        self.player_id = player.id
        # setup code

        print("[bright_cyan]Try help if you need help.[/bright_cyan]")
        while not self.exit:
            raw = input("> ")
            self.parse(raw)

if __name__ == "__main__":
    gm = Game()
    gm.start()