from math import sqrt
from random import randint, random

from level_generation.GenerationUtils import create_floor, place_entities, place_stairs
from map_objects.Shapes import Circle


class RandomWalkAlgorithm:
    def __init__(self):
        self.game_map = None
        self._percentGoal = .6
        self.walk_iterations = 50000  # cut off in case _percentGoal in never reached
        self.weighted_toward_center = 0.15
        self.weighted_toward_previous_generation = 0.7
        self.dungeon_level = 0
        self.encounter_interval = 35  # every (x) steps, place entities
        self.encounters = []

        self.radius = 11

        # Generation Variables
        self.filledGoal = 0
        self._previousDirection = None
        self._filled = 0
        self.random_walk_x = 0
        self.random_walk_y = 0

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, item_table, mob_table, object_table):
        # Creates an empty 2D array or clears existing array
        self.walk_iterations = max(self.walk_iterations, (map_width * map_height * 10))
        self.game_map = game_map
        self.dungeon_level = dungeon_level
        self.random_walk_x = randint(self.radius, map_width - self.radius - 1)
        self.random_walk_y = randint(self.radius, map_height - self.radius - 1)

        # Modify Percent Goal Depending on Dungeon Level
        # self._percentGoal = 0.1 + (self.dungeon_level * 0.015)

        self.filledGoal = map_width * map_height * self._percentGoal

        # Place Player at 1st Location
        # TODO: Sometimes player spawns inside a wall?
        player.x, player.y = self.random_walk_x, self. random_walk_y
        create_floor(game_map, player.x, player.y)
        self.encounters.append((player.x, player.y))

        for i in range(self.walk_iterations):
            self.walk(map_width, map_height)

            # Check for Encounter
            if self._filled % self.encounter_interval == 0:
                if self.encounter_within_proximity(self.random_walk_x, self.random_walk_y):

                    if self.radius < self.random_walk_x < map_width - self.radius and self.radius < self.random_walk_y < map_height - self.radius:
                        room = Circle(game_map, self.random_walk_x, self.random_walk_y, self.radius,
                                      len(game_map.rooms) + 1)
                        game_map.rooms.append(room)
                        place_entities(self.game_map, self.dungeon_level, room, entities, item_table, mob_table, object_table)
                        self.encounters.append((self.random_walk_x, self.random_walk_y))
                else:
                    # TODO: Find a way to not allow multiple iteration checks for encounter_within_proximity
                    # Note: The below line is a lie. We're not really filling up more spaces.
                    self._filled += 1

            if self._filled >= self.filledGoal:
                break

        # Place Stairs at Last Location
        entities.append(place_stairs(self.dungeon_level, self.random_walk_x, self.random_walk_y))
        create_floor(game_map, self.random_walk_x, self.random_walk_y)
        # self.print_generation_stats(i)

    def walk(self, map_width, map_height):
        # ==== Choose Direction ====
        north = 1.0
        south = 1.0
        east = 1.0
        west = 1.0

        # weight the random walk against edges
        if self.random_walk_x < map_width * 0.25:  # random walk is at far left side of map
            east += self.weighted_toward_center
        elif self.random_walk_x > map_width * 0.75:  # random walk is at far right side of map
            west += self.weighted_toward_center
        if self.random_walk_y < map_height * 0.25:  # random walk is at the top of the map
            south += self.weighted_toward_center
        elif self.random_walk_y > map_height * 0.75:  # random walk is at the bottom of the map
            north += self.weighted_toward_center

        # weight the random walk in favor of the previous direction
        if self._previousDirection == "north":
            north += self.weighted_toward_previous_generation
        if self._previousDirection == "south":
            south += self.weighted_toward_previous_generation
        if self._previousDirection == "east":
            east += self.weighted_toward_previous_generation
        if self._previousDirection == "west":
            west += self.weighted_toward_previous_generation

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
            direction = "north"
        elif north <= choice < north + south:
            dx = 0
            dy = 1
            direction = "south"
        elif north + south <= choice < north + south + east:
            dx = 1
            dy = 0
            direction = "east"
        else:
            dx = -1
            dy = 0
            direction = "west"

        # ==== Walk ====
        # check collision at edges
        if 0 < self.random_walk_x + dx < map_width - 1 and 0 < self.random_walk_y + dy < map_height - 1:
            self.random_walk_x += dx
            self.random_walk_y += dy
            # if self.game_map.tiles[self.random_walk_x][self.random_walk_y].blocked:
            if not self.game_map.walkable[self.random_walk_y][self.random_walk_x]:
                create_floor(self.game_map, self.random_walk_x, self.random_walk_y)
                self._filled += 1
            self._previousDirection = direction

    def encounter_within_proximity(self, x, y):
        # print('\nchecking from (%s, %s)' % (x, y))
        # TODO: Why do monsters still spawn next to each other?
        for ex, ey in self.encounters:
            # Check if Selected Area is too Close to other encounters
            # print('distance from (%s, %s): %s' % (ex, ey, sqrt((x - ex)**2 + (y - ey)**2)))
            if sqrt((x - ex)**2 + (y - ey)**2) <= self.radius:
                return False
        return True

    def print_generation_stats(self, cycles):
        print('\nGeneration Stats:')
        # print('Percent Filled:', '%s%%' % (self._filled/self.filledGoal * 100), self._filled, self.filledGoal)
        # print('Max Walks Iterations:', self.walk_iterations)
        print('Number of Walks:', cycles)
        print('Number of Open Floor:', self._filled)
        print('Open Floor/Walks Ratio:', self._filled/cycles)
        print('There are currently %s encounters generated.' % len(self.encounters[1:]))
        print('Number of Rooms:', len(self.game_map.rooms))
