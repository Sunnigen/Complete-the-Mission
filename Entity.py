import math

import tcod as libtcod
from tcod.path import AStar

from components.AI import get_direction
from components.Item import Item
from ItemFunctions import *
from RenderFunctions import RenderOrder


class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """
    def __init__(self, x, y, char, color, name, json_index, blocks=False, render_order=RenderOrder.CORPSE, fighter=None,
                 ai=None, item=None, inventory=None, stairs=None, level=None, equipment=None, equippable=None,
                 fov_color=None, furniture=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.json_index = json_index
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
        self.map_object = furniture

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

        if self.map_object:
            self.map_object.owner = self

    def change_map_object(self, tile_data, json_index):
        print('change_map_object')
        if self.map_object:
            self.char = tile_data.get("char")
            self.name = tile_data.get("name")
            self.color = tile_data.get("color")
            self.json_index = json_index

            # Update Furniture Class
            self.map_object.update(tile_data)

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

    def move_astar(self, target_x, target_y, entities, game_map, fov_map):
        # Obtain Random Point within Room
        # TODO: Store astar path and update if only map/situation changes
        # print('\n\nmove_astar')

        astar = AStar(game_map.walkable.astype(int), 1.41)
        astar_path = astar.get_path(self.y, self.x, target_y, target_x)

        if astar_path:
            # print('path found')
            y, x = astar_path.pop(0)

            # Check if Entity in the way
            if not game_map.transparent[y][x]:
                # print('path found but an entity blocks the way')
                self.ai.stuck_time += 1
                return
            self.ai.direction_vector = get_direction(self.x, self.y, x, y)
            game_map.transparent[self.y][self.x] = True  # unblock previous position
            game_map.transparent[y][x] = False  # block new position# Update Position
            self.x = x
            self.y = y
            return astar_path

        # else:
        #     print('NO PATH FOUND!')
        #     print(self.y, self.x, target.y, target.x)
            # for row in game_map.walkable.astype(int):
            #     print(row)
        #     print('astar:\n', astar.get_path(self.y, self.x, target.y, target.x))

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def distance_to(self, other_x, other_y):
        dx = other_x - self.x
        dy = other_y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)


def get_blocking_entities_at_location(entities, destination_x, destination_y):
    # Check if Entity is "Blocking" at X, Y Location Specified
    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity

    return None


def get_blocking_object_at_location(map_objects, destination_x, destination_y):
    # Check if Object is "Blocking" at X, Y Location Specified
    for map_object in map_objects:
        if map_object.x == destination_x and map_object.y == destination_y:
            return map_object
    return None