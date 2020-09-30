from math import sqrt

import numpy as np


from tcod.path import AStar, dijkstra2d, hillclimb2d, maxarray


class Position:
    x = 0
    y = 0

    def __init__(self, x, y, minimum_dist=1, movement_type="astar"):
        self.x = x
        self.y = y
        self.minimum_dist = minimum_dist

        # How Each Entity Determines its movement, Defined in their .json file
        if movement_type == "dijkstra":
            self.movement_function = self.move_dijkstra
        else:
            self.movement_function = self.move_astar

    def move(self, dx, dy):
        # Move the entity by a given amount
        self.x += dx
        self.y += dy

    def move_towards(self, target_x, target_y, game_map, entities):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = sqrt(dx ** 2 + dy ** 2)
        if distance == 0:
            return
        dy = int(round(dy / distance))
        dx = int(round(dx / distance))

        if not (game_map.is_blocked(self.x + dx, self.y + dy)) or not (game_map.tile_cost[self.x + dx][self.y + dy] >= 99):
            self.move(dx, dy)

    # def move_evade(self, target_x, target_y, game_map, distance):

    def move_astar(self, target_x, target_y, game_map, diagonal_cost=1.41):
        # Astar Pathfinding to Obtain Optimal Path to Target
        astar = AStar(game_map.tile_cost, diagonal_cost)
        # print('move_astar', self.y, self.x, target_y, target_x)
        return astar.get_path(self.y, self.x, target_y, target_x)

    def move_dijkstra(self, target_x, target_y, game_map):
        # print("Position x={} y={}, {}".format(self.x, self.y, self.movement_function))
        # print(self)
        # print('target : ', target_x, target_y)
        # for row in game_map.walkable[0:game_map.height - 1, 0:game_map.width - 1w

        # print(game_map.tile_cost[0:game_map.height - 1, 0:game_map.width - 1])

        # Obtain Cost Map - How much each Tile "costs" to travel to
        np.set_printoptions(linewidth=200)
        cost_map = np.array(game_map.tile_cost)[0:game_map.map.height + 1, 0:game_map.map.width + 1] * 1
        # print('cost_map')
        # for row in cost_map:
        #     print(row)

        # Obtain Dist Map - Walkable(0, False) vs Walkable(1, True)
        # dist_map = np.array(game_map.tile_cost)[0:game_map.map.height + 1, 0:game_map.map.width + 1]
        dist_map = maxarray((game_map.map.height + 1, game_map.map.width + 1), dtype=np.uint16)
        dist_map[target_y][target_x] = 0
        dijkstra2d(dist_map, cost_map, 1, 1)
        # dist_map[self.y][self.x] = 8

        print("TODO: Class: Position Set goal at minimum dist away from target")
        dijkstra_path = hillclimb2d(dist_map, (self.y, self.x), True, True)

        # Show on Map
        # dist_map[target_y][target_x] = 9
        # dist_map[self.y][self.x] = 8
        # for row in dist_map:
        #     print(row)
        # print("dijkstra_path : ", dijkstra_path)
        path = dijkstra_path.tolist()
        return path[1:]

    def move_farthest(self, entities, game_map):
        # Use Localized Cost Map To Find Best Path Furthest From Target
        dijkstra_path = []
        return dijkstra_path

    def distance(self, x, y):
        return sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def distance_to(self, other_x, other_y):
        dx = other_x - self.x
        dy = other_y - self.y
        return sqrt(dx ** 2 + dy ** 2) - 1

    def __repr__(self):
        return "Position x={} y={}".format(self.x, self.y)