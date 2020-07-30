from random import randint

import tcod

from components.AI import FollowAI
from components.Dialogue import Dialogue
from components.Particle import ParticleSystem
from GameMessages import Message
import EventFunctions
import ItemFunctions


def no_function(*args, **kwargs):
    # Place holder function for map objects that do not have an interactable function
    return []


def event_gate(*args, **kwargs):
    return [{'message': Message("You can't spot a keyhole. There has to be another way to open the gate?", tcod.dark_yellow)}]


def listen_door(*args, **kwargs):
    results = []
    return results


def unlock_door(*args, **kwargs):
    # print('unlock_door')
    owner_entity = args[0]
    door_entity = args[1]
    results = []

    results = [{"change_map_object": [door_entity, 6], 'message': Message('The {} open the {}.'.format(owner_entity.name, door_entity.name), tcod.yellow)}]
    return results


def see_through_key_hole(*args, **kwargs):
    door_entity = args[1]
    results = [{'see_through_key_hole': door_entity, 'message': Message('You look through the key hole into the next room.', tcod.yellow)}]
    return results


def lock_door(*args, **kwargs):
    owner_entity = args[0]
    door_entity = args[1]
    entities = kwargs.get('entities')
    game_map = kwargs.get('game_map')

    # blocking_entity = get_blocking_entities_at_location(entities, door_entity.position.x, door_entity.position.y)
    x = door_entity.position.x
    y = door_entity.position.y
    if not any([entity for entity in entities if entity.position.x == x and entity.position.y == y]) and \
            game_map.is_within_map(x, y) and not game_map.is_blocked(x, y):
        results = [{"change_map_object": [door_entity, 5],
                    'message': Message('You close the {}.'.format(door_entity.name.lower()), tcod.yellow)}]
    else:
        results = [{'message': Message('The {} can\'t close the {}. It is blocked!'.format(owner_entity.name, door_entity.name.lower()), tcod.red)}]

    return results


def nothing(*args, **kwargs):
    results = []

    return results


def push(*args, **kwargs):
    results = []

    return results


def break_container(*args, **kwargs):
    # print('break_container')
    attacker_entity = args[0]
    container_entity = args[1]
    entities = kwargs.get('entities')


    # print('container_entity:', container_entity.name)
    # print('attacker_entity:', attacker_entity.name)
    # print('container inventory:', container_entity.inventory.items)

    results = [{"change_map_object": [container_entity, 2],
                "spawn_particle": ["hit", container_entity.position.x, container_entity.position.y, None],
                'message': Message('You break open the {}...'.format(container_entity.name.lower()), tcod.yellow)}]

    for item in container_entity.inventory.items:
        entities.append(item)

    container_entity.inventory.drop_all_items()
    return results


def empty_chest(*args, **kwargs):
    # print('empty_chest')
    results = []
    results.append({'chest': False, 'message': Message('The chest is already been opened.', tcod.yellow)})
    return results


def open_gate(*args, **kwargs):
    caster = args[0]
    gate_entity = args[1]
    results = []
    player = kwargs.get('player')
    game_map = kwargs.get('game_map')

    jail_key = caster.inventory.check_item_by_index("jail_key")
    master_key = caster.inventory.check_item_by_index("master_key")

    if jail_key or master_key:

        # Don't Consume Key
        if not master_key:
            results.append({"change_map_object": [gate_entity, 2],
                            'message': Message('You unlock the cell consuming a {}.'.format(jail_key.name),
                                               tcod.yellow)})
            jail_key.item.use_function = eval("ItemFunctions.consume")
            results.extend(caster.inventory.use(jail_key))
        else:
            results.append({"change_map_object": [gate_entity, 2],
                            'message': Message('You unlock the cell.', tcod.yellow)})

        # Free Denizens of Jail and Make them Head towards Exit or Follow Player
        # if caster == player:

        if game_map.level == 'undergrave':
            for jail_cell in game_map.map.jail_cells:
                if gate_entity in jail_cell.entrances:
                    ai_type = 1
                    # ai_type = randint(1, 2)
                    for prisoner_entity in jail_cell.entities:
                        EventFunctions.change_faction(entity=prisoner_entity, new_faction='Rebels')

                        # TODO: Either follow player depending on alignment score/wander/head toward exit
                        if ai_type == 1:
                            prisoner_entity.dialogue = Dialogue(['Lead the way boss!'])
                            # encounter =
                            prisoner_entity.ai = FollowAI(follow_entity=player, encounter=prisoner_entity.ai.encounter)
                            prisoner_entity.ai.owner = prisoner_entity
                            # prisoner_entity.ai.encounter.main_target = game_map.stairs
                        else:
                            prisoner_entity.dialogue = Dialogue(['Freedom! I\'m getting outta here!!'])
                            prisoner_entity.ai.encounter.main_target = game_map.stairs

                    # Remove Jail from "Rooms to Avoid" because it has been opened. Room is now Patrollable.
                    game_map.map.jail_cells.remove(jail_cell)
                    break

    else:
        results.append({'message': Message('A locked jail gate blocks your way.', tcod.yellow)})

    return results


def table_pick_up(*args, **kwargs):
    target_entity = args[0]
    table_entity = args[1]
    results = []

    if table_entity.inventory.empty:
        results.append({'message': Message('You look on the table for anything good. You find nothing...', tcod.yellow)})
    else:
        item = table_entity.inventory.items.pop()
        results.append(
            {'message': Message('You look on the table for anything good. You find a {}.'.format(item.name), tcod.yellow)})
        results.extend(target_entity.inventory.add_item(item))

    return results


def open_chest(*args, **kwargs):
    chest_entity = args[1]
    chest_inventory = chest_entity.inventory
    target_inventory = kwargs.get('target_inventory')
    results = []

    results.append({'change_map_object': [chest_entity, 9], 'message': Message('You open the chest...', tcod.yellow)})
    # Transfer Chest Inventory to Target Inventory
    if chest_inventory:
        # print('Chest Items:', chest_inventory.items)
        while chest_inventory.items:
            # Check if Target Inventory is Full
            if len(target_inventory.items) >= target_inventory.capacity:
                results.append({'message': Message('You cannot carry any more, your inventory is full!', tcod.yellow)})
                # results.append({'message': Message('You close the chest.', tcod.yellow)})
                break
            item = chest_inventory.items.pop()
            results.extend(target_inventory.add_item(item))

    return results


def burn(*args, **kwargs):
    results = []
    caster = args[0]
    stove_entity = args[1]
    burn_damage = 10
    player = kwargs.get('player')

    if caster == player:
        identifier = "You burn yourself for {} damage.".format(burn_damage)
        tcod_color = tcod.flame
    else:
        identifier = "The {} burns itself for {} damage.".format(caster.name, burn_damage)
        tcod_color = tcod.dark_yellow
    fire_particle_system = ParticleSystem()
    results.append({"spawn_particle": ["fire", caster.position.x, caster.position.y, fire_particle_system], 'message': Message('{}'.format(identifier), tcod_color)})
    results.extend(caster.fighter.take_damage(burn_damage))
    return results


def next_floor(*args, **kwargs):
    print('next_floor')
    results = []

    return results
