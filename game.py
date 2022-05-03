from rich import print
from rich.table import Table
import uuid
from typing import Callable, Union, Any
from magic_rpg import *
from magic_io import RichText, COLOR

def create_object(game : Game, name: str, description: str, location: str = None):
    new_obj = GameObject()
    new_obj.states["name"] = name
    new_obj.states["description"] = description
    if location != None:
        new_obj.states["location"] = location
    game.add_object(new_obj)
    return new_obj

def get_in_location(game : Game, location_id):
    return game.get_by_state("location", lambda loc : loc == location_id)

def get_visible(game : Game, caller_id):
    caller : GameObject = game.get_by_id(caller_id)
    location = game.get_by_id(caller.states["location"])
    same_location = get_in_location(game, caller.states.get("location"))
    return [ game.react_to(caller.id, game.get_skill_id("look"), y.id) for y in same_location ]

def skill_look(game : "Game", args, skill_id, caller_id): # that info can kind of be bundled to an InvocationContext or similar
    caller : GameObject = game.get_by_id(caller_id)
    location = game.get_by_id(caller.states["location"])
    same_location = get_in_location(game, location.id)
    location_data = game.react_to(caller.id, skill_id, location.id) # caller optional
    object_datas = [ game.react_to(caller.id, skill_id, y.id) for y in same_location ]
    
    if len(args) > 1:
        for obj in object_datas:
            if obj["name"].lower() == args[1].lower() or (obj["synonyms"] != None and args[1].lower() in obj["synonyms"]):
                game.io.add_output(RichText(obj['name'], COLOR.YELLOW))
                game.io.add_output(f"{obj['description']}")
                return
    object_string = ', '.join([ obj["name"] for obj in object_datas ])
    game.io.add_output(RichText(location_data['name'], COLOR.YELLOW))
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

def skill_go(game : "Game", args, skill_id, caller_id):
    if len(args) < 2:
        game.io.add_output("go EXIT")
        return
    target = None
    
    for obj in get_visible(game, caller_id):
        if obj["name"].lower() == args[1].lower():
            target = obj
            break
    
    if target == None:
        game.io.add_output("You can't see that.")
        return
    
    destination_data = game.react_to(caller_id, skill_id, target.get("id"))
    
    if destination_data == None:
        game.io.add_output("You can't go there.")
        return
    
    caller : GameObject = game.get_by_id(caller_id)
    caller.states["location"] = destination_data["location_id"]
    game.io.clear_output()
    game.use_skill(caller_id, "look")

def reaction_look_visible(game : "Game", looker_id, self_id) -> dict:
    # print ( "Calling reaction_look_visible" )
    myself : GameObject = game.get_by_id(self_id)
    return { "id": myself.id, "name": myself.states.get("name"), "description": myself.states.get("description"), "synonyms": myself.states.get("synonyms") }

def reaction_go_can_go(game : "Game", enter_id, self_id) -> dict:
    myself : GameObject = game.get_by_id(self_id)
    return { "location_id": myself.states.get("destination") }

def game_setup(game : Game):

    look_skill = Skill("look", on_parsed=skill_look)
    create_skill = Skill("create", on_parsed=skill_create)
    go_skill = Skill("go", on_parsed=skill_go)
    look_reaction_visible = Reaction(look_skill.id, reaction_look_visible)
    go_reaction = Reaction(go_skill.id, reaction_go_can_go)

    room = create_object(game, "Room", "A small room.")
    big_room = create_object(game, "Big Room", "A much bigger room.")
    to_big_room = create_object(game, "door", "A big door.", room.id)
    to_big_room.states["destination"] = big_room.id
    to_small_room = create_object(game, "door", "A little door.", big_room.id)
    to_small_room.states["destination"] = room.id
    player = create_object(game, "Hero", "You look very handsome.", room.id)
    box = create_object(game, "Box", "It's a box", room.id)
    
    game.add_skill(look_skill)
    game.add_skill(create_skill)
    game.add_skill(go_skill)
    game.add_reaction(look_reaction_visible)
    game.add_reaction(go_reaction)
    player.skills.add(look_skill.id)
    player.skills.add(create_skill.id)
    player.skills.add(go_skill.id)
    player.reactions.add(look_reaction_visible.id)
    room.reactions.add(look_reaction_visible.id)
    big_room.reactions.add(look_reaction_visible.id)
    box.reactions.add(look_reaction_visible.id)
    to_big_room.reactions.add(look_reaction_visible.id)
    to_big_room.reactions.add(go_reaction.id)
    to_small_room.reactions.add(look_reaction_visible.id)
    to_small_room.reactions.add(go_reaction.id)

    game.player_id = player.id

if __name__ == "__main__":
    gm = Game()
    gm.before_start = game_setup
    gm.start()