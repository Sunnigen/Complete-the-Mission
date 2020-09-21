from math import ceil
from random import choice, randint

import tcod

from components.AI import BlindAI, ConfusedAI
from components.Particle import ParticleSystem
from GameMessages import Message


def consume(*args, **kwargs):
    return [{'consumed': True}]


def eat(*args, **kwargs):
    entity = args[0]
    name = kwargs.get('name')
    amount = kwargs.get('amount')
    print(args)
    print(kwargs)

    results = [{'consumed': True, 'message': Message('%s eats the %s.' % (entity.name, name), tcod.yellow)}]
    results.append({'message': Message('But since hunger clocks aren\'t coded in yet. Nothing happened', tcod.yellow)})
    return results


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
    print('heal:', args, kwargs)
    amount = kwargs.get('amount')

    results = [{'consumed': True, "spawn_particle": ["heal", entity.position.x, entity.position.y, None], 'message': Message('You consume the berry ...'.format(entity.name), tcod.yellow)}]

    if entity.fighter.hp >= entity.fighter.max_hp:
        results.append({'message': Message('But you don\'t feel any different.', tcod.yellow)})
    else:
        entity.fighter.heal(entity.fighter.max_hp)
        results.append({'message': Message('You regain some health.', tcod.green)})

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
    # fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    game_map = kwargs.get("game_map")
    maximum_range = kwargs.get('maximum_range')

    results = []

    target = None
    closest_distance = maximum_range + 1

    # Search Closest Entity
    for entity in entities:
        if entity.fighter and entity != caster and (entity.position.x, entity.position.y) in caster.fighter.curr_fov_map:
            distance = caster.position.distance_to(entity.position.x, entity.position.y)

            if distance < closest_distance and caster.faction.check_enemy(entity.faction.faction_name):
                target = entity
                closest_distance = distance

    if target:
        lightning_astar_path = caster.position.move_astar(target.position.x, target.position.y, game_map, diagonal_cost=1.00)
        results.append({'consumed': True, 'target': target, 'message': Message(
            'A lightning bolt strikes %s with a loud thunder! %s sustains %s damage.' % (target.name, target.name,
                                                                                         damage))})
        results.extend(target.fighter.take_damage(damage, caster))

        # Create Lightning Particles Along Path to Target Entity
        # TODO: Check if surrounding tiles conduct electricity
        lightning_particle_system = ParticleSystem()
        for path_x, path_y in lightning_astar_path:
            results.append({'spawn_particle': ["lightning", path_y, path_x, lightning_particle_system]})

    else:
        results.append({'consumed': False, 'target': None, 'message': Message('No enemy is close enough to strike.',
                                                                              tcod.red)})

    return results


def cast_fireball(*args, **kwargs):
    caster = args[0]
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    radius = kwargs.get('radius')
    game_map = kwargs.get('game_map')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    # Tile not within range
    if not fov_map.fov[target_x][target_y]:
        results.append({'consumed': False, 'message': Message('You cannot target this area!', tcod.yellow)})
        return results

    results.append({'consumed': True, 'message': Message('The fireball explodes, burning everything within %s tiles!' %
                                                         radius, tcod.orange)})

    # Damage Entities in Radius
    # _entities = [entity for entity in entities if entity.position]
    for entity in entities:
        if entity.position.distance(target_x, target_y) <= radius and entity.fighter:
            results.append({'message': Message('The %s gets burned for %s hit points.' % (entity.name, damage),
                                               tcod.orange)})
            results.extend(entity.fighter.take_damage(damage, caster))

    # "Destroy" Map Object
    print(game_map.map_objects)
    for entity in game_map.map_objects:
        if entity.position.distance(target_x, target_y) <= radius and entity.map_object.breakable and "flammable" in entity.map_object.properties:
            # map_object_component = entity.map_object

            if entity.inventory:

                for item in entity.inventory.items:
                    entities.append(item)

                entity.inventory.drop_all_items()

            results.append({"change_map_object": [entity, 2]})

    # Apply Fire Particle to Each Affected Tile
    # lower_bound = radius // 2
    # upper_bound = ceil(radius / 2)
    fire_particle_system = ParticleSystem()
    for x in range(target_x - radius, target_x + radius + 1):
        for y in range(target_y - radius, target_y + radius + 1):

            dx = target_x - x
            dy = target_y - y

            distance_squared = dx*dx + dy*dy

            # Check if Obstacle or Flammable Tile
            if game_map.tile_cost[y][x] != 0 and distance_squared <= radius * radius:
                results.append({"spawn_particle": ["fire", x, y, fire_particle_system]})

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
        if entity.position.x == target_x and entity.position.y == target_y and entity.ai:
            confused_ai = ConfusedAI(entity.ai, 10)

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


def cast_teleport(*args, **kwargs):
    caster = args[0]
    game_map = kwargs.get("game_map")
    target_x = kwargs.get("target_x")
    target_y = kwargs.get("target_y")
    reveal_all = kwargs.get("reveal_all")

    results = [{'message': Message('You focus on the crystal\'s reflection...', tcod.light_green)}]

    if (game_map.walkable[target_y][target_x] and game_map.tile_cost[target_y][target_x] == 1 and game_map.explored[target_y][target_x]) or reveal_all:
        results.append({'consumed': True,
                        'message': Message('A bright light engulfs you for a moment.', tcod.light_green)})

        # 10% Chance of Teleporting to to a Random Location!
        teleport_roll = randint(1, 10)
        if teleport_roll == 1:

            # Attempt to Find a Random Location
            max_tries = 30
            tries = 0
            random_x, random_y = None, None
            while tries < max_tries:
                random_x = randint(1, game_map.width - 1)
                random_y = randint(1, game_map.height - 1)

                # print('\n', random_x, random_y)
                # print(game_map.walkable[random_y][random_x], game_map.tile_cost[random_y][random_x], game_map.tileset_tiles[random_y][random_x])
                if game_map.walkable[random_y][random_x] and game_map.tile_cost[random_y][random_x] == 1:
                    break
                random_x, random_y = None, None
                tries += 1

            # Fail safe if no proper location is found
            if not random_x or not random_y:
                results.append({'message': Message('Nothing seems to have happened? You no longer have a crystal in your hands.', tcod.light_yellow)})
            else:
                results.append({'message': Message('You have teleported somewhere else entirely? You look around warily.', tcod.light_red)})
                game_map.walkable[random_y][random_x] = True
                game_map.transparent[random_y][random_x] = True
                caster.position.x, caster.position.y = random_x, random_y

        else:
            results.append({'message': Message('You have teleported successfully!', tcod.light_green)})
            game_map.walkable[caster.position.y][caster.position.x] = True
            game_map.transparent[caster.position.y][caster.position.x] = True
            caster.position.x, caster.position.y = target_x, target_y
    else:
        results.extend([{'consumed': False, 'message': Message('But you can\'t focus on the location. Nothing appears to have happened.', tcod.yellow)}])
    return results


def cast_blind(*args, **kwargs):
    blind_duration = 25
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
        if entity.position.x == target_x and entity.position.y == target_y and entity.ai:
            blind_ai = BlindAI(entity.ai, blind_duration)

            blind_ai.owner = entity
            entity.ai = blind_ai

            results.append({'consumed': True, 'message': Message(
                'The eyes of the %s look vacant, as he starts to stumble around!' %
                entity.name, tcod.light_green)}
                           )
            break
    else:
        results.append({'consumed': False, 'message': Message('There is no targetable enemy at that location.',
                                                              tcod.yellow)})

    return results
