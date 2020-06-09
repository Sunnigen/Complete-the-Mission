import tcod

from GameMessages import Message


def unlock(*args, **kwargs):
    results = []

    return results


def nothing(*args, **kwargs):
    results = []

    return results


def push(*args, **kwargs):
    results = []

    return results


def break_box(*args, **kwargs):
    print('break_box')
    results = [{'box': False, 'message': Message('You attempt to break open the box...', tcod.yellow)}]
    results.append({'message': Message('But you\'re not strong enough!', tcod.darker_yellow)})
    return results


def empty_chest(*args, **kwargs):
    print('empty_chest')
    results = []
    results.append({'chest': False, 'message': Message('The chest is already been opened.', tcod.yellow)})
    return results


def open_gate(*args, **kwargs):
    print('open_gate')
    results = []
    results.append({'message': Message('A locked jail gate blocks your way...', tcod.yellow)})
    return results


def table_pick_up(*args, **kwargs):
    print('table_pick_up')
    results = []
    results.append({'message': Message('You look on the table for anything good. You find nothing...', tcod.yellow)})
    return results


def open_chest(*args, **kwargs):
    print('open_chest')
    chest = args[1]
    chest_inventory = chest.inventory
    target_inventory = kwargs.get('target_inventory')
    results = []

    results.append({'chest': chest, 'message': Message('You open the chest...', tcod.yellow)})
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

        # Change to Open-Chest
        chest.char = 224
        # game_map.tileset_tiles[y][x]

    return results


def next_floor(*args, **kwargs):
    print('next_floor')
    results = []

    return results
