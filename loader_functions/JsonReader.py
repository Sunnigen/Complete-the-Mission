import json
import os


def obtain_mob_table():
    mob_file = "%s\\assets\\mobs.json" % os.getcwd()
    if not os.path.isfile(mob_file):
        print('Cannot find %s!!!' % mob_file)
        raise FileNotFoundError

    with open(mob_file, "r") as read_file:
        mob_table = json.load(read_file)

    # print('mob_table:', mob_table)
    return mob_table


def obtain_item_table():
    item_file = "%s\\assets\\items.json" % os.getcwd()
    if not os.path.isfile(item_file):
        print('Cannot locate %s!!!' % item_file)
        raise FileNotFoundError

    with open(item_file, "r") as read_file:
        item_table = json.load(read_file)

    # print('item_table:', item_table)
    return item_table


def obtain_tile_set(key_word=''):
    tile_set_file = "%s\\assets\\tile_set.json" % os.getcwd()

    if not os.path.isfile(tile_set_file):
        print('Cannot locate %s!!!' % tile_set_file)
        raise FileNotFoundError

    with open(tile_set_file, "r") as read_file:
        tile_set_table = json.load(read_file)

    # print('item_table:', item_table)
    return tile_set_table
