from loader_functions import JsonReader


FACTIONS = JsonReader.obtain_factions()


class Faction:
    owner = None

    def __init__(self, faction_name, **kwargs):
        self.faction_name = faction_name

    def check_ally(self, other_faction):
        return other_faction in FACTIONS.get(self.faction_name).get("ally")

    def check_enemy(self, other_faction):
        return other_faction in FACTIONS.get(self.faction_name).get("enemy")
