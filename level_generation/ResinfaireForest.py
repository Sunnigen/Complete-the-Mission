from level_generation.CellularAutomata import CellularAutomata
from level_generation.GenerationUtils import place_tile, create_floor


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


        for x, y in self.areas_of_interest:
            place_tile(self.game_map, x, y, '12')



        game_map.player.x = self.width // 2
        game_map.player.y = self.height // 2
