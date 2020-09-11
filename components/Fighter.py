import tcod
from GameMessages import Message


class Fighter:
    owner = None

    def __init__(self, hp, defense, power, attack_range=0.99, xp=0, fov_range=2, is_player=False, mob_level=None):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.god_mode = 0
        self.fov_range = fov_range
        self.attack_range = attack_range
        self.mob_level = mob_level

        self.is_player = is_player

        # self.curr_fov = set()  # set containing coordinates of what fighter can actually see
        self.curr_fov_map = []  # numpy 2d array of what fighter can actually see

        # Stats
        self.str = 0
        self.dex = 0
        self.agi = 0
        self.wis = 0
        self.int = 0
        self.con = 0
        
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

    def take_damage(self, amount, attacking_entity=None):
        results = []
        self.hp = max(0, self.hp - amount)

        # Entity has Died!
        if self.hp <= 0:
            if self.xp != 0:
                results.append({'dead': self.owner, 'xp': [self.xp, attacking_entity]})
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

            # Check Critical Hit from Not in FOV
            critical_hit_mod = 1 + (self.is_player * 3 * ((self.owner.position.y, self.owner.position.x) not in target.fighter.curr_fov_map))
            damage = (self.power - target.fighter.defense) * critical_hit_mod

        if damage > 0:
            results.append({'message': Message('%s attacks %s for %s hit points.' % (
                self.owner.name.capitalize(), target.name, str(damage)), tcod.white), "spawn_particle": ["hit", target.position.x, target.position.y, None]})
            results.extend(target.fighter.take_damage(damage, self.owner))
        else:
            # print('%s attacks %s, but does no damage.' % (self.owner.name.capitalize(), target.name))
            results.append({'message': Message('%s attacks %s, but does no damage!' % (
                self.owner.name.capitalize(), target.name), tcod.white)})

        return results

    def interact(self, entity, interact_type='move', **kwargs):
        results = []
        map_object_component = entity.map_object

        if map_object_component:
            # Pass Specific Kwargs to "Map Object" Class
            """
            Note:
            """
            kwargs = {**map_object_component.function_kwargs, **kwargs}
            map_use_results = []
            # Process map object's "interact_function"

            if interact_type == 'move':
                map_use_results = map_object_component.interact_function(self.owner, entity, **kwargs)
            elif interact_type == 'wait':
                map_use_results = map_object_component.wait_function(self.owner, entity, **kwargs)
            results.extend(map_use_results)

        return results
