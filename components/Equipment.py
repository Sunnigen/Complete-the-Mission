from EquipmentSlots import EquipmentSlots


class Equipment:
    def __init__(self, main_hand=None, off_hand=None, head=None, chest=None, legs=None, feet=None, hands=None,
                 trinket_1=None, trinket_2=None):
        self.equipment_dict = {
            EquipmentSlots.MAIN_HAND: main_hand,
            EquipmentSlots.OFF_HAND: off_hand,
            EquipmentSlots.HEAD: head,
            EquipmentSlots.CHEST: chest,
            EquipmentSlots.LEGS: legs,
            EquipmentSlots.FEET: feet,
            EquipmentSlots.HANDS: hands,
            EquipmentSlots.TRINKET_1: trinket_1,
            EquipmentSlots.TRINKET_2: trinket_2
        }

    @property
    def max_hp_bonus(self):
        bonus = 0

        for equipment in self.equipment_dict.values():
            if equipment:
                bonus += getattr(equipment.equippable, "max_hp_bonus")
        return bonus

    @property
    def power_bonus(self):
        bonus = 0

        for equipment in self.equipment_dict.values():
            if equipment:
                bonus += getattr(equipment.equippable, "power_bonus")

        return bonus

    @property
    def defense_bonus(self):
        bonus = 0

        for equipment in self.equipment_dict.values():
            if equipment:
                bonus += getattr(equipment.equippable, "defense_bonus")

        return bonus

    def toggle_equip(self, equippable_entity):
        results = []
        slot = eval(equippable_entity.equippable.slot)  # eval because equipment slot function is stored as string

        if self.equipment_dict[slot] == equippable_entity:
            # Remove equipped item if same equipped item is selected
            self.equipment_dict[slot] = None
            results.append({'dequipped': equippable_entity})
        else:
            # Remove equipped item
            if self.equipment_dict[slot]:
                results.append({'dequipped': self.equipment_dict[slot]})

            # Equip new item
            self.equipment_dict[slot] = equippable_entity
            results.append({'equipped': equippable_entity})

        return results
