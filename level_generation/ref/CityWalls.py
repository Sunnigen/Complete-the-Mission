from random import random


class CityWalls:
    '''
    The City Walls algorithm is very similar to the BSP Tree
    above. In fact their main difference is in how they generate
    rooms after the actual tree has been created. Instead of
    starting with an array of solid walls and carving out
    rooms connected by tunnels, the City Walls generator
    starts with an array of floor tiles, then creates only the
    exterior of the rooms, then opens one wall for a door.
    '''

    def __init__(self):
        self.level = []
        self.room = None
        self.MAX_LEAF_SIZE = 30
        self.ROOM_MAX_SIZE = 16
        self.ROOM_MIN_SIZE = 8

    def generateLevel(self, mapWidth, mapHeight):
        # Creates an empty 2D array or clears existing array
        self.level = [[0
                       for y in range(mapHeight)]
                      for x in range(mapWidth)]

        self._leafs = []
        self.rooms = []

        rootLeaf = Leaf(0, 0, mapWidth, mapHeight)
        self._leafs.append(rootLeaf)

        splitSuccessfully = True
        # loop through all leaves until they can no longer split successfully
        while (splitSuccessfully):
            splitSuccessfully = False
            for l in self._leafs:
                if (l.child_1 == None) and (l.child_2 == None):
                    if ((l.width > self.MAX_LEAF_SIZE) or
                            (l.height > self.MAX_LEAF_SIZE) or
                            (random.random() > 0.8)):
                        if (l.splitLeaf()):  # try to split the leaf
                            self._leafs.append(l.child_1)
                            self._leafs.append(l.child_2)
                            splitSuccessfully = True

        rootLeaf.createRooms(self)
        self.createDoors()

        return self.level

    def createRoom(self, room):
        # Build Walls
        # set all tiles within a rectangle to 1
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.level[x][y] = 1
        # Build Interior
        for x in range(room.x1 + 2, room.x2 - 1):
            for y in range(room.y1 + 2, room.y2 - 1):
                self.level[x][y] = 0

    def createDoors(self):
        for room in self.rooms:
            (x, y) = room.center()

            wall = random.choice(["north", "south", "east", "west"])
            if wall == "north":
                wallX = int(x)
                wallY = int(room.y1 + 1)
            elif wall == "south":
                wallX = int(x)
                wallY = int(room.y2 - 1)
            elif wall == "east":
                wallX = int(room.x2 - 1)
                wallY = int(y)
            elif wall == "west":
                wallX = int(room.x1 + 1)
                wallY = int(y)

            self.level[wallX][wallY] = 0

    def createHall(self, room1, room2):
        # This method actually creates a list of rooms,
        # but since it is called from an outside class that is also
        # used by other dungeon Generators, it was simpler to
        # repurpose the createHall method that to alter the leaf class.
        for room in [room1, room2]:
            if room not in self.rooms:
                self.rooms.append(room)


class Leaf:  # used for the BSP tree algorithm
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.MIN_LEAF_SIZE = 10
        self.child_1 = None
        self.child_2 = None
        self.room = None
        self.hall = None

    def splitLeaf(self):
        # begin splitting the leaf into two children
        if (self.child_1 != None) or (self.child_2 != None):
            return False  # This leaf has already been split

        '''
        ==== Determine the direction of the split ====
        If the width of the leaf is >25% larger than the height,
        split the leaf vertically.
        If the height of the leaf is >25 larger than the width,
        split the leaf horizontally.
        Otherwise, choose the direction at random.
        '''
        splitHorizontally = random.choice([True, False])
        if (self.width / self.height >= 1.25):
            splitHorizontally = False
        elif (self.height / self.width >= 1.25):
            splitHorizontally = True

        if (splitHorizontally):
            max = self.height - self.MIN_LEAF_SIZE
        else:
            max = self.width - self.MIN_LEAF_SIZE

        if (max <= self.MIN_LEAF_SIZE):
            return False  # the leaf is too small to split further

        split = random.randint(self.MIN_LEAF_SIZE, max)  # determine where to split the leaf

        if (splitHorizontally):
            self.child_1 = Leaf(self.x, self.y, self.width, split)
            self.child_2 = Leaf(self.x, self.y + split, self.width, self.height - split)
        else:
            self.child_1 = Leaf(self.x, self.y, split, self.height)
            self.child_2 = Leaf(self.x + split, self.y, self.width - split, self.height)

        return True

    def createRooms(self, bspTree):
        if (self.child_1) or (self.child_2):
            # recursively search for children until you hit the end of the branch
            if (self.child_1):
                self.child_1.createRooms(bspTree)
            if (self.child_2):
                self.child_2.createRooms(bspTree)

            if (self.child_1 and self.child_2):
                bspTree.createHall(self.child_1.getRoom(),
                                   self.child_2.getRoom())

        else:
            # Create rooms in the end branches of the bsp tree
            w = random.randint(bspTree.ROOM_MIN_SIZE, min(bspTree.ROOM_MAX_SIZE, self.width - 1))
            h = random.randint(bspTree.ROOM_MIN_SIZE, min(bspTree.ROOM_MAX_SIZE, self.height - 1))
            x = random.randint(self.x, self.x + (self.width - 1) - w)
            y = random.randint(self.y, self.y + (self.height - 1) - h)
            self.room = Rect(x, y, w, h)
            bspTree.createRoom(self.room)

    def getRoom(self):
        if (self.room):
            return self.room

        else:
            if (self.child_1):
                self.room_1 = self.child_1.getRoom()
            if (self.child_2):
                self.room_2 = self.child_2.getRoom()

            if (not self.child_1 and not self.child_2):
                # neither room_1 nor room_2
                return None

            elif (not self.room_2):
                # room_1 and !room_2
                return self.room_1

            elif (not self.room_1):
                # room_2 and !room_1
                return self.room_2

            # If both room_1 and room_2 exist, pick one
            elif (random.random() < 0.5):
                return self.room_1
            else:
                return self.room_2