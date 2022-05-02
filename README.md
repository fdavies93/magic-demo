[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/fd93) [![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC_BY--SA_4.0-orange.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

# MAGIC Text Adventure Framework

MAGIC, as the name suggests, is a framework for writing console-based text adventures. It leans towards the style of traditional text adventures or pen-and-paper RPGs and was originally conceived as a way for me to quickly test different logics for a pen-and-paper system I thought about many years ago -- without using dice, game pieces, etc.

If you want to understand the way the framework works, the best way is to dive into game.py, the basic demo, and take a look around.

If you want to contribute to the framework code, you can file a pull request or chat with me directly. I'm a regular on the ["Programmer's Hangout"](https://discord.com/invite/programming) Discord.

## Design Goals

The framework aims to be unopinionated, minimal and very extensible. RPG stats are not included in the framework, nor are basic verbs like "look" or "move" (although they will be in game.py). Even the basic concept of "a room" is actually just a state in an object's state dictionary; NPCs will merely be GameObjects with minds attached to them. This is a deliberate choice to solve several architecture issues with old-school MUD systems written in C.

Hard-programming features like "look" into a framework requires objects to have an ever-increasing number of flags such as "visible?" and callbacks like "reaction_to_counter_attack", ultimately leading to spaghetti code. On the other hand, while not implementing verbs into a framework leads to more verbose code, end-user developers can abstract away the complexity themselves while keeping the basic framework pristine.

**Because the framework is relatively minimal, it's recommended you implement your own methods to create basic objects and do other basic admin. The reference (game.py) will contain these.**

## Current Project Layout
* magic-battle-sim is a naive implementation of the basic concepts
* magic-rpg is a more sophisticated implementation 
* game.py is a basic demo designed to show how to implement game concepts using magic-rpg.py. It also serves as the main way of testing new features.

## Current Priorities - Framework
* Refactoring skills to allow skills to be used by NPCs.
* Refactoring skill help system to allow nesting of skill types (probably instantaneous vs. time-consuming in the reference implementation)
* Adding a save / load system for current game state (but not skills, reactions, or minds).
* Writing I/O for web hosted version.

## Current Priorities - Game.py
* Implementing exit-type objects which other objects can "go" to in order to change their current location.
* Implementing basic combat between actors using a stat system.
* Implementing a basic inventory and item system.