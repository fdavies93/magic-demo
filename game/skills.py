from magic_rpg import Game, GameObject
from interfaces.magic_io import RichText, COLOR
from game.utilities import get_in_location, create_object, get_target

def skill_look(game : "Game", args, skill_id, caller_id): # that info can kind of be bundled to an InvocationContext or similar
    caller : GameObject = game.get_by_id(caller_id)
    location = game.get_by_id(caller.states["location"])
    same_location = get_in_location(game, location.id)
    location_data = game.react_to(caller.id, skill_id, location.id) # caller optional
    object_datas = [ game.react_to(caller.id, skill_id, y.id) for y in same_location ]
    
    if len(args) > 1:
        for obj in object_datas:
            if obj["name"].lower() == args[1].lower() or (obj["synonyms"] != None and args[1].lower() in obj["synonyms"]):
                game.interface.send_to(caller_id, RichText(obj['name'], COLOR.YELLOW,underline=True, bold=True))
                game.interface.send_to(caller_id, f"{obj['description']}")
                return
    object_string = ', '.join([ obj["name"] for obj in object_datas ])
    game.interface.send_to(caller_id, RichText(location_data['name'], COLOR.YELLOW, underline=True, bold=True))
    game.interface.send_to(caller_id, f"{location_data['description']} You can see {object_string} here.")

def skill_create(game : "Game", args, skill_id, caller_id):
    if len(args) < 3:
        game.interface.send_to(caller_id,"create NAME DESCRIPTION")
        return
    caller : GameObject() = game.get_by_id(caller_id)
    location = game.get_by_id(caller.states["location"])

    new_obj = create_object(game, args[1], args[2], location.id)
    
    generic_look : str = game.get_reactions("look")[0] # need a better unique identifier for things like this

    new_obj.reactions.add(generic_look)

def skill_go(game : "Game", args, skill_id, caller_id):
    if len(args) < 2:
        game.interface.send_to(caller_id,"go EXIT")
        return
    
    target = get_target(game, caller_id, args[1])
    
    if target == None:
        game.interface.send_to(caller_id, "You can't see that.")
        return
    
    destination_data = game.react_to(caller_id, skill_id, target.get("id"))
    
    if destination_data == None:
        game.interface.send_to(caller_id, "You can't go there.")
        return
    
    caller : GameObject = game.get_by_id(caller_id)
    caller.states["location"] = destination_data["location_id"]
    # game.io.clear_output()
    game.use_skill("look", caller_id)

def skill_attack(game: "Game", args, skill_id, caller_id):
    if len(args) < 2:
        game.interface.send_to(caller_id, "attack TARGET")
        return
    
    target = get_target(game, caller_id, args[1])
    
    if target == None:
        game.interface.send_to(caller_id, "You can't see that.")
    
    attacked_data = game.react_to(caller_id, skill_id, target.get("id"))

def skill_say(game: "Game", args, skill_id, caller_id):
    if len(args) < 2:
        game.interface.send_to(caller_id, "say WORDS")
        return
    
    caller : GameObject = game.get_by_id(caller_id)
    listeners : list[GameObject] = get_in_location(game, caller.states["location"])

    for listener in listeners:
        game.react_to(caller_id, skill_id, listener.id, {"words": args[1]})