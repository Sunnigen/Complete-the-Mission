from random import randint

from level_generation.GenerationUtils import create_floor, create_hall, create_room, place_entities, place_stairs
from map_objects.Shapes import SquareRoom


class TunnelingAlgorithm:
    """

    - Tunnel from room to room, vertically or horizontally, to create a connected dungeon.
    - Will tunnel through any room regardless of entities or obstacles already generated.
    """
    def __init__(self):
        self.game_map = None
        self.dungeon_level = 0

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, item_table, mob_table):

        self.game_map = game_map
        self.dungeon_level = dungeon_level
        rooms = []
        num_rooms = 0

        for r in range(max_rooms):
            # Random Width and Height
            w = randint(room_min_size, room_max_size)
            h = randint(room_min_size, room_max_size)
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
                    player.x, player.y = new_room.center
                    create_floor(game_map, x, y)
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
        print("\nNumber of Rooms: %s" % len(game_map.rooms))
        center_of_last_room_x, center_of_last_room_y = rooms[num_rooms - 1].center
        entities.append(place_stairs(self.game_map.dungeon_level, center_of_last_room_x, center_of_last_room_y))
