from random import choice, randint

import tcod as libtcod
from tcod.map import Map

from loader_functions.JsonReader import obtain_item_table, obtain_mob_table, obtain_tile_set
from level_generation.FlameWoodPrison import FlameWoodPrison
from level_generation.CellularAutomata import CellularAutomataAlgorithm
from level_generation.GenerationUtils import place_tile
from level_generation.RandomWalk import RandomWalkAlgorithm
from level_generation.Tunneling import TunnelingAlgorithm
from loader_functions.DataLoaders import save_game
from GameMessages import Message


# LEVEL_GENERATION = [BSPTreeAlgorithm, CellularAutomataAlgorithm, RandomWalkAlgorithm, TunnelingAlgorithm]
# LEVEL_GENERATION = [CellularAutomataAlgorithm, RandomWalkAlgorithm, TunnelingAlgorithm]
# LEVEL_GENERATION = [RandomWalkAlgorithm]
# LEVEL_GENERATION = [CellularAutomataAlgorithm, RandomWalkAlgorithm]
# LEVEL_GENERATION = [TunnelingAlgorithm, RandomWalkAlgorithm]
# LEVEL_GENERATION = [TunnelingAlgorithm]
# LEVEL_GENERATION = [FlameWoodPrison, TunnelingAlgorithm, RandomWalkAlgorithm]
LEVEL_GENERATION = [FlameWoodPrison]

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
    def __init__(self, width, height, dungeon_level=1):
        super(GameMap, self).__init__(width, height)
        # Map Variables
        self.dungeon_level = dungeon_level
        self.explored = [[False for y in range(self.width)] for x in range(self.height)]
        self.tile_set = obtain_tile_set()
        blank_tile = self.tile_set['0'].get('char')
        self.char_tiles = [[blank_tile for y in range(self.width)] for x in range(self.height)]
        self.tileset_tiles = [[0 for y in range(self.width)] for x in range(self.height)]
        self.spawn_chances = {'mobs': {},
                              'items': {}}  # Used to display dungeon level stats
        self.rooms = []
        self.encounters = []  # Used to keep track of entities in the same group, centered on a room
        self.entrances = []
        self.player = None
        self.map_objects = []

    def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities, encounters):
        # Map Generation Variables
        self.player = player
        self.rooms = []
        if encounters:
            self.encounters = encounters
        else:
            self.encounters = []

        mob_table = obtain_mob_table()
        item_table = obtain_item_table()

        # Obtain only "Objects" from Tile Set
        furniture_table = {key: val for key, val in self.tile_set.items() if val.get('type') == 'object'}

        algorithm = choice(LEVEL_GENERATION)()  # Choose PCG and initialize it
        print('\n\nGeneration Type for Dungeon Level %s: %s' % (self.dungeon_level, algorithm.__class__))
        algorithm.generate_level(self, self.dungeon_level, max_rooms, room_min_size, room_max_size, map_width,
                                 map_height, player, entities, item_table, mob_table, furniture_table)

        # TODO: Make furniture entities a part of the map that updates once.
        # Place Furniture Entities
        for f in self.map_objects:
            print('char:', f.char, f.name, f.json_index)
            place_tile(self, f.x, f.y, f.json_index)

            # self.tiles[f.y][f.x] = f.char
            # if not f.furniture.walkable:
            #     self.walkable[f.y][f.x] = False

        # Place Doors
        for r in self.rooms:
            for ex, ey in r.entrances:
                # game_map, x, y, obj, transparent, fov, walkable
                place_tile(self, ex, ey, 5)

        for row in self.tileset_tiles:
            print(row)
        for row in self.char_tiles:
            print(row)

        # Generation Stats
        mob_count = {}
        item_count = {}
        furniture_count = {}
        for e in entities:
            if e.ai:
                if e.name in mob_count:
                    mob_count[e.name] += 1
                else:
                    mob_count[e.name] = 1
            elif e.item or e.equippable:
                if e.name in item_count:
                    item_count[e.name] += 1
                else:
                    item_count[e.name] = 0
            elif e.map_object:
                if e.name in furniture_count:
                    furniture_count[e.name] += 1
                else:
                    furniture_count[e.name] = 0

        print('\nMob List:')
        for mob, count in mob_count.items():
            print('\t%s: %s' % (mob, count))
        print('\nItem List:')
        for item, count in item_count.items():
            print('\t%s: %s' % (item, count))
        print('\nFurniture List:')
        for furniture, count in furniture_count.items():
            print('\t%s: %s' % (furniture, count))


        # for room in self.rooms:
        #     print(room.room_number)
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
        self.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'],
                      constants['map_width'], constants['map_height'], player, entities, self.encounters)

        # player.fighter.heal(player.fighter.max_hp // 2)

        message_log.add_message(Message('You advance to the next level: Dungeon Level %s!' % self.dungeon_level,
                                        libtcod.light_violet))

        return entities

    def obtain_open_floor(self, points):
        # Return list of coordinates within map and is not blocked by a wall
        # open_points = []
        #
        # for (x, y) in points:
        #     if not self.is_blocked(x, y) and self.is_within_map(x, y):
        #         open_points.append((x,y))
        open_points = [(x, y) for (x, y) in points if not self.is_blocked(x, y)]

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
