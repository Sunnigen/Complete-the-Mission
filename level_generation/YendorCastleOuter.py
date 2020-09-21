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
from map_objects.GameEvent import GameEvent, tile_index_at_position_condition
from RandomUtils import spawn_chance

TILESET = obtain_tile_set()
MOBS = obtain_mob_table("yendor_1_mobs")
PREFABS = obtain_prefabs()


class YendorCastleOuter(BinarySpacePartition):
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

            for x in range((map_width // 2), (map_width // 2)+11):  # end Room to main
                # =map_height-6-7
                place_tile(self.game_map, x, self.end_room.y+self.end_room.height, "51")
                place_tile(self.game_map, x, self.end_room.y + self.end_room.height+1, "51")

            # Place Map Objects

            # Levers
            self.create_lever_event(entities, particles)



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

    def create_lever_event(self, entities, particles):
        lever_index = "54"
        lever_stats = TILESET.get(lever_index)
        lever_entities = []
        r = None
        d = 0
        ref_coords = [(self.end_room.x, self.end_room.y), (self.start_room.x, self.start_room.y)]

        for room in self.sub_rooms:
            _d = 0
            for other_room_x, other_room_y in ref_coords:
                _d += distance(room.x, room.y, other_room_x, other_room_y)

            if _d > d:
                r = room
                d = _d

        x, y = self.obtain_point_within(r)

        if x and y:
            lever_entities.append(generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map, lever_stats,
                            lever_index, item_list=None, no_inventory=True))

            ref_coords.append((x, y))
        # Find 2nd Farthest Room
        print('Find 2nd Farthest Room')
        r = None
        d = 0
        for room in self.sub_rooms:
            _d = 0
            for other_room_x, other_room_y in ref_coords:
                _d += distance(room.x, room.y, other_room_x, other_room_y)

            if _d > d:
                r = room
                d = _d
        # print(r, _d)

        x, y = self.obtain_point_within(r)
        if x and y:
            lever_entities.append(generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map, lever_stats,
                            lever_index, item_list=None, no_inventory=True))



        # Game Event for Levers
        map_object_index = "35"
        map_object_stats = TILESET.get(map_object_index)
        iron_gate_entities = []
        for x in range(self.width // 2, self.height // 2 + 11):  # end Room to main
            # =map_height-6-7
            # place_tile(self.game_map, x, self.end_room.y + self.end_room.height, "51")
            # place_tile(self.game_map, x, self.end_room.y + self.end_room.height + 1, "51")
            iron_gate_entity = generate_object(x, self.end_room.y + self.end_room.height + 1, entities,
                                               self.game_map.map_objects, particles, self.game_map, map_object_stats,
                                               map_object_index)
            iron_gate_entities.append(iron_gate_entity)
        conditions = [tile_index_at_position_condition]
        condition_kwargs = {"tile_index": 53, "lever_entities": lever_entities}
        game_event = GameEvent(self.game_map, 'open_gate', conditions=conditions, condition_kwargs=condition_kwargs,
                               map_objects=iron_gate_entities, default_floor_tile="51")
        self.game_map.game_events.append(game_event)

    def obtain_point_within(self, room, padding=1):
        max_num_of_tries = 2 * room.width * room.height
        try_count = 0
        while try_count < max_num_of_tries:
            x = randint(room.x + padding, room.x + room.width - padding - 1)
            y = randint(room.y + padding, room.y + room.height - padding - 1)
            print(x, y)
            # Check if Spot is Open
            if self.game_map.walkable[y][x]:
                break
            else:
                x, y = None, None
            try_count += 1
        print(x, y)
        return x, y


def distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def center(self):
    x = self.x + self.width // 2
    y = self.y + self.height // 2
    return x, y