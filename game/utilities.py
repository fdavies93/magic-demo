from magic_rpg import Game, GameObject

def create_object(game : Game, name: str, description: str, location: str = None, on_tick = None, id = None):
    new_obj = GameObject(id)
    new_obj.states["name"] = name
    new_obj.states["description"] = description
    if location != None:
        new_obj.states["location"] = location
    game.add_object(new_obj)
    new_obj.on_tick = on_tick
    if on_tick != None:
        game.register_on_tick(new_obj.id)
    return new_obj

def get_in_location(game : Game, location_id):
    return game.get_by_state("location", lambda loc : loc == location_id)

def get_visible(game : Game, caller_id):
    caller : GameObject = game.get_by_id(caller_id)
    location = game.get_by_id(caller.states["location"])
    same_location = get_in_location(game, caller.states.get("location"))
    return [ game.react_to(caller.id, game.get_skill_id("look"), y.id) for y in same_location ]

def get_target(game : Game, caller_id, target_name):
    target = None
    
    for obj in get_visible(game, caller_id):
        if obj["name"].lower() == target_name.lower():
            target = obj
            break
    
    return target

def get_first_with_name(game : Game, name : str):
    return game.get_by_state( "name", lambda nm : nm == name )