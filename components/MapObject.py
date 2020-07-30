from MapObjectFunctions import *


class MapObject:
    def __init__(self, movable=False, breakable=False, walkable=False, interact_function=None, wait_function=None,
                 properties=None, **kwargs):
        self.movable = movable
        self.breakable = breakable
        self.walkable = walkable
        self.interact_function = interact_function
        self.wait_function = wait_function
        self.properties = properties
        self.function_kwargs = kwargs

    def update(self, map_object_data):
        self.movable = map_object_data.get('movable')
        self.breakable = map_object_data.get('breakable')
        self.walkable = map_object_data.get('walkable')
        self.interact_function = eval(map_object_data.get('interact_function', "no_function"))
        self.wait_function = eval(map_object_data.get('wait_function', "no_function"))
        # TODO: Check if not Updating function_kwargs causes elements before entity.change to still transfer over
        # self.function_kwargs = None
