from copy import deepcopy
from random import choice, choices, randint, shuffle
from math import sqrt

import numpy as np
import tcod
from tcod.bsp import BSP

from components.AI import AI, DefensiveAI, PatrolAI
from components.Encounter import Encounter
from level_generation.BSP import BinarySpacePartition
from level_generation.MazeWithRooms import MazeWithRooms
from level_generation.GenerationUtils import generate_mobs, generate_object, place_tile, create_floor, create_wall, generate_mob, place_prefab, place_stairs, place_entities
from level_generation.Prefab import Prefab
from loader_functions.JsonReader import obtain_tile_set, obtain_prefabs, obtain_mob_table
from RandomUtils import spawn_chance


class YendorCastleInner(MazeWithRooms):

    game_map = None
    dungeon_level = 0
    width = 1
    height = 1
    start_room = None
    end_room = None

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, particles, particle_systems, item_table, mob_table):
        self.game_map = game_map
        self.dungeon_level = dungeon_level

        if self.dungeon_level == 5:
            self.width = map_width
            self.height = map_height
            self.generate(map_width, map_height)
            self.assign_terrain(entities, particles)

            # Throne Room/End Room
            room_width = 30
            room_height = 15
            x = self.map_width // 2 - room_width // 2
            y = 0
            self.end_room = self.add_custom_room(x, y, room_width, room_height, buffer=2)

            # Start Room
            room_width = 20
            room_height = 10
            x = self.map_width // 2 - room_width // 2
            y = self.map_height - room_height - 1
            self.start_room = self.add_custom_room(x, y, room_width, room_height, buffer=3)

            # Assign Player/Stair Locations
            self.game_map.player.position.x, self.game_map.player.position.y = self.map_width//2, self.map_height - 1
            # self.game_map.player.position.x, self.game_map.player.position.y = self.map_width // 2, 0
            # self.game_map.player.position.x, self.game_map.player.position.y = center(self.start_room)
            place_stairs(self.game_map, self.dungeon_level, self.map_width // 2, 0)
            # place_stairs(self.game_map, self.dungeon_level, *center(self.end_room))

            # Place Entities in each of the Sub rooms generated in Main Room
            for room in self.rooms:
            # for room in self.sub_rooms:
                place_entities(self.game_map, self.dungeon_level, room, entities, item_table, mob_table)

        game_map.rooms = self.rooms
        # game_map.sub_rooms = self.sub_rooms

    def assign_terrain(self, entities, particles):
        # Place Floor
        for y in range(self.height):
            for x in range(self.width):
                if self.level[x][y] == 0:
                    place_tile(self.game_map, x, y, "51")
                    # create_floor(self.game_map, x, y)
                    self.game_map.tile_cost[y][x] = 1


def center(self):
    x = self.x1 + self.x2 // 2
    y = self.y1 + self.y2 // 2
    return x, y
