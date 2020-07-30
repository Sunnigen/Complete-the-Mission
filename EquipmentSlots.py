from enum import Enum


class EquipmentSlots(Enum):
    MAIN_HAND = 1
    OFF_HAND = 2
    HEAD = 3
    CHEST = 4
    LEGS = 5
    FEET = 6
    HANDS = 7
    TRINKET_1 = 8
    TRINKET_2 = 9


EQUIPMENT_SLOT_NAME = {EquipmentSlots.MAIN_HAND: 'on main hand',
                       EquipmentSlots.OFF_HAND: 'on off hand',
                       EquipmentSlots.HEAD: 'on the head',
                       EquipmentSlots.CHEST: 'on the chest',
                       EquipmentSlots.LEGS: 'on the legs',
                       EquipmentSlots.FEET: 'on the feet',
                       EquipmentSlots.HANDS: 'on the hands',
                       EquipmentSlots.TRINKET_1: 'your 1st trinket',
                       EquipmentSlots.TRINKET_2: 'your 2nd trinket'
                       }