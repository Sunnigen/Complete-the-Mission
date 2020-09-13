from copy import deepcopy
from random import choice, choices, randint, shuffle
from math import sqrt

import numpy as np
import tcod

from components.AI import AI, DefensiveAI, PatrolAI
from components.Encounter import Encounter
from level_generation.CellularAutomata import AreaofInterest, CellularAutomata
from level_generation.GenerationUtils import generate_mobs, generate_object, place_tile, create_floor, create_wall, generate_mob, place_prefab, place_stairs, place_entities
from level_generation.Prefab import Prefab
from loader_functions.JsonReader import obtain_tile_set, obtain_prefabs, obtain_mob_table
from RandomUtils import spawn_chance

TILESET = obtain_tile_set()
MOBS = obtain_mob_table("resinfaire_mobs")
PREFABS = obtain_prefabs()


class ResinFaireForest(CellularAutomata):
    dungeon_level = 0
    game_map = None
    town_center = None

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, particles, particle_systems, item_table, mob_table):
        self.game_map = game_map
        self.dungeon_level = dungeon_level
        self.width = map_width
        self.height = map_height

        mold = False
        castle_entrance = False
        if dungeon_level == 1:
            # Cellular Automata Properties
            self.wall_chance = 40
            self.min_count = 5
            self.iterations = 1
            self.pillar_iterations = 1
            self.flood_tries = 5
            self.goal_percentage = 30  # above 30% seems to be a good target
            self.encounter_spread_factor = 3
            self.sparse_wall_density = 10

            # Specific Dungeon Level Variables
            mold = False
            town = False


        elif dungeon_level == 2:
            # Cellular Automata Properties
            self.wall_chance = 40
            self.min_count = 5
            self.iterations = 2
            self.pillar_iterations = 1
            self.flood_tries = 5
            self.goal_percentage = 30  # above 30% seems to be a good target
            self.encounter_spread_factor = 5
            self.sparse_wall_density = 2
            # Specific Dungeon Level Variables
            mold = True
            town = False
        elif dungeon_level == 3:
            # Cellular Automata Properties
            self.wall_chance = 40
            self.min_count = 5
            self.iterations = 2
            self.pillar_iterations = 1
            self.flood_tries = 5
            self.goal_percentage = 30  # above 30% seems to be a good target
            self.encounter_spread_factor = 5
            self.sparse_wall_density = 50
            # Specific Dungeon Level Variables
            mold = True
            town = True
            castle_entrance = True
        else:

            # Cellular Automata Properties
            self.wall_chance = 40
            self.min_count = 5
            self.iterations = 1
            self.pillar_iterations = 1
            self.flood_tries = 5
            self.goal_percentage = 30  # above 30% seems to be a good target
            self.encounter_spread_factor = 10
            self.sparse_wall_density = 10
            # Specific Dungeon Level Variables
            mold = True
            town = choice([False, True])


        # Terrain Generation
        self.generate(castle_entrance)
        self.assign_tiles(mold=mold)
        # Terrain/Prefabs
        # self.generate_lake()
        if town:
            self.generate_town(room_min_size, room_max_size, entities, particles)
            self.generate_roads()
            self.generate_castle_entrance()

            # place_tile(self.game_map, x,  y+h, "46")

            x1 = self.end_area.x
            y1 = self.end_area.y + self.end_area.height

            x2, y2 = self.town_center.x, self.town_center.y-3

            self.generate_road(x1,y1,x2,y2,True)
        else:
            self.generate_roads()
        # self.generate_rivers()
        # self.generate_monster_nests()
        # self.generate_bases()


        # Area of Interest Locations
        # for area in self.areas_of_interest:
        #     place_tile(self.game_map, area.x, area.y, '3')

        # Select Player Starting Area
        # player.position.x, player.position.y = self.end_area.x, self.end_area.y
        player.position.x, player.position.y = self.start_area.x, self.start_area.y
        # max_tries = 30
        # tries = 0
        # while tries < max_tries:
        #     rx, ry = randint(4, self.width-4), randint(4, self.height-4)
        #     if self.game_map.walkable[ry][rx]:
        #         player.position.x, player.position.y = rx, ry
        #         self.game_map.tile_cost[ry][rx] = 99
        #         break

        # player.position.x, player.position.y = 10, 6

        # Spawn Groups of Entities
        # for area in self.areas_of_interest:
        #     self.generate_outpost(area, entities, particles)

        # self.ref_spawn_groups(entities)
        areas = deepcopy(self.areas_of_interest)
        for area in areas:
            place_entities(self.game_map, self.dungeon_level, area, entities, item_table, mob_table)

        # Game Map
        self.game_map = game_map
        self.dungeon_level = dungeon_level
        game_map.rooms = self.areas_of_interest
        place_stairs(game_map, self.dungeon_level, self.end_area.x, self.end_area.y + 2)

    def assign_tiles(self, mold=False):
        # Assign Tiles from Grid
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y] == 1:
                    if randint(0, 6) == 1 and mold:
                        place_tile(self.game_map, x, y, '46')  # normal tree
                    else:
                        place_tile(self.game_map, x, y, '13')  # moldfy tree

                elif self.grid[x][y] == 0:
                    if randint(0, 4) == 1:
                        place_tile(self.game_map, x, y, '44')  # normal grass
                    elif randint(0, 6) == 1 and mold:
                        place_tile(self.game_map, x, y, '45')  # fungus grass
                    else:
                        create_floor(self.game_map, x, y)

                # elif self.grid[x][y] == 2:  # river
                #     place_tile(self.game_map, x, y, '37')

                # elif self.grid[x][y] == 0:
                #     create_floor(game_map, x, y)

    def generate_castle_entrance(self):
        x = self.end_area.x
        y = self.end_area.y
        w = self.end_area.width
        h = self.end_area.height
        self.create_walled_room(x - w//2, y, w, h, False)
        for _y in range(y+1, y+w-1):
            place_tile(self.game_map, _y+(x - w//2), 0, "47")

        for i in range(1 + x - w//2, x+w//2):
            place_tile(self.game_map, i, y+h-1, "35")
        create_floor(self.game_map, x, y+h-1)

        for i in range(1 + x - w//2, x+w//2):
            create_floor(self.game_map, i, y+h)


        # place_tile(self.game_map, x,  y+h, "46")


    def generate_town(self, room_min_size, room_max_size, entities, particles):
        bsp_x = 10
        bsp_y = 15
        bsp_width = 40
        bsp_height = 30

        room_min_size = 5
        room_max_size = 9
        town_center_pos = (bsp_width//2 + bsp_x,  bsp_height//2 + bsp_y)

        bsp = tcod.bsp.BSP(x=bsp_x, y=bsp_y, width=bsp_width, height=bsp_height)
        bsp.split_recursive(
            depth=4,
            min_width=6,
            min_height=6,
            max_horizontal_ratio=1.5,
            max_vertical_ratio=1.5,
        )

        # Pre-process through Nodes to Assign Specific Buildings
        buildings = []
        for node in bsp.pre_order():
            if node.children:
                node1, node2 = node.children
                # print('Connect the rooms:\n%s\n%s' % (node1, node2))
            else:

                # w = randint(bsp_tree.room_min_size, min(bsp_tree.room_max_size, self.width - 1))
                # h = randint(bsp_tree.room_min_size, min(bsp_tree.room_max_size, self.height - 1))
                # x = randint(self.x, self.x + (self.width - 1) - w)
                # y = randint(self.y, self.y + (self.height - 1) - h)

                # print(room_min_size, min(room_max_size, node.width - 1))
                # print(room_min_size, min(room_max_size, node.height - 1))
                w = randint(room_min_size, min(room_max_size, node.width - 1))
                h = randint(room_min_size, min(room_max_size, node.height - 1))
                x = randint(node.x, node.x + (node.width - 1) - w)
                y = randint(node.y, node.y + (node.height - 1) - h)
                buildings.append((x, y, w, h))

        # Find Closest to Center
        # print('center:', (bsp_width//2) + bsp_x, (bsp_height//2) + bsp_y)
        # (2) Sorts, for x then for y
        buildings = sorted(buildings, key=lambda attribute: (distance(attribute[0] + (attribute[2]//2),
                                                                      attribute[1] + (attribute[3]//2),
                                                                      (bsp_width//2) + bsp_x,
                                                                      (bsp_height//2) + bsp_y)))

        t = buildings[0]
        # print('buildings:', buildings)
        # print("Towncenter:", t)

        town_center_area = AreaofInterest(*t)
        self.town_center = town_center_area
        self.areas_of_interest.append(town_center_area)
        town_center_prefab = PREFABS.get("town_center")
        p = Prefab()
        p.load_template(town_center_prefab)
        p.x, p.y = t[0], t[1]
        buildings.remove(t)

        for x, y, w, h in buildings:
            ruined = choice([False, True])
            self.clear_floor(x, y, w, h)
            self.create_walled_room(x, y, w, h, ruined)

            # Place Map Objects
            self.populate_building(x+1, y+1, w-2, h-2, entities, particles)
            door_x, door_y = self.generate_door(x, y, w, h, entities, particles)
            self.generate_road(door_x, door_y, town_center_area.x + 2, town_center_area.y + 2)

            if ruined:
                self.areas_of_interest.append(AreaofInterest(x, y, w, h))
                    # print('Dig a room for %s.' % node)

        # place_tile(self.game_map, bsp_width//2 + bsp_x,  bsp_height//2 + bsp_y, "46")

        # Place Town Center
        place_prefab(self.game_map, p, entities, particles, self.dungeon_level)

        # Road from Town Center to Castle Gates


    def center(self):
        center_x = int((self.x + self.x + self.width) / 2)
        center_y = int((self.y + self.y + self.height) / 2)
        return center_x, center_y

    def generate_door(self, x, y, w, h, entities, particles):
        # Door
        poss_locations = []

        # Top
        poss_locations.extend((i, y) for i in range(x + 1, x + w - 1))
        # # Bottom
        poss_locations.extend((i, y + h - 1) for i in range(x + 1, x + w - 1))
        # # Left
        poss_locations.extend((x, j) for j in range(y + 1, y + h - 1))
        # # Right
        poss_locations.extend((x + w - 1, j) for j in range(y + 1, y + h - 1))

        # print('poss_locations:', poss_locations)
        # Two Doors
        shuffle(poss_locations)
        if randint(0, 4) == 1:
            door_x, door_y = poss_locations.pop()
            # print('door:', door_x, door_y)
            create_floor(self.game_map, door_x, door_y)
            door_index = "5"
            door_stats = TILESET.get(door_index)
            generate_object(door_x, door_y, entities, self.game_map.map_objects, particles, self.game_map, door_stats,
                            door_index, item_list=None)

        door_x, door_y = poss_locations.pop()
        # print('door:', door_x, door_y)
        create_floor(self.game_map, door_x, door_y)
        door_index = "5"
        door_stats = TILESET.get(door_index)
        generate_object(door_x, door_y, entities, self.game_map.map_objects, particles, self.game_map, door_stats,
                        door_index, item_list=None)

        return door_x, door_y

    def populate_building(self, x, y, w, h, entities, particles):
        # Place Prefabs for Building
        chest = choices(population=[PREFABS.get("open_chest"), PREFABS.get("closed_chest")], weights=[50, 50], k=1)[0]
        prefab_list = [chest]
        for prefab in prefab_list:
            p = Prefab()
            p.load_template(prefab)
            tries = 0
            max_tries = 20
            while tries < max_tries:
                random_x = randint(x, x + w - p.width)
                random_y = randint(y, y + h - p.height)

                if self.grid[random_x][random_y] == 0 and self.game_map.walkable[random_y][random_x]:
                    p.x, p.y = random_x, random_y
                    place_prefab(self.game_map, p, entities, particles, self.dungeon_level)
                    tries = max_tries
                tries += 1





    def clear_floor(self, x, y, w, h):
        for room_x in range(x - 1, x + w + 1):
            for room_y in range(y - 1, y + h + 1):
                try:
                    create_floor(self.game_map, room_x, room_y)
                except:
                    pass

    def create_walled_room(self, room_x, room_y, room_width, room_height, ruined=True):
        # Sets Tiles in to Become Passable, but add walls around
        for x in range(room_x, room_x + room_width):
            for y in range(room_y, room_y + room_height):
                if x == room_x or \
                        x == room_x + room_width - 1 or \
                        y == room_y or \
                        y == room_y + room_height - 1:

                    if ruined:
                        if randint(0, 100) < 80:
                            create_wall(self.game_map, x, y)
                    else:
                        create_wall(self.game_map, x, y)
                else:
                    if ruined and randint(0, 100) < 25:
                        create_floor(self.game_map, x, y)
                    else:
                        place_tile(self.game_map, x, y, "47")
                    # create_floor(self.game_map, x, y)


    def generate_rivers(self):
        # print('generate_rivers')
        # print(self.game_map.tile_cost)
        number_of_rivers = randint(0, 1 + ((self.width+self.height) // (2 * 30)))
        # number_of_rivers = randint(1, 3)
        for i in range(number_of_rivers):
            river_width = randint(1, 3)

            # Cache River Starting Points
            direction = [[(0, randint(0, self.width - 1)), (self.height - 1, randint(0, self.width - 1))],
                         [(randint(0, self.height - 1), 0), (randint(0, self.height - 1), self.width - 1)]]
            river_points = choice(direction)
            shuffle(river_points)
            start_x, start_y = river_points.pop()
            end_x, end_y = river_points.pop()

            # AStar Pathfind Around Obstacles to End of Area
            astar = tcod.path.AStar(self.game_map.tile_cost, 1.41)
            river_path = astar.get_path(start_x, start_y, end_x, end_y)
            river_path.extend([(start_x, start_y), (end_x, end_y)])  # Add Start and End points

            # Generate River According to Width
            # print('river_path:', river_path)
            for x, y in river_path:
                direction = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1), (x, y)]
                for c_x, c_y in direction:
                    # TODO: Find a better way to adjust for width than this "try" statement
                    try:
                        1 // (abs(c_y + 1) + c_y + 1)
                        1 // (abs(c_x + 1) + c_x + 1)
                        # self.grid[c_y][c_x] = 2
                        place_tile(self.game_map, c_y, c_x, '37')
                    except:
                        pass

    def generate_road(self, x1,y1,x2,y2, wide=False):
        # Connect Roads between (2) Areas
        astar = tcod.path.AStar(self.game_map.tile_cost, 5)

        path = astar.get_path(y1, x1, y2, x2)
        for x, y in path:
            if self.game_map.tileset_tiles[y][x] == 2:

                if wide:
                    place_tile(self.game_map, y, x, '12')
                    place_tile(self.game_map, y+1, x, '12')
                    place_tile(self.game_map, y-1, x, '12')



    def generate_roads(self):
        # print('generate_roads')

        # Connect Start and End
        astar = tcod.path.AStar(self.game_map.tile_cost, 1.41)
        path = astar.get_path(self.start_area.center[1], self.start_area.center[0], self.end_area.center[1], self.end_area.center[0])
        for x, y in path:
            if randint(1, 4) == 1:
                place_tile(self.game_map, y, x, '12')

        # Connect All Areas of Interest
        prev_y, prev_x = self.areas_of_interest[0].center
        for area in self.areas_of_interest[1:]:
            center_y, center_x = area.center

            astar = tcod.path.AStar(self.game_map.tile_cost, 1.41)
            path = astar.get_path(prev_x, prev_y, center_x, center_y)
            # print('\n\nstart:', prev_x, prev_y)
            # print('end:', center_x, center_y)
            # print('path:', path)


            for c_x, c_y in path:
                if self.game_map.tileset_tiles[c_x][c_y] == 37: # River Tile
                    #TODO: Extend size of bridge to be (3) tiles wide
                    place_tile(self.game_map, c_y, c_x, '12')

            prev_x, prev_y = center_x, center_y

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

    def generate_outpost(self, area, entities, particles):
        if randint(1, 5) == 1:
            center_x, center_y = area.x, area.y
            faction = "Rebels"

            width = 5
            height = 5
            prefab = PREFABS.get('output_test')
            p = Prefab()
            p.load_template(prefab)
            p.x = center_x - (width // 2)
            p.y = center_y - (height // 2)
            place_prefab(self.game_map, p, entities, particles, self.dungeon_level)
            x, y = self.obtain_location(area, entities)

            if x and y:
                chest_index = "10"
                chest_stats = TILESET.get(chest_index)
                generate_object(x, y, entities, self.game_map.map_objects, particles, self.game_map, chest_stats,
                                chest_index, item_list=None, no_inventory=False)
        # else:
        #     faction = 'Imperials'

            self.spawn_encounter(area, entities, particles, faction)

        # for x in range(center_x - (width // 2)):
        #     for y in range(center_y - (height // 2)):

    def spawn_encounter(self, area, entities, particles, faction='Mindless'):
        if faction == 'Rebels':
            mob_index = 'rebel_fighter'
        elif faction == 'Imperials':
            mob_index = 'imperial_knight'

        mob_stats = MOBS.get(mob_index)
        # ai_type = DefensiveAI
        ai_type = AI
        # ai_type = choice([DefensiveAI, PatrolAI])
        encounter = Encounter(self.game_map, area, len(self.game_map.encounters) + 1, ai_type)
        for i in range(2):
            x, y = self.obtain_location(area, entities)
            if x and y:
                mob = generate_mob(x, y, mob_stats, mob_index, encounter, faction, ai_type, entities)
                entities.append(mob)
                encounter.mob_list.append(mob)

        self.game_map.encounters.append(encounter)

    def obtain_location(self, area, entities):
        # Attempt to Find an Empty Space to Place Mob
        center_x, center_y = area.x, area.y
        max_tries = 30
        tries = 0
        radius = (area.width + area.height - 1) // 2
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

def distance(x1, y1, x2, y2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
