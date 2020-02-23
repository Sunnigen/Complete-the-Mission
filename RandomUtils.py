from random import randint


def random_choice_index(chances):
    random_chance = randint(1, sum(chances))

    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w

        if random_chance <= running_sum:
            return choice
        choice += 1


def random_choice_from_dict(choice_dict):
    choices = list(choice_dict.keys())
    chances = list(choice_dict.values())

    return choices[random_choice_index(chances)]


def spawn_chance(table, dungeon_level):
    """
    :param table:  [drop chance percentage, item level]
    :param dungeon_level: if item level is within dungeon level, permissible to spawn
    :return:  drop chance percentage, will return 0 if dungeon level not high enough
    """
    # Table can be (1) list of values, or list of list of values to change the spawn rate per level
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0
