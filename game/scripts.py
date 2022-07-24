from magic_rpg import EventDataOnTick, Game, GameObject, Script

def shouter_on_tick(game : "Game", caller_id, ev_data : EventDataOnTick):
    tick_time = ev_data.cur_time
    shouter : GameObject = game.get_by_id(caller_id)

    last_tick = float(shouter.states["last_tick"])
    shout_frequency = float(shouter.states.get("shout_frequency"))
    # scripts should be responsible for ensuring proper sanitation of data

    if tick_time % shout_frequency < last_tick % shout_frequency:
        game.use_skill("say \"I can shout!\"", caller_id)

    shouter.states["last_tick"] = tick_time % shout_frequency

SCRIPTS = {
    Script("shouter_on_tick", shouter_on_tick)
}