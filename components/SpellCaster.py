from SpellFunctions import *


class Spell:
    type = None  # restorative, buff, offensive, environment
    name = ''
    cost = 0
    current_duration = 0
    max_duration = 1
    cost_type = None  # uses HP, MP, Stamina, Food, money, items, etc.
    current_cool_down = 0
    max_cool_down = 0  # how long it takes(turns) for spell to be available for use again
    active = False  # is the spell currently being used(mostly for duration spells)

    def __init__(self, description=None, spell_function=None, targeting=False, targeting_message=None, **kwargs):
        self.description = description
        self.spell_function = spell_function
        self.targeting = targeting
        self.targeting_message = targeting_message
        self.function_kwargs = kwargs
        self.max_cool_down = kwargs.get("cool_down", 0)
        self.type = kwargs.get("type", 0)

    @property
    def is_ready(self):
        # Check Cool Down Timer and Spell isn't Currently Active
        return True if self.current_cool_down <= 0 and not self.active else False

    def update_cool_down(self, dt=0):
        # Update Cool Down Timer
        self.current_cool_down -= 1

    def update_duration(self, dt=0):
        # Update Cool Down Timer
        self.current_duration -= 1

    def activate(self):
        # Activate Spell and Set Duration Counter
        self.active = True
        self.current_duration = self.max_duration  # set to 1 if instant
        self.current_cool_down = 0

    def deactivate(self):
        # Deactivate Spell and Set Cool Down Counter
        self.active = False
        self.current_cool_down = self.max_cool_down
        self.current_duration = 0

    def update(self, dt=0):
        # Check Cool Down Timer
        if not self.active:
            self.update_cool_down()
            return

        # Check Duration of Spell
        self.update_duration()

        if self.current_duration == 0:
            self.deactivate()

    def __repr__(self):
        return "{}".format(self.function_kwargs)


class SpellCaster:
    owner = None

    def __init__(self, spell_data):
        self.spells = []
        if spell_data:
            for spell in spell_data:
                self.spells.append(Spell(description=spell.get("description"),
                                         spell_function=eval(spell.get("spell_function")),
                                         targeting=spell.get("targeting"),
                                         targeting_message=spell.get("targeting_message"),
                                         name=spell.get("name"),
                                         cool_down=spell.get("cool_down", 0),
                                         type=set(spell.get("type")),
                                         cost=spell.get("cost", 0),
                                         value=spell.get("value", 0),
                                         range=spell.get("range", 0))
                                   )

    def __repr__(self):
        s = '{} skills/spells'.format(len(self.spells))

        for spell in self.spells:
            s += '\n\t{}'.format(spell)
        return s

    def has_spell_type(self, spell_type):
        # Check if Spellcaster has a specific spell type: restorative, offensive, etc.
        # Not elemental
        return True if any([spell.type for spell in self.spells if spell_type in spell.type]) else False

    def has_specific_spell(self, specific_spell):
        # Check if Spellcaster has a specfic spell
        for spell in self.spells:
            if spell.spell_function == specific_spell:
                return True
        return False

    def update_spells(self):
        # Update Spells for Cool Down/Duration
        for spell in self.spells:
            spell.update()

    @property
    def has_spells(self):
        # Return True if Spellcaster has any spells that aren't on cool down and aren't active
        return any([spell.is_ready for spell in self.spells])

    def cast(self, spell, caster, target, **kwargs):
        spell.activate()
        return spell.spell_function(caster=caster, target=target, spell=spell, **kwargs)
