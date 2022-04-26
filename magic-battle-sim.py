import math as math
from dataclasses import dataclass
from abc import ABC
from rich import print
from rich.panel import Panel
from rich.table import Table
from typing import Union
import random




@dataclass
class ActorStats:
    max_hp : int = 12
    cur_hp : int = 12
    might : int = 12
    acuity : int = 12
    gymnasia : int = 12
    intellect : int = 12
    charm : int = 12

class Skill():
    def __init__(self, name : str, on_use, description: "Some skill.", synonyms : list[str] = []):
        self.name = name
        self.description = description
        self.on_use = on_use
        self.synonyms = synonyms

class Actor:
    def __init__(self, name : str, synonyms : list[str] = [], description : str = "Some actor.", is_player = False, stats : ActorStats = ActorStats(), skills : list[Skill] = []):
        self.name = name
        self.description = description
        self.synonyms = synonyms
        self.stats = stats
        self.skills = skills
        self.is_player = is_player
        self._skill_dict = dict()
        
        self._build_skill_dict()

    def has_skill(self, skill_name : str) -> bool:
        return skill_name.lower() in self._skill_dict
    
    def get_skill(self, skill_name : str) -> Union[Skill, None]:
        if self.has_skill(skill_name):
            return self._skill_dict[skill_name.lower()]
        return None
        
    def _build_skill_dict(self):
        new_skills = dict()
        for skill in self.skills:
            new_skills[skill.name] = skill
            for synonym in skill.synonyms:
                new_skills[synonym] = skill
        self._skill_dict = new_skills

class Game:

    cmdnotes = [
        ["help", "Show this help text."],
        ["quit", "Quit the game."],
        ["skills", "List your skills (things you can do)."]
    ]

    def __init__(self):
        # probably want a system to set up locations
        self.skills = {
            "look": Skill("look", skill_look, "Lets you look at things."),
            "attack": Skill("attack", skill_attack, "Lets you attack things.", synonyms=["hit", "a"])
        }
    
        player_stats = ActorStats(might=100, acuity=100, gymnasia=12)

        self.actors = [
            Actor("Monster", description="It looks scary."), 
            Actor("Hero", synonyms=["me", "self", "myself"], description="You look nice today.", stats=player_stats, is_player=True, skills=[self.skills["look"], self.skills["attack"]])
        ]
        self.quit = False
        self.commands = {
            "help": self.help,
            "skills": self.show_skills,
            "quit": self.quit_fn
        }

    def help(self, args : list[str]):
        tbl = Table(title="Commands")
        tbl.add_column("Command", justify="center", style="cyan")
        tbl.add_column("Description", justify="center")
        for cmd in Game.cmdnotes:
            tbl.add_row(cmd[0], cmd[1])
        print(tbl)

    def get_player(self) -> Union[Actor, None]:
        for actor in self.actors:
            if actor.is_player:
                return actor
        return None
    
    def get_actor(self, name : str) -> Union[Actor, None]:
        for actor in self.actors:
            lname = actor.name.lower()
            if lname == name.lower():
                return actor
            elif len(actor.synonyms) > 0:
                for syn in actor.synonyms:
                    if syn.lower() == lname:
                        return actor
        return None
            

    def describe_actor(self, actor: Actor):
        description = f"This is a [bold]{actor.name}[/]. {actor.description}"
        if len(actor.synonyms) > 0:
            description += f" Other names for them are [italic]{', '.join(actor.synonyms)}[/]"
        print (description)
        tbl = Table()
        tbl.add_column("Stat", justify="center", style="yellow")
        tbl.add_column("Number", justify="center")
        for stat in actor.stats.__dict__:
            tbl.add_row(stat.capitalize(), str(actor.stats.__dict__[stat]))
        print(tbl)
    
    def show_skills(self, args: list[str]):
        # should skills be shared between actors? or should they be unique?
        player = self.get_player()
        if len(player.skills) == 0:
            print("Sadly, you have no skills.")
            return
        tbl = Table()
        tbl.add_column("Skill", justify="center", style="yellow")
        tbl.add_column("Description", justify="center")
        for skill in player.skills:
            tbl.add_row(skill.name, skill.description)
        print (tbl)

    def quit_fn(self, args : list[str]):
        self.quit = True

    def stub(self):
        print("[cyan]I don't understand that! You can write 'help' if you need help.")

    def show_welcome(self):
        print(Panel("Welcome to the MAGIC battle simulator, a quick test for MAGIC RPG system battles. You can type [cyan]'help'[/] to get started."))

    def parse_input(self, raw : str):
        split = raw.split(" ")
        player = self.get_player()
        if len(split) > 0 and split[0] in self.commands:
            self.commands[split[0]](split)
        elif len(split) > 0 and player.has_skill(split[0]): # need a mechanism to build valid skills into a dict
            player.get_skill(split[0]).on_use(split, Context(player, self))
        else:
            self.stub()

    def start(self):
        self.show_welcome()
        while not self.quit:
            raw = input()
            self.parse_input(raw)

@dataclass
class Context:
    actor : Actor
    game : Game

def skill_look(args : list[str], context : Context):
    game = context.game
    actor = context.actor
    if len(args) < 2:
        names = [f"[bold]{actor.name}[/]" for actor in game.actors]
        print(f"Here you can see { ', '.join(names) }.")
        return

    printed = False
    for actor in game.actors:
        if actor.name.lower() == args[1].lower() or args[1].lower() in actor.synonyms: # basic disambiguation
            game.describe_actor(actor)
            printed = True
            break
    if not printed:
        print("You can't see that!")

def skill_attack(args : list[str], context : Context):
    game = context.game
    actor = context.actor
    if len(args) < 2:
        print("You need to choose a target! (Try [cyan]look[/].)")
        print("[cyan]attack[/cyan] ACTOR")
        return
    target = game.get_actor(args[1])
    if target != None:
        hit_raw = float(actor.stats.acuity) / float(target.stats.gymnasia)
        hit_dice = math.floor(hit_raw)
        fractional_hit = hit_raw % 1
        if(random.random() < fractional_hit):
            hit_dice += 1
        dice_size = math.floor(float(actor.stats.might) / 2)
        damage = 0
        for die in range(hit_dice):
            damage += random.randint(1, dice_size)
        target.stats.cur_hp -= damage
        print(f"You bash the {target.name} using {hit_dice}d{dice_size}, dealing {damage}!")
        return
    print("I can't see that target.")

def main():
    game = Game()
    game.start()

if __name__ == "__main__":
    main()