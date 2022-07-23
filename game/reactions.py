from magic_rpg import Game, GameObject, Reaction
from interfaces.magic_io import RichText, COLOR

def reaction_look_visible(game : "Game", looker_id, self_id, params) -> dict:
    # print ( "Calling reaction_look_visible" )
    myself : GameObject = game.get_by_id(self_id)
    return { "id": myself.id, "name": myself.states.get("name"), "description": myself.states.get("description"), "synonyms": myself.states.get("synonyms") }

def reaction_say_can_hear(game: "Game", speaker_id, self_id, params) -> dict:
    speaker : GameObject = game.get_by_id(speaker_id)
    game.interface.send_to(self_id, [RichText(speaker.states.get("name") + ": ", COLOR.YELLOW), params["words"]])
    # game.io.add_output([RichText(speaker.states.get("name") + ": ", COLOR.YELLOW), params["words"]])
    return {}

def reaction_go_can_go(game : "Game", enter_id, self_id, params) -> dict:
    myself : GameObject = game.get_by_id(self_id)
    return { "location_id": myself.states.get("destination") }

REACTIONS = { 
    Reaction("look_visible", "look", reaction_look_visible),
    Reaction("go_can_go", "go", reaction_go_can_go),
    Reaction("listen_can_hear", "say", reaction_say_can_hear)
}