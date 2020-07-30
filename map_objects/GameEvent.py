import tcod

from components.Encounter import Encounter
from level_generation.GenerationUtils import generate_mob, place_tile
from loader_functions.JsonReader import obtain_item_table, obtain_mob_table, obtain_tile_set, obtain_particles
from GameMessages import Message
import MapObjectFunctions

import RenderFunctions

MOBS = obtain_mob_table('undergrave_prison')


class GameEvent:
    """
    Example:

    mobs = ['undergrave_guard', 'undergrave_dog', 'undergrave_bruiser', 'undergrave_officer']
    game_event = GameEvent(self.game_map, 5, 'spawn_mob', position=center(self.start_room),
                           mobs=[choice(mobs) for i in range(20)], faction='Imperials',
                           ai_type=FollowAI, area_of_interest=self.start_room, target_entity=self.game_map.player,
                           follow_entity=self.game_map.player)


    """

    def __init__(self, game_map, event_type=None, conditions=None, condition_kwargs=None, **kwargs):
        self.game_map = game_map
        self.event_type = event_type
        self.conditions = conditions
        self.condition_kwargs = condition_kwargs
        self.function_kwargs = kwargs

    def check_conditions(self):
        return all(condition(self.condition_kwargs) for condition in self.conditions)

    def activate_event(self, entities, particles):
        results = []
        if self.event_type == 'spawn_mob':
            mob_indexes = self.function_kwargs.get('mobs')
            faction = self.function_kwargs.get('faction')
            ai_type = self.function_kwargs.get('ai_type')
            area = self.function_kwargs.get('area_of_interest')
            spawn_x, spawn_y = self.function_kwargs.get('position')
            target_entity = self.function_kwargs.get('target_entity')
            follow_entity = self.function_kwargs.get('follow_entity')
            origin_x = self.function_kwargs.get('origin_x')
            origin_y = self.function_kwargs.get('origin_y')
            e = Encounter(self.game_map, area, len(self.game_map.encounters) + 1, ai_type=ai_type)

            if self.game_map.player.position.distance_to(spawn_x, spawn_y) < 5:
                results.append({'message': Message("You spot reinforcements coming from the above floor!", tcod.dark_yellow)})
            else:
                results.append({'Message': Message("You hear barking and yelling in the distance...", tcod.dark_yellow)})
            for mob_index in mob_indexes:
                x, y = self.game_map.obtain_closest_spawn_point(spawn_x, spawn_y)
                mob_stats = MOBS.get(mob_index)
                if x and y:
                    self.game_map.tile_cost[y][x] = 99
                    entities.append(generate_mob(x, y, mob_stats, mob_index, e, faction, ai_type, entities,
                                                 follow_entity=follow_entity, target_entity=target_entity,
                                                 origin_x=origin_x, origin_y=origin_y))
                else:
                    print('Error! Coudn\'t find open spawn point for {} at ({}, {})'.format(mob_stats.get('name'), spawn_x, spawn_y))
                # (x, y, mob_stats, mob_index, encounter_group, faction, ai, entities, dialogue_component=None):
        elif self.event_type == 'open_gate':
            map_objects = self.function_kwargs.get('map_objects')

            for map_object in map_objects:
                self.game_map.map_objects.remove(map_object)
                place_tile(self.game_map, map_object.position.x, map_object.position.y, "2")
                # results.append({"change_map_object": [map_object, 2], "message": Message("The {} has opened!".format(map_object.name))})
                results.append({"message": Message("The {} has opened!".format(map_object.name))})

        return results

    def __repr__(self):
        return_string = 'GameEvent EventType: "{}"'.format(self.event_type)
        for key, val in self.function_kwargs.items():
            return_string += '\n\t{}:{}'.format(key, val)
        return return_string

    # game_event = GameEvent(5, 'spawn_mob', mobs=['undergrave_guard', 'undergrave_guard', 'undergrave_dog'],
    #                        faction='Imperials', 'ai_type'=AI,' area_of_interest'


def entity_at_position_condition(condition_kwargs):
    entity = condition_kwargs.get('entity')
    x_start, x_end, y_start, y_end = condition_kwargs.get('area_of_interest')
    return x_start <= entity.position.x <= x_end and y_start <= entity.position.y <= y_end


def turn_count_condition(condition_kwargs):
    game_map = condition_kwargs.get("game_map")
    turn_count = condition_kwargs.get("turn_count")
    return game_map.turn_count >= turn_count


def check_entity_dead(condition_kwargs):
    target_entity = condition_kwargs.get("target_entity")
    return target_entity.render_order == RenderFunctions.RenderOrder.CORPSE
