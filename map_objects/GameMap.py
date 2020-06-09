import numpy as np
from random import choice

import tcod as libtcod
from tcod.map import Map

from loader_functions.JsonReader import obtain_item_table, obtain_mob_table, obtain_tile_set
from level_generation.UndergravePrison import UndergravePrison
from level_generation.ResinfaireForest import ResinFaireForest
from level_generation.GenerationUtils import place_tile
from level_generation.Overworld import Overworld
from level_generation.RandomWalk import RandomWalkAlgorithm
from level_generation.Tunneling import TunnelingAlgorithm
from GameMessages import Message


# LEVEL_GENERATION = [BSPTreeAlgorithm, CellularAutomataAlgorithm, RandomWalkAlgorithm, TunnelingAlgorithm]
LEVEL_GENERATION = [RandomWalkAlgorithm, TunnelingAlgorithm]

"""
1. Tunneling Algorithm
2. BSP Tree Algorithm
3. Random Walk Algorithm
4. Cellular Automata
5. Room Addition
6. City Buildings
7. Maze with Rooms
8. Messy BSP Tree
"""


class GameMap(Map):
    explored = [[]]  # boolean 2d numpy array of what player has explored
    tileset_tiles = [[]]  # 2d numpy array of indexes from tile_set.json
    map_objects = []  # list of map object entities that can be interacted with  does not need to be iterated through every frame
    # char_tiles = [[]]  # 2d numpy array of just the glyphs need to see if this is still needed
    level = ''  # name of level generation algorithm
    map = None
    player = None
    tile_cost = [[]]  # 2d numpy array of integers of "traversal costs" of each node

    entrances = []
    encounters = []  # Used to keep track of entities in the same group, centered on a room
    rooms = {}

    def __init__(self, width, height, dungeon_level=1):
        super(GameMap, self).__init__(width, height)
        # Map Variables
        self.dungeon_level = dungeon_level
        self.spawn_chances = {'mobs': {},
                              'items': {}}  # Used to display dungeon level stats
        self.tile_set = obtain_tile_set()

    def initialize_open_map(self):
        # Set Entire Map to Open Floor
        self.explored = [[False for x in range(self.width)] for y in range(self.height)]
        self.tile_cost = [[1 for x in range(self.width)] for y in range(self.height)]
        # blank_tile = self.tile_set['2'].get('char')
        # self.char_tiles = [[blank_tile for y in range(self.width)] for x in range(self.height)]
        self.tileset_tiles = [[2 for x in range(self.width)] for y in range(self.height)]

        for x in range(self.height):
            for y in range(self.width):
                self.walkable[x][y] = True
                self.transparent[x][y] = True
                self.fov[x][y] = True

    def initialize_closed_map(self):
        # Set Entire Map to Closed Walls
        self.explored = [[False for y in range(self.width)] for x in range(self.height)]
        self.tile_cost = [[0 for x in range(self.width)] for y in range(self.height)]
        # blank_tile = self.tile_set['1'].get('char')
        # self.char_tiles = [[blank_tile for y in range(self.width)] for x in range(self.height)]
        self.tileset_tiles = [[1 for y in range(self.width)] for x in range(self.height)]

        for x in range(self.height):
            for y in range(self.width):
                self.walkable[x][y] = False
                self.transparent[x][y] = False
                self.fov[x][y] = False

    def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities, encounters, level=None):
        # Map Generation Variables
        self.player = player
        self.rooms = []
        self.map = None
        if encounters:
            self.encounters = encounters
        else:
            self.encounters = []

        mob_table = obtain_mob_table()
        item_table = obtain_item_table()

        # Obtain only "Objects" from Tile Set
        furniture_table = {key: val for key, val in self.tile_set.items() if val.get('type') == 'object'}

        # print('level:', level)
        if level == 'overworld':
            self.initialize_open_map()
            self.level = 'overworld'
            self.map = Overworld()
        elif level == 'undergrave':
            self.initialize_closed_map()
            self.map = UndergravePrison()
            self.level = 'undergrave'
        elif level == 'resinfaire':
            self.map = ResinFaireForest()
            self.level = 'resinfaire'
        else:
            self.initialize_closed_map()
            self.map = choice(LEVEL_GENERATION)()
            self.level = 'Dungeon'

        print('\n\nGeneration Type for Dungeon Level %s: %s' % (self.dungeon_level, self.map.__class__))
        self.map.generate_level(self, self.dungeon_level, max_rooms, room_min_size, room_max_size, map_width,
                                map_height, player, entities, item_table, mob_table, furniture_table
                                )

        # Show Floor Layout
        # for row in self.tiles:
        #     print(''.join(row))

    def is_within_map(self, x, y):
        return 0 <= x <= self.width - 1 and 0 <= y <= self.height - 1

    def is_blocked(self, x, y):
        if self.is_within_map(x, y):
            return not self.walkable[y][x]
        return True

    def next_floor(self, player, message_log, constants):
        # Player Advances to the Next Floor
        self.dungeon_level += 1
        entities = [player]
        self.player = player
        self.encounters = []
        self.rooms = []
        self.entrances = []
        self.map_objects = []
        for y in range(self.height):
            for x in range(self.width):
                self.walkable[y][x] = False
                self.transparent[y][x] = True
                self.fov[y][x] = True
                self.explored[y][x] = False

        print('Advancing for to next level.', self.level)
        self.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'],
                      constants['map_width'], constants['map_height'], player, entities, self.encounters, self.level)

        # player.fighter.heal(player.fighter.max_hp // 2)

        message_log.add_message(Message('You advance to the next level: Dungeon Level %s!' % self.dungeon_level,
                                        libtcod.light_violet))

        return entities

    def obtain_open_floor(self, points):
        # print('obtain_open_floor', points)
        # Return list of coordinates within map and is not blocked by a wall
        open_points = []
        #
        for (x, y) in points:
            if self.walkable[y][x] and self.is_within_map(x, y):
            # if self.is_blocked(x, y) and self.is_within_map(x, y):
                open_points.append((x,y))
        # open_points = [(x, y) for (x, y) in points if self.is_blocked(x, y)]

        return open_points

    @property
    def spawn_rates(self):
        # TODO: Figure out why this doesn't store values correctly
        # a = {characteristic: [name, stats] for characteristic, table in
        #                self.spawn_chances.items() for name, stats in table.items()}

        a = {}
        return self.spawn_chances

    def print_spawn_rates(self):
        for characteristic, table in self.spawn_chances.items():
            print(characteristic)
            for name, stats in table.items():
                print('\t', name, stats)
