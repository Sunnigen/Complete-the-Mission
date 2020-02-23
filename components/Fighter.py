import tcod as libtcod


from GameMessages import Message


class Fighter:
    def __init__(self, hp, defense, power, xp=0):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.god_mode = 0

    @property
    def max_hp(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.max_hp_bonus
        else:
            bonus = 0

        return self.base_max_hp + bonus

    @property
    def power(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.power_bonus
        else:
            bonus = 0
        return self.base_power + bonus

    @property
    def defense(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.defense_bonus
        else:
            bonus = 0
        return self.base_defense + bonus

    def take_damage(self, amount):
        results = []

        # TODO: Proper God Mode will have increase att, def and HP shown and references in combat logs.
        if self.god_mode > 0:
            return results

        if self.hp - amount < 0:
            self.hp = 0
        else:
            self.hp -= amount

        if self.hp <= 0:
            results.append({'dead': self.owner, 'xp': self.xp})
        return results

    def heal(self, amount):
        self.hp += amount

        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def attack(self, target):
        results = []
        damage = self.power - target.fighter.defense

        if damage > 0:
            results.append({'message': Message('%s attacks %s for %s hit points.' % (
                self.owner.name.capitalize(), target.name, str(damage)), libtcod.white)})
            results.extend(target.fighter.take_damage(damage))
        else:
            # print('%s attacks %s, but does no damage.' % (self.owner.name.capitalize(), target.name))
            results.append({'message': Message('%s attacks %s, but does no damage!' % (
                self.owner.name.capitalize(), target.name), libtcod.white)})

        return results
