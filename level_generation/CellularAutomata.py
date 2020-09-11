from math import sqrt
from random import randint
from collections import deque

import numpy as np


class CellularAutomata:
    width = 20
    height = 20
    grid = None
    wall_chance = 40  # percentage chance of randomly generating wall
    min_count = 5  # min count of surrounding walls for the automata rules
    iterations = 0
    pillar_iterations = 1
    flood_tries = 5
    goal_percentage = 30
    open_percentage = 0
    encounter_spread_factor = 6

    sparse_wall_density = 3
    areas_of_interest = []  # areas of open space
    start_area = None
    end_area = None

    def create_entrance_exit(self, castle_entrance=False):
        # Assume Entrance at Bottom, Exit at Top


        # Generate Start Area
        # entrance_x = 0
        entrance_x = randint(2, len(self.grid) - 2)
        entrance_y = len(self.grid[0]) - 1
        width, height = 3, 3
        self.start_area = AreaofInterest(entrance_x, entrance_y, width, height)

        # Generate End Area
        # entrance_x = len(self.grid) - 1
        print('castle_entrance:', castle_entrance)
        if castle_entrance:

            entrance_x = self.width // 2
            width, height = 15, 8
        else:
            entrance_x = randint(2, len(self.grid) - 2)
            width, height = 3, 3
        entrance_y = 0

        self.end_area = AreaofInterest(entrance_x, entrance_y, width, height)

        # Clear Tiles Around Start/End
        for x in range(self.start_area.x - self.start_area.width//2, self.start_area.x + 1 + self.start_area.width//2):
            for y in range(self.start_area.y - self.start_area.height//2, self.start_area.y + 1 + self.start_area.height):
                try:
                    1 // (abs(y + 1) + y + 1)
                    1 // (abs(x + 1) + x + 1)
                    self.grid[x][y] = 0
                except IndexError:
                    pass
                except ZeroDivisionError:
                    pass

        for x in range(self.end_area.x - self.end_area.width//2, self.end_area.x + 1 + self.end_area.width//2):
            for y in range(self.end_area.y  - self.end_area.height//2, self.end_area.y + 1 + self.end_area.height//2):
                try:
                    1 // (abs(y + 1) + y + 1)
                    1 // (abs(x + 1) + x + 1)
                    self.grid[x][y] = 0
                except IndexError:
                    pass
                except ZeroDivisionError:
                    pass

        self.areas_of_interest.extend([self.start_area, self.end_area])

    def ensure_path(self):
        # self.print_grid()

        for area in [self.start_area, self.end_area]:
            closest_area = self.find_closest_area(area)
            if closest_area:
                # print(area, closest_area)
                x = area.x
                y = area.y
                end_x = closest_area.x
                end_y = closest_area.y
                connected = False
                while not connected:

                    if x > end_x:
                        x -= 1

                    elif x < end_x:
                        x += 1

                    if y > end_y:
                        y -= 1

                    elif y < end_y:
                        y += 1

                    # print('creating path at', x, y, x != end_x and y != end_y)
                    for dir_x, dir_y in [(x-1, y), (x+1, y), (x, y-1), (x, y+1), (x, y)]:
                        try:
                            self.grid[dir_x][dir_y] = 0
                        except IndexError:
                            pass

                    if x == end_x and y == end_y:
                        connected = True

        # self.print_grid()

    def find_closest_area(self, origin_area):
        dist = 999
        closest_area = AreaofInterest(x=-5000, y=5000, width=1, height=1)
        for area in self.areas_of_interest:
            _dist = distance(origin_area.x, origin_area.y, area.x, area.y)
            if _dist < dist and (area.x, area.y) != (origin_area.x, origin_area.y):
                dist = _dist
                closest_area = area
        return closest_area

    def generate(self, castle_entrance):
        self.reset_grid()
        self.areas_of_interest = []

        # Randomly populated grid
        self.populate_grid()

        # Iterate Cellular Automata Rules
        for i in range(self.pillar_iterations):
            # print("{0} iteration(s) of automata with pillars:".format(i + 1))
            self.automata_iteration(make_pillars=1)

        # Iterate Modified Cellular Automata Rules to Add Walls
        for i in range(self.iterations):
            # print("{0} iteration(s) of regular automata:".format(i + 1))
            self.automata_iteration(make_pillars=0)

        self.populate_grid(self.wall_chance / self.sparse_wall_density)
        self.flood_find_empty()
        self.create_entrance_exit(castle_entrance)
        self.find_areas_if_interest()
        self.ensure_path()
        """
        - self reminder to try checking map size 
        - https://stackoverflow.com/questions/1331471/in-memory-size-of-a-python-structure
        """

    def print_grid(self, wall_char="# ", empty_char=". ", area_char='$ ', grid=None):
        final_str = ""
        final_str += "\n"

        if grid:
            _grid = grid
        else:
            _grid = self.grid

        for i in range(len(_grid[0])):
            for j in range(len(_grid)):
                if _grid[j][i] == 0:
                    final_str += empty_char
                elif _grid[j][i] == 1:
                    final_str += wall_char
                elif _grid[j][i] == 2:
                    final_str += area_char
            final_str += "\n"
        final_str += "\n"
        print(final_str)

    def reset_grid(self):
        # All Floor
        new_grid = [[0 for x in range(self.height)] for y in range(self.width)]

        # Set Border to Wall
        for i in range(len(new_grid)):
            for j in range(len(new_grid[i])):
                if i == 0 or j == 0 or i == len(new_grid) - 1 or j == len(new_grid[0]) - 1:
                    new_grid[i][j] = 1

        # Assign Grid
        self.grid = new_grid

    def populate_grid(self, wall_chance=None):
        print('populate_grid')
        if not wall_chance:
            wall_chance = self.wall_chance

        # Randomly Populate Grid
        for i in range(len(self.grid)):  # reminder to test with: for index, value in enumerate(grid)
            for j in range(len(self.grid[0])):
                if randint(0, 100) <= wall_chance:  # test with list comprehension instead??
                    self.grid[i][j] = 1
        """
        bsp_x = 10
        bsp_y = 15
        bsp_width = 40
        bsp_height = 30
        """
        # self.grid[10:50][15:30] = np.zeros_like(self.grid[10:50][15:30])
        # for row in self.grid:
        #     print(row)
            
    def automata_iteration(self, make_pillars):
        make_grid = [row[:] for row in self.grid]
        for i in range(1, len(self.grid) - 1):
            for j in range(1, len(self.grid[0]) - 1):
                count = 0

                # Check 4x4 area around cell and count obstacles
                for k in range(-1, 2):
                    for l in range(-1, 2):
                        if self.grid[i + k][j + l] == 1:
                            count += 1

                # Add Wall or Remove Wall
                if count >= self.min_count or (count == 0 and make_pillars == 1):
                    make_grid[i][j] = 1
                else:
                    make_grid[i][j] = 0
        self.grid = make_grid

    @staticmethod
    def inside_circle(center_x, center_y, point_x, point_y, radius):
        dx = center_x - point_x
        dy = center_y - point_y
        distance_squared = dx * dx + dy * dy
        return distance_squared <= radius * radius

    def find_areas_if_interest(self, radius=1):
        # Find Areas of Interest to Spawn Prefabs or entities
        possible_areas = []

        for center_x in range(self.width):
            for center_y in range(self.height):

                open_area_count = 0
                # Cache Circle Dimensions
                top = max(0, center_y - radius)
                bottom = min(self.height, center_y + radius)
                left = max(0, center_x - radius)
                right = min(self.width, center_x + radius)

                # Iterate Through Circle Bounding Box
                for point_x in range(left, right):
                    for point_y in range(top, bottom):

                        # If not Wall and Coordinates not In Possible Areas Already
                        if self.grid[point_x][point_y] != 1 and (point_x, point_y) not in possible_areas:
                            open_area_count += 1

                # Add to Possible List for Areas-of-Interest
                if open_area_count >= 4:
                    possible_areas.append((center_x, center_y))

        # Among All Possible Areas, Remove Close Areas
        radius = min(self.width // self.encounter_spread_factor, self.height // self.encounter_spread_factor)
        possible_areas.extend([(self.start_area.x+1, self.start_area.y+1), (self.end_area.x+1, self.end_area.y+1)])
        areas = []
        while possible_areas:
            center_x, center_y = possible_areas.pop()

            # Cache Circle Dimensions to Measure Within
            top = max(0, center_y - radius)
            bottom = min(self.height, center_y + radius)
            left = max(0, center_x - radius)
            right = min(self.width, center_x + radius)

            # Check if Coordinates are Inside Circle, not in Possible Areas and not Center Origin
            for x in range(left, right):
                for y in range(top, bottom):
                    if self.inside_circle(center_x, center_y, x, y, radius) and (x, y) in possible_areas and \
                            (x, y) != (center_x, center_y):
                        possible_areas.remove((x, y))

            # Finally Add to Final List
            areas.append((center_x-1, center_y-1))
            # areas.append(AreaofInterest(x=center_x-1, y=center_y-1, width=3, height=3))
        areas.remove((self.start_area.x, self.start_area.y))
        areas.remove((self.end_area.x, self.end_area.y))
        self.areas_of_interest.extend([AreaofInterest(x=center_x-1, y=center_y-1, width=3, height=3) for center_x, center_y in areas])

    def flood_find_empty(self):
        times_remade = 0
        percentage = 0
        make_grid = [[1 for x in range(len(self.grid[0]))] for y in range(len(self.grid))]

        # Multiple Flood Fill Checks to Ensure Good Map, Removing Small Unconnected Caves
        while times_remade < self.flood_tries and percentage < self.goal_percentage:
            copy_grid = [row[:] for row in self.grid]
            open_count = 0
            times_remade += 1
            unvisited = deque([])
            make_grid = [[1 for x in range(len(self.grid[0]))] for y in range(len(self.grid))]

            # Select Random Starting Point
            randx = randint(0, len(self.grid) - 1)
            randy = randint(0, len(self.grid[0]) - 1)
            while self.grid[randx][randy] == 1:
                randx = randint(0, len(self.grid) - 1)
                randy = randint(0, len(self.grid[0]) - 1)
            unvisited.append([randx, randy])

            # Flood Fill to find All Open Spaces
            while len(unvisited) > 0:
                current = unvisited.popleft()
                make_grid[current[0]][current[1]] = 0
                for k in range(-1, 2):
                    for l in range(-1, 2):
                        if current[0] + k >= 0 and current[0] + k < len(self.grid) and current[1] + l >= 0 and \
                                current[1] + l < len(self.grid[0]):  # if we're not out of bounds
                            if copy_grid[current[0] + k][current[1] + l] == 0:  # if it's an empty space
                                copy_grid[current[0] + k][current[1] + l] = 2  # mark visited
                                open_count += 1
                                unvisited.append([current[0] + k, current[1] + l])
            percentage = open_count * 100 / (len(self.grid) * len(self.grid[0]))
            # print("counted {0}, {1}%...".format(open_count, percentage))
        self.grid = make_grid
        self.open_percentage = percentage

        # if percentage < self.goal_percentage:
        #     print("Failed to produce a big enough cave after {0} tries...".format(self.flood_tries))
        # else:
        #     print("Percentage of open space: {0}%".format(percentage))


class AreaofInterest:

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, x, y):
        return (
                self.x <= x < self.x + self.width
                and self.y <= y < self.y + self.height
        )

    @property
    def size(self):
        return self.width * self.height

    def __repr__(self):
        return "Area of Interest at (%s, %s) with width/height: (%s, %s)" % (self.x, self.y, self.width, self.height)

    @property
    def center(self):
        x = self.x + self.width // 2
        y = self.y + self.height // 2
        return x, y

    def obtain_point_within(self, padding):
        return randint(self.x, self.x + self.width), randint(self.y, self.y + self.height)


def distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


if __name__ == "__main__":
    c = CellularAutomata()
    c.width = 25
    c.height = 25
    c.wall_chance = 40
    c.min_count = 5
    c.iterations = 2
    c.pillar_iterations = 1
    c.flood_tries = 5
    c.goal_percentage = 30  # above 30% seems to be a good target
    c.encounter_spread_factor = 6
    c.sparse_wall_density = 2
    c.generate()

    for area in c.areas_of_interest:
        a_x, a_y = area.x, area.y
        c.grid[a_x][a_y] = 2

    c.print_grid()
