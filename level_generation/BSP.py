from math import sqrt
from random import choice, randint

from tcod.bsp import BSP


class BinarySpacePartition(BSP):
    def __init__(self):
        self.grid = None
        self.rooms = {}  # looks like {cell blocks: [rooms]}
        self.sub_rooms = []
        self.within_room = False
        self.cell_block_depth = 2
        self.cell_block_wall_buffer = 1
        self.cell_block_min_size = 12
        super(BinarySpacePartition, self).__init__(x=0, y=0, width=1, height=1)

    def print_grid(self, other_car="$ "):
        final_str = ""
        final_str += "\n"

        for i in range(len(self.grid[0])):
            for j in range(len(self.grid)):
                if self.grid[i][j] == 1:
                    final_str += "# "
                elif self.grid[i][j] == 0:
                    final_str += ". "
                else:
                    final_str += other_car
            final_str += "\n"
        final_str += "\n"
        print(final_str)

    def initialize_grid(self):
        self.grid = [[1 for j in range(self.height)] for y in range(self.width)]

    def generate(self):
        if self.width == 1 or self.height == 1:
            print('Initialize BSP Variables first!')
        self.initialize_grid()
        # Generate Cell Blocks
        if self.cell_block_depth > 0:
            self.iterate_bsp(depth=self.cell_block_depth, min_width=self.cell_block_min_size,
                             min_height=self.cell_block_min_size, wall_buffer=self.cell_block_wall_buffer)
        else:
            self.rooms[BSP(x=1, y=1, width=self.width-1, height=self.height-1)] = []

        # Generate Sub Rooms for Each Cell Block
        actual_cell_blocks = {}
        cell_blocks = self.rooms.keys()
        if len(cell_blocks) > 0:
            # Further Split Cell Blocks into Sub Rooms for Jail Cells and other Prefab Rooms
            # print('# Further Split Cell Blocks into Sub Rooms for Jail Cells and other Prefab Rooms')
            for cell_block in cell_blocks:
                # print('cell_block:', cell_block)
                bsp = BinarySpacePartition()
                bsp.x = cell_block.x
                bsp.y = cell_block.y
                bsp.width = cell_block.width - self.cell_block_wall_buffer
                bsp.height = cell_block.height - self.cell_block_wall_buffer
                bsp.iterate_bsp(depth=self.cell_block_depth * 2, min_width=self.cell_block_min_size//2,
                                min_height=self.cell_block_min_size//2 , within_room=True, cell_block=cell_block,
                                cell_block_rooms=self.rooms, grid=self.grid)
                actual_cell_blocks[bsp] = self.rooms[cell_block]  # TODO: replace this with a better implementation

            # TODO: replace this with a better implementation
            self.rooms = {}
            for cell_block, sub_rooms in actual_cell_blocks.items():
                if not sub_rooms:
                    self.rooms[cell_block] = [cell_block]
                    self.sub_rooms.append(cell_block)
                else:
                    self.rooms[cell_block] = sub_rooms
                    self.sub_rooms.extend(sub_rooms)

        # Connect All Cell Blocks
        self.connect_cell_blocks()
        # Center of All Rooms
        # for cell_block in self.rooms.keys():
        #     print('\nCell Block:', cell_block, ' with %s sub rooms:' % len(self.rooms[cell_block]))
        #     print('\tSub Rooms:', self.rooms[cell_block])

        # Mark Center for Each Room
        # for sub_rooms in self.rooms.values():
        #     for room in sub_rooms:
        #         x, y = center(room)
        #         self.grid[x][y] = 2

    def iterate_bsp(self, depth, min_width, min_height, wall_buffer=0, within_room=False, cell_block=None,
                    cell_block_rooms=None, grid=None):

        self.split_recursive(
            depth=depth,
            min_width=min_width,
            min_height=min_height,
            max_horizontal_ratio=1.25,
            max_vertical_ratio=1.25
        )

        actual_room_nodes = []
        # In pre order, leaf nodes are visited before the nodes that connect them.
        for node in self.pre_order():
            # Create a Room Within a Room or Carve Out a Room for Highest Level
            if not node.children:
                # ---Only Handled When Generating Sub Rooms---
                if within_room:
                    if grid:
                        self.grid = grid
                    self.create_walled_room(node, wall_buffer)
                    actual_room_nodes.append(node)
                # --------------------------------------------
                else:
                    # self.create_room(node, wall_buffer)
                    self.rooms[node] = None

        if len(actual_room_nodes) > 1:
            cell_block_rooms[cell_block] = actual_room_nodes
            self.connect_rooms(actual_room_nodes)

    def connect_rooms(self, actual_room_nodes):
        # Iterate Through All Room Pairs and Find/Force a Connection
        for i, node in enumerate(actual_room_nodes[1:]):
            next_node = actual_room_nodes[i]

            # Ensure Siblings Are Connected
            node_1, node_2 = node.parent.children
            self.create_hall(node_1, node_2)

            node_1, node_2 = next_node.parent.children
            self.create_hall(node_1, node_2)

            # Find Short Test Distance Between Children of Different Nodes
            distances = {}
            for node_1 in node.parent.children:
                for node_2 in next_node.parent.children:
                    if self.can_create_hall(node_1, node_2) and node_1 != node_2:
                        x1, y1 = center(node_1)
                        x2, y2 = center(node_2)
                        distances[calculate_distance(x1, y1, x2, y2)] = (node_1, node_2)

            if not distances:
                # Force a Connection Between Children of Both Nodes
                """
                Note: No distances are stored because the children pairs are so far away from each other they
                      do not overlap horizontally or vertically.
                """
                close_1 = choice(node.parent.children)
                close_2 = choice(next_node.parent.children)
                self.force_create_hall(close_1, close_2)
            else:
                # Connect Good Rooms
                close_1, close_2 = distances[min(distances)]
                self.create_hall(close_1, close_2)

    def connect_cell_blocks(self):
        """
        There are (3) results:
            1. Closest Rooms of Each Cell Block Overlap -> Connect as normal
            2. Closest Rooms of Each Cell Block Do Not Overlap - > Force Connection, ignoring existing rooms
            3. Cell Blocks do not Overlap -> Force Connection, ignore everything
        """
        cell_blocks = list(self.rooms.keys())
        # Chain Cell Blocks Together
        width = 3
        for i, cell_block in enumerate(cell_blocks[1:]):
            pairs = {}  # dictionary of distances between (2) rooms of different cell blocks
            previous_cell_block = cell_blocks[i]

            # Iterate Through Individual Rooms of Each Cell Block and Find Smallest Connection
            for room in self.rooms[cell_block]:
                for other_room in self.rooms[previous_cell_block]:
                    x1, y1 = center(room)
                    x2, y2 = center(other_room)
                    pairs[calculate_distance(x1, y1, x2, y2)] = (room, other_room)
            if pairs:
                closest = min(pairs)
                room1, room2 = pairs[closest]

                # Check if Connection Exists and Connect Rooms
                connected = self.create_hall(room1, room2, width)

                # If Rooms do Not Overlap at all, force a connection
                if not connected:
                    self.force_create_hall(room1, room2, width)
            else:
                # Force a Connecting Hall Between Cell Blocks
                print('somehow there is no pair?')
                self.force_create_hall(cell_block, previous_cell_block, width)

    def create_walled_room(self, room, buffer=0, ):
        # Sets Tiles in to Become Passable, but add walls around
        for x in range(room.x, room.x + room.width):
            for y in range(room.y, room.y + room.height):
                if x == room.x or \
                        x == room.x + room.width - buffer or \
                        y == room.y or \
                        y == room.y + room.height - buffer:

                    self.grid[x][y] = 1
                else:
                    self.grid[x][y] = 0

    @staticmethod
    def can_create_hall(room1, room2, buffer=0):
        x2, y2 = center(room2)

        # Note: Unless the Rooms are physically touching, they overlap either Horizontally or Vertically, not both.

        # Check if Room 1 Overlaps Room 2 Horizontally
        # print('Check if Room 1 Overlaps Room 2 Horizontally')
        for x in range(room1.x + buffer, room1.x + room1.width):
            if x == x2:
                return True

        # Check if Room 1 Overlaps Room 2 Vertically
        # print('Check if Room 1 Overlaps Room 2 Vertically')
        for y in range(room1.y + buffer, room1.y + room1.height):
            if y == y2:
                return True

        # Check if Room 1 "Kind of" Overlaps Horizontally
        for x in range(room1.x + buffer, room1.x + room1.width):
            if room2.x + buffer < x < room2.x + room2.width:
                return True

        # Check if Room 1 "Kind of" Overlaps Vertically
        for y in range(room1.y + buffer, room1.y + room1.height):
            if room2.y + buffer < y < room2.y + room2.height:
                return True

        # NO OVERLAP AT ALL!
        return False

    def force_create_hall(self, room1, room2, width=1):
        x1, y1 = center(room1)
        x2, y2 = center(room2)
        if randint(0, 1) == 1:
            self.create_h_tunnel(x1, x2, y1, width)
            self.create_v_tunnel(y1, y2, x2, width)
        else:  # else it starts vertically
            self.create_v_tunnel(y1, y2, x1, width)
            self.create_h_tunnel(x1, x2, y2, width)

    def create_h_tunnel(self, x1, x2, y, width):
        for x in range(min(x1, x2), max(x1, x2)):
            # create_path(game_map, x, y)
            self.grid[x][y] = 0

            if width > 1:
                self.grid[x][y-1] = 0
                self.grid[x][y+1] = 0


    def create_v_tunnel(self, y1, y2, x, width):
        for y in range(min(y1, y2), max(y1, y2)):
            self.grid[x][y] = 0

            if width > 1:
                self.grid[x-1][y] = 0
                self.grid[x+1][y] = 0

    def create_hall(self, room1, room2, width=1):
        x1, y1 = center(room1)
        x2, y2 = center(room2)

        # Note: Unless the Rooms are physically touching, they overlap either Horizontally or Vertically, not both.

        # Check if Room 1 Overlaps Room 2 Horizontally
        # print('Check if Room 1 Overlaps Room 2 Horizontally')
        for x in range(room1.x, room1.x + room1.width):
            if x == x2:
                self.create_v_tunnel(y1, y2, x, width)
                return True

        # Check if Room 1 Overlaps Room 2 Vertically
        # print('Check if Room 1 Overlaps Room 2 Vertically')
        for y in range(room1.y, room1.y + room1.height):
            if y == y2:
                self.create_h_tunnel(x1, x2, y, width)
                return True

        # Check if Room 1 "Kind of" Overlaps Horizontally
        for x in range(room1.x, room1.x + room1.width):
            if room2.x < x < room2.x + room2.width:
                self.create_v_tunnel(y1, y2, x, width)
                # place_tile(game_map, x, y1, '12')
                return True

        # Check if Room 1 "Kind of" Overlaps Vertically
        for y in range(room1.y, room1.y + room1.height):
            if room2.y < y < room2.y + room2.height:
                self.create_h_tunnel(x1, x2, y, width)
                return True

        # NO OVERLAP AT ALL!
        return False

    def create_room(self, room, wall_buffer):
        # Sets Tiles in to Become Passable
        for x in range(room.x + wall_buffer + 1, room.x + room.width - wall_buffer):
            for y in range(room.y + wall_buffer + 1, room.y + room.height - wall_buffer):
                self.grid[x][y] = 0

    def obtain_point_within(self, padding=3):
        raise AttributeError


def center(room):
    center_x = room.x + room.width // 2
    center_y = room.y + room.height // 2
    return center_x, center_y


def calculate_distance(x1, y1, x2, y2):
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)


if __name__ == '__main__':
    b = BinarySpacePartition()
    b.x = 0
    b.y = 0
    b.width = 200
    b.height = 200
    b.cell_block_wall_buffer = 4
    b.cell_block_depth = 6
    b.generate()
    b.print_grid()
