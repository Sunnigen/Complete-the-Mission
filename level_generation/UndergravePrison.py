from math import sqrt
from random import choice, choices, randint, shuffle

import numpy as np
import tcod

from components.AI import PatrolMob
from components.Encounter import Encounter

from level_generation.BSP import BinarySpacePartition
from level_generation.GenerationUtils import place_stairs, create_floor, create_wall, place_tile
from level_generation.GenerationUtils import generate_mob
from loader_functions.JsonReader import obtain_tile_set, obtain_prefabs, obtain_mob_table
from level_generation.Prefab import Prefab, place_prefab

TILE_SET = obtain_tile_set()
PREFABS = obtain_prefabs()
MOBS = obtain_mob_table()


class UndergravePrison(BinarySpacePartition):

    game_map = None
    dungeon_level = 0
    start_room = None  # designates player location
    end_room = None  # designates stair location
    jail_cells = []  # List of all jail cells

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, item_table, mob_table, furniture_table):
        self.width = map_width - 1
        self.height = map_height - 1
        self.game_map = game_map
        self.dungeon_level = dungeon_level
        self.jail_cells = []

        # Generate Cell Blocks and Their Rooms
        self.cell_block_depth = randint(1, 4)
        self.cell_block_wall_buffer = randint(3, 5)
        self.generate()

        # Terrain and Doodads
        self.assign_terrain()

        # Placement of Player and Stairs
        self.place_player_stairs(entities)

        # Populate Rooms
        self.populate_rooms(entities)

        # print('entity count:', len(entities))
        # print('encounter count:', len(self.game_map.encounters))

        # Game Map
        game_map.rooms = self.rooms
        game_map.sub_rooms = self.sub_rooms

    def assign_terrain(self):
        # Place Terrain and Doodads
        self.game_map.initialize_closed_map()
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[x][y] == 0:
                    create_floor(self.game_map, x, y)

        # print(len(self.grid[0]), len(self.grid))
        for y in range(self.height):
            for x in range(self.width):
                if self.game_map.tileset_tiles[y][x] == 2:
                    terrain = randint(1, 50)
                    if terrain == 1:  # puddle
                        self.generate_puddles(x, y)
                    elif terrain == 2:  # vine
                        self.generate_vines(x, y)


        for room_list in self.rooms.values():
            for room in room_list:

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
                        place_tile(self.game_map, x1, y1, "6")

                # Seperate Room into sections for small rooms
                bsp = tcod.bsp.BSP(x=room.x, y=room.y, width=room.width, height=room.height)
                bsp.split_recursive(
                    depth=randint(1, 2),
                    min_width=5,
                    min_height=5,
                    max_horizontal_ratio=3,
                    max_vertical_ratio=3
                )

                # Find All Nodes that Are an Actual Room
                for node in bsp.pre_order():
                    if not node.children:
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

                        # Select Room Type Based on Size of Room
                        modified_width = node.width + east_buffer - west_buffer
                        modified_height = node.height + south_buffer - north_buffer

                        if modified_height < 3 or modified_width < 3:
                            room_type = choice(['storage'])
                        elif modified_height < 6 or modified_width < 6:
                            room_type = choice(['storage', 'small_jail'])
                        elif modified_height < 10 or modified_width < 10:
                            room_type = choice(['storage', 'small_jail', 'medium_jail'])
                        else:
                            room_type = 'storage'
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



                        # Generate Room
                        if room_type == 'small_jail' or room_type == 'medium_jail':
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
                            j = JailCell(node.x + west_buffer, node.y + north_buffer,  node.width + east_buffer - west_buffer, node.height + south_buffer - north_buffer, room)
                            self.jail_cells.append(j)

                            # Place Prefab for Jail Cell
                            prefab_list = [PREFABS.get('toilet'), PREFABS.get('prison_bed'), PREFABS.get("chest")]
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
                                        place_prefab(self.game_map, p)
                                        tries = max_tries
                                    tries += 1

                        elif room_type == 'storage':
                            self.generate_storage_room(node, entrances, north_buffer, south_buffer, east_buffer, west_buffer)
                        # elif room_type == 'prefab':

    def generate_storage_room(self, node, entrances, north_buffer, south_buffer, east_buffer, west_buffer):
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
                        place_tile(self.game_map, x, y, choice(crate_barrel_chance))
        # place_tile(self.game_map, center_x, center_y, '16')

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

    def populate_rooms(self, entities):
        # Place Prisoners
        max_tries = 30
        prisoner_index = 'weak_prisoner'
        prisoner_dict = MOBS.get(prisoner_index)

        for jail in self.jail_cells:
            # Don't Spawn Entities in Player Room
            if jail.parent_room == self.start_room:
                continue

            encounter = Encounter(jail, len(self.game_map.encounters) + 1)
            entities_created = []

            if jail.size > 30:
                number_of_mobs = randint(3, 4)
            elif jail.size > 20:
                number_of_mobs = 2
            else:
                number_of_mobs = 1

            for i in range(number_of_mobs):
                tries = 0

                # Attempt to Find an Empty Space to Place Mob
                while tries < max_tries:
                    tries += 1
                    x = randint(jail.x + 1, jail.x + jail.width - 1)
                    y = randint(jail.y + 1, jail.y + jail.height - 1)

                    if self.game_map.walkable[y][x] and not any(
                            [entity for entity in entities if entity.x == x and entity.y == y]):
                        # Position is good
                        break
                    x, y = None, None

                # Check if Suitable Position Has Been Found
                if not x or not y:
                    continue

                # Spawn an Entity
                entities_created.append(generate_mob(x, y, prisoner_dict, prisoner_index, encounter))

            # If Entities were Created Add Entities and and Increment Encounters
            if entities_created:
                entities.extend(entities_created)
                self.game_map.encounters.append(encounter)

        # Place Enemies Not In Jail Cells
        no_spawn_rooms = [self.start_room, self.end_room]
        _rooms = [room for cell_block in self.rooms.values() for room in cell_block if room not in no_spawn_rooms]
        guard_index = 'undergrave_guard'
        guard_dict = MOBS.get(guard_index)

        for room in _rooms:
            spawn_check = randint(1, 3)

            if spawn_check == 2:
                encounter = Encounter(room, len(self.game_map.encounters) + 1)
                entities_created = []
                room_size = room.width * room.height
                if room_size > 30:
                    number_of_mobs = 2
                elif room_size > 20:
                    number_of_mobs = 1
                else:
                    number_of_mobs = 1

                for i in range(number_of_mobs):
                    tries = 0

                    # Attempt to Find an Empty Space to Place Mob
                    while tries < max_tries:
                        tries += 1
                        x = randint(room.x + 1, room.x + room.width - 1)
                        y = randint(room.y + 1, room.y + room.height - 1)

                        room_to_avoid = None
                        for j in self.jail_cells:
                            if j.parent_room == room:
                                room_to_avoid = j
                                break

                        # TODO: Don't spawn in jail cells!!!!
                        if room_to_avoid:
                            if not room_to_avoid.contains(x, y) and self.game_map.walkable[y][x] and not any(
                                    [entity for entity in entities if entity.x == x and entity.y == y]):
                                # Position is good
                                break
                            x, y = None, None

                        else:

                            if self.game_map.walkable[y][x] and not any(
                                    [entity for entity in entities if entity.x == x and entity.y == y]):
                                # Position is good
                                break
                            x, y = None, None

                    # Check if Suitable Position Has Been Found
                    if not x or not y:
                        continue

                    # Spawn an Entity
                    entities_created.append(generate_mob(x, y, guard_dict, guard_index, encounter, pop=PatrolMob))

                # If Entities were Created Add Entities and and Increment Encounters
                if entities_created:
                    entities.extend(entities_created)
                    self.game_map.encounters.append(encounter)

        # room = self.start_room
        # encounter = Encounter(room, len(self.game_map.encounters) + 1)
        # entities_created = []
        # room_size = room.width * room.height
        # if room_size > 30:
        #     number_of_mobs = randint(2, 3)
        # elif room_size > 20:
        #     number_of_mobs = 1
        # else:
        #     number_of_mobs = 1
        # number_of_mobs = 1
        # for i in range(number_of_mobs):
        #     tries = 0
        #
        #     # Attempt to Find an Empty Space to Place Mob
        #     while tries < max_tries:
        #         tries += 1
        #         x = randint(room.x + 1, room.x + room.width - 1)
        #         y = randint(room.y + 1, room.y + room.height - 1)
        #
        #         # TODO: Don't spawn in jail cells!!!!
        #         if self.game_map.walkable[y][x] and not any(
        #                 [entity for entity in entities if entity.x == x and entity.y == y]):
        #             # Position is good
        #             break
        #         x, y = None, None
        #
        #     # Check if Suitable Position Has Been Found
        #     if not x or not y:
        #         continue
        #
        #     # Spawn an Entity
        #     entities_created.append(generate_mob(x, y, guard_dict, guard_index, encounter, pop=PatrolMob))
        #
        # # If Entities were Created Add Entities and and Increment Encounters
        # if entities_created:
        #     entities.extend(entities_created)
        #     self.game_map.encounters.append(encounter)










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
        # Populate Each of the Rooms as follows
        # for cell_block, rooms_list in self.rooms.items():
        #     for room in rooms_list:

                # Test Create 1 Jail Cell in Each Room in a Random Corner
                # anchor_x =

                # max_width = room.width // 2 - 1
                # max_height = room.height // 2 - 1

    def generate_vines(self, x, y):
        # localized_layout = np.array([[abs(self.grid[y][x] - 1) for y in range(y-3, y+3)] for x in range(x-3, x+3)] if 0 <= x < self.width and 0 <= y < self.height else 999)
        localized_layout = np.array([[1 for y in range(y-3, y+3)] for x in range(x-3, x+3)] if 0 <= x < self.width and 0 <= y < self.height else 999)

        astar = tcod.path.AStar(localized_layout, diagonal=1)
        goal_x, goal_y = (randint(x - 3, x + 2) + 3, randint(y-3, y + 2) + 3)
        final_path = astar.get_path(2, 2, goal_x - x, goal_y - y)
        # for row in localized_layout:
        #     print(row)
        # print('start:', 2, 2)
        # print('goal:', goal_x - x, goal_y - y)

        for i, j in final_path:
            if self.grid[x + i][y + j] == 0:
            # print(i, j)
                place_tile(self.game_map, x + i, y + j, "16")
            else:
                break





        # direction = choice([-1, 1])
        # limit = randint(1, 4)
        #
        # for i in range(0, limit*direction, direction):
        #     place_tile(self.game_map, x-1, y, "16")
        #     place_tile(self.game_map, x+1, y, "16")
        #     place_tile(self.game_map, x, y + i, "16")

    def place_player_stairs(self, entities):
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
        self.game_map.player.x, self.game_map.player.y = center(self.start_room)

        # Place Stairs in Last Room
        self.end_room = sorted_rooms[-1]
        last_room_x, last_room_y = center(self.end_room)
        entities.append(place_stairs(self.dungeon_level, last_room_x, last_room_y))

        # def create_jail(self, game_map, room):


class JailCell:
    x = 0
    y = 0
    width = 0
    height = 0
    entrances = []
    parent_room = None  # bsp room jail cell resides in, not the node of a room, but the entire carved out room itself

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