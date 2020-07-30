from math import sqrt
from random import randint, random

from level_generation.GenerationUtils import create_floor, create_wall, place_entities, place_stairs
from map_objects.Shapes import Cave


class CellularAutomataAlgorithm:
    """
    Rather than implement a traditional cellular automata, I
    decided to try my hand at a method discribed by "Evil
    Scientist" Andy Stobirski that I recently learned about
    on the Grid Sage Games blog.
    """

    def __init__(self):
        self.game_map = None
        self.caves = []
        self.cave_centers = []
        self.dungeon_level = 0
        self.map_width = 0
        self.map_height = 0

        # Adjustable Generation Variables
        self.smooth_edges = True
        self.smoothing = 1
        self.wall_probability = 0.5  # the probability of a cell becoming a wall, recommended to be between .35 and .55

        self.ROOM_MIN_SIZE = 4  # size in total number of cells, not dimensions
        self.ROOM_MAX_SIZE = 10  # size in total number of cells, not dimensions
        self.iterations = 30000
        self.neighbors = 4  # number of neighboring walls for this cell to become a wall

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, item_table, mob_table):
        # def generate_level(self, game_map, map_width, map_height):
        # Creates an empty 2D array or clears existing array
        self.game_map = game_map
        self.dungeon_level = dungeon_level
        self.map_width = map_width
        self.map_height = map_height

        print('Random Fill Map')
        self.random_fill_map(map_width, map_height)
        print('Create Caves')
        self.create_caves(map_width, map_height)
        print('Get Caves')
        self.get_caves(map_width, map_height)
        print('Connect Caves')
        self.connect_caves(map_width, map_height)
        print('Clean Up Map')
        self.clean_up_map(map_width, map_height)
        # Find Center of Caves
        print('find_cave_centers')
        self.find_cave_centers()

        # Check if Caves were Actually Generation, Recall Same Generation
        if not self.cave_centers:
            print('Couldn\'t generate caves. Restarting...')
            self.reset_generation()
            entities = [player]
            self.generate_level(game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width,
                                 map_height, player, entities, item_table, mob_table)
            return False

        # Place Player and Stairs, Open Floor
        # TODO: Connect caves 1 and 2
        player.position.x, player.position.y = self.cave_centers[0].center
        create_floor(game_map, player.position.x, player.position.y)
        x, y = self.cave_centers[-1].center
        entities.append(place_stairs(self.dungeon_level, x, y))
        create_floor(game_map, x, y)

        # TODO: Ensure there is a path for player and path to stairs

        # Spawn Entities
        for cave in self.cave_centers:
            place_entities(game_map, dungeon_level, cave, entities, item_table, mob_table)
            # debug find centers

            # cx, cy = cave.center
            # print('cave center at: (%s, %s)' % (cx, cy))
            create_floor(game_map, cave.x, cave.y)
            # create_floor(game_map, cave.x, cave.y)
            # print('cave center at: (%s, %s)' % (cave.x, cave.y))

        self.print_generation_stats(entities)

    def random_fill_map(self, map_width, map_height):
        for y in range(2, map_height - 2):
            for x in range(2, map_width - 2):
                # print("(",x,y,") = ",self.game_map.tiles[x][y])
                if random() >= self.wall_probability:
                    create_floor(self.game_map, x, y)

    def create_caves(self, map_width, map_height):
        # ==== Create distinct caves ====
        for i in range(0, self.iterations):
            # Pick a random point with a buffer around the edges of the map
            tile_x = randint(2, map_width - 3)  # (2,map_width-3)
            tile_y = randint(2, map_height - 3)  # (2,map_height-3)

            # if the cell's neighboring walls > self.neighbors, set it to 1
            if self.get_adjacent_walls(tile_x, tile_y) > self.neighbors:
                # self.game_map.tiles[tile_x][tile_y] = 1
                create_wall(self.game_map, tile_x, tile_y)
            # or set it to 0
            elif self.get_adjacent_walls(tile_x, tile_y) < self.neighbors:
                create_floor(self.game_map, tile_x, tile_y)

        # ==== Clean Up Map ====
        self.clean_up_map(map_width, map_height)

    def clean_up_map(self, map_width, map_height):
        if self.smooth_edges:
            for i in range(0, 5):
                # Look at each cell individually and check for smoothness
                for x in range(2, map_width - 2):
                    for y in range(2, map_height - 2):
                        if self.game_map.is_blocked(x, y) and self.get_adjacent_walls_simple(x, y) <= self.smoothing:
                            create_floor(self.game_map, x, y)

    def create_tunnel(self, point1, point2, current_cave, map_width, map_height):
        # run a heavily weighted random Walk
        # from point1 to point1
        print('create_tunnel random walk')
        drunkard_x = point2[0]
        drunkard_y = point2[1]
        while (drunkard_x, drunkard_y) not in current_cave:
            # ==== Choose Direction ====
            north = 1.0
            south = 1.0
            east = 1.0
            west = 1.0

            weight = 1

            # weight the random walk against edges
            if drunkard_x < point1[0]:  # drunkard is left of point1
                east += weight
            elif drunkard_x > point1[0]:  # drunkard is right of point1
                west += weight
            if drunkard_y < point1[1]:  # drunkard is above point1
                south += weight
            elif drunkard_y > point1[1]:  # drunkard is below point1
                north += weight

            # normalize probabilities so they form a range from 0 to 1
            total = north + south + east + west
            north /= total
            south /= total
            east /= total
            west /= total

            # choose the direction
            choice = random()
            if 0 <= choice < north:
                dx = 0
                dy = -1
            elif north <= choice < (north + south):
                dx = 0
                dy = 1
            elif (north + south) <= choice < (north + south + east):
                dx = 1
                dy = 0
            else:
                dx = -1
                dy = 0

            # ==== Walk ====
            # check collision at edges
            if (0 < drunkard_x + dx < map_width - 1) and (0 < drunkard_y + dy < map_height - 1):
                drunkard_x += dx
                drunkard_y += dy
                if self.game_map.is_blocked(drunkard_x, drunkard_y):
                    create_floor(self.game_map, drunkard_x, drunkard_y)

    def get_adjacent_walls_simple(self, x, y):  # finds the walls in four directions
        wall_counter = 0
        # print("(",x,",",y,") = ",self.game_map.tiles[x][y])
        if self.game_map.is_blocked(x, y - 1):  # Check north
            wall_counter += 1
        if self.game_map.is_blocked(x, y + 1):  # Check south
            wall_counter += 1
        if self.game_map.is_blocked(x - 1, y):  # Check west
            wall_counter += 1
        if self.game_map.is_blocked(x + 1, y):  # Check east
            wall_counter += 1

        return wall_counter

    def get_adjacent_walls(self, tile_x, tile_y):  # finds the walls in 8 directions
        wall_counter = 0
        # print('get_adjacent_walls')
        # print(range(tile_x - 1, tile_x + 2), self.map_width)
        # print(range(tile_y - 1, tile_y + 2), self.map_height)
        for x in range(tile_x - 1, tile_x + 2):
            for y in range(tile_y - 1, tile_y + 2):

                if self.game_map.is_blocked(x, y):
                    if x != tile_x or y != tile_y:  # exclude (tile_x,tile_y)
                        wall_counter += 1
        return wall_counter

    def get_caves(self, map_width, map_height):
        # locate all the caves within self.game_map.tiles and store them in self.caves
        # print('locate all the caves within self.game_map.tiles and store them in self.caves')
        for x in range(1, map_width - 1):
            for y in range(1, map_height-1):
                if not self.game_map.is_blocked(x, y):
                    self.flood_fill(x, y)

        for tile_set in self.caves:
            for x, y in tile_set:
                create_floor(self.game_map, x, y)

        # check for 2 that weren't changed.
        """
        The following bit of code doesn't do anything. I 
        put this in to help find mistakes in an earlier 
        version of the algorithm. Still, I don't really 
        want to remove it.
        """
        # for x in range(0, map_width):
        #     for y in range(0, map_height):
        #         if self.game_map.tiles[x][y] == 2:
        #             print("(", x, ",", y, ")")

    def flood_fill(self, x, y):
        """
        flood fill the separate regions of the level, discard
        the regions that are smaller than a minimum size, and
        create a reference for the rest.
        """
        # TODO: Optimize calculations for flood fill in cellular automata
        cave = set()
        tile = (x, y)
        to_be_filled = set([tile])
        while to_be_filled:
            # print('to_be_filled:', to_be_filled)
            tile = to_be_filled.pop()

            if tile not in cave:
                cave.add(tile)
                create_wall(self.game_map, tile[0], tile[1])

                # check adjacent cells
                x = tile[0]
                y = tile[1]
                north = (x, y - 1)
                south = (x, y + 1)
                east = (x + 1, y)
                west = (x - 1, y)

                for direction in [north, south, east, west]:

                    if not self.game_map.is_blocked(direction[0], direction[1]):
                        if direction not in to_be_filled and direction not in cave:
                            to_be_filled.add(direction)

        if len(cave) >= self.ROOM_MIN_SIZE:
            self.caves.append(cave)

    def connect_caves(self, map_width, map_height):
        # TODO: Optimize calculations for connect_caves cellular automata
        # Find the closest cave to the current cave
        point1 = None
        for current_cave in self.caves:
            for point1 in current_cave: 
                break  # get an element from cave1
            point2 = None
            distance = 0
            # Show Caves
            # for i, coordinates in enumerate(self.caves):
            #     print('cave #%s:' % i, coordinates)
            print('There are %s caves.' % len(self.caves))
            for i, next_cave in enumerate(self.caves):
                print('Cave %s with %s points' % (1 + i, len(next_cave)))
                if next_cave != current_cave and not self.check_connectivity(current_cave, next_cave):
                    # choose a random point from next_cave
                    next_point = None
                    for next_point in next_cave: 
                        break  # get an element from cave1
                    # compare distance of point1 to old and new point2
                    # print('# compare distance of point1 to old and new point2')
                    # print(point1, next_point, next_cave)
                    new_distance = self.distance_formula(point1, next_point)
                    if new_distance < distance or distance == 0:
                        point2 = next_point
                        distance = new_distance
            print('done')
            # if point2:  # if all tunnels are connected, point2 == None
            #     self.create_tunnel(point1, point2, current_cave, map_width, map_height)

    @staticmethod
    def distance_formula(point1, point2):
        d = sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)
        return d

    def check_connectivity(self, cave1, cave2):
        # floods cave1, then checks a point in cave2 for the flood

        connected_region = set()
        # get an element from cave1
        # print('cave1:', cave1)
        if cave1:
            start = cave1.pop()
        else:
            start = ()
        # for start in cave1:
        #     break  # get an element from cave1

        to_be_filled = set([start])
        if start:
            while to_be_filled:
                tile = to_be_filled.pop()

                if tile not in connected_region:
                    connected_region.add(tile)

                    # check adjacent cells
                    x = tile[0]
                    y = tile[1]
                    north = (x, y - 1)
                    south = (x, y + 1)
                    east = (x + 1, y)
                    west = (x - 1, y)

                    for direction in [north, south, east, west]:
                        if not self.game_map.is_blocked(direction[0], direction[1]):
                            if direction not in to_be_filled and direction not in connected_region:
                                to_be_filled.add(direction)

        # get an element from cave2
        end = ()
        if cave2:
            end = cave2.pop()
            if end in connected_region:
                return True
        return False

        # for end in cave2:
        #     break  # get an element from cave2
        #
        # if end in connected_region:
        #     return True
        # else:
        #     return False

    def find_cave_centers(self):
        # Generate cave centers for spawns.
        # TODO: Integrate within main generation function
        for cave_coords in self.caves:
            c = Cave(self.game_map, cave_coords, len(self.game_map.rooms) + 1)
            self.cave_centers.append(c)
            self.game_map.rooms.append(c)

    def reset_generation(self):
        self.game_map = None
        self.caves = []
        self.cave_centers = []
        self.dungeon_level = 0
        self.map_width = 0
        self.map_height = 0

    def print_generation_stats(self, entities):
        print('\nCellular Automata Complete')
        print('Number of Caves:', len(self.cave_centers))
        print('Number of Entities:', len(entities) - 1)
