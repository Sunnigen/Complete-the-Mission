import math

import tcod as libtcod
from tcod.path import AStar

from components.AI import DIRECTIONS
from components.Item import Item
from RenderFunctions import RenderOrder


class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """
    def __init__(self, x, y, char, color, name, blocks=False, render_order=RenderOrder.CORPSE, fighter=None, ai=None,
                 item=None, inventory=None, stairs=None, level=None, equipment=None, equippable=None, fov_color=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.render_order = render_order
        self.fighter = fighter
        self.ai = ai
        self.item = item
        self.inventory = inventory
        self.stairs = stairs
        self.level = level
        self.equipment = equipment
        self.equippable = equippable
        self.fov_color = fov_color  # color if entity if NOT within FOV, but explored

        if self.fighter:
            self.fighter.owner = self

        if self.ai:
            self.ai.owner = self

        if self.item:
            self.item.owner = self

        if self.inventory:
            self.inventory.owner = self

        if self.stairs:
            self.stairs.owner = self

        if self.level:
            self.level.owner = self

        if self.equipment:
            self.equipment.owner = self

        if self.equippable:
            self.equippable.owner = self

            # Every equipment picked up is an item and gets added to inventory
            #   therefore needs to be defined as an Item()
            if not self.item:
                item = Item()
                self.item = item
                self.item.owner = self

    def move(self, dx, dy):
        # Move the entity by a given amount

        self.x += dx
        self.y += dy

    def move_towards(self, target_x, target_y, game_map, entities):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance == 0:
            return
        dy = int(round(dy / distance))
        dx = int(round(dx / distance))

        if not (game_map.is_blocked(self.x + dx, self.y + dy) or get_blocking_entities_at_location(entities, self.x + dx
                , self.y + dy)):

            self.move(dx, dy)

    def move_astar(self, target, entities, game_map, fov_map):
        # TODO: Store astar path and update if only map/situation changes
        # print('\n\nmove_astar')
        astar = AStar(game_map.walkable.astype(int), 1.41)
        astar_path = astar.get_path(self.y, self.x, target.y, target.x)

        if astar_path:
            # print('path found')
            y, x = astar_path[0]

            # Check if Entity in the way
            if not game_map.transparent[y][x]:
                # print('path found but an entity blocks the way')
                self.ai.stuck_time += 1
                return
            game_map.transparent[self.y][self.x] = True  # unblock previous position
            game_map.transparent[y][x] = False  # block new position

            # Calculate New Direction
            if y > self.y:
                self.ai.direction_vector = DIRECTIONS.get('north')
            elif y < self.y:
                self.ai.direction_vector = DIRECTIONS.get('south')
            if x > self.x:
                self.ai.direction_vector = DIRECTIONS.get('east')
            elif x < self.x:
                self.ai.direction_vector = DIRECTIONS.get('west')

            if x > self.x and y > self.y:
                self.ai.direction_vector = DIRECTIONS.get('north east')
            elif x < self.x and y < self.y:
                self.ai.direction_vector = DIRECTIONS.get('south west')
            elif x > self.x and y < self.y:
                self.ai.direction_vector = DIRECTIONS.get('south east')
            elif x < self.x and y > self.y:
                self.ai.direction_vector = DIRECTIONS.get('north west')

            # Update Position
            self.x = x
            self.y = y
        # else:
        #     print('NO PATH FOUND!')
        #     print(self.y, self.x, target.y, target.x)
            # for row in game_map.walkable.astype(int):
            #     print(row)
        #     print('astar:\n', astar.get_path(self.y, self.x, target.y, target.x))


    # def move_astar(self, target, entities, game_map):
    #     # TODO: Use python tcod.path.AStar or tcod.path.Dijkstra
    #     # Create FOV Map that has the dimensions of the Map
    #     fov = libtcod.map_new(game_map.width, game_map.height)
    #
    #     # Scan the current map each turn and set all the walls as unwalkable
    #     for y1 in range(game_map.height):
    #         for x1 in range(game_map.width):
    #             libtcod.map_set_properties(fov, x1, y1, not game_map.tiles[x1][y1].block_sight,
    #                                        not game_map.tiles[x1][y1].blocked)
    #
    #     # Scan all the objects to see if there are objects that must be navigated around
    #     # Check also that the object isn't self or the target (so that the start and the end points are free)
    #     # The AI class handles the situation if self is next to the target so it will not use this A* function anyway
    #     # for entity in entities:
    #     #     if entity.blocks and entity != self and entity != target:
    #     #         # Set the tile as a wall so it must be navigated around
    #     #         libtcod.map_set_properties(fov, entity.x, entity.y, True, False)
    #
    #     # Allocate an A* Path
    #     # The 1.41 is the normal diagonal cost of moving, it can be set as 0.0 if diagonal moves are prohibited
    #     diagonal_cost = 1.41
    #     # TODO: How to deal with other entities blocking the path
    #     my_path = libtcod.path_new_using_map(fov, diagonal_cost)
    #
    #     # Compute the path between self's coordinates and the target
    #     libtcod.path_compute(my_path, self.x, self.y, target.x, target.y)
    #
    #     # Check if the path exists, and in this case, also the path is shorter than 25 tiles
    #     # The path size matters if you want the monster to use alternative longer paths (for example through other rooms) if for example the player is in a corridor
    #     # It makes sense to keep path size relatively low to keep the monsters from running around the map if there's an alternative path really far away
    #
    #     max_path_length = 50
    #     if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < max_path_length:
    #         # Find the next coordinates in the computed full path
    #         x, y = libtcod.path_walk(my_path, True)
    #
    #         if x or y:
    #             # Set self's coordinates to the next path tile
    #             self.x = x
    #             self.y = y
    #     else:
    #         # Keep the old move function as a backup so that if there are no paths (for example another monster blocks a corridor)
    #         # it will still try to move towards the player (closer to the corridor opening)
    #         # print('\ndoing move_towards, no Astar')
    #         self.move_towards(target.x, target.y, game_map, entities)
    #
    #         # Delete the path to free memory
    #         libtcod.path_delete(my_path)

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)


def get_blocking_entities_at_location(entities, destination_x, destination_y):
    # Check if Entity is "Blocking" at X, Y Location Specified

    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity

    return None