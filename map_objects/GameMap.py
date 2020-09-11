from collections import deque
from copy import deepcopy
from random import choice

import tcod as libtcod
from tcod.map import Map

from level_generation.GenericDungeon import generic_dungeon
from level_generation.UndergravePrison import UndergravePrison
from level_generation.ResinfaireForest import ResinFaireForest
from level_generation.GenerationUtils import place_tile
from level_generation.Overworld import Overworld
from level_generation.RandomWalk import RandomWalkAlgorithm
from level_generation.Tunneling import TunnelingAlgorithm
from loader_functions.JsonReader import obtain_item_table, obtain_mob_table, obtain_tile_set
from GameMessages import Message



# LEVEL_GENERATION = [BSPTreeAlgorithm, CellularAutomataAlgorithm, RandomWalkAlgorithm, TunnelingAlgorithm]
# LEVEL_GENERATION = [RandomWalkAlgorithm]
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

MOBS = obtain_mob_table()
ITEMS = obtain_item_table()


class GameMap(Map):
    explored = [[]]  # boolean 2d numpy array of what player has explored
    tileset_tiles = [[]]  # 2d numpy array of indexes from tile_set.json
    map_objects = []  # list of map object entities that can be interacted with  does not need to be iterated through every frame
    # char_tiles = [[]]  # 2d numpy array of just the glyphs need to see if this is still needed
    level = ''  # name of level generation algorithm
    map = None
    player = None
    stairs = None
    tile_cost = [[]]  # 2d numpy array of integers of "traversal costs" of each node

    entrances = []
    mouse_rooms = []  # Used to keep track of room types for mouse display
    encounters = []  # Used to keep track of entities in the same group, centered on a room
    rooms = {}
    temporary_vision = []  # list of coordinates that are used for temporary vision for player
    next_floor_entities = []

    default_tile = 1

    turn_count = 0
    # turn_count = None
    game_events = []
    level_message = ''

    def __init__(self, width, height, dungeon_level=1):
        super(GameMap, self).__init__(width, height)
        # Map Variables
        self.turn_count = 0
        # self.turn_count = TurnCount()
        self.dungeon_level = dungeon_level
        self.spawn_chances = {'mobs': {},
                              'items': {}}  # Used to display dungeon level stats
        self.tile_set = obtain_tile_set()

    def initialize_open_map(self):
        # Set Entire Map to Open Floor
        self.explored = [[False for x in range(self.width)] for y in range(self.height)]
        self.tile_cost = [[1 for x in range(self.width)] for y in range(self.height)]
        self.tileset_tiles = [[2 for x in range(self.width)] for y in range(self.height)]
        self.map_objects = []
        self.mouse_rooms = []

        for x in range(self.height):
            for y in range(self.width):
                self.walkable[x][y] = True
                self.transparent[x][y] = True
                self.fov[x][y] = True

    def initialize_closed_map(self):
        # Set Entire Map to Closed Walls
        self.explored = [[False for y in range(self.width)] for x in range(self.height)]
        self.tile_cost = [[0 for x in range(self.width)] for y in range(self.height)]
        self.tileset_tiles = [[1 for y in range(self.width)] for x in range(self.height)]
        self.map_objects = []
        self.mouse_rooms = []

        for x in range(self.height):
            for y in range(self.width):
                self.walkable[x][y] = False
                self.transparent[x][y] = False
                self.fov[x][y] = False

    def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities, particles,
                 particle_systems, encounters, level=None):
        # Map Generation Variables
        self.game_events = []
        self.player = player
        self.stairs = None
        self.rooms = []
        self.map = None
        self.turn_count = 0
        if encounters:
            self.encounters = encounters
        else:
            self.encounters = []

        mob_table = MOBS
        item_table = obtain_item_table()

        # Obtain only "Objects" from Tile Set
        # furniture_table = {key: val for key, val in self.tile_set.items() if val.get('type') == 'object'}

        # print('level:', level)
        # if level == 'overworld':
        #     self.default_tile = 0
        #     self.initialize_open_map()
        #     self.level = 'overworld'
        #     self.map = Overworld()
        #
        # elif level == 'undergrave':
        #     self.default_tile = 1
        #     self.initialize_closed_map()
        #     self.map = UndergravePrison()
        #     self.level = 'undergrave'
        #
        # elif level == 'resinfaire':
        #     self.default_tile = 13
        #     self.initialize_closed_map()
        #     self.map = ResinFaireForest()
        #     self.level = 'resinfaire'
        #     mob_table = obtain_mob_table("resinfaire_mobs")
        #     item_table = obtain_item_table()
        #
        # else:
        #     self.default_tile = 1
        #     self.initialize_closed_map()
        #     self.map = choice(LEVEL_GENERATION)()
        #     self.level = 'Dungeon'
        self.dungeon_level = 3
        if self.dungeon_level == 1:
            self.level_message = "You begin your journey to the Castle of Yendor.\n\nThe tales of its plagued forest, massacred-crazed townsfolk and corrupt King perplex you as to venture to find out what happened."
            self.default_tile = 13
            self.initialize_closed_map()
            self.map = ResinFaireForest()
            self.level = 'resinfaire'
            mob_table = obtain_mob_table("resinfaire_mobs")
            map_width = 30
            map_height = 45
            item_table = obtain_item_table()
        elif self.dungeon_level == 2:
            self.level_message = "As you continue through Resinfaire Forest, you begin notice the normal denizens look slightly warped.\n\n\"What must've happened?\"\n-you wonder.\n\nYou step forward cautiously."
            self.default_tile = 13
            self.initialize_closed_map()
            self.map = ResinFaireForest()
            self.level = 'resinfaire'
            mob_table = obtain_mob_table("resinfaire_mobs")
            item_table = obtain_item_table()
            map_width = 40
            map_height = 55
        elif self.dungeon_level == 3:
            self.level_message = "You see a village in the distance"
            self.default_tile = 13
            self.initialize_closed_map()
            self.map = ResinFaireForest()
            self.level = 'resinfaire'
            mob_table = obtain_mob_table("resinfaire_mobs")
            item_table = obtain_item_table()
            map_width = 55
            map_height = 55
        else:
            self.level_message = "The journey continues. You clench your weapon tightly and trudge forward."
            self.default_tile = 1
            self.initialize_closed_map()
            self.map = choice(LEVEL_GENERATION)()
            self.level = 'Dungeon'

        print('\n\nGeneration Type for Dungeon Level %s: %s' % (self.dungeon_level, self.map.__class__))
        self.map.generate_level(self, self.dungeon_level, max_rooms, room_min_size, room_max_size, map_width,
                                map_height, player, entities, particles, particle_systems, item_table, mob_table)

        # If any Other Entities Escaped to the Next Level, Add them and Find a Suitable Place
        if self.next_floor_entities:
            print('\n\nThere are next floor entities!!!')
            for e in self.next_floor_entities:
                print('\t{}'.format(e.name))
            # entities.extend(deepcopy(self.next_floor_entities))
        self.next_floor_entities = []




        # map_print = np.empty(shape=(self.height, self.width), dtype=str, order="F")
        # # Mob and Item Entities
        # for entity in entities:
        #     print(entity.json_index, entity.name)
        #     try:
        #         map_print[entity.position.y][entity.position.x] = chr(MOBS.get("%s" % entity.json_index).get("char"))
        #     except:
        #         map_print[entity.position.y][entity.position.x] = chr(ITEMS.get("%s" % entity.json_index).get("char"))

        # # Map Object Entities
        # for entity in self.map_objects:
        #     map_print[entity.position.y][entity.position.x] = chr(self.tile_set.get("%s" % entity.json_index).get("char"))
        #
        # # Terrain
        # for x in range(self.width):
        #     for y in range(self.height):
        #         if not map_print[y][x]:
        #             map_print[y][x] = self.tile_set.get("%s" % self.tileset_tiles[y][x]).get('glyph')
        #
        # # Show Entire Map
        # for row in map_print:
        #     print(" ".join(row))
        #
        # Show All Encounters
        # print('\nEncounters:')
        # for e in self.encounters:
        #     print(e)

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
        particles = []
        particle_systems = []
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
                      constants['map_width'], constants['map_height'], player, entities, particles, particle_systems,
                      self.encounters, self.level)


        message_log.add_message(Message('You advance to the next level: Dungeon Level %s!' % self.dungeon_level,
                                        libtcod.light_violet))

        # if player.fighter.hp < player.fighter.max_hp // 5:
        #     message_log.add_message(Message('You slowly lurch forward, clutching your mortal wounds', libtcod.red))
        # elif player.fighter.hp < player.fighter.max_hp // 3:
        #     message_log.add_message(Message('The pain.', libtcod.orange))
        # elif player.fighter.hp < player.fighter.max_hp // 2:
        #     message_log.add_message(Message('You take sometime to tend to your wounds.', libtcod.orange))
        # else:
        if player.fighter.hp < player.fighter.max_hp:
            message_log.add_message(Message('You take sometime to tend to your wounds.', libtcod.light_orange))
        else:
            message_log.add_message(Message('You take take a breather before trudging on.', libtcod.light_green))
        player.fighter.heal(player.fighter.max_hp)
        return entities, particles, particle_systems

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

    def check_unoccupied(self, x, y):
        return self.walkable[y][x] and self.tile_cost[y][x] < 99

    def obtain_closest_spawn_point(self, origin_x, origin_y):
        if self.check_unoccupied(origin_x, origin_y):
            return (origin_x, origin_y)

        occupied_spaces = deque()
        occupied_spaces.append((origin_x, origin_y))
        open_space = None

        while not open_space and occupied_spaces:
            x, y = occupied_spaces.popleft()
            directions = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]

            for d_x, d_y in directions:
                if self.is_within_map(d_x, d_y):
                    if self.walkable[d_y][d_x]:
                        if self.tile_cost[d_y][d_x] == 99:
                            occupied_spaces.append((d_x, d_y))
                        elif self.tile_cost[d_y][d_x] == 1:
                            # print('spawning at ({},{}), walkable:{}, tile_cost:{}'.format(d_x, d_y, self.walkable[d_y][d_x], self.tile_cost[d_y][d_x]))
                            return (d_x, d_y)

        return (None, None)

    def obtain_map_objects(self, x, y):
        for map_object in self.map_objects:
            if (map_object.position.x, map_object.position.y) == (x, y):
                return map_object

        return None