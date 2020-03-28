import tcod as libtcod

from GameMessages import Message
from GameStates import GameStates
from RenderFunctions import RenderOrder


def kill_player(player):
    player.char = '%'
    player.color = libtcod.dark_red

    # return 'You died!', GameStates.PLAYER_DEAD
    return Message('You died!', libtcod.red), GameStates.PLAYER_DEAD


def kill_monster(monster):
    # death_message = '%s is dead!' % monster.name.capitalize()
    death_message = Message('%s is dead!' % monster.name.capitalize(), libtcod.orange)

    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of %s' % monster.name
    monster.render_order = RenderOrder.CORPSE

    return death_message
