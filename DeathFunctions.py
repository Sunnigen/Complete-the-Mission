import tcod as libtcod

from GameMessages import Message
from GameStates import GameStates
from RenderFunctions import RenderOrder


def kill_player(player):
    player.char = "%"  # 37
    player.color = libtcod.dark_red

    # return 'You died!', GameStates.PLAYER_DEAD
    return Message('You died!', libtcod.red), GameStates.PLAYER_DEAD


def kill_mob(mob):
    # death_message = '%s is dead!' % mob.name.capitalize()
    death_message = Message('%s is dead!' % mob.name.capitalize(), libtcod.orange)

    mob.char = "%"  # 37
    mob.color = libtcod.dark_red
    mob.blocks = False
    mob.fighter = None
    mob.ai = None
    mob.name = 'The remains of %s' % mob.name
    mob.render_order = RenderOrder.CORPSE

    return death_message
