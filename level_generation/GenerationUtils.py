from math import sqrt
from random import choice, choices, randint


from components.AI import AI, DefensiveAI, PatrolAI
from components.Dialogue import Dialogue
from components.Encounter import Encounter
from components.Equipment import Equipment
from components.Equippable import Equippable
from components.Faction import Faction
from components.Fighter import Fighter
from components.MapObject import MapObject
from components.Inventory import Inventory
from components.Item import Item
from components.Particle import Particle
from components.Position import Position
from components.SpellCaster import SpellCaster
from level_generation.Prefab import Prefab
from components.Stairs import Stairs
from Entity import Entity
from EquipmentSlots import EquipmentSlots
from GameMessages import Message
# Do not remove ItemFunctions! There are called out in json and eval()'ed
from ItemFunctions import *
# from ItemFunctions import cast_confuse, cast_fireball, cast_lightning, heal,
from loader_functions.JsonReader import obtain_item_table, obtain_mob_table, obtain_tile_set, obtain_particles, obtain_spells
from MapObjectFunctions import *
from RandomUtils import random_choice_from_dict, spawn_chance
from RenderFunctions import RenderOrder


TILE_SET = obtain_tile_set()
ITEMS = obtain_item_table()
MOBS = obtain_mob_table()
PARTICLES = obtain_particles()
SPELLS = obtain_spells()


def calculate_distance(x1, y1, x2, y2):
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)


def close_room(game_map, room):
    # Sets Tiles in to Become Passable
    for x in range(room.x1, room.x2):
        for y in range(room.y1, room.y2):
            create_wall(game_map, x, y)


def create_walled_room(game_map, room, buffer=0):
    # Sets Tiles in to Become Passable, but add walls around
    for x in range(room.x1, room.x2):
        for y in range(room.y1, room.y2):
            if x == room.x1 or x == room.x2 - buffer or y == room.y1 or y == room.y2 - buffer:
                create_wall(game_map, x, y)
            else:
                create_floor(game_map, x, y)


def create_room(game_map, room):
    # Sets Tiles in to Become Passable
    for x in range(int(room.x1) + 1, int(room.x2) - 1):
        for y in range(int(room.y1) + 1, int(room.y2) - 1):
            create_floor(game_map, x, y)


def create_hall(game_map, room1, room2):
    x1, y1 = room1.center
    x2, y2 = room2.center
    # x1, y1 = room1.x + room1.width // 2, room1.y + room1.height // 2
    # x2, y2 = room1.x + room1.width // 2, room2.y + room2.height // 2

    # Note: Unless the Rooms are physically touching, they overlap either Horizontally or Vertically, not both.

    # Check if Room 1 Overlaps Room 2 Horizontally
    # print('Check if Room 1 Overlaps Room 2 Horizontally')
    # for x in range(room1.x1, room1.x2 - 1):
    #     if room2.x1 < x < room2.x2:
    #         create_v_tunnel(game_map, y1, y2, x1)
    #         return None

    # Check if Room 1 Overlaps Room 2 Vertically
    # print('Check if Room 1 Overlaps Room 2 Vertically')
    # for y in range(room1.y1 + 1, room1.y2 - 1):
    #     if room2.y1 < y < room2.y2:
    #         create_h_tunnel(game_map, x1, x2, y1)
    #         return None

    if randint(0, 1) == 1:
        create_h_tunnel(game_map, x1, x2, y1)
        create_v_tunnel(game_map, y1, y2, x2)
    else:  # else it starts vertically
        create_v_tunnel(game_map, y1, y2, x1)
        create_h_tunnel(game_map, x1, x2, y2)


def create_h_tunnel(game_map, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        create_floor(game_map, x, y)


def create_v_tunnel(game_map, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        create_floor(game_map, x, y)


def create_floor(game_map, x, y):
    # Open (1) Tile
    # floor = TILE_SET['2']
    # game_map.transparent[y][x] = floor.get("transparent")
    # game_map.walkable[y][x] = floor.get("walkable")
    # game_map.tiles[y][x] = floor.get("char")  # "."
    place_tile(game_map, x, y, '2')


def create_wall(game_map, x, y):
    place_tile(game_map, x, y, '1')


def place_tile(game_map, x, y, obj):
    # Places Tile
    tile = TILE_SET.get(str(obj))
    game_map.transparent[y][x] = tile.get('transparent')
    game_map.fov[y][x] = tile.get('fov')
    game_map.walkable[y][x] = tile.get('walkable')
    game_map.tileset_tiles[y][x] = int(obj)
    game_map.tile_cost[y][x] = tile.get('tile_cost')


def find_wall_direction(room_from, room_to):
    directions = []
    x1, y1 = room_from.center
    x2, y2 = room_to.center

    if x1 < x2:
        directions.append('west')
    elif x1 > x2:
        directions.append('east')

    if y1 < y2:
        directions.append('north')
    elif y1 > y2:
        directions.append('south')

    if not directions:
        return None
    return choice(directions)


def create_door(game_map, sub_room, main_room):
    # Create a Single Opening at a Select Rectangle Wall
    direction = find_wall_direction(sub_room, main_room)
    x_door, y_door = sub_room.center
    if direction == 'south':
        x_door = (sub_room.x1 + 1 + sub_room.x2) // 2
        y_door = sub_room.y1 + 1
    elif direction == 'north':
        x_door = (sub_room.x1 - 1 + sub_room.x2) // 2
        y_door = sub_room.y2 - 1
    elif direction == 'east':
        x_door = sub_room.x1 + 1
        y_door = (sub_room.y1 + 1 + sub_room.y2) // 2
    elif direction == 'west':
        x_door = sub_room.x2 - 1
        y_door = (sub_room.y1 - 1 + sub_room.y2) // 2
    else:
        print('\n\nno door was created???')
        print('main_room:', main_room.center)
        print('sub_room:', sub_room.center)
    # create_hall(game_map, sub_room, main_room)
    # create_floor(game_map, x_door, y_door)
    return x_door, y_door


def generate_mob(x, y, mob_stats, mob_index, encounter_group, faction, ai, entities, dialogue_component=None,
                 follow_entity=None, target_entity=None, origin_x=None, origin_y=None):

    faction_component = Faction(faction_name=faction)
    inventory_component = Inventory(3)
    equipment_component = Equipment()

    fighter_component = Fighter(hp=mob_stats.get('hp'), defense=mob_stats.get('def'),
                                power=mob_stats.get('att'), xp=mob_stats.get('xp'), fov_range=mob_stats.get('fov_range'),
                                mob_level=mob_stats.get('mob_level'), attack_range=mob_stats.get('attack_range', 0.99))

    # Check if Mob Has Skills or Spells
    spells = mob_stats.get("spells", None)
    if spells:
        spell_data_list = []
        for spell_name in spells:
            spell_data_list.append(SPELLS.get(spell_name))
        spellcaster_component = SpellCaster(spell_data=spell_data_list)
    else:
        spellcaster_component = None

    if origin_x and origin_y:
        ai_component = ai(encounter=encounter_group, origin_x=origin_x, origin_y=origin_y, follow_entity=follow_entity,
                          target_entity=target_entity)
    else:
        ai_component = ai(encounter=encounter_group, origin_x=x, origin_y=y, follow_entity=follow_entity,
                          target_entity=target_entity)

    position_component = Position(x, y)
    mob_entity = Entity(mob_stats.get('glyph'), mob_stats.get('color'), mob_stats.get('name'), mob_index, position=position_component,
                        blocks=True, fighter=fighter_component, render_order=RenderOrder.ACTOR,
                        ai=ai_component, faction=faction_component, equipment=equipment_component,
                        inventory=inventory_component, spellcaster=spellcaster_component, dialogue=dialogue_component)

    # Add/Equip Inventory
    mob_inventory = mob_stats.get("inventory", [])
    for item_index in mob_inventory:
        # print('\ntem_index:', item_index)
        item_entity = create_item_entity(item_index)
        mob_entity.inventory.add_item(item_entity)
        # print(item_entity.name)
        if item_entity.equippable:
            mob_entity.equipment.toggle_equip(item_entity)
        # print('mob inventory:')
        # for entity in mob_entity.inventory.items:
        #     print('\t%s'  % entity.name)

    if isinstance(ai_component, PatrolAI):
        mob_entity.ai.goal_x = x
        mob_entity.ai.goal_y = y

    return mob_entity


def generate_object(x, y, entities, map_objects, particles, game_map, object_stats, object_index, item_list=None,
                    no_inventory=True):

    # Create an Object that has an "Interact" and "Wait" functions
    # _entities = [entity for entity in entities + map_objects if entity.position]
    if not any([entity for entity in entities + map_objects if entity.position.x == x and entity.position.y == y]) and \
            game_map.is_within_map(x, y) and not game_map.is_blocked(x, y):

        inventory = object_stats.get('inventory')
        inventory_component = None

        # Create Inventory
        # TODO: Check if Item Entities have been moved to their own list in Engine.py(not yet)
        if inventory or not no_inventory:
            inventory_component = Inventory(object_stats.get('inventory_capacity'))
            number_of_items = object_stats.get('inventory_capacity')

            # Check if Pre-defined items
            if item_list and no_inventory:
                # Spawn Items in Full View through Part of the Inventory
                for item in item_list:
                    if item.position:
                        item.position.x = x
                        item.position.y = y
                    entities.append(item)
                    inventory_component.add_item(item)
            elif not no_inventory and item_list:
                for item in item_list:
                    inventory_component.add_item(item)

            elif not no_inventory:
                inventory_component.items = _generate_random_items(number_of_items, game_map.dungeon_level)

        # Check for Particle Attached to Tile Object
        particle_index = object_stats.get('particle')
        if particle_index:
            particle_entity = generate_particle(x, y, particle_index)
            particles.append(particle_entity)

        movable = object_stats.get('moveable')
        breakable = object_stats.get('breakable')
        walkable = object_stats.get('walkable')
        properties = object_stats.get('properties')
        # items=[], movable=False, breakable=False, walkable=False, interact_function
        map_object_component = MapObject(name=object_stats.get('name'), movable=movable, breakable=breakable,
                                         walkable=walkable, properties=properties,
                                         interact_function=eval(object_stats.get('interact_function', "no_function")),
                                         wait_function=eval(object_stats.get("wait_function", "no_function")))
        position_component = Position(x, y)
        map_object_entity = Entity(object_stats.get('glyph'), object_stats.get('color'), object_stats.get('name'),
                                   json_index=object_index, position=position_component, render_order=RenderOrder.ITEM, furniture=map_object_component,
                                   inventory=inventory_component)
        # TODO: Directly Add to Game Map, might have to change
        game_map.map_objects.append(map_object_entity)
        place_tile(game_map, x, y, object_index)
        return map_object_entity


def _generate_random_items(number_of_items, dungeon_level):
    # Create Item Entities
    item_entities = []
    item_chances = {item: spawn_chance([[item_stats.get('spawn_chance'), item_stats.get('item_level')]],
                                       dungeon_level) for item, item_stats in ITEMS.items() if not item_stats.get('unique', False)
                    }

    # Generate Random Number of Items
    for i in range(number_of_items):
        # Randomly Select an Item to Spawn
        item_index = random_choice_from_dict(item_chances)
        item_stats = ITEMS[item_index]

        if item_stats.get('type') == 'consumable':
            item_component = Item(use_function=eval(item_stats.get('use_function', "nothing")),
                                  amount=item_stats.get('amount'),
                                  radius=item_stats.get('radius'),
                                  damage=item_stats.get('damage'),
                                  targeting_message=Message(item_stats.get('targeting_message')),
                                  targeting=item_stats.get('targeting'),
                                  maximum_range=item_stats.get('range'),
                                  targeting_type=item_stats.get('targeting_type'),
                                  description=item_stats.get('description')
                                  )

            item_entity = Entity(item_stats.get('glyph'), item_stats.get('color'), item_stats.get('name'),
                                 item_index, render_order=RenderOrder.ITEM, item=item_component)

        elif item_stats.get('type') == 'reuseable':
            item_component = Item(use_function=eval(item_stats.get('use_function', "nothing")), name=item_stats.get('name'),
                                  text=item_stats.get('text'), description=item_stats.get('description'))

            item_entity = Entity(item_stats.get('glyph'), item_stats.get('color'), item_stats.get('name'),
                                 item_index, render_order=RenderOrder.ITEM, item=item_component,
                                 )

        elif item_stats.get('type') == 'equip':
            equippable_component = Equippable(item_stats.get('slot'), power_bonus=item_stats.get('attack', 0),
                                              defense_bonus=item_stats.get('defense', 0),
                                              max_hp_bonus=item_stats.get('hp', 0),
                                              description=item_stats.get('description')
                                              )

            item_entity = Entity(item_stats.get('glyph'), item_stats.get('color'), item_stats.get('name'),
                                 item_index, equippable=equippable_component)
        item_entities.append(item_entity)


    return item_entities


def generate_objects(entities, map_objects, game_map, room, number_of_objects, object_chances, object_table):
    object_list = []
    for i in range(number_of_objects):
        x, y = room.obtain_point_within(2)

        if not any([entity for entity in entities + map_objects if entity.position.x == x and entity.position.y == y]) and \
                game_map.is_within_map(x, y) and not game_map.is_blocked(x, y):

            # Randomly Select an Object to Spawn
            object_index = random_choice_from_dict(object_chances)
            object_stats = object_table[object_index]

            # Inventory/Items Contained Within
            inventory = object_stats.get('inventory')
            inventory_component = None
            if inventory:
                inventory_component = Inventory(26)
                inventory_component.items = _generate_random_items()

                # for item in inventory_component.items:
                #     entities.append(item)


            # Interactable
            movable = object_stats.get('moveable')
            breakable = object_stats.get('breakable')
            walkable = object_stats.get('walkable')
            properties = object_stats.get('properties')
             # items=[], movable=False, breakable=False, walkable=False, interact_function
            furniture_component = MapObject(name=object_stats.get('name'), movable=movable,
                                            breakable=breakable, walkable=walkable, properties=properties,
                                            interact_function=eval(object_stats.get('interact_function')))
            position_component = Position(x, y)
            object_entity = Entity(object_stats.get('glyph'), object_stats.get('color'), object_stats.get('name'),
                                   json_index=object_index, position=position_component, render_order=RenderOrder.ITEM, furniture=furniture_component,
                                   inventory=inventory_component)

            map_objects.append(object_entity)
            object_list.append(object_entity)

    return object_list


def place_stairs(game_map, dungeon_level, x, y):
    object_index = "11"
    object_stats = TILE_SET.get(object_index)

    movable = object_stats.get('moveable')
    breakable = object_stats.get('breakable')
    walkable = object_stats.get('walkable')
    properties = object_stats.get('properties')

    position_component = Position(x, y)
    map_object_component = MapObject(name=object_stats.get('name'), movable=movable, breakable=breakable,
              walkable=walkable, properties=properties,
              interact_function=eval(object_stats.get('interact_function', "no_function")),
              wait_function=eval(object_stats.get("wait_function", "no_function")))

    stairs_entity = Entity(object_stats.get("char"), object_stats.get("color"), object_stats.get("name"),
                           furniture=map_object_component, json_index=object_index, position=position_component,
                           render_order=RenderOrder.STAIRS, stairs=Stairs(dungeon_level + 1))
    game_map.map_objects.append(stairs_entity)
    place_tile(game_map, x, y, object_index)
    game_map.stairs = stairs_entity


def place_prefab(game_map, prefab, entities, particles, dungeon_level, item_on_top=False, item_list=None):

    i = 0
    for x in range(prefab.x, prefab.x + prefab.width):
        for y in range(prefab.y, prefab.y + prefab.height):

            map_object = prefab.template[i]
            object_stats = TILE_SET.get(str(map_object))
            if object_stats.get('interact_function'):
                item_entities = []
                if item_on_top:
                    item_chances = {item: spawn_chance([[item_stats.get('spawn_chance'), item_stats.get('item_level')]],
                                                       dungeon_level) for item, item_stats in ITEMS.items() if
                                    not item_stats.get('unique', False)
                                    }
                    item_index = random_choice_from_dict(item_chances)
                    item_list = [item_index]
                    item_json_index = choice(item_list)
                    item_entity = create_item_entity(item_json_index, x, y)
                    item_entities.append(item_entity)

                generate_object(x, y, entities, game_map.map_objects, particles, game_map, object_stats, map_object,
                                item_list=item_entities, no_inventory=False)

            else:
                place_tile(game_map, x, y, map_object)
            i += 1


# **********************************************************************************************************************
# General Generation Functions


def create_item_entity(item_index, x=None, y=None):
    item_stats = ITEMS.get(item_index)
    if x and y:
        position_component = Position(x, y)
    else:
        position_component = None

    # Assemble an Item Entity with it's Required Components
    if item_stats.get('type') == 'consumable':
        item_component = Item(use_function=eval(item_stats.get('use_function', "nothing")),
                              amount=item_stats.get('amount'),
                              radius=item_stats.get('radius'),
                              damage=item_stats.get('damage'),
                              targeting_message=Message(item_stats.get('targeting_message')),
                              targeting=item_stats.get('targeting'),
                              maximum_range=item_stats.get('range'),
                              targeting_type=item_stats.get('targeting_type'),
                              description=item_stats.get('description')
                              )

        item_entity = Entity(item_stats.get('glyph'), item_stats.get('color'), item_stats.get('name'),
                             json_index=item_index, position=position_component, render_order=RenderOrder.ITEM,
                             item=item_component)

    elif item_stats.get('type') == 'reuseable':
        item_component = Item(use_function=eval(item_stats.get('use_function', "nothing")), name=item_stats.get('name'),
                              text=item_stats.get('text'), description=item_stats.get('description'))

        item_entity = Entity(item_stats.get('glyph'), item_stats.get('color'), item_stats.get('name'),
                             position=position_component, json_index=item_index, render_order=RenderOrder.ITEM,
                             item=item_component,
                             )

    elif item_stats.get('type') == 'equip':
        equippable_component = Equippable(item_stats.get('slot'), power_bonus=item_stats.get('attack', 0),
                                          defense_bonus=item_stats.get('defense', 0),
                                          max_hp_bonus=item_stats.get('hp', 0),
                                          description=item_stats.get('description')
                                          )

        item_entity = Entity(item_stats.get('glyph'), item_stats.get('color'), item_stats.get('name'),
                             position=position_component, render_order=RenderOrder.ITEM, json_index=item_index,
                             equippable=equippable_component)
    else:
        print('Item Name: %s, Item type: %s isn\'t a suitable item type! Double check ./assets/item.json' %
              (item_stats.get('name'), item_stats.get('type')))
        raise ValueError

    return item_entity


def generate_items(entities, game_map, room, number_of_items, item_chances, item_table):
    item_list = []
    for i in range(number_of_items):
        x, y = room.obtain_point_within(2)

        # Ensure another Entity doesn't already Exist in same coordinates
        # _entities = [entity for entity in entities if entity.position]
        try:
            if not any([entity for entity in entities if entity.position.x == x and entity.position.y == y]) and \
                    game_map.is_within_map(x, y) and not game_map.is_blocked(x, y):

                # Randomly Select an Item to Spawn
                item_index = random_choice_from_dict(item_chances)
                item_entity = create_item_entity(item_index, x, y)

                item_list.append(item_entity)
                entities.append(item_entity)
        except AttributeError as e:
            import traceback
            print('\n\n')
            print(traceback.format_exc())
            for e in entities:
                print(e)

            # file_name =
            # with

    return item_list


def create_mob_entity(x, y, mob_index, encounter, ai_type=AI, faction_name="Mindless"):
    mob_stats = MOBS.get(mob_index)
    faction_component = Faction(faction_name=faction_name)
    fighter_component = Fighter(hp=mob_stats.get('hp'), defense=mob_stats.get('def'),
                                power=mob_stats.get('att'), xp=mob_stats.get('xp'), fov_range=mob_stats.get('fov_range'),
                                mob_level=mob_stats.get('mob_level'))
    ai_component = ai_type(encounter=encounter, origin_x=x, origin_y=y)
    position_component = Position(x, y)
    mob_entity = Entity(mob_stats.get('glyph'), mob_stats.get('color'), mob_stats.get('name'), json_index=mob_index,
                        position=position_component, blocks=True, fighter=fighter_component,
                        render_order=RenderOrder.ACTOR, ai=ai_component, faction=faction_component)
    return mob_entity


def generate_particle(x, y, particle_index):
    p_stats = PARTICLES.get(particle_index)
    p_name = p_stats.get("name")
    p_lifetime = p_stats.get("lifetime")
    p_char = p_stats.get("glyph")
    p_fg = p_stats.get("fg")
    p_bg = p_stats.get("bg")
    p_propagate = p_stats.get("propagate", False)
    p_propagate_property = p_stats.get("propagate_property", None)
    p_forever = p_stats.get("forever", False)
    position_component = Position(x=x, y=y)
    particle_component = Particle(lifetime=p_lifetime, char=p_char, fg=p_fg, bg=p_bg, forever=p_forever,
                                      propagate=p_propagate, propagate_property=p_propagate_property)
    particle_entity = Entity(char=p_char, color=p_fg, name=p_name, json_index=particle_index,
                             position=position_component, particle=particle_component,
                             render_order=RenderOrder.PARTICLE)

    return particle_entity


def generate_mobs(entities, game_map, number_of_mobs, mobs, monster_chances, encounter, room=None, x=None, y=None):

    monster_list = []
    MOBS = mobs
    for i in range(number_of_mobs):
        # Choose A Random Location Within the Room
        if room:
            x, y = room.obtain_point_within(2)


        # Ensure another Entity doesn't already Exist in same coordinates
        # _entities = [entity for entity in entities if entity.position]
        try:
            if not any([entity for entity in entities if entity.position.x == x and entity.position.y == y]) and \
                    game_map.is_within_map(x, y) and not game_map.is_blocked(x, y):

                mob_index = random_choice_from_dict(monster_chances)
                mob_stats = MOBS.get(mob_index)
                faction = "Mindless"
                ai = AI
                mob_entity = generate_mob(x, y, mob_stats, mob_index, encounter, faction, ai, entities)

                entities.append(mob_entity)
                monster_list.append(mob_entity)
        except:
            print(entities)

    return monster_list


def place_entities(game_map, dungeon_level, room, entities, item_table, mob_table):

    # Get a Random Number of Monsters
    max_monsters_per_room = spawn_chance([[2, 1], [3, 4], [5, 6]], dungeon_level)
    max_items_per_room = spawn_chance([[1, 1], [2, 4]], dungeon_level)

    # number_of_mobs = 1
    number_of_mobs = randint(1, max_monsters_per_room)

    number_of_items = randint(0, max_items_per_room)

    monster_chances = {mob: spawn_chance([stats for stats in mob_stats.get('spawn_chance')], dungeon_level)
                       for mob, mob_stats in mob_table.items()
                       }
    # object_chances = {object: spawn_chance([[object_stats.get('spawn_chance'), object_stats.get('item_level')]],
    #                                    dungeon_level) for object, object_stats in object_table.items()
    #                 }

    item_chances = {item: spawn_chance([[item_stats.get('spawn_chance'), item_stats.get('item_level')]],
                                       dungeon_level) for item, item_stats in item_table.items() if not item_stats.get("unique", False)
                    }

    # print('Number of Items:', number_of_items)
    # print('Number of Monsters:', number_of_mobs)
    # For debug use, view loot table
    game_map.spawn_chances = {'mobs': monster_chances, 'items': item_chances}

    # Initiate Encounter
    # pop = [DefensiveAI]
    pop = [AI, DefensiveAI, PatrolAI]
    # weights = [100]
    weights = [33, 33, 33]
    encounter_type = choices(population=pop,
                             weights=weights,
                             k=1)[0]
    encounter = Encounter(game_map, room, len(game_map.encounters) + 1)

    # Generate Prefabs
    # furniture_list = generate_objects(entities, game_map.map_objects, game_map, room, 5, object_chances, object_table)

    # Generate Monsters
    # def generate_mobs(entities, game_map, number_of_mobs, mobs, monster_chances, encounter, room=None, x=None, y=None):
    encounter.mob_list = generate_mobs(entities, game_map, number_of_mobs, mob_table, monster_chances, encounter, room=room)
    # Generate Items
    item_list = generate_items(entities, game_map, room, number_of_items, item_chances, item_table)
    encounter.item_list = item_list

    # Group Created Monsters and Items into a Single Encounter
    game_map.encounters.append(encounter)
