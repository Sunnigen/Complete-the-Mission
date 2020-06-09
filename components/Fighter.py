import tcod as libtcod


from GameMessages import Message


class Fighter:
    def __init__(self, hp, defense, power, xp=0, fov=2, mob_level=None):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.god_mode = 0
        self.fov = fov
        self.mob_level = mob_level

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
        self.hp = max(0, self.hp - amount)

        # Entity has Died!
        if self.hp <= 0:
            if self.xp != 0:
                results.append({'dead': self.owner, 'xp': self.xp})
            else:
                results.append({'dead': self.owner})
        return results

    def heal(self, amount):
        self.hp += amount

        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def attack(self, target):
        results = []

        # TODO: Proper God Mode will have increase att, def and HP shown and references in combat logs.
        if target.fighter.god_mode > 0:
            damage = 0
            # results.append({'message': Message('The attack did nothing to the %s.' % self.owner.name)})
        else:
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

    def interact(self, entity, **kwargs):
        results = []
        map_object_component = entity.map_object

        if map_object_component:
            # Pass Specific Kwargs to "Furniture" Class
            """
            Note:
            """
            kwargs = {**map_object_component.function_kwargs, **kwargs}

            # Process map object's "interact_function"
            map_use_results = map_object_component.interact_function(self.owner, entity, **kwargs)
            results.extend(map_use_results)

        return results
