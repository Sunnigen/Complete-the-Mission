import tcod as libtcod

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


def empty_chest(*args, **kwargs):
    results = []

    results.append({'chest': False, 'message': Message('The chest is already been opened.', libtcod.yellow)})

    return results


def open_chest(*args, **kwargs):
    chest = args[1]
    chest_inventory = chest.inventory
    target_inventory = kwargs.get('target_inventory')
    results = []

    results.append({'chest': chest, 'message': Message('You open the chest...', libtcod.yellow)})
    # Transfer Chest Inventory to Target Inventory
    if chest_inventory:
        # print('Chest Items:', chest_inventory.items)
        while chest_inventory.items:
            # Check if Target Inventory is Full
            if len(target_inventory.items) >= target_inventory.capacity:
                results.append({'message': Message('You cannot carry any more, your inventory is full!', libtcod.yellow)})
                # results.append({'message': Message('You close the chest.', libtcod.yellow)})
                break
            item = chest_inventory.items.pop()
            results.extend(target_inventory.add_item(item))

        # Change to Open-Chest
        chest.char = 224
        # game_map.tileset_tiles[y][x]

    return results


def next_floor(*args, **kwargs):
    results = []

    return results
