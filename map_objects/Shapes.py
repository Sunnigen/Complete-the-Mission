
from random import choice, randint


class SquareRoom:
    def __init__(self, x, y, w, h, room_number):
        """
        :param x:  X coordinate of top left corner
        :param y:  y coordinate of top left corner
        :param w:  Width bottom right corner
        :param h:  Height bottom right corner
        """
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.room_number = room_number
        self.room_type = ''

    def check_point_within_room(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def check_point_within_horizontal(self, x):
        return self.x1 <= x <= self.x2

    def check_point_within_vertical(self, y):
        return self.y1 <= y <= self.y2

    def __repr__(self):
        return 'SquareRoom, x1=%s, y1=%s, x2=%s, y2=%s' % (self.x, self.y, self.x2, self.y2)

    @property
    def center(self):

        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        return center_x, center_y

    def intersect(self, other_shape):
        # returns true if this SquareRoomangle intersects with another SquareRoom
        return (self.x1 <= other_shape.x2 and self.x2 >= other_shape.x1 and
                self.y1 <= other_shape.y2 and self.y2 >= other_shape.y1)

    def obtain_point_within(self, padding=2):
        return randint(self.x1, self.x2), randint(self.y1, self.y2)

    @property
    def x(self):
        return self.x1
    # @property
    # def x(self):
    #     return int((self.x1 + self.x2) / 2)

    @property
    def y(self):
        return self.y1
    # @property
    # def y(self):
    #     return int((self.y1 + self.y2) / 2)

    @property
    def width(self):
        return self.x2 - self.x1

    @property
    def height(self):
        return self.y2 - self.y1

    @property
    def room_size(self):
        return int(self.height * self.width)


class Circle:
    def __init__(self, game_map, x, y, r, room_number):
        self.x1 = x - r
        self.y1 = y - r
        self.x2 = x + r
        self.y2 = y + r
        self.r = r
        self.game_map = game_map
        self.room_number = room_number
        self.room_type = ''

    @property
    def x(self):
        return self.x1

    @property
    def y(self):
        return self.y1

    @property
    def center(self):
        return self.x + self.r, self.y + self.r

    @property
    def width(self):
        return self.r + self.r

    @property
    def height(self):
        return self.r + self.r

    def intersect_point(self, x2, y2):
        """
        In general, x and y must satisfy (x - center_x)^2 + (y - center_y)^2 < radius^2, within circle

        Please note that points that satisfy the above equation with < replaced by == are considered the points on the
        circle, and the points that satisfy the above equation with < replaced by > are considered the outside the
        circle.
        """
        return (self.x + self.r - x2) ** 2 + (self.y + self.r - y2) ** 2 < self.r ** 2

    def check_point_within_room(self, x, y):
        return self.intersect_point(x, y)

    def intersect(self, *args):
        print('%s doesn\'t have an intersect function, only intersect_point(x, y).' % self.__class__)

    def obtain_point_within(self, padding=2):
        points = []
        for x in range(self.x1, self.x2):
            for y in range(self.y1, self.y2):
                if self.intersect_point(x, y):
                    points.append((x, y))


        (x, y) = choice(self.game_map.obtain_open_floor(points))
        return x, y


class PolygonRoom:
    def __init__(self, game_map, room_number, corners):
        self.game_map = game_map
        self.room_number = room_number
        self.corners = corners
        self.entrances = []
        self.room_type = ''

    @property
    def center(self):
        return (sum(p[0] for p in self.corners) / len(self.corners),
                    (sum(p[1] for p in self.corners) / len(self.corners))
                    )

    def obtain_point_within(self, padding=2):
        x, y = 0, 0
        return (x, y)

    def check_point_within_room(self, x, y, padding=2):
        return False


class Cave:
    # Used for cellular automata
    def __init__(self, game_map, coords, room_number):
        self.coords = coords
        self.game_map = game_map
        self.room_number = room_number
        self.room_type = ''

    @property
    def center(self):
    # def calculate_center(self):
        # Calculate Center of All Coordinates
        # TODO: Implement "Weighted" coordinates
        # TODO: Sometimes a cave has no coordinates
        coords_count = len(self.coords)
        x_count = 0
        y_count = 0
        for x, y in self.coords:
            x_count += x
            y_count += y
        # centroid =
        return x_count//coords_count, y_count//coords_count
        # self.center = centroid

    def check_point_within_room(self, x, y):
        return (x, y) in self.coords

    def obtain_point_within(self, padding=2):
        return choice(tuple(self.coords))

    @property
    def x(self):
        x_count = 0
        coords_count = len(self.coords)
        for x, y in self.coords:
            x_count += x
        return x_count//coords_count

    @property
    def y(self):
        y_count = 0
        coords_count = len(self.coords)
        for x, y in self.coords:
            y_count += x
        return y_count // coords_count


class BSPContainer:
    pass


class BSPRoom(SquareRoom):

    def __init__(self, x, y, w, h, room_number):
        super(BSPRoom, self).__init__(x, y, w, h, room_number)
        # print('creating room #%s' % room_number)
        self.hallway = None
        self.parent_room = None
        self.sub_rooms = []
        self.entrances = []

    def check_point_within_room(self, x, y, padding=2):
        return self.x1 + padding <= x <= self.x2 - padding and self.y1 + padding <= y <= self.y2 - padding

    def obtain_point_within(self, padding=2):
        return randint(self.x1 + padding, self.x2 - padding), randint(self.y1 + padding, self.y2 - padding)

    def obtain_entrances(self, game_map):
        entrances = []

        limit = 3
        count = 0
        consecutive = False

        y = self.y1 + 1
        for x in range(self.x1+1, self.x2):
            if game_map.walkable[y][x]:
                entrances.append((x, y))
                consecutive = True
            else:
                consecutive = False

            if consecutive:
                count += 1

            if count > limit:
                entrances = []
                break

        self.entrances.extend(entrances)


        count = 0
        entrances = []
        consecutive = False

        y = self.y2 - 1
        for x in range(self.x1+1, self.x2):
            if game_map.walkable[y][x]:
                entrances.append((x, y))
                consecutive = True
            else:
                consecutive = False

            if consecutive:
                count += 1

            if count > limit:
                entrances = []
                break

        self.entrances.extend(entrances)

        count = 0
        entrances = []
        consecutive = False

        x = self.x1 + 1
        for y in range(self.y1+1, self.y2):
            if game_map.walkable[y][x]:
                entrances.append((x, y))
                consecutive = True
            else:
                consecutive = False

            if consecutive:
                count += 1

            if count > limit:
                entrances = []
                break

        self.entrances.extend(entrances)

        count = 0
        entrances = []
        consecutive = False

        x = self.x2 - 1
        for y in range(self.y1+1, self.y2):
            if game_map.walkable[y][x]:
                entrances.append((x, y))
                consecutive = True
            else:
                consecutive = False

            if consecutive:
                count += 1

            if count > limit:
                entrances = []
                break

        self.entrances.extend(entrances)


class MouseRoom:

    # Used primarily to identify room types for debugging
    def __init__(self, x, y, width, height, room_type):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.room_type = room_type

    def check_point_within_room(self, point_x, point_y):
        return self.x < point_x < self.x + self.width and self.y < point_y < self.y + self.height

    def __repr__(self):
        return "Room: {} ({}, {}) to ({}, {})".format(self.room_type, self.x, self.y, self.x + self.width, self.y + self.height)