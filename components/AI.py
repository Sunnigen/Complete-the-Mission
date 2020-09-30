from random import choice, randint

import tcod as libtcod

from GameMessages import Message
from loader_functions.JsonReader import obtain_mob_table
from map_objects.GameMapUtils import get_map_object_at_location

# from SpellFunctions import cast_mend, cast_thorn_spike, no_spell

MOBS = obtain_mob_table()


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


class AI:
    """
    Mob -> Can Find closest Target and Attack
    """
    path = []
    stuck_time = 0
    stuck_time_max = 2  # time waiting stuck, though path exists
    current_target = None  # Entity or None
    last_target_position = None  # (x, y) tuple or None
    wait_time_max = 20
    wait_time = 0
    target_not_within_fov_counter = 0
    target_not_within_fov_max = 10

    def __init__(self, encounter=None, *args, **kwargs):
        self.direction_vector = get_random_direction()
        self.encounter = encounter
        if encounter:
            self.destination_room = encounter.main_room
            # print('self.destination_room:', self.destination_room)

    def check_engaging_target(self):
        return True if self.current_target or self.last_target_position else False

    def remove_encounter(self):
        # Remove Entity from Encounter due to transfer or death
        self.encounter.remove_entity(self.owner)

    def advance_on_current_target(self, entities, game_map, fov_map, dist, radius, results, target_x, target_y):
        mob = self.owner

        # Check to Cast Spell or Perform Skill
        can_cast_spells = getattr(self.owner.spellcaster, 'has_spells', None)
        if self.current_target and can_cast_spells:
            if self.owner.spellcaster.has_spells:

                # Select Spell
                # Check Self HP to Heal
                if self.owner.fighter.hp <= self.owner.fighter.max_hp // 2 and self.owner.spellcaster.has_spell_type("restorative"):
                    try:
                        spell_to_cast = choice([spell for spell in self.owner.spellcaster.spells if spell.type & {"restorative"} and spell.is_ready])
                        target = self.owner
                    except IndexError:
                        # Empty sequence/no spells
                        spell_to_cast = None
                        target = None

                elif self.owner.faction.check_enemy(self.current_target.faction.faction_name):
                    try:
                        spell_to_cast = choice([spell for spell in self.owner.spellcaster.spells if spell.type & {"offensive", "buff", "environment"} and spell.is_ready])
                        target = self.current_target
                    except IndexError:
                        # Empty sequence/no spells
                        spell_to_cast = None
                        target = None

                else:
                    spell_to_cast = None
                    target = None

                if spell_to_cast:
                    results.extend(self.owner.spellcaster.cast(spell_to_cast, caster=self.owner, target=target))
                    return results


                # Check Enemy to cast Spell
                # if self.owner.faction.check_enemy(self.current_target.faction.faction_name) and \
                #     mob.position.distance_to(self.current_target.position.x, self.current_target.position.y) < 5:
                #     # Select Self Buff or Offensive Spell
                #     results.extend(self.owner.spellcaster.cast(cast_thorn_spike, spell, target=self.current_target))
                #     return results

        # Check if Stuck to Reset Path
        if self.stuck_time > self.stuck_time_max:
            self.path = []
            self.stuck_time = 0

        # Target is Within Range, Attack
        if self.current_target:
            if self.current_target.fighter.hp > 0 and \
                    mob.position.distance_to(self.current_target.position.x, self.current_target.position.y) <= self.owner.fighter.attack_range:
                # print('# Target is Within Range, Attack')

                attack_results = mob.fighter.attack(self.current_target)
                results.extend(attack_results)
                return results

        # Close distance to Target or Evade
        if (self.current_target and not self.path) or \
                (self.last_target_position and not self.path) or \
                (self.current_target and not (target_y, target_x) in self.path):

            self.path = mob.position.movement_function(target_x, target_y, game_map, )
            # self.path = mob.position.move_astar(target_x, target_y, game_map)

        # Move Entity to Next Floor if Seeking
        if self.encounter.main_target == game_map.stairs and \
                self.owner.position.x == game_map.stairs.position.x and \
                self.owner.position.y == game_map.stairs.position.y:
            entities.remove(self.owner)
            self.encounter.mob_list.remove(self.owner)
            game_map.next_floor_entities.append(self.owner)

            tile_index = game_map.tileset_tiles[self.owner.position.y][self.owner.position.x]
            game_map.tile_cost[self.owner.position.y][self.owner.position.x] = game_map.tile_set.get(
                '%s' % tile_index).get('tile_cost')
            results.append({'message': Message('{} ascended to the next level!'.format(self.owner.name))})

        # Finally Move
        if len(self.path) > 0:
            results.extend(self.move_on_path(game_map, entities, results))
            self.direction_vector = get_direction(self.owner.position.x, self.owner.position.y, target_x, target_y)

        return results

    def move_on_path(self, game_map, entities, results):
        print('\n\nmove_on_path')
        print(self.path)
        mob = self.owner
        y, x = self.path[0]
        self.direction_vector = get_direction(self.owner.position.x, self.owner.position.y, x, y)

        # Check if Entity can Interact with Map Object
        map_object_entity = get_map_object_at_location(game_map.map_objects, x, y)

        if map_object_entity:
            interact_results = mob.fighter.interact(map_object_entity, interact_type='move',
                                                            target_inventory=mob.inventory,
                                                            entities=entities, is_player=False, game_map=game_map)
            # Remove Player Only Messages
            # TODO: Might have to keep "some" messages from other mob interaction with map objects
            for r in interact_results:
                r.pop('message', None)

            results.extend(interact_results)

        # Check if Entity in the way
        # print('# Check if Entity in the way')
        # print('map_object_entity:', map_object_entity)
        if not game_map.walkable[y][x] or game_map.tile_cost[y][x] > 98:
            self.stuck_time += 1
            # print('returning results:', results)
            return results

        # Remove Step from Path and Update Direction FOV
        self.path.pop(0)

        # Update Previous and New Destination on Game Map
        # game_map.transparent[self.owner.y][sealf.owner.x] = True  # unblock previous position
        # game_map.transparent[y][x] = False  # block new position# Update Position
        tile_index = game_map.tileset_tiles[y][x]
        game_map.tile_cost[self.owner.position.y][self.owner.position.x] = game_map.tile_set.get('%s' % tile_index).get('tile_cost')
        game_map.tile_cost[y][x] = 99

        # Finally Update Entity Position
        self.owner.position.x = x
        self.owner.position.y = y

        # Spawn Sound Particle if not in player FOV
        # print('# Spawn Sound Particle if not in player FOV')
        # print('{} pos: {}'.format(self.owner.name, self.owner.position))
        if not (x, y) in game_map.player.fighter.curr_fov_map:
            results.append({"spawn_particle": ["sound", x, y, None]})

        return results

    def take_turn(self, fov_map, game_map, entities):
        results = []
        mob = self.owner
        radius = self.owner.fighter.fov_range

        if self.current_target:
            self.wait_time = 0
            target_x, target_y = self.current_target.position.x, self.current_target.position.y

            # Change Direction to Face Target
            dist = mob.position.distance_to(target_x, target_y)

            # Target is in FOV map and Within Entities FOV range
            if (target_y, target_x) in fov_map and self.target_not_within_fov_counter <= self.target_not_within_fov_max:
            # if (target_y, target_x) in fov_map and radius >= dist and self.target_not_within_fov_counter <= self.target_not_within_fov_max:
                self.last_target_position = target_x, target_y
                results = self.advance_on_current_target(entities, game_map, fov_map, dist, radius, results, target_x,
                                                         target_y)
                self.target_not_within_fov_counter = 0
            elif self.target_not_within_fov_counter <= self.target_not_within_fov_max:
            # elif radius >= dist and self.target_not_within_fov_counter <= self.target_not_within_fov_max:
                self.last_target_position = target_x, target_y
                results = self.advance_on_current_target(entities, game_map, fov_map, dist, radius, results, target_x,
                                                         target_y)
                self.target_not_within_fov_counter += 1

            else:
                # Cannot Find Entity
                self.idle_guard()

        elif self.last_target_position:
            # Go to Last Position Where Previous Entity was Seen
            target_x, target_y = self.last_target_position

            results = self.advance_on_current_target(entities, game_map, fov_map, radius, radius, results, target_x,
                                                     target_y)

            # Check if At Last Position to Find Previous Entity
            if mob.position.distance(target_x, target_y) < 1.4 or self.check_if_stuck():

                # Wait to check surroundings as if Looking for Lost Target
                if self.check_if_waiting():
                    self.last_target_position = None
                    self.path = []
                    self.wait_time = 0
        else:
            self.idle_guard()
        return results

    def check_if_waiting(self):
        # Wait in Destination Room before Traveling Onward
        if self.wait_time < self.wait_time_max:
            # print('I am currently waiting! Wait time currently:', self.wait_time)
            self.wait_time += 1
            self.stuck_time = 0  # reset because no longer stuck
            d = randint(0, 1)
            if d == 1:
                self.direction_vector = get_random_direction()
            return False
        return True

    def check_if_stuck(self):
        if self.stuck_time < self.stuck_time_max:
            return False
        # print('I\'m definitely stuck. Changing destination')
        return True

    def idle_guard(self):
        self.current_target = None
        self.target_not_within_fov_counter = 0
        d = randint(0, 1)
        if d == 1:
            self.direction_vector = get_random_direction()
            

class DefensiveAI(AI):
    """
    Defensive -> Return to origin if no target
    """

    def __init__(self, **kwargs):
        self.origin_x = kwargs.get('origin_x')
        self.origin_y = kwargs.get('origin_y')
        super(DefensiveAI, self).__init__(**kwargs)

    def take_turn(self, fov_map, game_map, entities):
        # print('\n\ntake turn')
        # print('curr target:', self.current_target)
        # print('last position:', self.last_target_position)
        # print('curr pos:', self.owner.position)
        results = []
        mob = self.owner
        radius = self.owner.fighter.fov_range

        if self.current_target:
            results = super(DefensiveAI, self).take_turn(fov_map, game_map, entities)

        elif self.last_target_position:
            # Go to Last Position Where Previous Entity was Seen
            target_x, target_y = self.last_target_position

            results = self.advance_on_current_target(entities, game_map, fov_map, radius, radius, results, target_x,
                                                     target_y)

            # Check if At Last Position to Find Previous Entity
            if mob.position.distance(target_x, target_y) < 1.4 or self.check_if_stuck():

                # Wait to check surroundings as if Looking for Lost Target
                if self.check_if_waiting():
                    self.last_target_position = None
                    self.path = []
                    self.wait_time = 0

        # Check if Within Main Area
        elif self.owner.position.x != self.origin_x or self.owner.position.y != self.origin_y:
            if self.check_if_stuck():
                self.path = []
                # self.current_target = None
                self.stuck_time = 0

            # Move Back to Origin Spot
            if not self.path:
                # print('# Move Back to Origin Spot')
                # print(self.owner.position.x, self.owner.position.y)
                # print(self.origin_x, self.origin_y, game_map.tileset_tiles[self.origin_x][self.origin_y])
                self.path = mob.position.move_astar(self.origin_x, self.origin_y, game_map)
                # print('path:', self.path)

            results.extend(self.move_on_path(game_map, entities, results))

        # Shuffle Different Origin Spot
        elif self.wait_time > self.wait_time_max:
            self.wait_time = 0
        else:
            self.idle_guard()

        return results
    

class FollowAI(DefensiveAI):
    """
    FollowMob -> Will follow designated unit. Otherwise will act like DefensiveAI.
    """
    follow_entity = None
    follow_distance = 1
    # follow_max_distance = 5
    wait_time_max = 2

    def __init__(self, follow_entity, **kwargs):
        self.follow_entity = follow_entity
        self.follow_distance = randint(1, 2)
        super(FollowAI, self).__init__(**kwargs)

    def take_turn(self, fov_map, game_map, entities):
        
        # If there is no Entity to Follow act like DefensiveAI
        if not self.follow_entity:
            # Set to "Defend" Current Position
            self.origin_x = self.owner.position.x
            self.origin_y = self.owner.position.y

        else:
            # Set to "Defend" position of the Entity it is following
            self.origin_x = self.follow_entity.position.x
            self.origin_y = self.follow_entity.position.y

        return super(FollowAI, self).take_turn(fov_map, game_map, entities)


class PatrolAI(AI):
    """
    Patrol -> Will move between areas of interest contained within map
    """
    goal_x = -100
    goal_y = -100

    def take_turn(self, fov_map, game_map, entities):
        results = []
        mob = self.owner
        radius = self.owner.fighter.fov_range

        # Seek/Attack Player if in Range, otherwise Patrol to other Rooms
        if self.current_target:
            results = super(PatrolAI, self).take_turn(fov_map, game_map, entities)
            # self.wait_time = 0
            # target_x, target_y = self.current_target.position.x, self.current_target.position.y
            # 
            # # Change Direction to Face Target
            # self.direction_vector = get_direction(self.owner.position.x, self.owner.position.y, target_x, target_y)
            # dist = mob.position.distance_to(target_x, target_y)
            # 
            # # Target is in FOV map and Within Entities FOV range
            # if (target_y, target_x) in fov_map and radius >= dist:
            #     self.last_target_position = self.current_target.position.x, self.current_target.position.y
            #     results = self.advance_on_current_target(entities, game_map, fov_map, dist, radius, results, target_x, target_y)
            # 
            # else:
            #     # Cannot Find Entity
            #     self.idle_guard()

        elif self.last_target_position:

            # Go to Last Position Where Previous Entity was Seen
            target_x, target_y = self.last_target_position

            results = self.advance_on_current_target(entities, game_map, fov_map, radius, radius, results, target_x,
                                                     target_y)

            # Check if At Last Position to Find Previous Entity
            if mob.position.distance(target_x, target_y) < 1.4 or self.check_if_stuck():

                # Wait to check surroundings as if Looking for Lost Target
                if self.check_if_waiting():
                    self.last_target_position = None
                    self.path = []
                    self.wait_time = 0
        else:
            # print('\nGoing back to normal patrol')
            # print('current wait time:', self.wait_time)
            # print(self.path)

            # Obtain coordinate to next room and move there
            if hasattr(game_map, 'sub_rooms'):
                self.patrol(game_map.sub_rooms)
            else:
                self.patrol(game_map.rooms)

            # Establish a New Path or Continue on Existing Path
            if not self.path and self.wait_time < 1:

                # Select a Goal that is Possible to Reach
                rooms_to_avoid = []

                # print('\n\nself.destination_room:', self.destination_room.x, self.destination_room.y,
                #       self.destination_room.width, self.destination_room.height)
                if game_map.level.lower() == 'undergrave':
                # if hasattr(game_map, 'jail_cells'):
                    for j in game_map.map.jail_cells:
                        # print(j.parent_room, j.parent_room.x, j.parent_room.y, j.parent_room.width,
                        #       j.parent_room.height)
                        if j.parent_room == self.destination_room:

                            rooms_to_avoid.append(j)

                # print('rooms_to_avoid:', rooms_to_avoid)


                # Select a Possible Random Point in Next Area of Interest
                tries = 0
                max_tries = 30
                while tries < max_tries:
                    room_x = randint(self.destination_room.x + 1, self.destination_room.x + self.destination_room.width - 1)
                    room_y = randint(self.destination_room.y + 1, self.destination_room.y + self.destination_room.height - 1)

                    # Coordinates are Reachable and Not Obstructed by an Obstacle
                    if rooms_to_avoid:
                        self.goal_x, self.goal_y = room_x, room_y
                        for _room in rooms_to_avoid:
                            if _room.contains(room_x, room_y):
                                # print('room contains!')
                                self.goal_x, self.goal_y = None, None
                        if self.goal_x and self.goal_y and game_map.walkable[room_y][room_x]:
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

                    self.path = mob.position.move_astar(self.goal_x, self.goal_y, game_map)

                    if self.path:
                        results.extend(self.move_on_path(game_map, entities, results))

            elif self.path:
                # Continue on Existing Path
                results.extend(self.move_on_path(game_map, entities, results))

        return results

    def check_if_at_destination(self):
        # Check if Patrol mob has Reached Center Coordinate of Destination Room
        # print('check_if_at_destination', self.owner.distance_to(self.goal_x, self.goal_y))
        # print('destination: (%s, %s)' % (self.destination_room.x, self.destination_room.y) )
        if self.owner.position.distance_to(self.goal_x, self.goal_y) <= 2:
            # print('true')
            return True
        # print('patroling to room #%s' % self.destination_room.room_number)
        # print('false')
        return False

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
        if room_number >= len(game_map_rooms):
            room_number = 0
        self.destination_room = game_map_rooms[room_number - 1]


class PursueAI(AI):

    def __init__(self, target_entity, **kwargs):
        self.target_entity = target_entity
        super(PursueAI, self).__init__(**kwargs)

    def take_turn(self, fov_map, game_map, entities):
        # If there is no Entity to Follow act like DefensiveAI

        if not self.target_entity:
            # Set to "Defend" Current Position
            self.origin_x = self.owner.position.x
            self.origin_y = self.owner.position.y

        else:
            # Set to "Defend" position of the Entity it is following
            self.origin_x = self.target_entity.position.x
            self.origin_y = self.target_entity.position.y

        return super(PursueAI, self).take_turn(fov_map, game_map, entities)


class FleeAI(AI):
    goal_x = None
    goal_y = None

    def __init__(self, previous_ai):
        self.previous_ai = previous_ai
        super(FleeAI, self).__init__(previous_ai.encounter)

    def take_turn(self, fov_map, game_map, entities):
        results = []
        mob = self.owner

        # Find Closest Allied Encounter and Inform Them
        if not self.goal_x and not self.goal_y:
            self.goal_x, self.goal_y = self.find_closest_allies(game_map)

        # Find Farthest Area Away(Dijkstra)
        if not self.goal_x and not self.goal_y:
            pass
        # do dijkstra map stuff

        return results

    def find_closest_allies(self, game_map):
        possible_encounters = {}
        for encounter in game_map.encounters:
            if encounter.faction_compatibility(self.owner.faction):
                possible_encounters[self.owner.position.distance_to(encounter.main_room.x, encounter.main_room.y)] = encounter.main_room
        if possible_encounters:
            return possible_encounters[min(possible_encounters)]

        return (None, None)


class ConfusedAI(AI):
    def __init__(self, previous_ai, duration=20):
        self.previous_ai = previous_ai
        self.duration = duration
        super(ConfusedAI, self).__init__(previous_ai.encounter)

    def take_turn(self, fov_map, game_map, entities):
        results = []
        mob = self.owner

        # Blind Mob AI
        if self.duration > 0:
            random_x = mob.position.x + randint(0, 2) - 1
            random_y = mob.position.y + randint(0, 2) - 1

            if random_x != mob.position.x and random_y != mob.position.y:

                self.direction_vector = get_direction(mob.position.x, mob.position.y, random_x, random_y)
                mob.position.move_towards(random_x, random_y, game_map, entities)
            else:
                self.direction_vector = get_next_direction()

            self.duration -= 1
            results.append({"spawn_particle": ["confusion", mob.position.x, mob.position.y, None]})
        else:
            # Confusion Wore Off
            mob.ai = self.previous_ai
            results.append({'message': Message('The %s is no longer confused!' % mob.name, libtcod.red)})

        return results


class BlindAI(AI):
    def __init__(self, previous_ai, duration=10):
        self.previous_ai = previous_ai
        self.duration = duration
        super(BlindAI, self).__init__(previous_ai.encounter)

    def take_turn(self, fov_map, game_map, entities):
        results = []
        mob = self.owner
        mob.fighter.fov_range = 1

        # Blind Mob AI
        if self.duration > 0:
            self.duration -= 1
        else:
            # Blind Wore Off Restore Default
            mob.ai = self.previous_ai
            mob.fighter.fov_range = MOBS.get(mob.json_index).get('fov_range')
            results.append({'message': Message('The %s can see clearly now!' % mob.name, libtcod.red)})
        return results
