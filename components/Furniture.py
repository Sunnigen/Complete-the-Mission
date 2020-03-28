from MapObjectFunctions import *


class Furniture:
    def __init__(self, movable=False, breakable=False, walkable=False, interact_function=None, **kwargs):
        self.movable = movable
        self.breakable = breakable
        self.walkable = walkable
        self.interact_function = interact_function
        self.function_kwargs = kwargs

    def update(self, map_object_data):
        self.movable = map_object_data.get('movable')
        self.breakable = map_object_data.get('breakable')
        self.walkable = map_object_data.get('walkable')
        self.interact_function = eval(map_object_data.get('interact_function'))
        # TODO: Check if not Updating function_kwargs causes elements before entity.change to still transfer over
        # self.function_kwargs = None
