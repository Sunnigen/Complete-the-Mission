import tcod as libtcod

from components.Position import Position

from GameMessages import Message


class Inventory:
    def __init__(self, capacity, items=None):
        # Default argument of [] is mutable! Meaning it will save it's state between function calls.
        self.capacity = capacity
        if not items:
            self.items = []
        else:
            self.items = items

    def check_item_by_index(self, item_json_index):
        # Return Item if the Item Exists in Inventory by json_index
        for item in self.items:
            if item_json_index == item.json_index:
                return item
        return None

    @property
    def empty(self):
        return len(self.items) < 1

    def add_item(self, item):
        results = []

        # Check for too many items
        if len(self.items) >= self.capacity:
            results.append({
                'item_added': None,
                'message': Message('You cannot carry any more, your inventory is full!', libtcod.yellow)
            })
        else:
            results.append({
                'item_added': item,
                'message': Message('You pick up the %s.' % item.name, libtcod.blue)
            })

            # Remove Item Component

            self.items.append(item)

        return results

    def use(self, item_entity, **kwargs):
        results = []
        item_component = item_entity.item
        # Check if Item Has a "Use" or "Equip" Function
        if not item_component.use_function:
            equippable_component = item_entity.equippable
            if equippable_component:
                results.append({'equip': item_entity})
            else:
                results.append({'message': Message('The %s cannot be used.' % item_entity.name, libtcod.yellow)})
        else:
            # Check Item Type if Targeting Component is Required
            if item_component.targeting and not (kwargs.get('target_x') or kwargs.get('target_y')):
                results.append({'targeting': item_entity})
            else:
                kwargs = {**item_component.function_kwargs, **kwargs}

                # Most Important Connecting Function
                # Note: Pass the user and various catch-all-keyword-args
                item_use_results = item_component.use_function(self.owner, **kwargs)

                # Check if Item is Altered after Usage
                for item_use_result in item_use_results:
                    # Remove Item from Inventory
                    if item_use_result.get('consumed'):
                        self.remove_item(item_entity)
                        break

                    # Keep Item in Inventory
                    if item_use_result.get('reuseable'):
                        # results.append({'message': Message("")})
                        break

                results.extend(item_use_results)

        return results

    def remove_item(self, item):
        self.items.remove(item)

    def drop_item(self, item_entity, entity_owner=''):
        results = []

        # Untoggle Item if Equipped
        if item_entity in self.owner.equipment.equipment_dict.values():
            self.owner.equipment.toggle_equip(item_entity)

        # Drop Item at Owner Location and Create/Update Position Component
        if not item_entity.position:
            position_component = Position(self.owner.position.x, self.owner.position.y)
            item_entity.position = position_component
        else:
            item_entity.position.x, item_entity.position.y = self.owner.position.x, self.owner.position.y
            print('actually updated position component!', item_entity.name)

        self.remove_item(item_entity)
        results.append({'item_dropped': item_entity, 'message': Message('{} dropped the {}.'.format(self.owner.name, item_entity.name),
                                                                 libtcod.yellow)})

        return results

    def drop_all_items(self):
        results = []

        while self.items:
            item_entity = self.items.pop()
            # Untoggle Item if Equipped
            if self.owner.equipment:
                if item_entity in self.owner.equipment.equipment_dict.values():
                    self.owner.equipment.toggle_equip(item_entity)

            # Drop Item at Owner Location and Create/Update Position Component
            if not item_entity.position:
                position_component = Position(self.owner.position.x, self.owner.position.y)
                item_entity.position = position_component
            else:
                item_entity.position.x, item_entity.position.y = self.owner.position.x, self.owner.position.y
                print('actually updated position component!', item_entity.name)

            # self.remove_item(item_entity)
            results.append({'item_dropped': item_entity,
                            'message': Message('{} dropped the {}.'.format(self.owner.name, item_entity.name),
                                               libtcod.yellow)})

        return results
