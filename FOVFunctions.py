import numpy as np

import tcod as libtcod
from tcod.map import Map
from tcod.map import compute_fov as enemy_computer_fov


def initialize_fov(game_map):
    fov_map = Map(game_map.width, game_map.height)
    for x in range(game_map.width):
        for y in range(game_map.height):
            # TODO: Verify if python 2D matrixes and numpy arrays are the same, but just reversed. :|
            fov_map.transparent[y][x] = game_map.transparent[y][x]
            fov_map.walkable[y][x] = game_map.walkable[y][x]
    return fov_map


def temp_block_vision():
    pass


def recompute_fov(fov_map, x, y, radius, light_walls=True, algorithm=0):
    fov_map.compute_fov(x, y, radius, light_walls, algorithm)


def enemy_recompute_fov(fov_map, pov, radius, light_walls, algorithm):
    return enemy_computer_fov(fov_map, pov, radius, light_walls, algorithm)


def definite_enemy_fov(fov_map, entities, radius, light_walls=True, algorithm=0):
    new_enemy_fov_map = np.zeros(fov_map.transparent.shape, dtype=bool)
    _new_enemy_fov_map = np.zeros(fov_map.transparent.shape, dtype=bool)
    # Cycle Through all Enemies and Combine FOV Map
    for e in entities:
        if e.ai:
            # Obtain Facing Direction Vector and Temporarily Block Vision
            temp_block = []
            for vx, vy in [(i, j) for i in range(-1, 2) for j in range(-1, 2)]:
                if not (vx, vy) in e.ai.direction_vector:  # don't block if within direction vector
                    tx, ty = e.x + vx, e.y + vy
                    if 0 < tx < fov_map.width and 0 < ty < fov_map.height:  # block if within map
                        fov_map.transparent[ty][tx] = False
                        temp_block.append((tx, ty))

            # Temporarily Calculate Enemy-Individual FOV
            _new_enemy_fov_map = enemy_recompute_fov(fov_map.transparent, (e.y, e.x), radius, light_walls, algorithm)

            # Remove Temporary Block
            for vx, vy in temp_block:
                if fov_map.walkable[vy][vx]:
                    fov_map.transparent[vy][vx] = True

            # Add to Main Enemy FOV Map
            new_enemy_fov_map += _new_enemy_fov_map

    return new_enemy_fov_map
