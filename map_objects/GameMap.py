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
    explored = [[]]
    tileset_tiles = [[]]
    char_tiles = [[]]

    def __init__(self, width, height, dungeon_level=1):
        super(GameMap, self).__init__(width, height)
        # Map Variables
        self.dungeon_level = dungeon_level
        self.spawn_chances = {'mobs': {},
                              'items': {}}  # Used to display dungeon level stats
        self.tile_set = obtain_tile_set()
        self.rooms = {}
        self.encounters = []  # Used to keep track of entities in the same group, centered on a room
        self.entrances = []
        self.player = None
        self.map_objects = []
        self.level = ''
        self.map = None

    def initialize_open_map(self):
        # Set Entire Map to Open Floor
        self.explored = [[False for y in range(self.width)] for x in range(self.height)]
        blank_tile = self.tile_set['2'].get('char')
        self.char_tiles = [[blank_tile for y in range(self.width)] for x in range(self.height)]
        self.tileset_tiles = [[2 for y in range(self.width)] for x in range(self.height)]

        for x in range(self.height):
            for y in range(self.width):
                self.walkable[x][y] = True
                self.transparent[x][y] = True
                self.fov[x][y] = True

    def initialize_closed_map(self):
        # Set Entire Map to Closed Walls
        self.explored = [[False for y in range(self.width)] for x in range(self.height)]
        blank_tile = self.tile_set['1'].get('char')
        self.char_tiles = [[blank_tile for y in range(self.width)] for x in range(self.height)]
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
                                 map_height, player, entities, item_table, mob_table, furniture_table)
        # TODO: Make furniture entities a part of the map that updates once.
        # Place Furniture Entities
        # for f in self.map_objects:
        #     print('char:', f.char, f.name, f.json_index)
        #     place_tile(self, f.x, f.y, f.json_index)

            # self.tiles[f.y][f.x] = f.char
            # if not f.furniture.walkable:
            #     self.walkable[f.y][f.x] = False




        # for row in self.tileset_tiles:
        #     print(row)
        # for row in self.char_tiles:
        #     print(row)

        # Generation Stats
        # mob_count = {}
        # item_count = {}
        # furniture_count = {}
        # for e in entities:
        #     if e.ai:
        #         if e.name in mob_count:
        #             mob_count[e.name] += 1
        #         else:
        #             mob_count[e.name] = 1
        #     elif e.item or e.equippable:
        #         if e.name in item_count:
        #             item_count[e.name] += 1
        #         else:
        #             item_count[e.name] = 0
        #     elif e.map_object:
        #         if e.name in furniture_count:
        #             furniture_count[e.name] += 1
        #         else:
        #             furniture_count[e.name] = 0
        #
        # print('\nMob List:')
        # for mob, count in mob_count.items():
        #     print('\t%s: %s' % (mob, count))
        # print('\nItem List:')
        # for item, count in item_count.items():
        #     print('\t%s: %s' % (item, count))
        # print('\nFurniture List:')
        # for furniture, count in furniture_count.items():
        #     print('\t%s: %s' % (furniture, count))


        # for room in self.rooms:1
        # self.transparent[player.y][player.x] = False  # block new position

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
