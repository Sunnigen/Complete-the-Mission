import tcod as libtcod


from GameMessages import Message


class Fighter:
    def __init__(self, hp, defense, power, xp=0, fov=2):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.god_mode = 0
        self.fov = fov

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

    def interact(self, entity, **kwargs):
        # Process through Map Object's Use Function
        # inventory = entity.inventory
        print('\ninteract')
        # print('map_object:', map_object)
        # print('map_object name:', map_object.name)
        # print('map_object char:', map_object.char)
        # print('kwargs:', kwargs)
        # if inventory:
        #     print('inventory items:', inventory.items)
        #     for item in inventory.items:
        #         print(item.name)
        # else:
        #     print('no inventory :(')
        results = []
        map_object_component = entity.map_object

        if map_object_component:
            # Pass Specific Kwargs to "Furniture" Class
            """
            Note:
            """
            kwargs = {**map_object_component.function_kwargs, **kwargs}

            # Process "interact_function"
            map_use_results = map_object_component.interact_function(self.owner, entity, **kwargs)
            results.extend(map_use_results)

        return results
