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


def get_random_direction():
    return DIRECTIONS.get(choice(list(DIRECTIONS.keys())))


def get_next_direction():
    return DIRECTIONS.get(choice(list(DIRECTIONS.keys())))


def get_direction(x1, y1, x2, y2):
    # Calculate New Direction
    direction = None
    if y2 > y1:
        direction = 'north'
    elif y2 < y1:
        direction = 'south'
    if x2 > x1:
        direction = 'east'
    elif x2 < x1:
        direction = 'west'

    if x2 > x1 and y2 > y1:
        direction = 'north east'
    elif x2 < x1 and y2 < y1:
        direction = 'south west'
    elif x2 > x1 and y2 < y1:
        direction = 'south east'
    elif x2 < x1 and y2 > y1:
        direction = 'north west'

    if not direction:
        print('could not find direction!')
        print(x1, x2, y2, y2)
        direction = get_random_direction()
    return DIRECTIONS.get(direction)


class Mob:
    def __init__(self, encounter=None, *args, **kwargs):
        self.direction_vector = get_random_direction()
        self.stuck_time_max = 2  # time waiting stuck, though path exists
        self.stuck_time = 0
        self.encounter = encounter
        self.wait_time_max = randint(4, 10)  # time waiting at objective
        self.wait_time = 0
        self.path = []
        if encounter:
            self.destination_room = encounter.main_room


class BasicMob(Mob):

    def take_turn(self, target, fov_map, game_map, entities, radius):
        results = []
        monster = self.owner

        # TODO: Python 2D array to numpy array is reversed.
        dist = monster.distance_to(target)
        # if fov_map[target.y][target.x] and radius >= dist:
        #
        #     if radius >= dist >= 2:
        #
        #         # monster.move_towards(target.x, target.y, game_map, entities)
        #         monster.move_astar(target.x, target.y, entities, game_map, fov_map)
        #
        #     elif target.fighter.hp > 0 and monster.distance_to(target) <= 2:
        #         # print('The {0} insults you! Your ego is damaged!'.format(monster.name))
        #         # monster.fighter.attack(target)
        #         attack_results = monster.fighter.attack(target)
        #         results.extend(attack_results)
        #
        #     # Change Direction to Face Target
        #     self.direction_vector = get_direction(self.owner.x, self.owner.y, target.x, target.y)
        # else:
        d = randint(0, 4)
        if d == 1:
            self.direction_vector = get_random_direction()
        return results


class DefensiveMob(Mob):
    """
    DefensiveMob will chase, but return to main room
    """

    def __init__(self, **kwargs):
        self.origin_x = kwargs.get('origin_x')
        self.origin_y = kwargs.get('origin_y')
        super(DefensiveMob, self).__init__(**kwargs)

    def take_turn(self, target, fov_map, game_map, entities, radius):
        results = []
        monster = self.owner

        # TODO: Python 2D array to numpy array is reversed.
        dist = monster.distance_to(target)
        if fov_map[target.y][target.x] and radius >= dist:

            if radius >= dist >= 2:

                # monster.move_towards(target.x, target.y, game_map, entities)
                monster.move_astar(target.x, target.y, entities, game_map, fov_map)

            elif target.fighter.hp > 0 and monster.distance_to(target) <= 2:
                # print('The {0} insults you! Your ego is damaged!'.format(monster.name))
                # monster.fighter.attack(target)
                attack_results = monster.fighter.attack(target)
                results.extend(attack_results)

            # Change Direction to Face Target
            self.direction_vector = get_direction(self.owner.x, self.owner.y, target.x, target.y)

        # Check if Within Main Area
        elif self.owner.x != self.origin_x and self.owner.y != self.origin_y:
        # elif not self.encounter.main_room.check_point_within_room(self.owner.x, self.owner.y):
            # Move Back to Origin Spot
            # TODO: Why doesn't the mob go back to the same exact area?
            # print('I need to go back to my origin spot! Origin(%s, %s), Current(%s, %s)' %
            #       (self.origin_x, self.origin_y, self.owner.x, self.owner.y))
            monster.move_astar(self.origin_x, self.origin_y, entities, game_map, fov_map)
        else:
            d = randint(0, 4)
            if d == 1:
                self.direction_vector = get_random_direction()
        return results


class PatrolMob(Mob):
    """
    PatrolMob will move between previous room, main room and next room
    """
    def take_turn(self, target, fov_map, game_map, entities, radius):
        results = []
        monster = self.owner

        # Seek/Attack Player if in Range, otherwise Patrol to other Rooms
        # TODO: Python 2D array to numpy array is reversed.
        dist = monster.distance_to(target)
        # if fov_map[target.y][target.x] and radius >= dist:
        #
        #     # Close distance to Player
        #     if radius+1 >= monster.distance_to(target) >= 2:
        #         monster.move_astar(target.x, target.y, entities, game_map, fov_map)
        #
        #     # Player is Within Range, Attack
        #     elif target.fighter.hp > 0 and monster.distance_to(target) <= 2:
        #         attack_results = monster.fighter.attack(target)
        #         results.extend(attack_results)
        #
        #     # Change Direction to Face Target
        #     self.direction_vector = get_direction(self.owner.x, self.owner.y, target.x, target.y)
        # else:
            # Obtain coordinate to next room and move there
        self.patrol(game_map.rooms)
        # TODO: Reduce astar calculation frequency. Only use astar if stuck, map changes, objective changes, etc.
        if not self.path:
            room_x, room_y = self.destination_room.obtain_point_within(padding=3)
            self.path = monster.move_astar(room_x, room_y, entities, game_map,
                                           fov_map)
        else:
            # print('NOT calculating astar')
            y, x = self.path[0]

            # Check if Entity in the way
            if not game_map.transparent[y][x]:
                # print('path found but an entity blocks the way')
                self.stuck_time += 1
                return results
            self.path.pop(0)
            self.direction_vector = get_direction(self.owner.x, self.owner.y, x, y)
            game_map.transparent[self.owner.y][self.owner.x] = True  # unblock previous position
            game_map.transparent[y][x] = False  # block new position# Update Position
            self.owner.x = x
            self.owner.y = y

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
                self.direction_vector = get_random_direction()
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
            self.path = []
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
