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
        direction = choice(list(DIRECTIONS.keys()))
    return DIRECTIONS.get(direction)


class Mob:
    """
    Mob -> Can Find closest Target and Attack
    """

    def __init__(self, encounter=None, *args, **kwargs):
        self.direction_vector = get_random_direction()
        self.stuck_time_max = 2  # time waiting stuck, though path exists
        self.stuck_time = 0
        self.encounter = encounter
        self.path = []
        self.current_target = None
        if encounter:
            self.destination_room = encounter.main_room
            # print('self.destination_room:', self.destination_room)

    def advance_on_current_target(self, entities, game_map, fov_map, dist, radius, results):
        mob = self.owner
        attack_range = 1.5

        # print('\n%s advancing attack: %s' % (self.owner.name, self.current_target.name))
        # print(self.owner.x, self.owner.y, self.current_target.x, self.current_target.y)
        # print('current path:', self.path)

        # Change Direction to Face Target
        self.direction_vector = get_direction(self.owner.x, self.owner.y, self.current_target.x, self.current_target.y)

        # Close distance to Target
        if radius >= dist > attack_range and not self.path:
            self.path = mob.move_astar(self.current_target.x, self.current_target.y, entities, game_map, fov_map)
            # print('# Close distance to Target')
            results.extend(self.move_on_path(game_map, results))

        # Target is Within Range, Attack
        # TODO: Attach Range Variable
        elif self.current_target.fighter.hp > 0 and \
                mob.distance_to(self.current_target.x, self.current_target.y) <= attack_range:
            # print('# Target is Within Range, Attack')
            attack_results = mob.fighter.attack(self.current_target)
            results.extend(attack_results)

        elif radius >= dist > attack_range and self.path:
            # Continue on Path
            results.extend(self.move_on_path(game_map, results))

        return results

    def move_on_path(self, game_map, results):
        y, x = self.path[0]

        # Check if Entity in the way
        # TODO: Replace with recalculation of path using a cost map
        if not game_map.transparent[y][x] or not game_map.walkable[y][x]:
            self.stuck_time += 1
            return results

        self.path.pop(0)
        self.direction_vector = get_direction(self.owner.x, self.owner.y, x, y)
        game_map.transparent[self.owner.y][self.owner.x] = True  # unblock previous position
        game_map.transparent[y][x] = False  # block new position# Update Position
        self.owner.x = x
        self.owner.y = y
        # print('path left:', self.path)
        return []


    def take_turn(self, fov_map, game_map, entities):
        results = []
        mob = self.owner
        radius = self.owner.fighter.fov

        if self.current_target:
            dist = mob.distance_to(self.current_target.x, self.current_target.y)
            if fov_map[self.current_target.y][self.current_target.x] and radius >= dist:
                results = self.advance_on_current_target(entities, game_map, fov_map, dist, radius, results)

            else:
                self.idle_guard()

        else:
            self.idle_guard()
        return results

    def idle_guard(self):
        self.current_target = None
        d = randint(0, 4)
        if d == 1:
            self.direction_vector = get_random_direction()


class DefensiveMob(Mob):
    """
    Defensive -> Return to origin if no target
    """

    def __init__(self, **kwargs):
        self.origin_x = kwargs.get('origin_x')
        self.origin_y = kwargs.get('origin_y')
        super(DefensiveMob, self).__init__(**kwargs)

    def take_turn(self, fov_map, game_map, entities):
        results = []
        mob = self.owner
        radius = self.owner.fighter.fov

        # TODO: Python 2D array to numpy array is reversed.
        # print('\n\ntake_turn')
        # print('current_target:', self.current_target)
        # print('curr pos: (%s, %s)' % (self.owner.x, self.owner.y))
        # print('origin: (%s, %s)' % (self.origin_x, self.origin_y))
        # print(self.owner.x != self.origin_x or self.owner.y != self.origin_y)
        if self.current_target:
            dist = mob.distance_to(self.current_target.x, self.current_target.y)
            if fov_map[self.current_target.y][self.current_target.x] and radius >= dist:
                results = self.advance_on_current_target(entities, game_map, fov_map, dist, radius, results)
            else:
                self.current_target = None

        # Check if Within Main Area
        elif self.owner.x != self.origin_x or self.owner.y != self.origin_y:

            if self.stuck_time > self.stuck_time_max:
                self.path = []
                self.current_target = None
                self.stuck_time = 0

            # Move Back to Origin Spot
            # TODO: Why doesn't the mob go back to the same exact area?
            if not self.path:
                self.path = mob.move_astar(self.origin_x, self.origin_y, entities, game_map, fov_map)
                # print('new path made:', self.path)
                results.extend(self.move_on_path(game_map, results))
            else:
                # Continue on Existing Path
                # print('# Continue on Existing Path')
                results.extend(self.move_on_path(game_map, results))
        else:
            self.idle_guard()

        return results


class PatrolMob(Mob):
    """
    Patrol -> Will move between areas of interest contained within map
    """
    goal_x = -100
    goal_y = -100

    wait_time_max = 20
    wait_time = 0

    def take_turn(self, fov_map, game_map, entities):
        results = []
        mob = self.owner
        radius = self.owner.fighter.fov

        # Seek/Attack Player if in Range, otherwise Patrol to other Rooms
        # TODO: Python 2D array to numpy array is reversed.
        if self.current_target:

            dist = mob.distance_to(self.current_target.x, self.current_target.y)
            if fov_map[self.current_target.y][self.current_target.x] and radius >= dist:
                results = self.advance_on_current_target(entities, game_map, fov_map, dist, radius, results)
            else:
                self.idle_guard()
        else:

            # Obtain coordinate to next room and move there
            if hasattr(game_map, 'sub_rooms'):
                self.patrol(game_map.sub_rooms)
            else:
                self.patrol(game_map.rooms)

            # Establish a New Path or Continue on Existing Path
            if not self.path and self.wait_time < 1:

                # Select a Goal that is Possible to Reach
                room_to_avoid = None

                if hasattr(game_map, 'jail_cells'):
                    for j in game_map.map.jail_cells:
                        if j.parent_room == self.destination_room:
                            room_to_avoid = j
                            break

                # Select a Possible Random Point in Next Area of Interest
                tries = 0
                max_tries = 30
                while tries < max_tries:
                    room_x = randint(self.destination_room.x + 1, self.destination_room.x + self.destination_room.width - 1)
                    room_y = randint(self.destination_room.y + 1, self.destination_room.y + self.destination_room.height - 1)

                    # Coordinates are Reachable and Not Obstructed by an Obstacle
                    if room_to_avoid:
                        if not room_to_avoid.contains(room_x, room_y) and game_map.walkable[room_y][room_x]:
                            self.goal_x, self.goal_y = room_x, room_y
                            break
                    else:
                        # Check if Random Coordinates are Reachable
                        if game_map.walkable[room_y][room_x]:
                            self.goal_x, self.goal_y = room_x, room_y
                            break

                    self.goal_x, self.goal_y = None, None
                    tries += 1

                # Finally Move To Suitable Coordinate
                if self.goal_x and self.goal_y:
                    self.path = mob.move_astar(self.goal_x, self.goal_y, entities, game_map, fov_map)

                    if self.path:
                        results.extend(self.move_on_path(game_map, results))

            elif self.path:
                # Continue on Existing Path
                results.extend(self.move_on_path(game_map, results))

        return results

    def check_if_at_destination(self):
        # Check if Patrol mob has Reached Center Coordinate of Destination Room
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


class FleeMob(Mob):
    def __init__(self, previous_ai):
        self.previous_ai = previous_ai
        super(FleeMob, self).__init__(previous_ai.encounter)

    def take_turn(self, fov_map, game_map, entities):
        results = []
        mob = self.owner

        return results


class ConfusedMob(Mob):
    def __init__(self, previous_ai, duration=10):
        self.previous_ai = previous_ai
        self.duration = duration
        super(ConfusedMob, self).__init__(previous_ai.encounter)

    def take_turn(self, fov_map, game_map, entities):
        results = []
        mob = self.owner

        # Confused Monster AI
        if self.duration > 0:
            random_x = mob.x + randint(0, 2) - 1
            random_y = mob.y + randint(0, 2) - 1

            if random_x != mob.x and random_y != mob.y:
                mob.move_towards(random_x, random_y, game_map, entities)

            self.duration -= 1
        else:
            # Confusion Wore Off
            mob.ai = self.previous_ai
            results.append({'message': Message('The %s is no longer confused!' % mob.name, libtcod.red)})

        return results
