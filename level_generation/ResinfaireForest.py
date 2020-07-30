from random import choice, randint, shuffle

import numpy as np
import tcod

from components.Encounter import Encounter
from components.AI import DefensiveAI, PatrolAI
from level_generation.CellularAutomata import CellularAutomata
from level_generation.GenerationUtils import place_tile, create_floor, generate_mob, place_stairs
from loader_functions.JsonReader import obtain_tile_set, obtain_prefabs, obtain_mob_table


MOBS = obtain_mob_table()


class ResinFaireForest(CellularAutomata):
    dungeon_level = 0
    game_map = None

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, particles, particle_systems, item_table, mob_table):
        self.width = randint(30, map_width - 1)
        self.height = randint(30, map_height - 1)
        # self.width = 50
        # self.height = 50
        self.game_map = game_map
        self.dungeon_level = dungeon_level

        # Cellular Automata Properties
        self.wall_chance = 35
        self.min_count = 5
        self.iterations = 1
        self.pillar_iterations = 2
        self.flood_tries = 5
        self.goal_percentage = 30  # above 30% seems to be a good target
        self.encounter_spread_factor = 2
        self.sparse_wall_density = 10

        self.generate()
        # self.print_grid('# ', '. ')

        # Terrain/Prefabs
        # self.generate_lake()
        # self.generate_rivers()
        # self.generate_monster_nests()
        # self.generate_bases()

        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y] == 1:
                    place_tile(game_map, x, y, '13')
                elif self.grid[x][y] == 0:
                    create_floor(game_map, x, y)
                # elif self.grid[x][y] == 0:
                #     create_floor(game_map, x, y)

        self.generate_rivers()

        # Area of Interest Locations
        for area in self.areas_of_interest:
            place_tile(self.game_map, area.x, area.y, '3')

        # Select Player Starting Area
        max_tries = 30
        tries = 0
        while tries < max_tries:
            rx, ry = randint(4, self.width-4), randint(4, self.height-4)
            if self.game_map.walkable[ry][rx]:
                player.position.x, player.position.y = rx, ry
                self.game_map.tile_cost[ry][rx] = 99
                break

        # player.position.x, player.position.y = 10, 6

        # Spawn Groups of Entities
        for area in self.areas_of_interest:
            if randint(1, 4) == 1:
                self.generate_outpost(area, entities)

        # self.ref_spawn_groups(entities)

        # Game Map
        game_map.rooms = self.areas_of_interest
        last_room_x, last_room_y = self.areas_of_interest[-1].center
        place_stairs(game_map, self.dungeon_level, last_room_x, last_room_y)

    def generate_rivers(self):
        # print('generate_rivers')
        # print(self.game_map.tile_cost)
        number_of_rivers = randint(1, 3)
        for i in range(number_of_rivers):
            river_width = randint(1, 3)

            # Cache River Starting Points
            direction = [[(0, randint(0, self.width - 1)), (self.height - 1, randint(0, self.width - 1))],
                         [(randint(0, self.height - 1), 0), (randint(0, self.height - 1), self.width - 1)]
                         ]
            river_points = choice(direction)
            shuffle(river_points)
            start_x, start_y = river_points.pop()
            end_x, end_y = river_points.pop()

            # AStar Pathfind Around Obstacles to End of Area
            astar = tcod.path.AStar(self.game_map.tile_cost, 1.41)
            river_path = astar.get_path(start_x, start_y, end_x, end_y)
            river_path.extend([(start_x, start_y), (end_x, end_y)])  # Add Start and End points

            # Generate River According to Width
            for x, y in river_path:
                direction = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1), (x, y)]
                for c_x, c_y in direction:
                    # TODO: Find a better way to adjust for width than this "try" statement
                    try:
                        place_tile(self.game_map, c_y, c_x, '37')
                    except:
                        pass


    def generate_lake(self):
        noise = tcod.noise.Noise(
            dimensions=2,
            algorithm=tcod.NOISE_SIMPLEX,
            implementation=tcod.noise.TURBULENCE,
            hurst=0.5,
            lacunarity=2.0,
            octaves=4,
            seed=None,
        )

        # Create a 5x5 open multi-dimensional mesh-grid.
        ogrid = [np.arange(self.width, dtype=np.float32),
                 np.arange(self.height, dtype=np.float32)]

        # Scale the grid.
        scale = 1 / ((self.width + self.height) / 2)
        ogrid[0] *= scale
        ogrid[1] *= scale

        # Return the sampled noise from this grid of points.
        samples = noise.sample_ogrid(ogrid)
        # print(samples)

        for i in range(self.width):
            for j in range(self.height):
                if samples[i][j] > 0.975:
                    self.grid[i][j] = 3


    def ref_spawn_groups(self, entities):
        # Test function to spawn warring groups of factions

        """
        rebel_fighter
        rebel_squad_leader
A
        imperial_captain
        imperial_warrior
        imperial_knight
        """

        for area in self.areas_of_interest:
            center_x, center_y = area.center
            dice_roll = randint(1, 2)
            # ai_type = PatrolAI
            # ai_type = DefensiveAI
            # ai_type = PatrolAI
            ai_type = choice([DefensiveAI, PatrolAI])
            encounter = Encounter(self.game_map, area, len(self.game_map.encounters) + 1, ai_type)
            # dice_roll = 1
            if dice_roll == 1:
                # Spawn "Imperial" Group
                faction = "Imperials"
                imperial_index = 'imperial_knight'
                imperial_stats = MOBS.get(imperial_index)
                if self.game_map.walkable[center_y][center_x]:
                    entities.append(generate_mob(center_x, center_y, imperial_stats, imperial_index, encounter, faction, ai_type, entities))
                else:
                    x, y = self.obtain_location(area, entities)
                    if x and y:
                        mob = generate_mob(x, y, imperial_stats, imperial_index, encounter, faction, ai_type, entities)
                        entities.append(mob)
                        encounter.mob_list.append(mob)

                imperial_index = 'imperial_warrior'
                imperial_stats = MOBS.get(imperial_index)
                for i in range(2):
                    x, y = self.obtain_location(area, entities)
                    if x and y:
                        mob = generate_mob(x, y, imperial_stats, imperial_index, encounter, faction, ai_type, entities)
                        entities.append(mob)
                        encounter.mob_list.append(mob)

            else:
            # elif dice_roll == 2:
                # Spawn "Rebel" Group
                faction = "Rebels"

                rebel_index = 'rebel_fighter'
                rebel_stats = MOBS.get(rebel_index)
                for i in range(2):
                    x, y = self.obtain_location(area, entities)
                    if x and y:
                        mob = generate_mob(x, y, rebel_stats, rebel_index, encounter, faction, ai_type, entities)
                        entities.append(mob)
                        encounter.mob_list.append(mob)

            self.game_map.encounters.append(encounter)

    def generate_outpost(self, area, entities):
        if randint(1, 2) == 1:
            center_x, center_y = area.x, area.y
            faction = "Rebels"


    def obtain_location(self, area, entities):
        # Attempt to Find an Empty Space to Place Mob
        center_x, center_y = area.x, area.y
        max_tries = 30
        tries = 0
        radius = (area.width + area.height) // 2
        # _entities = [entity for entity in entities if entity.position]
        x, y = None, None
        while tries < max_tries:
            x = randint(center_x - radius, center_x + radius)
            y = randint(center_y - radius, center_y + radius)

            if not 0 <= x < self.width or not 0 <= y < self.height:
                tries += 1
                continue
            if self.game_map.walkable[y][x] and not any(
                    [entity for entity in entities if entity.position.x == x and entity.position.y == y]):
                # Position is good
                # print('# Position is good')
                return (x, y)
            tries += 1
            x, y = None, None

        # Could not find a suitable location
        print('could not find a suitable location!')
        return x, y