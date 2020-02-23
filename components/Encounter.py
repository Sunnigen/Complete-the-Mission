

class Encounter:
    """
    - Group all entities and items as a single entity or relate between them
    """
    def __init__(self, main_room, encounter_number, encounter_type='basic'):
        self.encounter_number = encounter_number
        # self.entities = entities
        # self.items = items
        self.monster_list = []
        self.item_list = []
        self.main_room = main_room
        self.encounter_type = encounter_type

    def print_encounter(self):
        print('\nEncounter #%s' % self.encounter_number)
        print('Main Room: %s' % self.main_room.__class__)
        print('Room Number: %s' % self.main_room.room_number)
        print('Monsters:')
        if not self.monster_list:
            print('\tNo monsters')
        else:
            for e in self.monster_list:
                print('\t%s' % e.name)
        print('Items:')
        if not self.item_list:
            print('\tNo items')
        else:
            for i in self.item_list:
                print('\t%s' % i.name)
