"""
FlameWoodPrison.py - Represent the 1st entire section.

Flamewood Prison - A giant sprawling prison within the Flamewood territory that houses all the prisoners that rebelled
                   against the Flamewood Army.

Enemies:
- Flamewood Warden - The Overseer of the Flamewood Prison.
- Guard - Most common enemy within Flamewood Prison.
- *Prisoner - All prisoners are to be hostile or neutral to player
- Guard Dog - Sharper eye sight, smell and hearing compared to guards


* Guardian, Sentry, Sentinal, Defender, Warder, Patrol, Watcher, Shepherd
* Prison Officer, Officer, Jailor,

Progression:
- (10) - (20) levels in total
- Mid boss fight half way through
- 1st level is story based
- 2nd through 5th floors are tutorials for stealth mechanics
- Last level will contain final fight with Flamewood
- Too much time spent in each floor will attract more and more guards

Each floor of the prison will have:
    Common:
        - Small Jail Cell
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
    Uncommon:
        - Alchemy Lab
        - Nursery
    Rare:
        - Alternate secret exit to next floor/skip next floors
        - Abandoned Wing of Jail Floor


"""
from operator import attrgetter
from random import choice, choices, random, randint

from components.AI import *
from components.Encounter import Encounter
from level_generation.GenerationUtils import calculate_distance, create_hall, create_room, create_wall, \
    create_walled_room, place_entities, place_stairs, generate_items, generate_mobs, generate_objects
from loader_functions.JsonReader import obtain_item_table, obtain_mob_table, obtain_tile_set
from map_objects.Shapes import BSPRoom
from RandomUtils import random_choice_from_dict, spawn_chance


def check_open_sides(game_map, x, y):
    count = 0
    # Find how many open sides
    for direction in [(x - 1, y), (x + 1, y), (x, y + 1), (x, y - 1)]:
        if not game_map.is_blocked(*direction):
           count += 1
    if count > 1:
        return False
    return True


def close_extra_spaces(game_map):
    for x in range(game_map.width):
        for y in range(game_map.height):

            if check_open_sides(game_map, x, y):
                create_wall(game_map, x, y)


class FlameWoodPrison:
    def __init__(self):
        self.game_map = None
        self.room = None
        self._leafs = []
        self.dungeon_level = 0
        self.MAX_LEAF_SIZE = 25
        self.rooms = []
        self.sub_rooms = []
        self.connecting_rooms = []
        self.start_room = None
        self.end_room = None

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, item_table, mob_table, furniture_table):
        self.game_map = game_map
        self.dungeon_level = dungeon_level

        self.rooms = []
        self.sub_rooms = []
        self._leafs = []
        self.connecting_rooms = []

        # Reiterate BSP for Sub Rooms
        map_x_start, map_y_start = 0, 0
        self._leafs = self.iterate_bsp(entities, item_table, mob_table, map_width, map_height, map_x_start, map_y_start)
        if len(self.rooms) > 2:
            # Search for Biggest Room
            max_iter = 100
            within_room = True

            # Further Split Cell Blocks into Sub Rooms for Jail Cells and other Prefab Rooms
            # jail_room = max(self.rooms[1:-1], key=attrgetter('room_size'))
            for cell_block in self.rooms:
                map_x_start = cell_block.x1
                map_y_start = cell_block.y1
                room_width = cell_block.x2 - map_x_start
                room_height = cell_block.y2 - map_y_start
                cell_block.sub_rooms = self.iterate_bsp(entities, item_table, mob_table, room_width, room_height,
                                                        map_x_start, map_y_start, max_iter, within_room, cell_block)

        # Ensure All Cell Blocks Flow Together
        self.connect_cell_blocks(game_map)

        # Remove Random Hallways and Spaces
        for i in range(10):
            close_extra_spaces(game_map)

        # Find All Entrances
        self.assign_entrances(game_map)
        entrances = [entrance for sub_room in self.sub_rooms for entrance in sub_room.entrances]

        no_entrances = 0
        one_entrances = 0
        two_entrances = 0
        three_entrances = 0
        multi_entrances = 0

        no_entrances_room = []
        one_entrances_room = []
        two_entrances_room = []
        three_entrances_room = []
        multi_entrances_room = []
        for sub_room in self.sub_rooms:
            if len(sub_room.entrances) == 1:
                one_entrances += 1
                one_entrances_room.append(sub_room)
            elif len(sub_room.entrances) == 2:
                two_entrances += 1
                two_entrances_room.append(sub_room)
            elif len(sub_room.entrances) == 3:
                three_entrances += 1
                three_entrances_room.append(sub_room)
            elif len(sub_room.entrances) > 3:
                multi_entrances += 1
                multi_entrances_room.append(sub_room)
            else:
                no_entrances += 1
                no_entrances_room.append(sub_room)

        print("\nNumber of Cell Blocks: %s\nNumber of Sub Room: %s" % (len(self.rooms), len(self.sub_rooms)))

        # Select Which Room for Stairs and Player
        self.place_player_stairs(entities, player)

        # Populate and Designate Rooms
        self.designate_rooms(entities, game_map, no_entrances, one_entrances, two_entrances, three_entrances, multi_entrances,
                             no_entrances_room, one_entrances_room, two_entrances_room, three_entrances_room,
                             multi_entrances_room)

        # Place Encounters in None Player Room
        # sub_rooms = self.sub_rooms.copy()
        # sub_rooms.remove(self.start_room)
        # sub_rooms.remove(self.end_room)
        # for sub_room in sub_rooms:
        #     place_entities(game_map, dungeon_level, sub_room, entities, item_table, mob_table, furniture_table)

        # Add Rooms References to Game Map
        game_map.rooms.extend(self.sub_rooms)
        # game_map.rooms.extend(self.rooms)
        game_map.entrances = entrances

    def iterate_bsp(self, entities, item_table, mob_table, map_width, map_height, map_x_start, map_y_start,
                    max_iter=randint(4, 10), within_room=False, cell_block=None):

        root_leaf = Leaf(self, map_x_start, map_y_start, map_width, map_height)
        _leafs = [root_leaf]
        # TODO: Find a balance between max_iter and map size
        _iter = 0

        split_successfully = True
        # loop through all leaves until they can no longer split successfully
        while split_successfully:
            split_successfully = False

            for l in _leafs:
                if _iter > max_iter:
                    break
                if not l.child_1 and not l.child_2:  # if leaf has no child
                    if l.width > self.MAX_LEAF_SIZE or l.height > self.MAX_LEAF_SIZE or random() > 0.8:
                        if l.split_leaf():  # try to split the leaf
                            _leafs.append(l.child_1)
                            _leafs.append(l.child_2)
                            _iter += 1

        # Actually Generate the Rooms
        root_leaf.create_bsp_room(self, entities, item_table, mob_table, within_room, cell_block)
        return _leafs

    def connect_cell_blocks(self, game_map):
        # Connect Cell to Closest Sub Room of Child
        while self._leafs:
            leaf = self._leafs.pop()
            _rooms1 = set()
            _rooms2 = set()
            # Connect rooms together
            best_room_pair = None
            smallest_distance = 1000
            if leaf.child_1 and leaf.child_2:
                # _rooms1.extend(r for r in leaf.child_1.get_bsp_room().sub_rooms if r.room)
                # _rooms1.extend(r for r in leaf.child_1.get_bsp_room().sub_rooms if r.room)

                # TODO: Find exact way to find connecting bsp rooms
                for i in range(50):
                    # _rooms2.add(leaf.child_2.get_bsp_room())
                    for r in leaf.child_2.get_bsp_room().sub_rooms:
                        if r.room:
                            _rooms2.add(r)

                    for r in leaf.child_1.get_bsp_room().sub_rooms:
                        if r.room:
                            _rooms1.add(r)
                # _rooms1.append(leaf.child_1.get_bsp_room())
                # _rooms2.append(leaf.child_2.get_bsp_room())

                # Connect to Closest Rooms
                for r1 in _rooms1:
                    for r2 in _rooms2:
                        rx1, ry1 = r1.center
                        rx2, ry2 = r2.center
                        check_distance = calculate_distance(rx1, ry1, rx2, ry2)
                        if smallest_distance > check_distance:
                            smallest_distance = check_distance
                            best_room_pair = [r1, r2]

                create_hall(game_map, best_room_pair[0], best_room_pair[1])
                if smallest_distance > 50:
                    print('\nsmallest distance is: %s' % smallest_distance)
                    print('pair chosen:', best_room_pair[0].center, best_room_pair[1].center)
                    self.connecting_rooms.extend(best_room_pair)

    def place_player_stairs(self, entities, player):
        # Assign room for Stairs and Player
        begin_end_select = randint(1, 2)
        if not self.sub_rooms:  # no sub rooms and number of main rooms is less than 3
            rooms = self.rooms
            if len(self.rooms) > 2:
                if begin_end_select == 1:
                    start_x, start_y = rooms[0].center
                    last_x, last_y = rooms[1].center
                    start_room = rooms[0]
                    end_room = rooms[1]
                else:
                    last_x, last_y = rooms[1].center
                    start_x, start_y = rooms[0].center
                    start_room = rooms[1]
                    end_room = rooms[0]
            else:
                half_way = len(self.sub_rooms) // 2
                if begin_end_select == 1:
                    start_room = choice(rooms[:half_way])
                    end_room = choice(rooms[half_way:])
                    start_x, start_y = start_room.center
                    last_x, last_y = end_room.center

                else:
                    end_room = choice(rooms[:half_way])
                    start_room = choice(rooms[half_way:])
                    last_x, last_y = start_room.center
                    start_x, start_y = end_room.center
        else:

            if not self.sub_rooms:
                rooms = self.rooms
            else:
                rooms = self.sub_rooms

            half_way = len(self.sub_rooms) // 2
            if begin_end_select == 1:
                start_room = choice(rooms[:half_way])
                end_room = choice(rooms[half_way:])
                start_x, start_y = start_room.center
                last_x, last_y = end_room.center
            else:
                end_room = choice(rooms[:half_way])
                start_room = choice(rooms[half_way:])
                last_x, last_y = end_room.center
                start_x, start_y = start_room.center

        # Place Player and Stairs
        self.start_room = start_room
        self.end_room = end_room
        # player.position.x, player.position.y = start_x, start_y
        entities.append(place_stairs(self.game_map.dungeon_level, last_x, last_y))

    def assign_entrances(self, game_map):
        # Find Doors/Entrances for Each Room
        for sub_room in self.sub_rooms:
            sub_room.obtain_entrances(game_map)
            # x, y = sub_room.center
            # print("\nSub Room at (%s, %s), Width: %s, Height: %s has %s entrances" % (x, y, sub_room.x2 - sub_room.x1,
            #                                                                           sub_room.y2 - sub_room.y1,
            #                                                                           len(sub_room.entrances)))
            # if sub_room.entrances:
            #     print(sub_room.entrances)

    def designate_rooms(self, entities, game_map, no_entrances, one_entrances, two_entrances, three_entrances, multi_entrances,
                        no_entrances_room, one_entrances_room, two_entrances_room, three_entrances_room,
                        multi_entrances_room):
        print('\nDesignate Rooms:')
        print('No Entrances: %s\nOne Entrance: %s\nTwo Entrances: %s\nThree Entrances: %s\nMulti Entrances: %s' %
              (no_entrances, one_entrances, two_entrances, three_entrances, multi_entrances))

        mob_table = obtain_mob_table()
        item_table = obtain_item_table()

        # Obtain only "Objects" from Tile Set
        object_table = {key: val for key, val in game_map.tile_set.items() if val.get('type') == 'object'}

        monster_chances = {mob: spawn_chance([stats for stats in mob_stats.get('spawn_chance')], self.dungeon_level)
                           for mob, mob_stats in mob_table.items()
                           }
        object_chances = {object: spawn_chance([[object_stats.get('spawn_chance'), object_stats.get('item_level')]],
                                               self.dungeon_level) for object, object_stats in object_table.items()
                          }

        item_chances = {item: spawn_chance([[item_stats.get('spawn_chance'), item_stats.get('item_level')]],
                                           self.dungeon_level) for item, item_stats in item_table.items()
                        }

        # generate_items(entities, game_map, room, number_of_items, item_chances, item_table):
        # generate_mobs(entities, game_map, room, number_of_mobs, monster_chances, mob_table, encounter_type, encounter):
        # generate_objects(entities, game_map, room, number_of_items, object_chances, object_table):

        for room in no_entrances_room:
            c = choice(['treasure_room', 'hard_monster_room', 'dead_prisoner_room'])
            encounter_type = None
            encounter = None
            number_of_items = 0
            number_of_objects = 0
            number_of_mobs = 0
            if c == 'treasure_room':
                number_of_items = randint(1, 5)
                number_of_objects = randint(2, 5)
            elif c == 'hard_monster_room':
                encounter_type = DefensiveAI
                encounter = Encounter(room, len(game_map.encounters), encounter_type)
                number_of_objects = randint(1, 2)
                number_of_mobs = 1
            generate_mobs(entities, game_map, room, number_of_mobs, monster_chances, mob_table, encounter_type,
                          encounter)
            generate_items(entities, game_map, room, number_of_items, item_chances, item_table)
            generate_objects(entities, game_map.map_objects, game_map, room, number_of_objects, object_chances,
                             object_table)
            room.room_type = c

        for room in one_entrances_room:
            c = choice(['alarm_room', 'small_jail_cell', 'supply_room', 'food_storage_room', 'office_room'])
            encounter_type = None
            encounter = None
            number_of_items = 0
            number_of_objects = 0
            number_of_mobs = 0
            if c == 'alarm_room':
                encounter_type = DefensiveAI
                encounter = Encounter(room, len(game_map.encounters), encounter_type)
                number_of_items = randint(0, 2)
                number_of_objects = randint(2, 5)
                number_of_mobs = randint(0, 1)
            elif c == 'small_jail_cell':
                encounter_type = DefensiveAI
                encounter = Encounter(room, len(game_map.encounters), encounter_type)
                number_of_items = randint(0, 2)
                number_of_objects = randint(2, 5)
                number_of_mobs = randint(1, 2)
            elif c == 'supply_room':
                number_of_items = randint(2, 5)
                number_of_objects = randint(5, 7)
            elif c == 'food_storage_room':
                number_of_items = randint(2, 5)
                number_of_objects = randint(5, 7)
            elif c == 'office_room':
                number_of_items = randint(2, 3)
                number_of_objects = randint(5, 7)
            generate_mobs(entities, game_map, room, number_of_mobs, monster_chances, mob_table, encounter_type,
                          encounter)
            generate_items(entities, game_map, room, number_of_items, item_chances, item_table)
            generate_objects(entities, game_map.map_objects, game_map, room, number_of_objects, object_chances,
                             object_table)
            room.room_type = c

        for room in two_entrances_room:
            c = choice(['small_jail_cell', 'medium_jail_cell'])
            encounter_type = None
            encounter = None
            number_of_items = 0
            number_of_objects = 0
            number_of_mobs = 0
            if c == 'small_jail_cell':
                pop = [DefensiveAI, PatrolAI]
                weights = [80, 20]
                encounter_type = choices(population=pop,
                                         weights=weights,
                                         k=1)[0]

                encounter = Encounter(room, len(game_map.encounters), encounter_type)
                number_of_items = randint(0, 2)
                number_of_objects = randint(2, 5)
                number_of_mobs = randint(0, 1)
            elif c == 'medium_jail_cell':
                pop = [DefensiveAI, PatrolAI]
                weights = [80, 20]
                encounter_type = choices(population=pop,
                                         weights=weights,
                                         k=1)[0]

                encounter = Encounter(room, len(game_map.encounters), encounter_type)
                number_of_items = randint(0, 2)
                number_of_objects = randint(2, 5)
                number_of_mobs = randint(0, 3)
            room.room_type = c
            generate_mobs(entities, game_map, room, number_of_mobs, monster_chances, mob_table, encounter_type,
                          encounter)
            generate_items(entities, game_map, room, number_of_items, item_chances, item_table)
            generate_objects(entities, game_map.map_objects, game_map, room, number_of_objects, object_chances,
                             object_table)

        for room in three_entrances_room + multi_entrances_room:
            c = choice(['medium_jail_cell', 'large_jail_cell'])
            encounter_type = None
            encounter = None
            number_of_items = 0
            number_of_objects = 0
            number_of_mobs = 0

            if c == 'medium_jail_cell':
                pop = [DefensiveAI, PatrolAI]
                weights = [80, 20]
                encounter_type = choices(population=pop,
                                         weights=weights,
                                         k=1)[0]

                encounter = Encounter(room, len(game_map.encounters), encounter_type)
                number_of_items = randint(0, 2)
                number_of_objects = randint(2, 5)
                number_of_mobs = randint(0, 3)
            elif c == 'large_jail_cell':
                pop = [DefensiveAI, PatrolAI]
                weights = [80, 20]
                encounter_type = choices(population=pop,
                                         weights=weights,
                                         k=1)[0]

                encounter = Encounter(room, len(game_map.encounters), encounter_type)
                number_of_items = randint(0, 4)
                number_of_objects = randint(4, 7)
                number_of_mobs = randint(0, 5)

            generate_items(entities, game_map, room, number_of_items, item_chances, item_table)
            generate_mobs(entities, game_map, room, number_of_mobs, monster_chances, mob_table, encounter_type,
                          encounter)
            generate_objects(entities, game_map.map_objects, game_map, room, number_of_objects, object_chances, object_table)
            room.room_type = c

        """
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


class Leaf:  # used for the BSP tree algorithm
    def __init__(self, main_tree, x, y, width, height):
        self.main_tree = main_tree
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.MIN_LEAF_SIZE = 6
        self.child_1 = None
        self.child_2 = None
        self.room = None
        self.room_1 = None
        self.room_2 = None
        self.parent_room = None

    @property
    def center(self):
        center_x = int((self.x + self.x + self.width) / 2)
        center_y = int((self.y + self.y + self.height) / 2)
        return center_x, center_y

    @property
    def x1(self):
        return self.x

    @property
    def x2(self):
        return self.x + self.width

    @property
    def y1(self):
        return self.y

    @property
    def y2(self):
        return self.y + self.height

    def split_leaf(self):
        # begin splitting the leaf into two children
        # print('\nsplit_leaf')
        if self.child_1 or self.child_2:
            return False  # This leaf has already been split
        '''
        ==== Determine the direction of the split ====
        If the width of the leaf is >25% larger than the height,
        split the leaf vertically.
        If the height of the leaf is >25 larger than the width,
        split the leaf horizontally.
        Otherwise, choose the direction at random.
        '''
        split_horizontally = False
        if self.width / self.height >= 1.25:
            split_horizontally = False
        elif self.height / self.width >= 1.25:
            split_horizontally = True

        if split_horizontally:
            max_size = self.height - self.MIN_LEAF_SIZE
        else:
            max_size = self.width - self.MIN_LEAF_SIZE

        if max_size <= self.MIN_LEAF_SIZE:
            return False  # the leaf is too small to split further

        split = randint(self.MIN_LEAF_SIZE, max_size)  # determine where to split the leaf

        # print('split val:', split)

        inc = 0

        if split_horizontally:
            # print('split_horizontally')
            self.child_1 = Leaf(self.main_tree,
                                self.x + inc,
                                self.y + inc,
                                self.width - inc,
                                split - inc)
            self.child_2 = Leaf(self.main_tree,
                                self.x + inc,
                                self.y + split + inc,
                                self.width - inc,
                                self.height - split - inc)
        else:
            # print('split_vertically')
            self.child_1 = Leaf(self.main_tree,
                                self.x + inc,
                                self.y + inc ,
                                split - inc,
                                self.height - inc)
            self.child_2 = Leaf(self.main_tree,
                                self.x + split + inc,
                                self.y + inc,
                                self.width - split - inc,
                                self.height - inc)
        return True

    def create_bsp_room(self, bsp_tree, entities, item_table, mob_table, within_room, parent_room):

        if self.child_1 or self.child_2:
            # recursively search for children until you hit the end of the branch

            if self.child_1:
                self.child_1.create_bsp_room(bsp_tree, entities, item_table, mob_table, within_room, parent_room)
            if self.child_2:
                self.child_2.create_bsp_room(bsp_tree, entities, item_table, mob_table, within_room, parent_room)

            # Connect rooms together
            if self.child_1 and self.child_2:
                create_hall(bsp_tree.game_map, self.child_1.get_bsp_room(), self.child_2.get_bsp_room())

        elif not self.child_1 and not self.child_2:
            # Create rooms in the end branches of the bsp tree
            # w = randint(bsp_tree.room_min_size, min(bsp_tree.room_max_size, self.width - 1))
            # h = randint(bsp_tree.room_min_size, min(bsp_tree.room_max_size, self.height - 1))
            # x = randint(self.x, self.x + (self.width - 1) - w)
            # y = randint(self.y, self.y + (self.height - 1) - h)
            if within_room:
                x = self.x - 1
                y = self.y - 1
                if self.width + 2 >= bsp_tree.game_map.width:
                    w = self.width - 1
                else:
                    w = self.width + 2
                if self.height + 2 >= bsp_tree.game_map.height:
                    h = self.height - 1
                else:
                    h = self.height + 2
            else:

                x = self.x
                y = self.y
                w = self.width - 1
                h = self.height - 1

            self.room = BSPRoom(x, y, w, h, len(bsp_tree.game_map.rooms) + len(self.main_tree.sub_rooms) + 1)

            # Check if a Sub Room or Main Room i`s Being Created
            if within_room:
                # Build walls to outer perimeter of room and Add to Subrooms
                self.main_tree.sub_rooms.append(self.room)
                self.room.parent_room = parent_room  # assign a "parent room" to link rooms together
                create_walled_room(bsp_tree.game_map, self.room)
            else:
                # Carve out a room and add to main rooms
                # create_room(bsp_tree.game_map, self.room)
                self.main_tree.rooms.append(self.room)

    def get_bsp_room(self):
        if self.room:
            return self.room

        else:
            if self.child_1:
                # print('obtaining bsp room from child 1')
                self.room_1 = self.child_1.get_bsp_room()
            if self.child_2:
                # print('obtaining bsp room from child 2')
                self.room_2 = self.child_2.get_bsp_room()

            # print('finally choosing a room')
            if not self.child_1 and not self.child_2:
                # neither room_1 nor room_2
                return None

            elif not self.room_2:
                # room_1 and !room_2
                return self.room_1

            elif not self.room_1:
                # room_2 and !room_1
                return self.room_2

            # If both room_1 and room_2 exist, pick one
            elif random() < 0.5:
                # print('both rooms exist!')
                # print('room_1:', self.room_1.center)
                # print('room_2:', self.room_2.center)
                return self.room_1
            else:
                # print('both rooms exist!')
                # print('room_1:', self.room_1.center)
                # print('room_2:', self.room_2.center)
                return self.room_2


def populate_room(game_map, room, room_type):
    if room_type == 1:
        pass