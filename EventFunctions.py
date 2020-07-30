def no_event(*args, **kwargs):
    print('\nno_event')
    print('args:', args)
    print('kwargs:', kwargs)
    return None


def change_faction(*args, **kwargs):
    results = []
    entity = kwargs.get("entity")
    new_faction = kwargs.get("new_faction")
    entity.faction.faction_name = new_faction
    return results


def give_item(*args, **kwargs):
    item_owner = args[0]
    item_receiver = args[1]
    item_names = kwargs.get('items')
    results = []

    for item_entity in item_owner.inventory.items:
        if item_entity.name in item_names:
            item_owner.inventory.remove_item(item_entity)
            results.extend(item_receiver.inventory.add_item(item_entity))

    return results


class EventObject:

    # Class to hold events that occur from dialogue

    def __init__(self, event, **kwargs):
        self.event = event
        self.event_kwargs = kwargs
