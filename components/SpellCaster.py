from SpellFunctions import *


class Spell:
    type = None
    name = ''
    cost = 0
    cost_type = None
    cool_down = 0
    cool_down_timer = 0
    active = True

    def __init__(self, description=None, spell_function=None, targeting=False, targeting_message=None, **kwargs):
        self.description = description
        self.spell_function = spell_function
        self.targeting = targeting
        self.targeting_message = targeting_message
        self.function_kwargs = kwargs
        self.active = False

    def __repr__(self):
        return "{}".format(self.function_kwargs)


class SpellCaster:
    owner = None

    def __init__(self, spell_data):
        self.spells = []
        if spell_data:
            for spell in spell_data:
                self.spells.append(Spell(description=spell.get("description"),
                                         spell_function=eval(spell.get("spell_function", "no_spell")),
                                         targeting=spell.get("targeting"),
                                         targeting_message=spell.get("targeting_message"),
                                         name=spell.get("name"),
                                         cool_down=spell.get("cool_down", 0),
                                         cost=spell.get("cost", 0),
                                         value=spell.get("value", 0),
                                         range=spell.get("range", 0))
                                   )

    def __repr__(self):
        s = '{} skills/spells'.format(len(self.spells))

        for spell in self.spells:
            s += '\n\t{}'.format(spell)
        return s

    def has_specific_spell(self, specific_spell):
        for spell in self.spells:
            if spell.spell_function == specific_spell:
                return True
        return False

    @property
    def has_spells(self):
        return False
        # return len(self.spells) > 0

    def cast(self, spell, **kwargs):
        return spell(kwargs)

    # def check_cost(self, spell):
    #     return

    def check_cool_down(self, spell):
        return spell.cool_down_timer == 0
