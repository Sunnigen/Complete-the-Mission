from copy import deepcopy
from random import choice, choices, randint, shuffle
from math import sqrt

import numpy as np
import tcod
from tcod.bsp import BSP

from components.AI import AI, DefensiveAI, PatrolAI
from components.Encounter import Encounter
from level_generation.BSP import BinarySpacePartition
from level_generation.GenerationUtils import generate_mobs, generate_object, place_tile, create_floor, create_wall, generate_mob, place_prefab, place_stairs, place_entities
from level_generation.Prefab import Prefab
from loader_functions.JsonReader import obtain_tile_set, obtain_prefabs, obtain_mob_table
from RandomUtils import spawn_chance

TILESET = obtain_tile_set()
MOBS = obtain_mob_table("yendor_1_mobs")
PREFABS = obtain_prefabs()


class YendorCastle(BinarySpacePartition):
    game_map = None
    dungeon_level = 0
    sub_room_depth = 8  # How much to further split up each room of each cell block
    start_room = None
    end_room = None


    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, particles, particle_systems, item_table, mob_table):
        self.game_map = game_map
        self.dungeon_level = dungeon_level

        if self.dungeon_level == 4:
            self.width = map_width
            self.height = map_height
            self.cell_block_min_size = 15
            self.cell_block_depth = 2
            self.cell_block_wall_buffer = 5
            self.sub_room_depth = 3

            self.initialize_grid()

            self.start_room = BSP(x=map_width//2, y=map_height-6, width=10, height=6)
            # create_floor(self.game_map, (map_width//2) + 5, map_height-6)

            # self.rooms[self.start_room] = []
            # Generate Cell Blocks
            self.create_walled_room(self.start_room)

            self.end_room = BSP(x=map_width//2, y=0, width=10, height=6)
            # self.rooms[self.end_room] = []
            self.create_walled_room(self.end_room)

            main_room = BSP(x=0, y=7, width=map_width, height=map_height-6-7)
            main_room.split_recursive(
                depth=self.cell_block_depth * 2,
                min_width=self.cell_block_min_size // 2,
                min_height=self.cell_block_min_size // 2,
                max_horizontal_ratio=1.25,
                max_vertical_ratio=1.25
            )
            self.rooms[main_room] = []

            # Generate Rooms
            for cell in self.rooms.keys():
                self.create_walled_room(cell, self.cell_block_wall_buffer)
            # self.rooms.pop(self.start_room)
            for node in main_room.pre_order():
                if not node.children:
                    self.create_walled_room(node, 0)
                    self.rooms[main_room].append(node)
                    self.sub_rooms.append(node)
            self.sub_rooms.append(self.end_room)

            # Connect All Rooms
            self.connect_rooms(self.rooms[main_room])

            # Place Tiles
            self.assign_terrain(entities, particles)

            # Assign Player/Stair Locations
            self.game_map.player.position.x, self.game_map.player.position.y = center(self.start_room)
            place_stairs(self.game_map, self.dungeon_level, *center(self.end_room))

            # Connect Start, Main and End Rooms
            for x in range((map_width // 2), (map_width // 2)+11):  # start room to main
                place_tile(self.game_map, x, map_height - 6, "51")

            for x in range((map_width // 2), (map_width // 2)+11):  # end toom to main
                # =map_height-6-7
                place_tile(self.game_map, x, self.end_room.y+self.end_room.height, "51")
                place_tile(self.game_map, x, self.end_room.y + self.end_room.height+1, "51")

            # Place Entities in each of the Sub rooms generated in Main Room
            for room in self.sub_rooms:
                place_entities(self.game_map, self.dungeon_level, room, entities, item_table, mob_table)

        game_map.rooms = self.rooms
        game_map.sub_rooms = self.sub_rooms

    def assign_terrain(self, entities, particles):
        # Place Floor
        self.game_map.initialize_closed_map()
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[x][y] == 0:
                    place_tile(self.game_map, x, y, "51")
                    # create_floor(self.game_map, x, y)
                    self.game_map.tile_cost[y][x] = 1

        # Place Floor Doodads
        for y in range(self.height):
            for x in range(self.width):
                if self.game_map.tileset_tiles[y][x] == 2:
                    terrain = randint(1, 100)
                    if terrain == 1:  # puddle
                        self.generate_puddles(x, y)
                    elif terrain == 2:  # vine
                        # elif 2 <= terrain <= 10:  # vine
                        self.generate_vines(x, y)

    def generate_puddles(self, x, y):
        # Place Different Sized Puddles throughout Map
        size = randint(1, 2)
        place_tile(self.game_map, x, y, "17")
        if size == 2:
            # Iterate through different directions
            for dir_x, dir_y in [(x, y + 1), (x + 1, y), (x - 1, y), (x, y - 1), ]:
                if 0 <= dir_x < self.width and 0 <= dir_y < self.height:
                    if self.grid[dir_x][dir_y] == 0:
                        place_tile(self.game_map, dir_x, dir_y, '17')

    def generate_vines(self, x, y):
        # Create a localized Layout of SizexSize and Use Astar to make a path for vines
        size = randint(2, 5)

        localized_layout = np.array([[1 for y in range(y-size, y+size)] for x in range(x-size, x+size)] if 0 <= x < self.width and 0 <= y < self.height else 999)

        astar = tcod.path.AStar(localized_layout, diagonal=1)
        goal_x, goal_y = (randint(x - size, x + size-1) + size, randint(y-size, y + size - 1) + size)
        final_path = astar.get_path(size, size, goal_x - x, goal_y - y)

        for i, j in final_path:
            if 0 <= x + i < self.width and 0 <= y + j < self.height:
                if self.grid[x + i][y + j] == 0:
                    place_tile(self.game_map, x + i, y + j, "16")
                else:
                    break


def center(self):
    x = self.x + self.width // 2
    y = self.y + self.height // 2
    return x, y