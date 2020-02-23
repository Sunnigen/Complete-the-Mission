from random import choice, randint


import tcod as libtcod


from GameMessages import Message


# DIRECTIONS = {
#     'east': [(1, -1)],
#     'north': [(0, 1)],
#     'south': [(0, -1)],
#     'west': [(-1, 0)],
#
#     'south west': [(-1, -1)],
#     'south east': [(1, -1)],
#
#     'north west': [(-1, 1)],
#     'north east': [(1, 1)]
# }

DIRECTIONS = {
    'east': [(1, -1), (1, 1), (1, 0)],
    'north': [(0, 1), (-1, 1), (1, 1)],
    'south': [(0, -1), (-1, -1), (1, -1)],
    'west': [(-1, 0), (-1, 1), (-1, -1)],

    'south west': [(-1, 0), (-1, -1), (0, -1)],
    'south east': [(1, 0), (1, -1), (0, -1)],

    'north west': [(-1, 0), (-1, 1), (0, 1)],
    'north east': [(1, 0), (1, 1), (0, 1)]

}


class BasicMonster:
    def __init__(self, *args, **kwargs):
        pass

    def take_turn(self, target, fov_map, game_map, entities, radius):
        results = []
        monster = self.owner

        # TODO: Python 2D array to numpy array is reversed.
        if fov_map[target.y][target.x]:

            if radius >= monster.distance_to(target) >= 2:
                # monster.move_towards(target.x, target.y, game_map, entities)
                monster.move_astar(target, entities, game_map, fov_map)

            elif target.fighter.hp > 0 and monster.distance_to(target) <= 2:
                # print('The {0} insults you! Your ego is damaged!'.format(monster.name))
                # monster.fighter.attack(target)
                attack_results = monster.fighter.attack(target)
                results.extend(attack_results)

        return results


class PatrolMonster:
    """
    PatrolMonster will move between previous room, main room and next room
    """

    def __init__(self, encounter_group):
        self.encounter_group = encounter_group
        self.destination_room = encounter_group.main_room
        self.wait_time_max = 7  # time waiting at objective
        self.wait_time = 0
        self.stuck_time_max = 2  # time waiting stuck, though path exists
        self.stuck_time = 0
        self.direction_vector = self.get_random_direction()

    @staticmethod
    def get_random_direction():
        return DIRECTIONS.get(choice(list(DIRECTIONS.keys())))

    def take_turn(self, target, fov_map, game_map, entities, radius):
        results = []
        monster = self.owner

        # Seek/Attack Player if in Range, otherwise Patrol to other Rooms
        # TODO: Python 2D array to numpy array is reversed.
        # if fov_map[target.y][target.x]:
        #
        #     # Close distance to Player
        #     if radius+1 >= monster.distance_to(target) >= 2:
        #         monster.move_astar(target, entities, game_map, fov_map)
        #
        #     # Player is Within Range, Attack
        #     elif target.fighter.hp > 0 and monster.distance_to(target) <= 2:
        #         attack_results = monster.fighter.attack(target)
        #         results.extend(attack_results)
        # else:
            # Obtain coordinate to next room and move there

        self.patrol(game_map.rooms)
        # TODO: Reduce astar calculation frequency. Only use astar if stuck, map changes, objective changes, etc.
        monster.move_astar(self.destination_room, entities, game_map, fov_map)
        return results

    def check_if_at_destination(self):
        # Check if Patrol Monster has Reached Center Coordinate of Destination Room
        if self.owner.distance_to(self.destination_room) <= 2:
            return True
        # print('patroling to room #%s' % self.destination_room.room_number)
        return False

    def check_if_stuck(self):
        if self.stuck_time < self.stuck_time_max:
            return False
        # print('I\'m definitely stuck. Changing destination')
        return True

    def check_if_waiting(self):
        # Wait in Destination Room before Traveling Onward
        if self.wait_time < self.wait_time_max:
            self.wait_time += 1
            self.stuck_time = 0  # reset because no longer stuck
            d = randint(0, 1)
            if d == 1:
                self.direction_vector = self.get_random_direction()
            return False
        return True

    def patrol(self, game_map_rooms):
        """
        Check:
        - If destination reached and wait time at destination exceeded
        - If stuck for more than stuck_time_max amount of time and destination not reached
        """
        if self.check_if_at_destination():
            if self.check_if_waiting():
                self.change_room_number(game_map_rooms)
                return None
            # print('I am waiting, wait time %s so far.' % self.wait_time)
            return None

        if self.check_if_stuck() and not self.check_if_at_destination():
            self.change_room_number(game_map_rooms)
            return None

    def change_room_number(self, game_map_rooms):
        # TODO: Select high-value or random coordinate in the room rather than center.
        #  self.destination_room.high_value_coordinate/random coordinate weighted toward center.
        self.stuck_time = 0
        self.wait_time = 0
        room_number = self.destination_room.room_number
        if room_number >= len(game_map_rooms):
            room_number = 0
        self.destination_room = game_map_rooms[room_number]
        # print('new room #%s' % self.destination_room.room_number)


class ConfusedMonster:
    def __init__(self, previous_ai, duration=10):
        self.previous_ai = previous_ai
        self.duration = duration

    def take_turn(self, target, fov_map, game_map, entities, radius):
        results = []

        # Confused Monster AI
        if self.duration > 0:
            random_x = self.owner.x + randint(0, 2) - 1
            random_y = self.owner.y + randint(0, 2) - 1

            if random_x != self.owner.x and random_y != self.owner.y:
                self.owner.move_towards(random_x, random_y, game_map, entities)

            self.duration -= 1
        else:
            # Confusion Wore Off
            self.owner.ai = self.previous_ai
            results.append({'message': Message('The %s is no longer confused!' % self.owner.name, libtcod.red)})

        return results
