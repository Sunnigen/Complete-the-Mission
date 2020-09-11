from components.Item import Item
from ItemFunctions import *
from RenderFunctions import RenderOrder


class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """
    def __init__(self, char, color, name, json_index, position=None, blocks=False, render_order=RenderOrder.CORPSE,
                 fighter=None, spellcaster=None, ai=None, item=None, inventory=None, stairs=None, level=None, equipment=None,
                 equippable=None, furniture=None, faction=None, particle=None, dialogue=None):
        # Required Components
        # self.x = x
        # self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.json_index = json_index

        # "Optional" Components
        self.position = position
        self.blocks = blocks
        self.render_order = render_order
        self.fighter = fighter
        self.spellcaster = spellcaster
        self.ai = ai
        self.item = item
        self.inventory = inventory
        self.stairs = stairs
        self.level = level
        self.equipment = equipment
        self.equippable = equippable
        self.map_object = furniture
        self.faction = faction
        self.particle = particle
        self.dialogue = dialogue

        if self.faction:
            self.faction.owner = self

        if self.fighter:
            self.fighter.owner = self

        if self.spellcaster:
            self.spellcaster.owner = self

        if self.ai:
            self.ai.owner = self

        if self.item:
            self.item.owner = self

        if self.inventory:
            self.inventory.owner = self

        if self.stairs:
            self.stairs.owner = self

        if self.level:
            self.level.owner = self

        if self.equipment:
            self.equipment.owner = self

        if self.equippable:
            self.equippable.owner = self

            # Every equipment picked up is an item and gets added to inventory
            #   therefore needs to be defined as an Item()
            if not self.item:
                item = Item()
                self.item = item
                self.item.owner = self

        if self.map_object:
            self.map_object.owner = self

        if self.particle:
            self.particle.owner = self

        if self.position:
            self.position.owner = self

        if self.dialogue:
            self.dialogue.owner = self

    def change_entity(self, tile_data, json_index):
        # print('change_map_object')
        if self.map_object:
            self.char = tile_data.get("char")
            self.name = tile_data.get("name")
            self.color = tile_data.get("color")
            self.json_index = json_index

            # Update MapObject Class
            self.map_object.update(tile_data)

    def __repr__(self):
        return "Entity json_index:{} name:{} position:{} render_order:{}".format(self.json_index, self.name, self.position, self.render_order)