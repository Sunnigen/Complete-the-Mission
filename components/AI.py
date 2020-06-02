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
        self.wait_time_max = 10
        # self.wait_time_max = randint(4, 10)  # time waiting at objective
        self.wait_time = 0
        self.path = []
        if encounter:
            self.destination_room = encounter.main_room


class BasicMob(Mob):

    def take_turn(self, target, fov_map, game_map, entities, radius):
        results = []
        monster = self.owner

        # TODO: Python 2D array to numpy array is reversed.
        dist = monster.distance_to(target.x, target.y)
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
    goal_x = -100
    goal_y = -100

    def take_turn(self, target, fov_map, game_map, entities, radius):
        results = []
        monster = self.owner

        # Seek/Attack Player if in Range, otherwise Patrol to other Rooms
        # TODO: Python 2D array to numpy array is reversed.
        # dist = monster.distance_to(target)
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
        if hasattr(game_map, 'sub_rooms'):
            self.patrol(game_map.sub_rooms)
        else:
            self.patrol(game_map.rooms)
        # self.patrol(game_map.rooms)
        # TODO: Reduce astar calculation frequency. Only use astar if stuck, map changes, objective changes, etc.
        if not self.path and self.wait_time < 1:

            # Select a Goal that is Possible to Reach
            # print('# Select a Goal that is Possible to Reach')
            # print('self.destination_room:', self.destination_room)
            # print('wait time:', self.wait_time)

            room_to_avoid = None

            if hasattr(game_map, 'jail_cells'):
                for j in game_map.map.jail_cells:
                    if j.parent_room == self.destination_room:
                        room_to_avoid = j
                        break
            tries = 0
            max_tries = 30

            while tries < max_tries:
                room_x = randint(self.destination_room.x + 1, self.destination_room.x + self.destination_room.width - 1)
                room_y = randint(self.destination_room.y + 1, self.destination_room.y + self.destination_room.height - 1)
                # print('\n\n room_x: %s, room_y: %s' % (room_x, room_y))
                # print(self.destination_room.x, self.destination_room.x + self.destination_room.width,)
                # print(self.destination_room.y, self.destination_room.y + self.destination_room.height,)

                # Coordinates are Reachable and Not Obstructed by an Obstalce

                if room_to_avoid:
                    # print('Checking:', room_x, room_y, not room_to_avoid.contains(room_x, room_y),
                    #       game_map.walkable[room_y][room_x])
                    if not room_to_avoid.contains(room_x, room_y) and game_map.walkable[room_y][room_x]:
                        self.goal_x, self.goal_y = room_x, room_y
                        break

                else:
                    # print('Checking:', room_x, room_y, game_map.walkable[room_y][room_x])
                    if game_map.walkable[room_y][room_x]:
                        self.goal_x, self.goal_y = room_x, room_y
                        break

                self.goal_x, self.goal_y = None, None
                tries += 1

            if self.goal_x and self.goal_y:
                self.path = monster.move_astar(self.goal_x, self.goal_y, entities, game_map, fov_map)
                # print('new path calculated', self.path)
            # else:
                # print(' no new_ path calculated')
        elif self.path:
            # print('going on path')
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
        # print('check_if_at_destination', self.owner.distance_to(self.goal_x, self.goal_y))
        # print('destination: (%s, %s)' % (self.destination_room.x, self.destination_room.y) )
        if self.owner.distance_to(self.goal_x, self.goal_y) <= 2:
            # print('true')
            return True
        # print('patroling to room #%s' % self.destination_room.room_number)
        # print('false')
        return False

    def check_if_stuck(self):
        if self.stuck_time < self.stuck_time_max:
            return False
        # print('I\'m definitely stuck. Changing destination')
        return True

    def check_if_waiting(self):
        # Wait in Destination Room before Traveling Onward
        # print('self.check_if_waiting')
        if self.wait_time < self.wait_time_max:
            # print('I am currently waiting! Wait time currently:', self.wait_time)
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
        # print('patrol')
        if self.check_if_at_destination():
            # print('should be going to check_if_waiting')
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
        room_number = game_map_rooms.index(self.destination_room)
        # room_number = self.destination_room.room_number
        if room_number >= len(game_map_rooms):
            room_number = 0
        self.destination_room = game_map_rooms[room_number - 1]


class ConfusedMonster(Mob):
    def __init__(self, previous_ai, duration=10):
        self.previous_ai = previous_ai
        self.duration = duration
        super(ConfusedMonster, self).__init__(previous_ai.encounter)

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
