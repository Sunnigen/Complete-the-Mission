from copy import deepcopy
from math import ceil, sqrt
from random import choice, choices, randint, shuffle

import numpy as np
from tcod.bsp import BSP
import tcod

from components.AI import AI, DefensiveAI, FollowAI, PatrolAI, PursueAI
from components.Dialogue import Dialogue
from components.Encounter import Encounter

import EventFunctions
from level_generation.BSP import BinarySpacePartition
from level_generation.GenerationUtils import place_stairs, create_floor, create_wall, place_tile, generate_mob, \
    generate_object, place_prefab, create_item_entity
from loader_functions.JsonReader import obtain_tile_set, obtain_prefabs, obtain_mob_table, obtain_item_table
from level_generation.Prefab import Prefab
from map_objects.GameEvent import check_entity_dead, entity_at_position_condition, GameEvent, turn_count_condition
from map_objects.Shapes import MouseRoom

from RandomUtils import random_choice_from_dict, spawn_chance

TILE_SET = obtain_tile_set()
PREFABS = obtain_prefabs()
MOBS = obtain_mob_table("undergrave_prison")
ITEMS = obtain_item_table()


class UndergravePrison(BinarySpacePartition):

    game_map = None
    dungeon_level = 0
    start_room = None  # designates player location
    end_room = None  # designates stair location
    jail_cells = []  # List of all jail cells
    enemy_table = []
    possible_rooms = {"rare": [], "uncommon": [], "common":[]}

    sub_room_depth = 5  # How much to further split up each room of each cell block

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, particles, particle_systems, item_table, mob_table):
        self.width = map_width - 1
        self.height = map_height - 1
        # self.width = randint(30, map_width - 1)
        # self.height = randint(30, map_height - 1)
        self.game_map = game_map
        self.dungeon_level = dungeon_level
        self.jail_cells = []
        self.enemy_table = []

        # Generate Loot/Enemy Table
        if self.dungeon_level == 1:

            # self.possible_rooms['uncommon'] = ['armory', 'supply_room']
            self.pre_load_map(entities, particles)

        elif self.dungeon_level == 5:
            # self.possible_rooms['rare'] = ['kitchen','office', 'alarm_room', 'torture_room', 'portal_room', 'hard_monster_room',
            #                                'guard_dormitory']

            self.pre_load_map(entities, particles)

        # elif self.dungeon_level == 5:
        #     self.pre_load_map('mid_level')
        # elif self.dungeon_level == 10:
        #     self.pre_load_map('end_game')

        else:
            # self.possible_rooms['rare'] = ['kitchen', 'alarm_room', 'torture_room', 'portal_room', 'hard_monster_room',
            #                                'guard_dormitory']
            self.possible_rooms['rare'] = ['armory', 'armory', 'armory']
            self.possible_rooms['uncommon'] = ['armory', 'supply_room']

            # Main Jails
            if self.dungeon_level < 5:
                self.width = 30
                self.width, self.height = 30, 30
                self.cell_block_min_size = 15
                self.cell_block_depth = 2
                self.cell_block_wall_buffer = 5
                self.sub_room_depth = 3

            elif self.dungeon_level < 10:
                # Generate Cell Blocks and Their Rooms
                self.cell_block_min_size = randint(10, 30)
                self.cell_block_depth = randint(0, 10)
                self.cell_block_wall_buffer = randint(1, 10)
                self.sub_room_depth = randint(2, 20)

            print('\n\n{}\nWidth, Height: ({}, {})\ncell_block_depth: {}\ncell_block_size: {}\ncell_block_wall_buffer: {}\nsub_room_depth: {}'.format(
                game_map.level.title(), self.width, self.height,  self.cell_block_depth, self.cell_block_min_size, self.cell_block_wall_buffer, self.sub_room_depth))

            # Random Room Generated
            self.generate()

            # Terrain and Doodads
            self.assign_terrain(entities, particles)

            # Placement of Player and Stairs
            self.random_place_player_stairs(entities, particles)

            # Place Prisoners
            self.generate_prisoners(entities)

            # Place Mobs
            self.generate_guards(entities, particles)

        # Random Events
        # mobs = ['undergrave_guard', 'undergrave_dog']
        # conditions = [turn_count_condition]
        # condition_kwargs = {"game_map": self.game_map, "turn_count": 5}
        # game_event = GameEvent(self.game_map, 'spawn_mob', conditions=conditions, condition_kwargs=condition_kwargs,
        #                        position=center(self.start_room), mobs=[choice(mobs) for i in range(2)],
        #                        faction='Imperials', ai_type=FollowAI, area_of_interest=self.start_room,
        #                        target_entity=self.game_map.player, follow_entity=self.game_map.player)
        # self.game_map.game_events.append(game_event)
        # Update Game Map
        game_map.rooms = self.rooms
        game_map.sub_rooms = self.sub_rooms

    def pre_load_map(self, entities, particles):
        if self.dungeon_level == 1:
            self.possible_rooms['rare'] = ['armory', 'alarm_room']
            self.width = 50
            self.height = 50
            self.initialize_grid()

            self.start_room = BSP(x=1, y=10, width=9, height=9)
            self.rooms[self.start_room] = []

            self.end_room = BSP(x=40, y=10, width=9, height=9)
            self.rooms[self.end_room] = []

            main_room = BSP(x=11, y=1, width=28, height=28)
            main_room.split_recursive(
                depth=self.cell_block_depth * 2,
                min_width=self.cell_block_min_size//2,
                min_height=self.cell_block_min_size//2,
                max_horizontal_ratio=1.25,
                max_vertical_ratio=1.25
            )
            self.rooms[main_room] = []

            # Generate Cell Blocks
            for cell in self.rooms.keys():
                self.create_walled_room(cell, self.cell_block_wall_buffer)

            # self.rooms.pop(self.start_room)

            for node in main_room.pre_order():
                if not node.children:
                    self.create_walled_room(node, 0)
                    self.rooms[main_room].append(node)
                    self.sub_rooms.append(node)

            self.sub_rooms.append(self.end_room)

            # for sub_room_list in self.rooms.values():
            #     for sub_room in sub_room_list:
            #         # self.create_walled_room(sub_room, self.cell_block_wall_buffer)
            #         self.sub_rooms.append(sub_room)

            # Manually Connect Cell Blocks
            for x in range(9, 12):
                for y in range(13, 16):
                    self.grid[x][y] = 0
                    create_floor(self.game_map, x, y)
            for x in range(39, 41):
                for y in range(11, 18):
                    self.grid[x][y] = 0
                    create_floor(self.game_map, x, y)

            # Connect All Rooms
            self.connect_rooms(self.rooms[main_room])

            # Connect Cell Blocks
            # self.connect_cell_blocks()

            # Terrain and Doodads
            self.assign_terrain(entities, particles)

            # Place Player/Stairs
            self.game_map.player.position.x, self.game_map.player.position.y = (2, 14)
            # self.game_map.player.position.x, self.game_map.player.position.y = (40, 14)
            self.game_map.tile_cost[self.game_map.player.position.y][self.game_map.player.position.x] = 99

            place_stairs(self.game_map, self.dungeon_level, 44, 14)

            # Populate Rooms
            self.generate_prisoners(entities)
            self.generate_guards(entities, particles)

            # Player Jail Room
            self.generate_jail_cell(self.start_room, self.start_room, 0, 0, 0, -6, 0, entities, particles)

            # Add Patrols Appearing from Top Floor
            conditions = [turn_count_condition]
            condition_kwargs = {"turn_count": 25, "game_map": self.game_map}
            mobs = ['undergrave_guard']
            game_event = GameEvent(self.game_map, 'spawn_mob', conditions=conditions, condition_kwargs=condition_kwargs,
                                   position=center(self.end_room),
                                   mobs=[choice(mobs) for i in range(1)], faction='Imperials',
                                   ai_type=PatrolAI, area_of_interest=self.end_room)
            self.game_map.game_events.append(game_event)

            # Add 2nd Patrols Appearing from Top Floor
            conditions = [turn_count_condition]
            condition_kwargs = {"turn_count": 50, "game_map": self.game_map}
            mobs = ['undergrave_guard']
            game_event = GameEvent(self.game_map, 'spawn_mob', conditions=conditions, condition_kwargs=condition_kwargs,
                                   position=center(self.end_room),
                                   mobs=[choice(mobs) for i in range(1)], faction='Imperials',
                                   ai_type=PatrolAI, area_of_interest=self.end_room)
            self.game_map.game_events.append(game_event)

            # Add Permanent Guards to End Room
            # self.end_room = BSP(x=40, y=10, width=9, height=9)
            conditions = [turn_count_condition]
            condition_kwargs = {"turn_count": 75, "game_map": self.game_map}
            origin_x = randint(self.end_room.x + 2, self.end_room.x + self.end_room.width - 2)
            origin_y = randint(self.end_room.y + 2, self.end_room.y + self.end_room.height - 2)
            game_event = GameEvent(self.game_map, 'spawn_mob', conditions=conditions, condition_kwargs=condition_kwargs,
                                   position=center(self.end_room), mobs=['undergrave_guard'], faction='Imperials',
                                   ai_type=DefensiveAI, area_of_interest=self.end_room, origin_x=origin_x, origin_y=origin_y)
            self.game_map.game_events.append(game_event)

            condition_kwargs = {"turn_count": 77, "game_map": self.game_map}
            origin_x = randint(self.end_room.x + 2, self.end_room.x + self.end_room.width - 2)
            origin_y = randint(self.end_room.y + 2, self.end_room.y + self.end_room.height - 2)
            game_event = GameEvent(self.game_map, 'spawn_mob', conditions=conditions, condition_kwargs=condition_kwargs,
                                   position=center(self.end_room), mobs=['undergrave_guard'], faction='Imperials',
                                   ai_type=DefensiveAI, area_of_interest=self.end_room, origin_x=origin_x, origin_y=origin_y)
            self.game_map.game_events.append(game_event)

            condition_kwargs = {"turn_count": 79, "game_map": self.game_map}
            origin_x = randint(self.end_room.x + 2, self.end_room.x + self.end_room.width - 2)
            origin_y = randint(self.end_room.y + 2, self.end_room.y + self.end_room.height - 2)
            game_event = GameEvent(self.game_map, 'spawn_mob', conditions=conditions, condition_kwargs=condition_kwargs,
                                   position=center(self.end_room), mobs=['undergrave_guard'], faction='Imperials',
                                   ai_type=DefensiveAI, area_of_interest=self.end_room, origin_x=origin_x, origin_y=origin_y)
            self.game_map.game_events.append(game_event)

        if self.dungeon_level == 5:
            self.possible_rooms['rare'] = ['armory', 'armory', 'armory']
            self.possible_rooms['uncommon'] = ['armory', 'supply_room']
            self.width = 50
            self.height = 50
            self.initialize_grid()

            min_size = 9

            main_room = BSP(x=2, y=15, width=self.width - 3, height=20)
            self.rooms[main_room] = [main_room]
            # self.rooms[main_room] = [
            #     BSP(x=2, y=16, width=min_size, height=min_size), BSP(x=25, y=25, width=min_size, height=min_size)
            # ]

            self.start_room = BSP(x=18, y=2, width=15, height=10)
            self.rooms[self.start_room] = []

            self.end_room = BSP(x=18, y=40, width=15, height=9)
            self.rooms[self.end_room] = []

            # Generate Cell Blocks
            for cell in self.rooms.keys():
                self.create_walled_room(cell, self.cell_block_wall_buffer)

            # Connect Cell Blocks
            self.connect_cell_blocks()

            self.sub_rooms.append(self.start_room)
            self.sub_rooms.append(self.end_room)

            # Generate Specific Rooms
            for sub_room_list in self.rooms.values():
                for sub_room in sub_room_list:
                    # self.create_walled_room(sub_room, self.cell_block_wall_buffer)
                    self.sub_rooms.append(sub_room)

            # self.rooms[self.start_room] = [self.start_room]
            # self.rooms[self.end_room] = [self.end_room]

            # Open Side for Door
            self.grid[10][20] = 0
            self.grid[25][29] = 0

            # Terrain and Doodads
            self.assign_terrain(entities, particles)

            # Specific Terrain

            # Jail Opening for Player/Stairs
            for i in range(19, 19 + 13):
                place_tile(self.game_map, i, 8, "14")
            place_tile(self.game_map, 25, 8, "2")
            place_tile(self.game_map, 24, 34, "14")
            place_tile(self.game_map, 26, 34, "14")

            # Placement of Player and Stairs
            # x, y = self.find_open_spawn_spot(self.start_room, entities, particles)
            self.game_map.player.position.x, self.game_map.player.position.y = (25, 4)
            self.game_map.tile_cost[self.game_map.player.position.y][self.game_map.player.position.x] = 99

            # Attempt to Find an Empty Space to Place Player
            # x, y = self.find_open_spawn_spot(self.end_room, entities, particles)
            place_stairs(self.game_map, self.dungeon_level, 25, 46)

            # Populate Rooms
            self.generate_prisoners(entities)

            # Warden Boss
            mob_index = "warden"
            mob_stats = MOBS.get(mob_index)
            faction = 'Imperials'
            ai_type = PursueAI
            encounter = Encounter(self.game_map, main_room, len(self.game_map.encounters) + 1)

            x, y = self.find_open_spawn_spot(main_room, entities, particles)
            warden_mob = generate_mob(x, y, mob_stats, mob_index, encounter, faction, ai_type, entities)
            entities.append(warden_mob)

            # Check Warden is Dead and Player Goes to Iron Gate
            map_object_index = "35"
            map_object_stats = TILE_SET.get(map_object_index)
            iron_gate_entity = generate_object(25, 34, entities, self.game_map.map_objects, particles, self.game_map,
                                               map_object_stats, map_object_index)
            conditions = [entity_at_position_condition, check_entity_dead]
            condition_kwargs = {"area_of_interest": (24, 26, 33, 35), "entity": self.game_map.player,
                                'target_entity': warden_mob}
            game_event = GameEvent(self.game_map, 'open_gate', conditions=conditions, condition_kwargs=condition_kwargs,
                                   map_objects=[iron_gate_entity])
            self.game_map.game_events.append(game_event)

    def assign_terrain(self, entities, particles):
        # Place Floor
        self.game_map.initialize_closed_map()
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[x][y] == 0:

                    create_floor(self.game_map, x, y)
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

        # Special Rooms
        rare_rooms = deepcopy(self.possible_rooms['rare'])
        uncommon_rooms = deepcopy(self.possible_rooms['uncommon'])

        shuffle(rare_rooms)
        shuffle(uncommon_rooms)
        """
       treasure_room', 'hard_monster_room', 'animal_prisoner_room
       alarm_room', 'small_jail_cell', 'supply_room', 'food_storage_room', 'office_room

       Jail Cell
           - Weak prisoner
           - Bed
           - Shackles
              - Armory
       - Supply/Food
       - Administrative/Guard Room
           - Documents containing which prisoners have something of interest
               - Special Items
               -
       - Alarm Room
       - Living Quarters
        """

        # Generate Sub Rooms
        for room_list in self.rooms.values():
            if not room_list:
                continue
            print('\n\nThere are {} rooms in this cell block.'.format(len([room for room in room_list])))

            # node for node in bsp.pre_order() if not node.children
            for room in room_list:
                # print(room)
                # Find Entrances Around Each Room
                entrances = []
                for x in range(room.x, room.x + room.width + 1):
                    for y in range(room.y, room.y + room.height + 1):
                        if self.grid[x][y] == 0:
                            if x == room.x or \
                                    x == room.x + room.width or \
                                    y == room.y or \
                                    y == room.y + room.height:
                                entrances.append((x, y))

                # Place Doors in Openings that Are (1) Cell wide
                # print('entrances:', entrances)
                for e in entrances:
                    x1, y1 = e
                    too_close = False
                    for x2, y2 in entrances:
                        if (x2, y2) == (x1, y1):
                            continue
                        dist = manhattan_distance(x1, y1, x2, y2)

                        if dist == 1:
                            too_close = True
                            break

                    if not too_close:
                        door_index = "5"
                        door_stats = TILE_SET.get(door_index)
                        generate_object(x1, y1, entities, self.game_map.map_objects, particles, self.game_map, door_stats,
                                    door_index, item_list=None)

                # Seperate Room into sections for small rooms
                bsp = tcod.bsp.BSP(x=room.x, y=room.y, width=room.width, height=room.height)
                bsp.split_recursive(
                    depth=self.sub_room_depth,
                    # depth=randint(5, 10),
                    min_width=9,
                    min_height=9,
                    max_horizontal_ratio=1.5,
                    max_vertical_ratio=1.5
                )

                # Count All Nodes that Are an Actual Room
                actual_rooms = [node for node in bsp.pre_order() if not node.children and node.width > 0 and node.height > 0]

                # Select Unique Room Type
                room_type = ''
                if rare_rooms and len(actual_rooms) == 1 and len(entrances) < 4:
                    # room_type = 'kitchen'
                    room_type = rare_rooms.pop()

                # print('\n\n\nThere are {} sub_rooms in this room with {}.'.format(len(actual_rooms), "%s entrance" % len(entrances) if len(entrances) == 1 else "%s entrances" % len(entrances)))
                for node in actual_rooms:
                    # Set and Find Buffers to Ensure Whatever is Placed will not block entrance
                    south_buffer = 0
                    north_buffer = 0
                    east_buffer = 0
                    west_buffer = 0
                    buffer_increment = 3

                    # Verify if North Side has Entrances
                    count = 0
                    wall_count = node.width - 1
                    for x in range(node.x, node.x + node.width):
                        if self.grid[x][node.y] == 1:
                            count += 1
                        elif (x, node.y) in entrances:
                            # Exit because an entrance exits that we do not want to block
                            count = -10
                            break

                    if count > wall_count:
                        # north_buffer -= 2
                        pass
                    else:
                        north_buffer += buffer_increment

                    # Verify if South Side has Entrances
                    count = 0
                    wall_count = node.width - 1
                    for x in range(node.x, node.x + node.width):
                        if self.grid[x][node.y + node.height] == 1:
                            count += 1
                        elif (x, node.y + node.height) in entrances:
                            # Exit because an entrance exits that we do not want to block
                            count = -10
                            break

                    if count > wall_count:
                        # south_buffer += 2
                        pass
                    else:
                        south_buffer -= buffer_increment

                    # Verify if West Side has Entrances
                    count = 0
                    wall_count = node.height - 1
                    for y in range(node.y, node.y + node.height):
                        if self.grid[node.x][y] == 1:
                            count += 1
                        elif (node.x, y) in entrances:
                            # Exit because an entrance exits that we do not want to block
                            count = -10
                            break

                    if count > wall_count:
                        # west_buffer -= 2
                        pass
                    else:
                        west_buffer += buffer_increment

                    # Verify if East Side has Entrances
                    count = 0
                    wall_count = node.height - 1
                    for y in range(node.y, node.y + node.height):
                        if self.grid[node.x + node.width][y] == 1:
                            count += 1
                        elif (node.x + node.width, y) in entrances:
                            # Exit because an entrance exits that we do not want to block
                            count = -10
                            break

                    if count > wall_count:
                        # east_buffer += 2
                        pass
                    else:
                        east_buffer -= buffer_increment

                    # Ensure Jail Doesn't Fully Block Way to Other side of Room
                    if south_buffer == -buffer_increment and north_buffer == buffer_increment and \
                            east_buffer == 0 and west_buffer == 0:
                        a = randint(0, 1)
                        if a == 1:
                            east_buffer -= buffer_increment
                        else:
                            west_buffer += buffer_increment
                    elif east_buffer == -buffer_increment and west_buffer == buffer_increment and \
                            south_buffer == 0 and north_buffer == 0:
                        a = randint(0, 1)
                        if a == 1:
                            north_buffer += buffer_increment
                        else:
                            south_buffer -= buffer_increment

                    modified_width = node.width + east_buffer - west_buffer
                    modified_height = node.height + south_buffer - north_buffer

                    if modified_height < 3 or modified_width < 3:
                        print('***modified height or width is too small***')
                        room_type  = 'storage'

                    if not room_type:

                        if uncommon_rooms:

                            room_type_population = ['jail', 'storage', "uncommon"]
                            room_weights = [60, 15, 25]
                            room_type = choices(population=room_type_population, weights=room_weights, k=1)[0]

                            if room_type == "uncommon":
                                room_type = choice(uncommon_rooms)

                        else:
                            room_type_population = ['jail', 'storage']
                            room_weights = [75, 25]
                            room_type = choices(population=room_type_population, weights=room_weights, k=1)[0]


                    # elif modified_height < 6 or modified_width < 6:
                    #     room_type = choice(['storage', 'jail', 'jail', 'jail', 'unique'])
                    # elif modified_height < 10 or modified_width < 10:
                    #     room_type = choice(['storage', 'jail', 'jail', 'jail', 'guard_dormitory', 'unique'])
                    # elif modified_height < 20 or modified_width < 20:
                    #     room_type = choice(['jail', 'jail', 'jail', 'guard_dormitory','unique'])
                    # else:
                    #     room_type = choice(['jail', 'jail', 'guard_dormitory', 'storage'])
                    #
                    # if modified_height < 3 or modified_width < 3:
                    #     room_type = 'storage'
                    # else:
                    #     room_type = 'jail'
                    # room_type = 'food_storage_room'
                    # print('\nSub Room Type: {}.'.format(room_type))
                    # print(node)

                    # 'office', 'alarm_room', 'torture_room', 'portal_room', 'hard_monster_room', 'guard_dormitory']
                    # uncommon_rooms = ['armory', 'food_storage_room', 'supply_room'

                    # Generate Room
                    if room_type == 'jail':
                        self.generate_jail_cell(node, room, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles)
                    elif room_type == 'storage':
                        self.generate_storage_room(node, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles)

                    elif room_type == 'office':
                        self.generate_storage_room(node, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles)

                    elif room_type == 'kitchen':
                        self.generate_kitchen(node, entrances, north_buffer, south_buffer, east_buffer, west_buffer,
                                              entities, particles)

                    elif room_type == 'guard_dormitory':
                        self.generate_guard_dormitory(node, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles)

                    elif room_type == 'alarm_room':
                        self.generate_alarm_room(node, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles)

                    elif room_type == 'armory':
                        self.generate_armory_room(node, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles)

                    self.game_map.mouse_rooms.append(
                        MouseRoom(node.x, node.y, node.width, node.height, room_type ))

    def generate_kitchen(self, node, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles):
        # print('\n\nkitchen')
        # print(entrances)
        # print('north_buffer: {}, south_buffer: {}, east_buffer: {}, west_buffer: {}'.format(north_buffer, south_buffer, east_buffer, west_buffer))

        # Place Tables on All Sides of Room
        # print('\n# Place Tables on All Sides of Room')
        table_index = '27'
        table_stats = TILE_SET.get(table_index)

        crate_index = '18'


        barrel_index = '19'

        stove_index = '32'
        stove_stats = TILE_SET.get(stove_index)

        sink_index = '33'
        sink_stats = TILE_SET.get(sink_index)

        required_map_objects = [stove_index, sink_index]

        for x in range(node.x + 1, node.x + node.width + 1):
            for y in range(node.y + 1, node.y + node.height + 1):
                if x == node.x + 1 or \
                        x == node.x + node.width - 1 or \
                        y == node.y + 1 or \
                        y == node.y + node.height - 1:

                    place_object = True
                    for e_x, e_y in entrances:
                        if abs(x - e_x) + abs(y - e_y) <= 2:
                            place_object = False

                    if place_object:

                        if required_map_objects:
                            map_object_index = required_map_objects.pop()
                            map_object_stats = TILE_SET.get(map_object_index)
                            generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map,
                                            map_object_stats, map_object_index)

                        if randint(1, 25) == 1:
                            # Stove Map Object and It's Stove Fire Particle
                            generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map,
                                            stove_stats, stove_index)
                        elif randint(1, 25) == 1:
                            # Sink Map Object
                            generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map,
                                            sink_stats, sink_index)
                        else:
                            food_entities = []
                            if randint(1, 5) != 1:
                                if randint(1, 50) <= 5:
                                    food_entities = [create_item_entity(choice(['meat', 'bread']), x, y)]

                                generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map,
                                                table_stats, table_index, item_list=food_entities, no_inventory=True)
                            else:

                                # Generate Crate/Barrel
                                index = choice([barrel_index, crate_index])
                                stats = TILE_SET.get(index)
                                generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map,
                                                stats, index, item_list=food_entities, no_inventory=True)

        prefab_list = [PREFABS.get("open_chest"), PREFABS.get("closed_chest")]
        table_direction = choice(['vertical', 'horizontal'])
        if table_direction == 'horizontal':
            prefab_list.extend([PREFABS.get('long_horizontal_table'), PREFABS.get('medium_horizontal_table'),
                                PREFABS.get('short_horizontal_table')])
        else:
            prefab_list.extend([PREFABS.get('long_vertical_table'), PREFABS.get('medium_vertical_table'),
                                PREFABS.get('short_vertical_table')])

        # Table Inbetween
        for x in range(node.x + 3, node.x + node.width - 2):
            for y in range(node.y + 3, node.y + node.height - 2):

                if self.game_map.walkable[y][x]:
                # if randint(1, 2) == 1 and self.game_map.walkable[y][x]:
                    if table_direction == 'horizontal':
                        if (node.x + 3) % 2 != 0 and y % 2 != 0:
                            p = Prefab()
                            p.load_template(choice(prefab_list))
                            p.x, p.y = x, y
                            if p.x + p.width < node.x + node.width - 2:
                                place_prefab(self.game_map, p, entities, particles, self.dungeon_level)

                        elif (node.x + 3) % 2 == 0 and y % 2 == 0:
                            p = Prefab()
                            p.load_template(choice(prefab_list))
                            p.x, p.y = x, y
                            if p.x + p.width < node.x + node.width - 2:
                                place_prefab(self.game_map, p, entities, particles, self.dungeon_level)
                    else:
                        if (node.y + 3) % 2 != 0 and x % 2 != 0:
                            p = Prefab()
                            p.load_template(choice(prefab_list))
                            p.x, p.y = x, y
                            if p.y + p.height < node.y + node.height - 2:
                                place_prefab(self.game_map, p, entities, particles, self.dungeon_level)

                        elif (node.y + 3) % 2 == 0 and x % 2 == 0:
                            p = Prefab()
                            p.load_template(choice(prefab_list))
                            p.x, p.y = x, y

                            if p.y + p.height < node.y + node.height - 2:
                                place_prefab(self.game_map, p, entities, particles, self.dungeon_level)

    def generate_jail_cell(self, node, room, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities,
                           particles):
        # Place Jail Cells Along Outer Edge with Pillars at Each Corner
        for x in range(node.x + west_buffer, node.x + node.width + east_buffer + 1):
            for y in range(node.y + north_buffer, node.y + node.height + south_buffer + 1):
                if x == node.x + west_buffer or \
                        x == node.x + node.width + east_buffer or \
                        y == node.y + north_buffer or \
                        y == node.y + node.height + south_buffer:

                    # Top Left Corner
                    if x == node.x + west_buffer and y == node.y + north_buffer:
                        create_wall(self.game_map, x, y)
                    # Bottom Left Corner
                    elif x == node.x + west_buffer and y == node.y + node.height + south_buffer:
                        create_wall(self.game_map, x, y)
                    # Bottom Right Corner
                    elif x == node.x + node.width + east_buffer and y == node.y + node.height + south_buffer:
                        create_wall(self.game_map, x, y)
                    # Top Right Corner
                    elif x == node.x + node.width + east_buffer and y == node.y + north_buffer:
                        create_wall(self.game_map, x, y)
                    elif self.grid[x][y] == 0:
                        place_tile(self.game_map, x, y, '14')

        # Cache Jail Location
        j = JailCell(node.x + west_buffer, node.y + north_buffer, node.width + east_buffer - west_buffer,
                     node.height + south_buffer - north_buffer, room)
        self.jail_cells.append(j)

        # Place Prefabs for Jail Cell
        number_of_beds = [PREFABS.get('prison_bed') for i in range(ceil(j.size / 20))]
        chest = choices(population=[PREFABS.get("open_chest"), PREFABS.get("closed_chest")], weights=[90, 10], k=1)[0]
        prefab_list = [PREFABS.get('toilet'),  chest]
        prefab_list.extend(number_of_beds)
        # print('number_of_beds:', number_of_beds)
        shuffle(prefab_list)
        for prefab in prefab_list:
            p = Prefab()
            p.load_template(prefab)
            tries = 0
            max_tries = 20
            while tries < max_tries:
                random_x = randint(j.x + 1, j.x + j.width - p.width)
                random_y = randint(j.y + 1, j.y + j.height - p.height)

                if self.grid[random_x][random_y] == 0 and self.game_map.tileset_tiles[random_y][random_x] == 2:
                    p.x, p.y = random_x, random_y
                    place_prefab(self.game_map, p, entities, particles, self.dungeon_level)
                    tries = max_tries
                tries += 1

        # Place Jail Cell Entrance;
        jail_gate_index = "15"
        jail_gate_stats = TILE_SET.get(jail_gate_index)
        _entrances = []
        if north_buffer != 0:
            x = j.x + j.width // 2
            y = j.y
            place_tile(self.game_map, x, y, '2')
            entrance_entity = generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map, jail_gate_stats,
                            jail_gate_index, item_list=None)
            _entrances.append(entrance_entity)
        if west_buffer != 0:
            x = j.x
            y = j.y + j.height // 2
            place_tile(self.game_map, x, y, '2')
            entrance_entity = generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map,
                                              jail_gate_stats, jail_gate_index, item_list=None)
            _entrances.append(entrance_entity)

        if south_buffer != 0:
            x = j.x + j.width // 2
            y = j.y + j.height
            place_tile(self.game_map, x, y, '2')
            entrance_entity = generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map,
                                              jail_gate_stats, jail_gate_index, item_list=None)
            _entrances.append(entrance_entity)
        if east_buffer != 0:
            x = j.x + j.width
            y = j.y + j.height // 2
            place_tile(self.game_map, x, y, '2')
            entrance_entity = generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map,
                                              jail_gate_stats, jail_gate_index, item_list=None)
            _entrances.append(entrance_entity)

        j.entrances = _entrances

    def generate_alarm_room(self, node, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles):
        p = Prefab()
        prefab = PREFABS.get("alarm_room")
        center_x, center_y = center(node)
        p.load_template(prefab, x=center_x-1, y=center_y-1)
        place_prefab(self.game_map, p, entities, particles, self.dungeon_level)

    def generate_guard_dormitory(self, node, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles):

        prefab_list = []
        for prefab_json_index in ["guard_bed", "short_vertical_table"]:
            p = Prefab()
            prefab = PREFABS.get(prefab_json_index)
            p.load_template(prefab)
            prefab_list.append(p)
        prefab_list_weights = [90, 10]

        for x in range(node.x + west_buffer + 1, node.x + node.width + east_buffer):
            for y in range(node.y + north_buffer + 1, node.y + node.height + south_buffer):
                if x % 2 == 0 and y % 4 == 0 and p.height + y <= node.y + node.height:

                    p.x, p.y = x, y
                    p = choices(population=prefab_list, weights=prefab_list_weights, k=1)[0]
                    item_on_top = False
                    if p == prefab_list[1]:
                        item_on_top = True
                    place_prefab(self.game_map, p, entities, particles, self.dungeon_level, item_on_top)

                if x % 2 == 1 and y % 4 == 0:
                    if randint(0, 100) < 5:
                        chest_index = "10"
                        chest_stats = TILE_SET.get(chest_index)
                        generate_object(x, y, entities, self.game_map.map_objects, particles,  self.game_map, chest_stats,
                                        chest_index, item_list=None, no_inventory=False)

    def generate_armory_room(self, node, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles):
        weapons = []
        armor = []
        item_frequency = 15

        for equipment, equip_dict in ITEMS.items():

            if equip_dict['item_level'] <= self.dungeon_level:
                slot = equip_dict.get('slot')
                if slot == "EquipmentSlots.OFF_HAND" or slot == "EquipmentSlots.MAIN_HAND":
                    weapons.append(equipment)
                elif slot:
                    armor.append(equipment)

        armory_items = choice([weapons, armor])
        room_size = node.width * node.height

        # Layup Type
        dice_roll = randint(1, 2)
        # if dice_roll == 1:

        # Randomly Place Items
        number_of_items = ceil(room_size // item_frequency)
        for i in range(number_of_items):
            item_index = choice(armory_items)
            x = randint(node.x + 1, node.x + node.width - 1)
            y = randint(node.y + 1, node.y + node.height - 1)
            entities.append(create_item_entity(item_index, x, y))

    def generate_storage_room(self, node, entrances, north_buffer, south_buffer, east_buffer, west_buffer, entities, particles):
        crate_barrel_chance = ['18', '19']
        center_x, center_y = center(node)
        for x in range(node.x + west_buffer, node.x + node.width + east_buffer + 1):
            for y in range(node.y + north_buffer, node.y + node.height + south_buffer + 1):
                # Check for Open Floor
                if self.grid[x][y] == 0:
                    chance = 15
                    # Check West Wall
                    if x <= node.x + self.width // 2 and west_buffer > 1:
                        chance += 40

                    # Check East Wall
                    if node.x + self.width // 2 < x and east_buffer > 1:
                        chance += 40

                    # Check North Wall
                    if node.y + self.height // 2 < y and north_buffer > 1:
                        chance += 40

                    # Check South Wall
                    if y <= node.y + self.height // 2 and south_buffer > 1:
                        chance += 40

                    dice_roll = randint(0, 100)
                    if dice_roll < chance:
                        item_entities = None
                        no_inventory = True
                        if randint(1, 6) < 2:
                            item_list = ['meat', 'bread', 'healing_potion', 'fireball_scroll', 'confusion_scroll',
                                         'lightning_scroll', 'teleport_crystal', 'blind_powder', 'poison_vial']
                            item_entities = [create_item_entity(choice(item_list))]
                            no_inventory = False

                        crate_barrel_index = choice(crate_barrel_chance)
                        crate_barrel_stats = TILE_SET.get(crate_barrel_index)
                        # place_tile(self.game_map, x, y, choice(crate_barrel_chance))
                        # x, y, entities, map_objects, game_map, object_stats, object_index, item_list=None
                        generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map, crate_barrel_stats,
                                        crate_barrel_index, item_list=item_entities, no_inventory=no_inventory)

                    else:
                        dice_roll = randint(0, 100)
                        if dice_roll < 5:
                            chest_index = "10"
                            chest_stats = TILE_SET.get(chest_index)
                            generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map, chest_stats,
                                            chest_index, item_list=None, no_inventory=False)

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

    def generate_prisoners(self, entities):
        # return
        # Place Prisoners
        max_tries = 30
        faction = "Prisoners of War"
        prisoner_pop = ["weak_prisoner", "strong_prisoner"]
        prisoner_weights = [80, 20]

        ai_type = AI

        for jail in self.jail_cells:
            encounter = Encounter(self.game_map, jail, len(self.game_map.encounters) + 1)
            entities_created = []

            number_of_mobs = ceil(jail.size / 29)

            for i in range(number_of_mobs):
                prisoner_index = choices(population=prisoner_pop, weights=prisoner_weights, k=1)[0]
                prisoner_dict = MOBS.get(prisoner_index)
                tries = 0

                # Attempt to Find an Empty Space to Place Mob
                x, y = None, None
                while tries < max_tries:
                    tries += 1
                    x = randint(jail.x + 1, jail.x + jail.width - 1)
                    y = randint(jail.y + 1, jail.y + jail.height - 1)

                    if self.game_map.walkable[y][x] and not \
                            any([entity for entity in entities if entity.position.x == x and entity.position.y == y]):
                        # Position is good
                        break
                    x, y = None, None

                # Check if Suitable Position Has Been Found
                if not x or not y:
                    continue

                # Spawn an Entity
                dialogue_component = Dialogue(['Hey! How did you get out?',
                                               'You gotta break {} outta here!'.format("us" if number_of_mobs > 1 else "me"),
                                               "I saw one of the guards had a key."
                                               ]
                                              )
                mob = generate_mob(x, y, prisoner_dict, prisoner_index, encounter, faction, ai_type, entities,
                                   dialogue_component)

                # "block" new position
                self.game_map.tile_cost[y][x] = 99
                encounter.mob_list.append(mob)
                entities_created.append(mob)

            # If Entities were Created Add Entities and Increment Encounter
            if entities_created:
                entities.extend(entities_created)
                self.game_map.encounters.append(encounter)
                jail.entities = entities_created

    def generate_guards(self, entities, particles):
        # Place Enemies Not In Jail Cells
        no_spawn_rooms = [self.start_room, self.end_room]
        _rooms = [room for cell_block in self.rooms.values() for room in cell_block if room not in no_spawn_rooms]
        faction = "Imperials"
        undergrave_mobs_table = {
            mob: spawn_chance([stats for stats in mob_stats.get('spawn_chance')], self.dungeon_level)
            for mob, mob_stats in MOBS.items()}

        if not _rooms:
            _rooms = [cell_block for cell_block in self.rooms.keys()]

        for room in _rooms:
            # ai_type_pop = [DefensiveAI, PatrolAI]
            # ai_type_weights = [80, 20]
            # ai_type = choices(population=ai_type_pop, weights=ai_type_weights, k=1)[0]
            ai_type = DefensiveAI
            # spawn_check = 2
            # spawn_check = 1
            spawn_check = randint(1, 2)

            if spawn_check == 2:
                encounter = Encounter(self.game_map, room, len(self.game_map.encounters) + 1)
                entities_created = []
                room_size = room.width * room.height

                # number_of_mobs = ceil(room_size / 60)
                number_of_mobs = 1

                for i in range(number_of_mobs):

                    # Attempt to Find an Empty Space to Place Mob
                    x, y = self.find_open_spawn_spot(room, entities, particles)

                    # Check if Suitable Position Has Been Found
                    if not x or not y:
                        continue

                    # Spawn an Entity
                    mob_index = random_choice_from_dict(undergrave_mobs_table)
                    mob_stats = MOBS[mob_index]
                    mob = generate_mob(x, y, mob_stats, mob_index, encounter, faction, ai_type, entities)

                    # "block" new mob position
                    self.game_map.tile_cost[y][x] = 99

                    encounter.mob_list.append(mob)
                    entities_created.append(mob)

                # If Entities were Created Add Entities and and Increment Encounters
                if entities_created:
                    entities.extend(entities_created)
                    self.game_map.encounters.append(encounter)



        """
        treasure_room', 'hard_monster_room', 'dead_prisoner_room
        alarm_room', 'small_jail_cell', 'supply_room', 'food_storage_room', 'office_room
        small_jail_cell', 'medium_jail_cell
        medium_jail_cell', 'large_jail_cell

        Small Jail Cell
            - Weak prisoner
            - Bed
            - Shackles
        - Medium Jail Cell
        - Large Jail Cell
        - Armory
        - Supply/Food
        - Administrative/Guard Room
            - Documents containing which prisoners have something of interest
                - Special Items
                -
        - Alarm Room
        - Living Quarters

        """

    def find_open_spawn_spot(self, room, entities, particles):
        max_tries = 30
        tries = 0
        # Attempt to Find an Empty Space to Place Mob
        x, y = None, None
        while tries < max_tries:
            tries += 1
            x = randint(room.x + 1, room.x + room.width - 1)
            y = randint(room.y + 1, room.y + room.height - 1)

            rooms_to_avoid = []
            for j in self.jail_cells:
                if j.parent_room == room:
                    rooms_to_avoid.append(j)

            # Ensure Spawn Position is not Inside Jail Cell
            if rooms_to_avoid:
                for _room in rooms_to_avoid:
                    # print('_room:', _room)
                    if _room.contains(x, y) or not self.game_map.walkable[y][x] or any([entity for entity in entities if entity.position.x == x and entity.position.y == y]):
                        # Position is good
                        x, y = None, None
                        break
                if x and y:
                    break
            else:

                if self.game_map.walkable[y][x] and not any(
                        [entity for entity in entities if entity.position.x == x and entity.position.y == y]):
                    # Position is good
                    break
                x, y = None, None

        if not x or not y:
            x, y = center(room)

        return x, y

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

    def random_place_player_stairs(self, entities, particles):
        # Sort Rooms by center_x, center_y or both
        sorting_algorithm = randint(1, 4)
        reverse_order = choice([False, True])

        rooms = [room for rooms in self.rooms.values() for room in rooms]
        if sorting_algorithm == 1:
            sorted_rooms = sorted(rooms, key=lambda z: sum(center(z)), reverse=reverse_order)
        elif sorting_algorithm == 2:
            sorted_rooms = sorted(rooms, key=lambda z: z.x, reverse=reverse_order)
        else:
            sorted_rooms = sorted(rooms, key=lambda z: z.y, reverse=reverse_order)

        # Place Player in 1st Room
        self.start_room = sorted_rooms[0]
        center_x, center_y = center(self.start_room)

        # Attempt to Find an Empty Space to Place Mob
        x, y = self.find_open_spawn_spot(self.start_room, entities, particles)

        # Check if Suitable Position Has Been Found
        if not x or not y:
            x, y = center_x, center_y

        self.game_map.player.position.x, self.game_map.player.position.y = x, y
        self.game_map.tile_cost[center_y][center_x] = 99

        # Place Stairs in Last Room
        self.end_room = sorted_rooms[-1]
        last_room_x, last_room_y = center(self.end_room)
        x, y = self.find_open_spawn_spot(self.end_room, entities, particles)
        # Check if Suitable Position Has Been Found
        if not x or not y:
            x, y = last_room_x, last_room_y
        place_stairs(self.game_map, self.dungeon_level, x, y)


class JailCell:
    x = 0
    y = 0
    width = 0
    height = 0
    entrances = []
    parent_room = None  # bsp room jail cell resides in, not the node of a room, but the entire carved out room itself
    entities = []  # entities to spawn within Jail Cell

    def __init__(self, x, y, width, height, parent_room):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.parent_room = parent_room

    def contains(self, x, y):
        return (
                self.x <= x < self.x + self.width
                and self.y <= y < self.y + self.height
        )

    @property
    def size(self):
        return self.width * self.height

    def __repr__(self):
        return "Jail Cell at (%s, %s) with width/height: (%s, %s)" % (self.x, self.y, self.width, self.height)

    @property
    def center(self):
        x = self.x + self.width // 2
        y = self.y + self.height // 2
        return x, y


def center(room):
    # Utility Used for obtaining center coordinate of rooms
    center_x = room.x + room.width // 2
    center_y = room.y + room.height // 2
    return center_x, center_y


def manual_center(x, width, y, height):
    # Utility Used for obtaining center coordinate of rooms
    center_x = x + width // 2
    center_y = y + height // 2
    return center_x, center_y


def calculate_distance(x1, y1, x2, y2):
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)


def manhattan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)
