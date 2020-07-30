from random import randint

from level_generation.GenerationUtils import create_floor, create_room, place_entities, place_stairs, generate_object
from map_objects.Shapes import SquareRoom


class TunnelingAlgorithm:
    """

    - Tunnel from room to room, vertically or horizontally, to create a connected dungeon.
    - Will tunnel through any room regardless of entities or obstacles already generated.
    """
    game_map = None
    dungeon_level = 0
    room_min_size = 6
    room_max_size = 30

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, particles, particle_systems, item_table, mob_table):

        self.game_map = game_map
        self.dungeon_level = dungeon_level
        self.room_max_size = min(map_height // 5, map_width // 5)
        self.room_min_size = min(map_height // 7, map_width // 7)
        rooms = []
        num_rooms = 0

        for r in range(max_rooms):
            # Random Width and Height
            w = randint(self.room_min_size, self.room_max_size)
            h = randint(self.room_min_size, self.room_max_size)
            # Random Position without going out of the boundaries of the map
            x = randint(0, map_width - w - 1)
            y = randint(0, map_height - h - 1)

            # "Rect" class makes rectangles easier to work with
            new_room = SquareRoom(x, y, w, h, len(game_map.rooms) + 1)

            # Check if Room Intersects with Existing Rooms
            for other_room in rooms:
                if new_room.intersect(other_room):
                    break

            else:
                # No Intersections, so this room is Valid
                # "Paint" it to the map's tiles
                create_room(game_map, new_room)

                if num_rooms == 0:
                    # 1st Room, Set Player to Start Here
                    player.position.x, player.position.y = new_room.center
                    game_map.tile_cost[player.position.y][player.position.x] = 99
                else:
                    # Connect Every Room after 1st Room to Previous Room With Tunnel
                    # Create connection between previous room and new room
                    previous_map = rooms[num_rooms - 1]
                    create_hall(game_map, previous_map, new_room)

                # Determine Monster Placement and Population
                place_entities(game_map, dungeon_level, new_room, entities, item_table, mob_table)

                # finally, append the new room to the list
                rooms.append(new_room)
                game_map.rooms.append(new_room)

                num_rooms += 1

        # Add End-of-Level Stairs
        last_room_x, last_room_y = rooms[num_rooms - 1].center
        place_stairs(self.game_map, self.dungeon_level, last_room_x, last_room_y)


def create_h_tunnel(game_map, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        create_floor(game_map, x, y)


def create_v_tunnel(game_map, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        create_floor(game_map, x, y)


def create_hall(game_map, room1, room2):
    x1, y1 = room1.center
    x2, y2 = room2.center

    if randint(0, 1) == 1:
        create_h_tunnel(game_map, x1, x2, y1)
        create_v_tunnel(game_map, y1, y2, x2)
    else:  # else it starts vertically
        create_v_tunnel(game_map, y1, y2, x1)
        create_h_tunnel(game_map, x1, x2, y2)


# if __name__ == '__main__':
#     TunnelingAlgorithm