from EquipmentSlots import EquipmentSlots


class Equipment:
    def __init__(self, main_hand=None, off_hand=None):
        self.main_hand = main_hand
        self.off_hand = off_hand

    @property
    def max_hp_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.max_hp_bonus

        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.max_hp_bonus

        return bonus

    @property
    def power_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.power_bonus

        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.power_bonus

        return bonus

    @property
    def defense_bonus(self):
        bonus = 0

        if self.main_hand and self.main_hand.equippable:
            bonus += self.main_hand.equippable.defense_bonus

        if self.off_hand and self.off_hand.equippable:
            bonus += self.off_hand.equippable.defense_bonus

        return bonus

    def toggle_equip(self, equippable_entity):
        results = []
        slot = eval(equippable_entity.equippable.slot)
        if slot == EquipmentSlots.MAIN_HAND:
            if self.main_hand == equippable_entity:
                # Remove equipped item if same equipped item is selected
                self.main_hand = None
                results.append({'dequipped': equippable_entity})
            else:
                # Remove equipped item
                if self.main_hand:
                    results.append({'dequipped': self.main_hand})

                # Equip new item
                self.main_hand = equippable_entity
                results.append({'equipped': equippable_entity})
        elif slot == EquipmentSlots.OFF_HAND:
            if self.off_hand == equippable_entity:
                # Remove equipped item if same equipped item is selected
                self.off_hand = None
                results.append({'dequipped': equippable_entity})
            else:
                # Remove equipped item
                if self.off_hand :
                    results.append({'dequipped': self.off_hand})

                # Equip new item
                self.off_hand = equippable_entity
                results.append({'equipped': equippable_entity})

        return results