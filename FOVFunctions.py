import numpy as np

import tcod
from tcod.map import Map
from tcod.map import compute_fov


from loader_functions.JsonReader import obtain_tile_set


TILE_SET = obtain_tile_set()


def initialize_fov(game_map):
    fov_map = Map(game_map.width, game_map.height)
    for x in range(game_map.width):
        for y in range(game_map.height):
            # TODO: Verify if python 2D matrixes and numpy arrays are the same, but just reversed. :|
            fov_map.transparent[y][x] = game_map.transparent[y][x]
            fov_map.walkable[y][x] = game_map.walkable[y][x]
            fov_map.fov[y][x] = game_map.fov[y][x]
    return fov_map


def recompute_fov(fov_map, x, y, radius, entrances, light_walls=True, algorithm=0):
    # TODO: Enable FOV for an open or closed door

    for door_x, door_y in entrances:
        fov_map.transparent[door_y][door_x] = True

    fov_map.compute_fov(x, y, radius, light_walls, algorithm)


def enemy_recompute_fov(transparency_map, pov, radius, light_walls=True, algorithm=tcod.FOV_RESTRICTIVE):
    return compute_fov(transparency_map, pov, radius, light_walls, algorithm)


def definite_enemy_fov(game_map, fov_map, entrances, entities, light_walls=False, algorithm=0):
    new_enemy_fov_map = np.zeros(fov_map.transparent.shape, dtype=bool)
    _new_enemy_fov_map = np.zeros(fov_map.transparent.shape, dtype=bool)
    _entrances = entrances.copy()

    # TODO: Does it matter if AI cannot "see" the "wall"?
    light_walls = False

    # Cycle Through all Enemies and Combine FOV Map
    for e in entities:
        if e.ai and e.position:
            # Obtain Facing Direction Vector and Temporarily Block Vision
            temp_block = [(e.position.x, e.position.y)]

            if (e.position.x, e.position.y) in _entrances:
                _entrances.remove((e.position.x, e.position.y))

            # TODO: Enable FOV for an open or closed door
            for door_x, door_y in _entrances:
                fov_map.transparent[door_y][door_x] = False
                temp_block.append((door_x, door_y))

            # Place FOV "walls" to look in specific direction
            for vx, vy in [(i, j) for i in range(-1, 2) for j in range(-1, 2)]:
                if not (vx, vy) in e.ai.direction_vector:  # don't block if within direction vector
                    tx, ty = e.position.x + vx, e.position.y + vy
                    if 0 < tx < fov_map.width and 0 < ty < fov_map.height:  # block if within map
                        fov_map.transparent[ty][tx] = False
                        temp_block.append((tx, ty))

            # Temporarily Calculate Enemy-Individual FOV
            _new_enemy_fov_map = enemy_recompute_fov(fov_map.transparent, (e.position.y, e.position.x),
                                                     e.fighter.fov_range, light_walls, algorithm)

            # Update Individual Fighter FOV
            e.fighter.curr_fov_map = _new_enemy_fov_map

            # Remove Temporary Block
            for vx, vy in temp_block:
                # fov_map.transparent[vy][vx] = True
                tile = '%s' % game_map.tileset_tiles[vy][vx]
                if TILE_SET.get(tile).get("transparent"):
                # if game_map.fov[vy][vx]:
                    fov_map.transparent[vy][vx] = True

            # Add to Main Enemy FOV Map
            new_enemy_fov_map += _new_enemy_fov_map

    return new_enemy_fov_map
