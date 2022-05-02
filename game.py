from rich import print
from rich.table import Table
import uuid
from typing import Callable, Union, Any
from magic_rpg import *

def create_object(game : Game, name: str, description: str, location: str = None):
    new_obj = GameObject()
    new_obj.states["name"] = name
    new_obj.states["description"] = description
    if location != None:
        new_obj.states["location"] = location
    game.add_object(new_obj)
    return new_obj


def skill_look(game : "Game", args, skill_id, caller_id): # that info can kind of be bundled to an InvocationContext or similar
    caller : GameObject = game.get_by_id(caller_id)
    location = game.get_by_id(caller.states["location"])
    same_location = game.get_by_state("location",lambda loc : loc == caller.states["location"])
    location_data = game.react_to(caller.id, skill_id, location.id) # caller optional
    object_datas = [ game.react_to(caller.id, skill_id, y.id) for y in same_location ]
    
    if len(args) > 1:
        for obj in object_datas:
            if obj["name"].lower() == args[1].lower() or (obj["synonyms"] != None and args[1].lower() in obj["synonyms"]):
                game.io.add_output(f"{obj['name']}")
                game.io.add_output(f"")
                game.io.add_output(f"{obj['description']}")
                return
    object_string = ', '.join([ obj["name"] for obj in object_datas ])
    game.io.add_output(f"{location_data['name']}")
    game.io.add_output(f"{location_data['description']} You can see {object_string} here.")

def skill_create(game : "Game", args, skill_id, caller_id):
    if len(args) < 3:
        game.io.add_output("create NAME DESCRIPTION")
        return
    caller : GameObject() = game.get_by_id(caller_id)
    location = game.get_by_id(caller.states["location"])

    new_obj = create_object(game, args[1], args[2], location.id)
    
    generic_look : str = game.get_reactions("look")[0] # need a better unique identifier for things like this

    new_obj.reactions.add(generic_look)

def reaction_look_visible(game : "Game", looker_id, self_id) -> dict:
    # print ( "Calling reaction_look_visible" )
    myself : GameObject = game.get_by_id(self_id)
    return { "name": myself.states.get("name"), "description": myself.states.get("description"), "synonyms": myself.states.get("synonyms") }


def game_setup(game : Game):

    look_skill = Skill("look", on_parsed=skill_look)
    create_skill = Skill("create", on_parsed=skill_create)
    look_reaction_visible = Reaction(look_skill.id, reaction_look_visible)

    room = create_object(game, "A room", "A small room.")
    player = create_object(game, "Hero", "You look very handsome.", room.id)
    box = create_object(game, "Box", "It's a box", room.id)
    
    game.add_skill(look_skill)
    game.add_skill(create_skill)
    game.add_reaction(look_reaction_visible)
    player.skills.add(look_skill.id)
    player.skills.add(create_skill.id)
    player.reactions.add(look_reaction_visible.id)
    room.reactions.add(look_reaction_visible.id)
    box.reactions.add(look_reaction_visible.id)
    game.player_id = player.id

if __name__ == "__main__":
    gm = Game()
    gm.before_start = game_setup
    gm.start()