from math import ceil
from random import choice, randint

import tcod

from components.AI import AI
from components.Encounter import Encounter
from level_generation.CellularAutomata import AreaofInterest
from level_generation.GenerationUtils import generate_mobs, generate_object, place_tile, create_floor, create_wall, generate_mob, place_prefab, place_stairs, place_entities
from RandomUtils import random_choice_from_dict, spawn_chance


class Arena:
    dungeon_level = 0
    game_map = None
    town_center = None
    width = 30
    height = 30
    areas_of_interest = []

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, particles, particle_systems, item_table, mob_table):
        self.game_map = game_map
        self.dungeon_level = dungeon_level
        self.width = map_width
        self.height = map_height
        self.assign_terrain()

        # Player/Stairs
        player.position.x, player.position.y = map_width//2, map_height - 1
        place_stairs(game_map, self.dungeon_level, map_width//2, map_height - 1)

        # Generate Mobs
        area_width = map_width//2
        area_height = map_height//5
        area_x = map_width//2 - area_width//2
        area_y = map_height // 4
        area = AreaofInterest(x=area_x , y=area_y, width=area_width, height=area_height)
        self.areas_of_interest.append(area)
        number_of_mobs = randint(5, 10)
        ai_type = AI
        encounter = Encounter(self.game_map, area, len(self.game_map.encounters) + 1, ai_type)
        monster_chances = {mob: spawn_chance([stats for stats in mob_stats.get('spawn_chance')], randint(1, 6))
                           for mob, mob_stats in mob_table.items()
                           }
        mob_list = generate_mobs(entities, game_map, number_of_mobs, mob_table, monster_chances, encounter, room=area)
        encounter.mob_list = mob_list

        self.game_map.encounters.append(encounter)
        self.game_map.rooms = self.areas_of_interest

    def assign_terrain(self):
        # Open floor to include a circular arena
        center_x, center_y = self.width//2, self.height//2
        radius = (self.width + self.height) // 4
        for x in range(self.width):
            for y in range(self.height):

                # Circular Arena
                if self.inside_circle(center_x, center_y, x, y, radius):
                    place_tile(self.game_map, x, y, "51")

    @staticmethod
    def inside_circle(center_x, center_y, point_x, point_y, radius):
        dx = center_x - point_x
        dy = center_y - point_y
        distance_squared = dx * dx + dy * dy
        return distance_squared <= radius * radius
