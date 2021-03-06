from magic_rpg import GameObject, Game, Skill, Reaction
from game.utilities import create_object
from game.skills import *
from game.reactions import *
from game.scripts import *
import json

def game_setup(game : Game):

    game.add_skills(SKILLS)
    game.add_reactions(REACTIONS)
    game.add_scripts(SCRIPTS)

    room = create_object(game, "Room", "A small room.", id="room")
    big_room = create_object(game, "Big Room", "A much bigger room.", id="big_room")
    to_big_room = create_object(game, "door", "A big door.", location="room")
    to_big_room.states["destination"] = "big_room"
    to_small_room = create_object(game, "door", "A little door.", "big_room")
    to_small_room.states["destination"] = "room"
    box = create_object(game, "Box", "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.", "room")
    
    shouter = create_object(game, "Shouter", "An annoying shouty guy.", "room")
    shouter.states["last_shout"] = 0
    shouter.states["shout_frequency"] = 5

    game.register_event("tick", shouter.id, "shouter_on_tick")

    can_see = { shouter, room, big_room, box, to_big_room, to_small_room }
    can_go = { to_big_room, to_small_room }

    game.imbue_skill(shouter, "say")

    for obj in can_see:
        game.imbue_reaction(obj, "look_visible")
    
    for obj in can_go:
        game.imbue_reaction(obj, "go_can_go")

def game_state_load(game : Game, file : str):
    game.add_skills(SKILLS)
    game.add_reactions(REACTIONS)
    game.add_scripts(SCRIPTS)

    with open(file, mode="r") as f:
        state = json.load(f)
    
    game.load_state(state)

def game_state_save(game : Game, file : str):
    print(game.dump_state())
    with open(file, mode="w") as f:
        json.dump(game.dump_state(), f, indent=4)