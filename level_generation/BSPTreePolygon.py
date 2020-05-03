from operator import attrgetter
from random import choice, random, randint

import numpy as np
import matplotlib.path as pltpath
from shapely.geometry import Polygon

from level_generation.GenerationUtils import create_walled_room, create_door, create_hall, create_room, place_tile, place_entities, place_stairs
from map_objects.Shapes import BSPRoom


class BSPTreePolygonAlgorithm:
    def __init__(self):
        self.game_map = None
        self.room = None
        self._leafs = []
        self.dungeon_level = 0
        self.MAX_LEAF_SIZE = 3
        self.room_min_size = 1
        self.room_max_size = 5
        self.rooms = []
        self.sub_rooms = []

    def obtain_min_max_coordinates(self, vertices):
        v = sorted(vertices, key=lambda x: x[0])
        x_min = v[0][0]
        x_max = v[-1][0]

        v = sorted(vertices, key=lambda x: x[1])
        y_min = v[0][1]
        y_max = v[-1][1]

        return x_min, y_min, x_max, y_max

    def generate_level(self, game_map,max_rooms, room_min_size, room_max_size, map_width, map_height,
                       entities, item_table, mob_table, map_x_start, map_y_start, vertices=[]):
        self.game_map = game_map
        # self.dungeon_level = dungeon_level
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

        x_min = map_x_start
        y_min = map_y_start
        width = map_width - x_min
        height = map_height - y_min

        # Obtain Min and Max Values of Polygon
        if vertices != []:
            x_min, y_min, x_max, y_max = self.obtain_min_max_coordinates(vertices)
            width = x_max - x_min
            height = y_max - y_min

        print('x/y min:', x_min, y_min)
        print('width/height:', width, height)
        print('vertices:', vertices)

        # BSP Algorithm
        self._leafs = self.iterate_bsp(entities, item_table, mob_table, width, height, x_min, y_min, vertices)

        # Select Which Room for Stairs and Player
        # begin_end_select = randint(1, 2)
        # if begin_end_select == 1:
        #     start_x, start_y = self.rooms[0].center
        #     last_x, last_y = self.rooms[-1].center
        # else:
        #     last_x, last_y = self.rooms[0].center
        #     start_x, start_y = self.rooms[-1].center

        # Place Player
        # player.x, player.y = start_x, start_y
        # Place Stairs
        # entities.append(place_stairs(self.game_map.dungeon_level, last_x, last_y))

        # Further Split Individual Rooms
        # print('\nNumber of Rooms:', len(self.rooms))
        # if len(self.rooms) > 2:
        #     # Search for Biggest Room
        #     max_iter = 100
        #     within_room = True
        #
        #     # jail_room = max(self.rooms[1:-1], key=attrgetter('room_size'))
        #     for jail_room in self.rooms[1:-1]:
        #         jail_room.child_1 = None
        #         jail_room.child_2 = None
        #         map_x_start = jail_room.x1
        #         map_y_start = jail_room.y1
        #         room_width = jail_room.x2 - map_x_start
        #         room_height = jail_room.y2 - map_y_start
        #         self.iterate_bsp(entities, item_table, mob_table, room_width, room_height, map_x_start, map_y_start,
        #                          max_iter, within_room)

        # Add Rooms References to Game Map
        game_map.rooms.extend(self.rooms)

    def iterate_bsp(self, entities, item_table, mob_table, map_width, map_height, map_x_start, map_y_start, vertices,
                    max_iter=1, within_room=False):
        root_leaf = Leaf(self, map_x_start, map_y_start, map_width, map_height, vertices)
        _leafs = []
        _leafs.append(root_leaf)
        # TODO: Find a balance between max_iter and map size
        max_iter = 100
        # max_iter = randint(4, 10)
        _iter = 0

        split_successfully = True
        # loop through all leaves until they can no longer split successfully
        while split_successfully:
            split_successfully = False

            for l in _leafs:
                if _iter > max_iter:
                    # print('max iterations exceeded')
                    break
                if not l.child_1 and not l.child_2:  # if leaf has no child
                    if l.width > self.MAX_LEAF_SIZE or l.height > self.MAX_LEAF_SIZE or random() > 0.5:
                        if l.split_leaf():  # try to split the leaf
                            _leafs.append(l.child_1)
                            _leafs.append(l.child_2)
                            # break
                            _iter += 1



        # Actually Generate the Rooms
        root_leaf.create_bsp_room(self, entities, item_table, mob_table, within_room)
        return _leafs


class Leaf:  # used for the BSP tree algorithm
    def __init__(self, main_tree, x, y, width, height, vertices):
        self.main_tree = main_tree
        self.vertices = vertices
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.MIN_LEAF_SIZE = 5  # distance from edge to cut
        self.child_1 = None
        self.child_2 = None
        self.room = None
        self.room_1 = None
        self.room_2 = None

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

        self.MIN_LEAF_SIZE = randint(4, 6)
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
                                split - inc,
                                self.vertices)
            self.child_2 = Leaf(self.main_tree,
                                self.x + inc,
                                self.y + split + inc,
                                self.width - inc,
                                self.height - split - inc,
                                self.vertices)
        else:
            # print('split_vertically')
            self.child_1 = Leaf(self.main_tree,
                                self.x + inc,
                                self.y + inc ,
                                split - inc,
                                self.height - inc,
                                self.vertices)
            self.child_2 = Leaf(self.main_tree,
                                self.x + split + inc,
                                self.y + inc,
                                self.width - split - inc,
                                self.height - inc,
                                self.vertices)
        return True

    def create_bsp_room(self, bsp_tree, entities, item_table, mob_table, within_room):

        if self.child_1 or self.child_2:
            # recursively search for children until you hit the end of the branch
            if self.child_1:
                self.child_1.create_bsp_room(bsp_tree, entities, item_table, mob_table, within_room)
            if self.child_2:
                self.child_2.create_bsp_room(bsp_tree, entities, item_table, mob_table, within_room)

            # Connect rooms together
            # if self.child_1 and self.child_2:
            #
            #     door_x, door_y = create_door(bsp_tree.game_map, self.child_1.get_bsp_room(), self.child_2.get_bsp_room())
            #     place_tile(bsp_tree.game_map, door_x, door_y, "6")
                # create_hall(bsp_tree.game_map, self.child_1.get_bsp_room(), self.child_2.get_bsp_room())

        else:
            # Create rooms in the end branches of the bsp tree
            # w = randint(bsp_tree.room_min_size, min(bsp_tree.room_max_size, self.width - 1))
            # h = randint(bsp_tree.room_min_size, min(bsp_tree.room_max_size, self.height - 1))
            # x = randint(self.x, self.x + (self.width - 1) - w)
            # y = randint(self.y, self.y + (self.height - 1) - h)

            buffer = 1

            x = int(self.x + buffer)
            y = int(self.y + buffer)
            w = int(self.width - buffer)
            h = int(self.height - buffer)

            voronoi_plot = Polygon(self.vertices)
            room_polygon = Polygon(((x, y), (x + w, y), (x, y + h), (x + w, y + h)))
            if voronoi_plot.contains(room_polygon):
                self.room = BSPRoom(y, x, h, w, len(bsp_tree.game_map.rooms) + 1)
                # self.room = BSPRoom(x, y, w, h, len(bsp_tree.game_map.rooms) + 1)
                self.main_tree.rooms.append(self.room)
                bsp_tree.game_map.rooms.append(self.room)
                # if within_room:
                    # print('creating walled room')
                create_walled_room(bsp_tree.game_map, self.room, buffer=buffer)
                # else:
                #     create_room(bsp_tree.game_map, self.room)
                # place_entities(bsp_tree.game_map, bsp_tree.dungeon_level, self.room, entities, item_table,
                #                mob_table)

    def get_bsp_room(self):
        if self.room:
            return self.room

        else:
            if self.child_1:
                self.room_1 = self.child_1.get_bsp_room()
            if self.child_2:
                self.room_2 = self.child_2.get_bsp_room()

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
                return self.room_1
            else:
                return self.room_2
