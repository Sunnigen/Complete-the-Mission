from copy import deepcopy

from components.AI import *


class Encounter:
    """
    - Group all entities and items as a single entity or relate between them
    - encounter_type are AI classes from components.AI
    """
    def __init__(self, game_map, main_room, encounter_number, ai_type=AI):
        self.encounter_number = encounter_number
        self.game_map = game_map
        self.mob_list = []
        self.target_list = set()
        self.item_list = []
        self.main_room = main_room
        self.encounter_type = ai_type  # component.AI
        self.main_target = None

    def signal_other_encounters(self, origin_x, origin_y, target_entity):
        # Pass target_entity to other close by Enounters, must by-pass "clean_target_list"
        pass

    def remove_entity(self, entity):
        if entity in self.mob_list:
            self.mob_list.remove(entity)
        # if entity in self.item_list:
        #     self.item_list.remove(entity)

    def clean_target_list(self):
        # Remove Targets from Entity List if No Mob has it as a target
        # _mob_list = deepcopy(self.target_list)
        _mob_list = set()
        for mob in self.mob_list:

            if mob.ai.current_target:
                # TODO: Might run into an issue with current_targets that were never added into self.target_list
                try:
                    _mob_list.add(mob.ai.current_target)
                except ValueError as error:
                    print('Value Error!')
                    print('%s is not in self.target_list' % mob.ai.current_target.name)
                    print('error:', error)

        self.target_list = _mob_list

    def unite(self):
        # If Mobs in this encounter are engaging other targets, pass the closest enemy target position to unaware mobs

        # Don't Gang up on Targets if none exist
        self.clean_target_list()
        if not self.target_list:

            # Seek Main Target
            if self.main_target:
                for mob in self.mob_list:
                    mob.ai.last_target_position = (self.main_target.position.x, self.main_target.position.y)
            return

        # Assign mobs with no target to ones currently being pursued
        for mob in self.mob_list:
            if not mob.ai.current_target:  # and not mob.ai.last_target_position:
                possible_targets = {mob.position.distance_to(entity.position.x, entity.position.y): entity for entity in self.target_list}
                target = possible_targets[min(possible_targets)]
                mob.ai.last_target_position = (target.position.x, target.position.y)
                # print("%s at (%s, %s) is now pursuing %s at (%s, %s)" % (mob.name, mob.x, mob.y, target.name, target.x, target.y))

    def __repr__(self):
        a = '\n\nEncounter #%s' % self.encounter_number
        a += '\nMain Room: %s' % self.main_room.__class__
        if hasattr(self.main_room, 'room_number'):
            a += '\nRoom Number: %s' % self.main_room.room_number

        a += '\nMobs:'
        if not self.mob_list:
            a += '\n\tNo monsters'
        else:
            for e in self.mob_list:
                a += '\n\t%s' % e.name
        a += '\nItems:'
        if not self.item_list:
            a += '\n\tNo items'
        else:
            for i in self.item_list:
                a += '\n\t%s' % i.name
        return a
