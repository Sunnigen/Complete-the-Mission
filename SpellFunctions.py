import tcod

from GameMessages import Message


def no_spell(*args, **kwargs):
    pass


def cast_mend(*args, **kwargs):
    target = kwargs.get("target")
    caster = kwargs.get("caster")
    spell = kwargs.get("spell")
    heal_amount = spell.function_kwargs.get("value", 0)

    target.fighter.heal(heal_amount)

    if caster != target:
        results = [{'consumed': True, "spawn_particle": ["heal", target.position.x, target.position.y, None],
                    'message': Message('The {} casts mend on {}...'.format(caster.name, target.name), tcod.yellow)}]
    else:
        results = [{'consumed': True, "spawn_particle": ["heal", target.position.x, target.position.y, None],
                    'message': Message('The {} casts mend on itself...'.format(caster.name, target.name), tcod.yellow)}]
    return results


def cast_thorn_spike(*args, **kwargs):
    print('cast_thorn_spike', args, kwargs)

    target = kwargs.get("target")
    caster = kwargs.get("caster")
    spell = kwargs.get("spell")
    heal_amount = spell.function_kwargs.get("value", 0)

    results = []
    return results


def cast_spirit_sight(*args, **kwargs):
    print('cast_spirit_sight', args, kwargs)
    results = []
    return results


def cast_holy_strike(*args, **kwargs):
    print("cast_holy_strike", args, kwargs)
    results = []
    return results


def cast_plague_bite(*args, **kwargs):
    print("cast_plague_bite", args, kwargs)
    results = []
    return results


def cast_plague_touch(*args, **kwargs):
    print("cast_plague_touch", args, kwargs)
    results = []
    return results


def cast_plague_growth(*args, **kwargs):
    print("cast_plague_growth", args, kwargs)
    results = []
    return results


def cast_plague_goblin(*args, **kwargs):
    print("cast_plague_goblin", args, kwargs)
    results = []
    return results
