import tcod as libtcod

from GameMessages import Message


class Inventory:
    def __init__(self, capacity, items=[]):
        self.capacity = capacity
        self.items = items

    @property
    def empty(self):
        return False if len(self.items) > 0 else True

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

            self.items.append(item)

        return results

    def use(self, item_entity, **kwargs):
        results = []
        item_component = item_entity.item
        # Check if Item Has a "Use" or "Equip" Function
        if item_component.use_function is None:
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

    def drop_item(self, item):
        results = []

        # Untoggle Item if Equipped
        if self.owner.equipment.main_hand == item or self.owner.equipment.off_hand == item:
            self.owner.equipment.toggle_equip(item)

        # Drop Item at Owner Location
        item.x = self.owner.x
        item.y = self.owner.y
        self.remove_item(item)
        results.append({'item_dropped': item, 'message': Message('You dropped the %s.' % item.name,
                                                                 libtcod.yellow)})

        return results
