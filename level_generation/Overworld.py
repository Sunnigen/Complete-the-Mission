from copy import copy
from functools import partial
import math

import numpy as np

from scipy.spatial import ConvexHull, Delaunay

import matplotlib.pyplot as plt


from kivy.clock import Clock

import tcod
import tcod.noise
import tcod.path

from level_generation import BSPTreePolygon, FiniteVoronoi, GenerationUtils
from map_objects.Shapes import PolygonRoom


class Overworld:
    game_map = None
    dungeon_level = 0
    noise = None
    plots = []

    # def __init__(self, **kwargs):
    #     self.game_map = None
    #     self.dungeon_level = 0

    def generate_level(self, game_map, dungeon_level, max_rooms, room_min_size, room_max_size, map_width, map_height,
                       player, entities, item_table, mob_table, object_table):

        self.game_map = game_map
        # self.dungeon_level = dungeon_level
        # # Initialize Noise
        # self.noise = tcod.noise.Noise(
        #     dimensions=2,
        #     algorithm=tcod.NOISE_SIMPLEX,
        #     implementation=tcod.noise.TURBULENCE,
        #     hurst=0.5,
        #     lacunarity=2.0,
        #     octaves=4,
        #     seed=None,
        # )
        #
        # # Generate WidthxHeight Map
        # ogrid = [np.arange(map_width, dtype=np.float32),
        #          np.arange(map_height, dtype=np.float32)]
        # # print('ogrid:', ogrid)
        #
        # # Scale Grid
        # # ogrid[0] *= 0.25
        # # ogrid[1] *= 0.25
        #
        # # Return the sampled noise from this grid of points
        # samples = self.noise.sample_ogrid(ogrid)
        # print('map size:', samples.shape)
        # print('map noise:', samples)
        #
        #
        # # Place Entities
        player.x, player.y = map_width // 2, map_height // 2

        # Voronoi Generation
        polygons, map_size, center_points, vertices = FiniteVoronoi.voronoi_polygons(
            max(map_width // 6, map_height // 6),
            (map_width, map_height)
        )

        # Generate Roads
        # print('delaunay_points:', delaunay_points)
        # road_vertices = np.array([c for v in polygons for c in v])
        # plt.plot([p[0] for p in delaunay_points], [p[1] for p in delaunay_points], 'yo')
        # delaunay_tri = Delaunay(delaunay_points)

        # plt.triplot(delaunay_points[:, 0], delaunay_points[:, 1], delaunay_tri.simplices.copy())
        # plt.plot(delaunay_points[:, 0], delaunay_points[:, 1], 'o')

        road_connections = {}
        # print('len:', len(delaunay_points))
        # print('Connecting Paths')
        for vertex_set in polygons:
            # print('pindex:', pindex, p)
            # neighbor_x, neighbor_y = find_neighbor_vertices(pindex, delaunay_tri)
            # point = tuple(delaunay_tri.points[pindex])

            for pindex, vertex in enumerate(vertex_set[1:]):
                previous_vertex = tuple(vertex_set[pindex])
                vertex = tuple(vertex)
                # print('previous_vertex:', previous_vertex)
                # print('vertex:', vertex)

                if not road_connections.get(vertex):
                    # print('point:', type(point))
                    road_connections[vertex] = []

                    # Check if Point already Exists
                    # if not delaunay_connections.get((x, y)):

                if road_connections.get(previous_vertex):
                    if vertex in road_connections[previous_vertex]:
                        continue

                road_connections[vertex].append(previous_vertex)
                    # elif (x, y)



        # print('delaunay_connections:')
        # print(len(delaunay_connections.keys()))
        # for point, neighbors in delaunay_connections.items():
            # print(point, neighbors)
            # for neighbor_point in neighbors:
            #     connect_points(game_map, [point, neighbor_point], tile= '12')



        # Generate each Voronoi Polygon as a "Room" and Create Paths Around Each Plot
        for room_number, poly in enumerate(polygons):
            # print('poly', poly)
            plot = PolygonRoom(game_map, room_number, poly)
            self.plots.append(plot)
            z = sorted(poly, key=lambda x:x[0]*x[1])
            # poly.sort(key=lambda x:x[0]*x[1])
            b = BSPTreePolygon.BSPTreePolygonAlgorithm()
            min_x, min_y = z[0]
            max_x, max_y = z[-1]
            # print(min_x, min_y, max_x, max_y)
            b.generate_level(game_map, max_rooms, room_min_size, room_max_size, max_x-1, max_y-1,
                       entities, item_table, mob_table, min_x-1, min_y-1, poly)

            # x = [p[0] for p in poly]
            # y = [p[1] for p in poly]
            # centroid = (sum(x) / len(poly), sum(y) / len(poly))
            #
            # # Re-Order Vertices in Clockwise Around Centroid
            # vertex_angles = []
            # for vertex in poly:
            #     vertex_angles.append((angle_between(centroid, vertex), vertex))
            # # print('vertex_angles:',vertex_angles)
            # vertex_angles = sorted(vertex_angles, key=lambda v: v[0])
            # vertex_angles.append(vertex_angles[0])
            # # print('vertex_angles:', vertex_angles)
            # roads = []
            # for v in vertex_angles:
            #     roads.append(v[1])
            # connect_points(game_map, roads, '12')
        game_map.rooms.extend(self.plots)
        # for point, neighbors in road_connections.items():
        #     for neighbor_point in neighbors:
        #         connect_points(game_map, [point, neighbor_point], thickness=1, tile='12')


        # Outerwalls
        # TODO: Sometimes the convex hull does not generate?
        unpack_polygons = np.array([c for v in polygons for c in v])
        hull = ConvexHull(points=unpack_polygons, qhull_options='QG6')
        corner_points = []
        for simplex in hull.simplices:
            x, y = unpack_polygons[simplex, 0], unpack_polygons[simplex, 1]
            corner_points.append([x, y])
            # plt.plot(x, y, 'k-')
        # Verticies of Outerwalls
        wall_corner_points = np.array(corner_points)
        true_corner_points = []
        for pairs in wall_corner_points:
            true_corner_points.extend([(int(pairs[0][0]), int(pairs[1][0])), (int(pairs[0][1]), int(pairs[1][1]))])

        # print('# Vertices of Outerwalls')
        for x, y in true_corner_points:
            GenerationUtils.place_tile(game_map, x - 1, y - 1, '3')


        # Draw Lines for all Outside Vertices Forming Wall
        all_vertices = []
        for poly in polygons:
            for vertex in poly:
                all_vertices.append(tuple(vertex))

        # Plot Unique Vertices
        unique_vertices = []
        for vertex in all_vertices:
            if all_vertices.count(vertex) <= 2:
                unique_vertices.append(vertex)

        # Map Center

        x = [p[0] for p in unique_vertices]
        y = [p[1] for p in unique_vertices]
        centroid = (sum(x) / len(unique_vertices), sum(y) / len(unique_vertices))

        # Re-Order Vertices in Clockwise Around Centroid
        vertex_angles = []
        for vertex in unique_vertices:
            vertex_angles.append((angle_between(centroid, vertex), vertex))
        vertex_angles = sorted(vertex_angles)
        vertex_angles.append(vertex_angles[0])
        # print('vertex_angles:', vertex_angles)

        walls = []
        for v in vertex_angles:
            walls.append(v[1])

        for point, neighbors in road_connections.items():
            for neighbor_point in neighbors:
                connect_points(game_map, [point, neighbor_point], thickness=3, tile='12')
        # print('walls:', walls)

        # Connect Walls
        connect_points(game_map, walls, '1', thickness=3)

        # Vertex Center for Each Wall
        # TODO: Create Towers/Entrances
        # for v in vertex_angles:
        #     x = int(v[1][0])
        #     y = int(v[1][1])
        #     GenerationUtils.place_tile(game_map, x - 1, y - 1, '3')

        # plt.plot([v[1][0] for v in vertex_angles], [v[1][1] for v in vertex_angles], '.r-')


        # Clock.schedule_once(partial(FiniteVoronoi.plot_polygons, polygons, map_size, center_points, vertices), 0.25)
        FiniteVoronoi.plot_polygons(polygons, map_size, center_points, vertices, show=False)


        # Center Points of Each Polygon
        # print('# Center Points of Each Polygon')
        # print('center_points', center_points)
        for point in center_points:
            x, y = point
            GenerationUtils.place_tile(game_map, int(x - 1), int(y - 1), '10')

        # plt.show()

    # def assign_terrain(self, map_noise, map_width, map_height):
    #     colors = np.empty_like(map_noise)
    #     for x in map_width:
    #         for y in map_height:
    #             noise_val = map_noise[x][y]
    #             if noise_val >= 0.9:  # mountain
    #                 colors[x][y] = "M"
    #             if noise_val >= 0.9:
    #
    #     return colors


def connect_points(game_map, points, tile='1', thickness=1):
    """

    :param game_map:
    :param points:
    :param tile:
    :param thickness:
    :return:
    """

    map = np.ones_like(game_map.walkable, order="F")
    print('\nmap.shape:', map.shape, game_map.walkable.shape)
    total_path = []
    astar = tcod.path.AStar(map)

    for i, p in enumerate(points[:-1]):
    # for i, p in enumerate(points[:-1]):
        start_x, start_y = int(p[0]), int(p[1])
        goal = points[i+1]
        goal_x, goal_y = int(goal[0]), int(goal[1])
        path = astar.get_path(start_x=start_y - 1, start_y=start_x - 1, goal_x=goal_y - 1, goal_y=goal_x - 1)
        total_path.extend(path)
        # if len(points) < 5:
        #     print('total_path:', total_path)
        #     print('start/goal points:', start_x - 1, start_y - 1, goal_x - 1, goal_y - 1)
        #     print('starting points:', points)

    # Place Tiles onto Game Map
    if total_path:
        x, y = total_path[0]
        GenerationUtils.place_tile(game_map, int(y - 1), int(x - 1), tile)

        # Place Tiles
        for i, point in enumerate(total_path[1:]):
            x, y = point
            GenerationUtils.place_tile(game_map, int(x-1), int(y-1), tile)

            if thickness > 1:
                # TODO: Allow any amount of thickness. This only accepts 3 at the moment.
                prev_x, prev_y = total_path[i]
                thickness_coordinates = []

                # Check Relative Distance between Current and Previous Point
                if prev_x != x and prev_y != y:
                    thickness_coordinates.extend([(x, prev_y), (prev_x, y)])

                elif prev_x != x:
                    # Add Points Above and Below
                    thickness_coordinates.extend([(x, y+1), (prev_x, y-1)])

                elif prev_y != y:
                    # Add Points Above and Below
                    thickness_coordinates.extend([(x-1, y), (x+1, y)])

                # Place Extra Points
                for coordinates in thickness_coordinates:
                    x, y = coordinates
                    if game_map.is_within_map(x, y):
                        GenerationUtils.place_tile(game_map, int(x - 1), int(y - 1), tile)

    else:
        print('No total path!\nPoints:', points)


def angle_between(centroid, vector):
    # Utility function for calculating angle between a centroid and a point
    myradians = math.atan2(vector[1] - centroid[1], vector[0] - centroid[0])
    angle = math.degrees(myradians)
    return angle


def find_neighbor_indices(pindex, triang):
    """

    Parameters
    ----------
    pindex - integer of center point
    triang - scipy.spatial.Delaunay

    Returns
    -------
    list of integers - all indices of points that are connect to pindex center point

    Note: Do not use directly, use from find_neighbor_vertices()
    """
    return triang.vertex_neighbor_vertices[1][triang.vertex_neighbor_vertices[0][pindex]:triang.vertex_neighbor_vertices[0][pindex+1]]


def find_neighbor_vertices(pindex, triang):
    """

    Parameters
    ----------
    pindex - integer of center point
    triang - scipy.spatial.Delaunay

    Returns
    -------
    neighbor_x - list of all x coordinates of neighboring vertices of pindex point
    neighbor_y - list of all y coordinates of neighboring vertices of pindex point

    """
    neighbor_indices = find_neighbor_indices(pindex, triang)
    neighbor_x = []
    neighbor_y = []
    for n in neighbor_indices:
        neighbor_x.append(triang.points[n][0])
        neighbor_y.append(triang.points[n][1])
    return neighbor_x, neighbor_y
