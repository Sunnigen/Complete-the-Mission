from math import sqrt
import random

import numpy as np


class MazeWithRooms:
    # ==== Maze With Rooms ====
    """
    Python implimentation of the rooms and mazes algorithm found at
    http://journal.stuffwithstuff.com/2014/12/21/rooms-and-mazes/
    by Bob Nystrom
    """

    def __init__(self):
        self.level = []
        self.rooms = []

        self.ROOM_MAX_SIZE = 10
        self.ROOM_MIN_SIZE = 4
        self.map_width = 10
        self.map_height = 10

        self.build_room_attempts = 500
        self.connection_chance = 0.02
        self.windingPercent = 0.02
        self.allowDeadEnds = False
        self._regions = None
        self._current_region = -1

    def generate(self, map_width, map_height):
        # The level dimensions must be odd
        self.level = [[1 for y in range(map_height)] for x in range(map_width)]
        if map_width % 2 == 0:
            map_width -= 1
        if map_height % 2 == 0:
            map_height -= 1
        self.rooms = []
        self.map_width = map_width
        self.map_height = map_height

        self._regions = [[None for y in range(map_height)] for x in range(map_width)]

        self._current_region = -1  # the index of the current region in _regions

        # Prefab Rooms

        # Throne Room
        room_width = 30
        room_height = 15
        x = self.map_width // 2 - room_width // 2
        y = 0
        self.add_custom_room(x, y, room_width, room_height)

        # Start Room
        room_width = 20
        room_height = 10
        x = self.map_width // 2 - room_width // 2
        y = self.map_height - room_height
        self.add_custom_room(x, y, room_width, room_height, buffer=5)

        # Random Rooms
        self.add_rooms()  # ?

        # Fill in the empty space around the rooms with mazes
        for y in range(1, map_height, 2):
            for x in range(1, map_width, 2):
                if self.level[x][y] != 1:
                    continue
                start = (x, y)
                self.grow_maze(start)

        self.connect_regions()

        if not self.allowDeadEnds:
            self.remove_dead_ends()

        return self.level

    def grow_maze(self, start):
        north = (0, -1)
        south = (0, 1)
        east = (1, 0)
        west = (-1, 0)

        cells = []
        last_direction = None

        self.start_region()
        self.carve(start[0], start[1])

        cells.append(start)

        while cells:
            cell = cells[-1]

            # see if any adjacent cells are open
            unmade_cells = set()

            '''
            north = (0,-1)
            south = (0,1)
            east = (1,0)
            west = (-1,0)
            '''
            for direction in [north, south, east, west]:
                if self.can_carve(cell, direction):
                    unmade_cells.add(direction)

            if unmade_cells:
                """
                Prefer to carve in the same direction, when
                it isn't necessary to do otherwise.
                """
                if ((last_direction in unmade_cells) and
                        (random.random() > self.windingPercent)):
                    direction = last_direction
                else:
                    direction = unmade_cells.pop()

                new_cell = ((cell[0] + direction[0]), (cell[1] + direction[1]))
                self.carve(new_cell[0], new_cell[1])

                new_cell = ((cell[0] + direction[0] * 2), (cell[1] + direction[1] * 2))
                self.carve(new_cell[0], new_cell[1])
                cells.append(new_cell)

                last_direction = direction

            else:
                # No adjacent uncarved cells
                cells.pop()
                last_direction = None

    def add_custom_room(self, x, y, room_width, room_height, buffer=2):
        # Place a Custom/Prefab Room at Coordinates
        room = Rect(x, y, room_width, room_height, buffer=buffer)
        self.rooms.append(room)
        self.start_region()
        self.create_room(room)
        return room

    def add_rooms(self):
        for i in range(self.build_room_attempts):

            """
            Pick a random room size and ensure that rooms have odd 
            dimensions and that rooms are not too narrow.
            """
            room_width = random.randint(int(self.ROOM_MIN_SIZE / 2), int(self.ROOM_MAX_SIZE / 2)) * 2 + 1
            room_height = random.randint(int(self.ROOM_MIN_SIZE / 2), int(self.ROOM_MAX_SIZE / 2)) * 2 + 1
            x = (random.randint(0, self.map_width - room_width - 1) / 2) * 2 + 1
            y = (random.randint(0, self.map_height - room_height - 1) / 2) * 2 + 1

            room = Rect(x, y, room_width, room_height, buffer=random.randint(0, 1))
            # check for overlap with previous rooms
            failed = False
            for other_room in self.rooms:
                if room.intersect(other_room):
                    failed = True
                    break

            if not failed:
                self.rooms.append(room)
                self.start_region()
                self.create_room(room)

    def connect_regions(self):
        # Find all of the tiles that can connect two regions
        north = (0, -1)
        south = (0, 1)
        east = (1, 0)
        west = (-1, 0)

        connector_regions = [[None for y in range(self.map_height)] for x in range(self.map_width)]

        for x in range(1, self.map_width - 1):
            for y in range(1, self.map_height - 1):
                if self.level[x][y] != 1:
                    continue

                # count the number of different regions the wall tile is touching
                regions = set()
                for direction in [north, south, east, west]:
                    new_x = x + direction[0]
                    new_y = y + direction[1]
                    region = self._regions[new_x][new_y]
                    if region:
                        regions.add(region)

                if len(regions) < 2:
                    continue

                # The wall tile touches at least two regions
                connector_regions[x][y] = regions

        # make a list of all of the connectors
        connectors = set()
        for x in range(0, self.map_width):
            for y in range(0, self.map_height):
                if connector_regions[x][y]:
                    connector_position = (x, y)
                    connectors.add(connector_position)


        # keep track of the regions that have been merged.
        merged = {}
        open_regions = set()
        for i in range(self._current_region + 1):
            merged[i] = i
            open_regions.add(i)

        # connect the regions
        number_of_tries = 0
        max_tries = 250
        while len(open_regions) > 1:
            if number_of_tries > max_tries:
                break
            number_of_tries += 1
            # get random connector
            # connector = connectors.pop()
            for connector in connectors:
                break

            # carve the connection
            self.add_junction(connector)

            # merge the connected regions
            x = connector[0]
            y = connector[1]

            # make a list of the regions at (x,y)
            regions = []
            for n in connector_regions[x][y]:
                # get the regions in the form of merged[n]
                actual_region = merged[n]
                regions.append(actual_region)

            dest = regions[0]
            sources = regions[1:]

            '''
            Merge all of the effective regions. You must look
            at all of the regions, as some regions may have
            previously been merged with the ones we are
            connecting now.
            '''
            for i in range(self._current_region + 1):
                if merged[i] in sources:
                    merged[i] = dest

            # clear the sources, they are no longer needed
            # print('sources:', sources)
            # print('open_regions:', open_regions)
            for s in sources:
                if s in open_regions:
                    open_regions.remove(s)

            # remove the unneeded connectors
            to_be_removed = set()
            for pos in connectors:
                # remove connectors that are next to the current connector
                if distance(connector, pos) < 2:
                    # remove it
                    to_be_removed.add(pos)
                    continue

                regions = set()
                x = pos[0]
                y = pos[1]
                for n in connector_regions[x][y]:
                    actual_region = merged[n]
                    regions.add(actual_region)
                if len(regions) > 1:
                    continue

                if random.random() < self.connection_chance:
                    self.add_junction(pos)

                # remove it
                if len(regions) == 1:
                    to_be_removed.add(pos)

            connectors.difference_update(to_be_removed)

    def create_room(self, room):
        # set all tiles within a rectangle to 0
        for x in range(int(room.x1), int(room.x2)):
            for y in range(int(room.y1), int(room.y2)):
                self.carve(x, y)

    def add_junction(self, pos):
        self.level[pos[0]][pos[1]] = 0

    def remove_dead_ends(self):
        done = False

        north = (0, -1)
        south = (0, 1)
        east = (1, 0)
        west = (-1, 0)

        while not done:
            done = True

            for y in range(1, self.map_height):
                for x in range(1, self.map_width):
                    if self.level[x][y] == 0:

                        exits = 0
                        for direction in [north, south, east, west]:
                            try:
                                if self.level[x + direction[0]][y + direction[1]] == 0:
                                    exits += 1
                            except IndexError:
                                continue
                        if exits > 1:
                            continue

                        done = False
                        self.level[x][y] = 1

    def can_carve(self, pos, direction):
        """
        gets whether an opening can be carved at the location
        adjacent to the cell at (pos) in the (dir) direction.
        returns False if the location is out of bounds or if the cell
        is already open.
        """
        x = pos[0] + direction[0] * 3
        y = pos[1] + direction[1] * 3

        if not (0 < x < self.map_width) or not (0 < y < self.map_height):
            return False

        x = pos[0] + direction[0] * 2
        y = pos[1] + direction[1] * 2

        # return True if the cell is a wall (1)
        # false if the cell is a floor (0)
        return self.level[x][y] == 1

    def start_region(self):
        self._current_region += 1

    def carve(self, x, y):
        self.level[x][y] = 0
        try:
            self._regions[x][y] = self._current_region
        except IndexError:
            print(x, y)
            print(self._regions)


# ==== Helper Classes/Funtions ====
def distance(point1, point2):
    d = sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)
    return d


class Rect:  # used for the tunneling algorithm
    def __init__(self, x, y, w, h, buffer=0):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.buffer = buffer
        self.width = w
        self.height = h

    @property
    def x(self):
        return self.x1

    @property
    def y(self):
        return self.y1

    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    def intersect(self, other):
        # returns true if this rectangle intersects with another one
        return (self.x1 < other.x2 + other.buffer and self.x2 + other.buffer > other.x1 and
                self.y1 < other.y2 + other.buffer and self.y2 + other.buffer > other.y1)


if __name__ == '__main__':
    width = 55
    height = 55
    m = MazeWithRooms()
    m.generate(width, height)
    level = [[0 for y in range(height)] for x in range(width)]
    for y in range(width):
        for x in range(height):
            if m.level[x][y] == 1:
                level[x][y] = '#'
            else:
                level[x][y] = '.'

    # Rotate Matrix and Print
    level = np.rot90(level, k=1, axes=(1, 0))
    for row in level:
        print(" ".join(row))
