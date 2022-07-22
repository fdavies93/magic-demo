from magic_rpg import GameObject, Game, Skill, Reaction
from game.utilities import create_object
from game.skills import *
from game.reactions import *

def shouter_on_tick(game : "Game", tick_time, caller_id):
    shouter : GameObject = game.get_by_id(caller_id)
    if shouter.states.get("last_shout") + shouter.states.get("shout_frequency") < tick_time:
        shouter.states["last_shout"] = tick_time
        game.use_skill("say \"I can shout!\"", caller_id)

def game_setup(game : Game):

    look_skill = Skill("look", on_parsed=skill_look)
    create_skill = Skill("create", on_parsed=skill_create)
    go_skill = Skill("go", on_parsed=skill_go)
    # attack_skill = Skill("attack", on_parsed=skill_attack, synonyms=["hit","bash"])
    say_skill = Skill("say", on_parsed=skill_say)
    look_reaction_visible = Reaction("look_visible", look_skill.id, reaction_look_visible)
    go_reaction = Reaction("go_can_go", go_skill.id, reaction_go_can_go)
    listen_reaction = Reaction("listen_can_hear", say_skill.id, reaction_say_can_hear)

    room = create_object(game, "Room", "A small room.")
    big_room = create_object(game, "Big Room", "A much bigger room.")
    to_big_room = create_object(game, "door", "A big door.", room.id)
    to_big_room.states["destination"] = big_room.id
    to_small_room = create_object(game, "door", "A little door.", big_room.id)
    to_small_room.states["destination"] = room.id
    player = create_object(game, "Hero", "You look very handsome.", room.id)
    box = create_object(game, "Box", "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.", room.id)
    shouter = create_object(game, "Shouter", "An annoying shouty guy.", room.id, on_tick=shouter_on_tick)
    shouter.states["last_shout"] = 0
    shouter.states["shout_frequency"] = 5

    game.add_skill(look_skill)
    game.add_skill(create_skill)
    game.add_skill(go_skill)
    # game.add_skill(attack_skill)
    game.add_skill(say_skill)
    game.add_reaction(look_reaction_visible)
    game.add_reaction(listen_reaction)
    game.add_reaction(go_reaction)
    
    shouter.skills.add(say_skill.id)
    shouter.reactions.add(look_reaction_visible.id)

    player.skills.add(look_skill.id)
    player.skills.add(create_skill.id)
    player.skills.add(go_skill.id)
    # player.skills.add(attack_skill.id)
    player.skills.add(say_skill.id)
    player.reactions.add(look_reaction_visible.id)
    player.reactions.add(listen_reaction.id)
    room.reactions.add(look_reaction_visible.id)
    big_room.reactions.add(look_reaction_visible.id)
    box.reactions.add(look_reaction_visible.id)
    to_big_room.reactions.add(look_reaction_visible.id)
    to_big_room.reactions.add(go_reaction.id)
    to_small_room.reactions.add(look_reaction_visible.id)
    to_small_room.reactions.add(go_reaction.id)

    game.player_id = player.id