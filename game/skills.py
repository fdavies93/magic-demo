from magic_rpg import Game, GameObject, Skill
from interfaces.magic_io import RichText, COLOR
from game.utilities import get_in_location, create_object, get_target

def send_state(game : "Game", caller_id : str, target_id : str):
    game.interface.send_to(caller_id, RichText("STATE", color=COLOR.YELLOW))
    target = game.get_by_id(target_id)
    for key, value in target.states.items():
        out = [
            RichText(key, color=COLOR.GREEN),
            f" | {str(value)}"
        ]
        game.interface.send_to(caller_id, out)

def send_reactions(game : "Game", caller_id : str, target_id : str):
    target = game.get_by_id(target_id)

    reactions = []

    for reaction_id in target.reactions:
        reaction = game.reactions.get(reaction_id)
        reactions.append(reaction.name)
    
    out = [
        RichText("REACTIONS: ", color=COLOR.YELLOW, underline=True),
        ', '.join(reactions)        
    ]

    game.interface.send_to( caller_id, out )

def send_skills(game : "Game", caller_id : str, target_id : str):
    target = game.get_by_id(target_id)

    skills = []

    for skill_id in target.skills:
        skill = game.skills.get(skill_id)
        skills.append(skill.name)
    
    out = [
        RichText("SKILLS: ", color=COLOR.YELLOW, underline=True),
        ', '.join(skills)        
    ]

    game.interface.send_to( caller_id, out )

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
                if caller.states.get("admin") == True:
                    game.interface.send_to(caller_id, RichText(f"ID of {obj.get('name')} is {obj.get('id')}.", COLOR.GREEN, bold=True))
                return
    object_string = ', '.join([ obj["name"] for obj in object_datas ])
    game.interface.send_to(caller_id, RichText(location_data['name'], COLOR.YELLOW, underline=True, bold=True))
    game.interface.send_to(caller_id, f"{location_data['description']} You can see {object_string} here.")

    if caller.states.get("admin") == True:
        game.interface.send_to(caller_id, RichText(f"ID of {location.states.get('name')} is {location.id}.", COLOR.GREEN, bold=True))

def skill_inspect(game : "Game", args, skill_id, caller_id):
    if len(args) < 2:
        game.interface.send_to(caller_id,"inspect ID")
        return

    obj = game.game_objects.get(args[1])
    if obj == None:
        game.interface.send_to(caller_id, RichText(f"Couldn't find object with id {args[1]}.", color=COLOR.RED, bold=True))
        return

    game.interface.send_to(caller_id, RichText(f"ID of {obj.states.get('name')} is {obj.id}.", COLOR.GREEN, bold=True))
    send_state(game, caller_id, obj.id)
    send_skills(game, caller_id, obj.id)
    send_reactions(game, caller_id, obj.id)

def skill_create(game : "Game", args, skill_id, caller_id):
    if len(args) < 3:
        game.interface.send_to(caller_id,"create NAME DESCRIPTION [ID]")
        return
    caller : GameObject = game.get_by_id(caller_id)
    location = game.get_by_id(caller.states["location"])

    id = None
    if len(args) == 4:
        id = args[3]
    new_obj = create_object(game, args[1], args[2], location.id, id=id)
    
    generic_look : str = game.get_reactions("look")[0] # need a better unique identifier for things like this

    new_obj.reactions.add(generic_look)

def skill_destroy(game: "Game", args, skill_id, caller_id):
    if len(args) < 2:
        game.interface.send_to(caller_id,"destroy TARGET_ID")
        return

    target = game.get_by_id(args[1])
    
    if target == None:
        game.interface.send_to(caller_id, RichText(f"Couldn't find object with id {args[1]}.", color=COLOR.RED, bold=True))    
        return
    
    game.remove_obj(args[1])
    game.interface.send_to(caller_id, RichText(f"Object with id {args[1]} removed successfully.", COLOR.GREEN, bold=True))

def skill_set(game : "Game", args, skill_id, caller_id):
    if len(args) < 4:
        game.interface.send_to(caller_id, "set TARGET_ID STATE VALUE")
        return
    
    target = game.get_by_id(args[1])
    
    if target == None:
        game.interface.send_to(caller_id, RichText(f"Couldn't find object with id {args[1]}.", color=COLOR.RED, bold=True))    
        return

    target.states[args[2]] = args[3]
    game.interface.send_to(caller_id, RichText(f"Set state {args[2]} to {args[3]} on object with id {args[1]} successfully.", COLOR.GREEN, bold=True))

def skill_unset(game : "Game", args, skill_id, caller_id):
    if len(args) < 3:
        game.interface.send_to(caller_id, "unset TARGET_ID STATE")
        return

    target = game.get_by_id(args[1])
    
    if target == None:
        game.interface.send_to(caller_id, RichText(f"Couldn't find object with id {args[1]}.", color=COLOR.RED, bold=True))    
        return

    if args[2] not in target.states:
        game.interface.send_to(caller_id, RichText(f"Object {args[1]} has no state property {args[2]}", color=COLOR.RED, bold=True))    
        return

    del target.states[args[2]]
    game.interface.send_to(caller_id, RichText(f"Unset state {args[2]} on object with id {args[1]} successfully.", COLOR.GREEN, bold=True))

def skill_list(game : "Game", args, skill_id, caller_id):
    if len(args) < 2 or args[1] not in {"objects", "reactions", "skills"}:
        game.interface.send_to(caller_id,"list [objects | reactions | skills]")
        return

    if args[1] == "skills":
        output = RichText(", ".join([skill.name for skill in game.skills.values()]), color=COLOR.GREEN)
        game.interface.send_to(caller_id, output)
    elif args[1] == "reactions":
        output = RichText(", ".join([reaction.name for reaction in game.reactions.values()]), color=COLOR.GREEN)
        game.interface.send_to(caller_id, output)
    elif args[1] == "objects":
        for object in game.game_objects.values():
            output = [
                RichText(f"{object.id}", color=COLOR.GREEN),
                f" | {object.states.get('name')}"
            ]
            game.interface.send_to(caller_id, output)

def skill_imbue(game : "Game", args, skill_id, caller_id):
    if len(args) < 4 or (len(args) == 4 and args[1] not in {"reaction", "skill"}):
        game.interface.send_to(caller_id, "imbue [reaction | skill] TARGET_ID NAME")
        return

    target = game.game_objects.get(args[2])
    
    if target == None:
        game.interface.send_to(caller_id, RichText(f"Couldn't find object with id {args[1]}.", color=COLOR.RED, bold=True))    
        return

    if args[1] == "reaction":
        reactions = game.get_reactions_by_name(args[3])
        if len(reactions) == 0:
            game.interface.send_to(caller_id, RichText(f"Couldn't find reaction with name {args[3]}.", color=COLOR.RED, bold=True))    
            return
        game.imbue_reaction(target, args[3])
    elif args[2] == "skill":
        skill = game.get_skill_id(args[3])
        if skill == None:
            game.interface.send_to(caller_id, RichText(f"Couldn't find skill with name {args[3]}.", color=COLOR.RED, bold=True))    
            return
        game.imbue_skill(target, skill)
    
    game.interface.send_to(caller_id, RichText(f"Successfully imbued {target.id} with {args[1]} {args[3]}.", color=COLOR.GREEN))

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

SKILLS = {
    Skill("look", on_parsed=skill_look),
    Skill("inspect", on_parsed=skill_inspect),
    Skill("create", on_parsed=skill_create),
    Skill("go", on_parsed=skill_go),
    Skill("say", on_parsed=skill_say),
    Skill("destroy", on_parsed=skill_destroy),
    Skill("set", on_parsed=skill_set),
    Skill("unset", on_parsed=skill_unset),
    Skill("list", on_parsed=skill_list),
    Skill("imbue", on_parsed=skill_imbue)
}