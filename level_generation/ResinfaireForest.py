from random import choice, randint

from components.Encounter import Encounter
from components.AI import DefensiveMob, PatrolMob
from level_generation.CellularAutomata import CellularAutomata
from level_generation.GenerationUtils import place_tile, create_floor, generate_mob
from loader_functions.JsonReader import obtain_tile_set, obtain_prefabs, obtain_mob_table


MOBS = obtain_mob_table()


class ResinFaireForest(CellularAutomata):
    dungeon_level = 0
    game_map = None

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, item_table, mob_table, furniture_table):
        self.width = map_width - 1
        self.height = map_height - 1
        self.game_map = game_map
        self.dungeon_level = dungeon_level
        self.game_map.initialize_closed_map()

        self.generate()
        # self.print_grid('# ', '. ')

        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y] == 1:
                    place_tile(game_map, x, y, '13')
                elif self.grid[x][y] == 0:
                    create_floor(game_map, x, y)


        # for x, y in self.areas_of_interest:
        #     place_tile(self.game_map, x, y, '3')

        # Select Player Starting Area
        max_tries = 30
        tries = 0
        while tries < max_tries:
            rx, ry = randint(4, self.width-4), randint(4, self.height-4)
            if self.game_map.walkable[ry][rx]:
                player.x, player.y = rx, ry
                break

        # Spawn Groups of Entities
        self.ref_spawn_groups(entities)

        # Game Map
        game_map.rooms = self.areas_of_interest


    def ref_spawn_groups(self, entities):
        # Test function to spawn warring groups of factions

        """
        rebel_fighter
        rebel_squad_leader

        imperial_captain
        imperial_warrior
        imperial_knight
        """

        for area in self.areas_of_interest:
            center_x, center_y = area.center
            dice_roll = randint(1, 2)
            # ai_type = PatrolMob
            # ai_type = DefensiveMob
            ai_type = choice([DefensiveMob, PatrolMob])
            encounter = Encounter(area, len(self.game_map.encounters) + 1, ai_type)

            if dice_roll == 1:
                # Spawn "Imperial" Group
                faction = "Imperials"
                imperial_index = 'imperial_knight'
                imperial_stats = MOBS.get(imperial_index)
                if self.game_map.walkable[center_y][center_x]:
                    entities.append(generate_mob(center_x, center_y, imperial_stats, ai_type, encounter, faction, ai_type))
                else:
                    x, y = self.obtain_location(center_x, center_y, entities)
                    if x and y:
                        entities.append(generate_mob(x, y, imperial_stats, ai_type, encounter, faction, ai_type))

                imperial_index = 'imperial_warrior'
                imperial_stats = MOBS.get(imperial_index)
                for i in range(2):
                    x, y = self.obtain_location(center_x, center_y, entities)
                    if x and y:
                        entities.append(generate_mob(x, y, imperial_stats, ai_type, encounter, faction, ai_type))

            else:
                # Spawn "Rebel" Group
                faction = "Rebels"
                # rebel_index = 'imperial_knight'
                # rebel_stats = MOBS.get(rebel_index)
                # if self.game_map.walkable[center_y][center_x]:
                #     entities.append(generate_mob(center_x, center_y, rebel_stats, ai_type, encounter, faction))
                # else:
                #     x, y = self.obtain_location(center_x, center_y, entities)
                #     if x and y:
                #         entities.append(generate_mob(x, y, rebel_stats, ai_type, encounter, faction))

                rebel_index = 'rebel_fighter'
                rebel_stats = MOBS.get(rebel_index)
                for i in range(2):
                    x, y = self.obtain_location(center_x, center_y, entities)
                    if x and y:
                        entities.append(generate_mob(x, y, rebel_stats, ai_type, encounter, faction, ai_type))

    def obtain_location(self, center_x, center_y, entities):
        # Attempt to Find an Empty Space to Place Mob
        max_tries = 30
        tries = 0
        radius = 2
        while tries < max_tries:
            x = randint(center_x - radius, center_x + radius)
            y = randint(center_y - radius, center_y + radius)

            if not 0 <= x < self.width or not 0 <= y < self.height:
                tries += 1
                continue
            if self.game_map.walkable[y][x] and not any(
                    [entity for entity in entities if entity.x == x and entity.y == y]):
                # Position is good
                return x, y
            tries += 1
            x, y = None, None

        # Check if Suitable Position Has Been Found
        if not x or not y:
            return None, None