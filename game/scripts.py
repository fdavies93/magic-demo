from magic_rpg import EventDataOnTick, Game, GameObject, Script

def shouter_on_tick(game : "Game", caller_id, ev_data : EventDataOnTick):
    tick_time = ev_data.cur_time
    shouter : GameObject = game.get_by_id(caller_id)
    if shouter.states.get("last_shout") + shouter.states.get("shout_frequency") < tick_time:
        shouter.states["last_shout"] = tick_time
        game.use_skill("say \"I can shout!\"", caller_id)

SCRIPTS = {
    Script("shouter_on_tick", shouter_on_tick)
}