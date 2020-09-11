from enum import Enum


class GameStates(Enum):
    DEBUG_MENU = 0
    PLAYER_TURN = 1
    ENEMY_TURN = 2
    PLAYER_DEAD = 3
    SHOW_INVENTORY = 4
    DROP_INVENTORY = 5
    TARGETING = 6
    LEVEL_UP = 7
    CHARACTER_SCREEN = 8
    READ = 9
    DIALOGUE = 10
    EVENT_MESSAGE = 11
