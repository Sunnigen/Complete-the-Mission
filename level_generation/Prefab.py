# General Class to load and place prefabs
class Prefab:
    width = 0
    height = 0
    template = None
    name = ''
    x = -1
    y = -1

    def load_template(self, prefab_dict, x=None, y=None):

        self.width = prefab_dict.get('width')
        self.height = prefab_dict.get('height')
        self.template = prefab_dict.get('template')
        self.name = prefab_dict.get('name')
        if x or y:
            self.set_position(x, y)

    def set_position(self, x, y):
        self.x = x
        self.y = y
