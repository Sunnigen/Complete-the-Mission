from random import choice

import tcod

from components.AI import ConfusedMob
from GameMessages import Message


def read(*args, **kwargs):
    name = kwargs.get('name')
    text = kwargs.get('text')
    results = []
    if name == "Dungeon Map":
        results.append({'map': True, 'message': Message('You take the %s out of your inventory.' % name, tcod.yellow)})
    else:

        results.append({'reuseable': True,
                        'message': Message('You place the %s back in your inventory.' % name,
                                                              tcod.yellow)})
        results.append({'message': Message(text)})
    return results


def heal(*args, **kwargs):
    entity = args[0]
    amount = kwargs.get('amount')

    results = [{'consumed': True, 'message': Message('You drink the vial...', tcod.yellow)}]

    if entity.fighter.hp >= entity.fighter.max_hp:
        results.append({'message': Message('But you don\'t feel any different.', tcod.yellow)})
    else:
        entity.fighter.heal(amount)
        results.append({'message': Message('Your wounds start to feel better.', tcod.green)})

    return results


def poison(*args, **kwargs):
    entity = args[0]
    amount = kwargs.get('amount')
    results = []
    results.append({'consumed': True, 'message': Message('The liquid %s your throat!.' % choice(['stings', 'burns']),
                                                         tcod.darker_yellow)})
    results.append({'message': Message('Perhaps it wasn\'t a good idea to quaff it...', tcod.darker_yellow)})
    results.extend(entity.fighter.take_damage(amount))

    return results


def cast_lightning(*args, **kwargs):
    caster = args[0]
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    maximum_range = kwargs.get('maximum_range')

    results = []

    target = None
    closest_distance = maximum_range + 1

    for entity in entities:
        if entity.fighter and entity != caster and tcod.map_is_in_fov(fov_map, entity.x, entity.y):
            distance = caster.distance_to(entity.x, entity.y)

            if distance < closest_distance:
                target = entity
                closest_distance = distance
    if target:
        results.append({'consumed': True, 'target': target, 'message': Message(
            'A lightning bolt strikes %s with a loud thunder! %s sustains %s damage.' % (target.name, target.name,
                                                                                         damage))})
        results.extend(target.fighter.take_damage(damage))
    else:
        results.append({'consumed': False, 'target': None, 'message': Message('No enemy is close enough to strike.',
                                                                              tcod.red)})

    return results


def cast_fireball(*args, **kwargs):
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    radius = kwargs.get('radius')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    # Tile not within range
    if not tcod.map_is_in_fov(fov_map, target_x, target_y):
        results.append({'consumed': False, 'message': Message('You cannot this area!', tcod.yellow)})
        return results

    results.append({'consumed': True, 'message': Message('The fireball explodes, burning everything within %s tiles!' %
                                                         radius, tcod.orange)})

    # Damage Entities in Radius
    for entity in entities:
        if entity.distance(target_x, target_y) <= radius and entity.fighter:
            results.append({'message': Message('The %s gets burned for %s hit points.' % (entity.name, damage),
                                               tcod.orange)})
            results.extend(entity.fighter.take_damage(damage))

    return results


def cast_confuse(*args, **kwargs):
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    if not tcod.map_is_in_fov(fov_map, target_x, target_y):
        results.append({'consumed': False, 'message': Message('You cannot target a tile outside your field of vision.',
                                                              tcod.yellow)})
        return results

    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.ai:
            confused_ai = ConfusedMob(entity.ai, 10)

            confused_ai.owner = entity
            entity.ai = confused_ai

            results.append({'consumed': True, 'message': Message(
                'The eyes of the %s look vacant, as he starts to stumble around!' %
                entity.name, tcod.light_green)}
                           )
            break
    else:
        results.append({'consumed': False, 'message': Message('There is no targetable enemy at that location.',
                                                              tcod.yellow)})

    return results


def cast_blind(*args, **kwargs):
    results = []
    return results
