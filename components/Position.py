from math import sqrt

from tcod.path import AStar, Dijkstra


class Position:
    x = 0
    y = 0

    def __init__(self, x, y):
        self.x = x
        self.y = y

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

    def move_astar(self, target_x, target_y, game_map, diagonal_cost=1.41):
        # Astar Pathfinding to Obtain Optimal Path to Target
        astar = AStar(game_map.tile_cost, diagonal_cost)
        # print('move_astar', self.y, self.x, target_y, target_x)
        return astar.get_path(self.y, self.x, target_y, target_x)

    def move_dijkstra(self, target_x, target_y, game_map):
        dijkstra_path = []
        return dijkstra_path

    def move_farthest(self, entities, game_map):
        # Use Cost Map To Find Best Path Furthest From Target
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