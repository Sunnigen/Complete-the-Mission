import math
from random import randint

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np
from scipy.spatial import ConvexHull, Voronoi

from level_generation.voronoi_gen_utils import random_color, voronoi_finite_polygons_2d


def voronoi_polygons(n=50, map_size=(100, 100)):
    random_seeds = np.random.rand(n, 2) * map_size
    vor = Voronoi(random_seeds)
    regions, vertices = voronoi_finite_polygons_2d(vor)
    used_seeds = []
    used_vertices = []
    polygons = []
    for i, reg in enumerate(regions):
        # Remove Polygons/Points/Vertices that aren't completely Within Map Size
        not_add = True
        polygon = vertices[reg]
        for point in polygon:
            if not 0 < point[0] <= map_size[0] or not 0 < point[1] <= map_size[1]:
                not_add = False
                break
        if not not_add:
            continue
        used_seeds.append([random_seeds[i][0].round(), random_seeds[i][1].round()])
        used_vertices.append(vertices[i].round())
        polygons.append(polygon.round())
    # print('polygons:', polygons)
    # for p in polygons:
    #     print(p)
    # print('used_seeds:', len(used_seeds))
    used_vertices = np.array(used_vertices)
    # print('used_vertices:', len(used_vertices))
    # print('ridge points:', vor.ridge_points)
    # print('ridge vertices:', vor.ridge_vertices)
    return polygons, map_size, used_seeds, used_vertices


def angle_between(centroid, vector):
    myradians = math.atan2(vector[1] - centroid[1], vector[0] - centroid[0])
    angle = math.degrees(myradians)
    return angle


def plot_polygons(polygons, map_size, points, vertices, ax=None, alpha=0.5, linewidth=0.7, saveas=None, show=True, dt=0):
    # Configure plot
    if ax is None:
        plt.figure(figsize=(10, 5))
        ax = plt.subplot(121)
    # Remove ticks
    # ax.set_xticks([])
    # ax.set_yticks([])
    # ax.axis("equal")
    # Set limits
    # ax.set_xlim(0, map_size[0])
    # ax.set_ylim(0, map_size[1])
    plt.xlim(0, max(map_size))
    plt.ylim(0, max(map_size))
    # Add polygons
    for poly in polygons:
        colored_cell = Polygon(poly,
                               linewidth=linewidth,
                               alpha=alpha,
                               facecolor=random_color(as_str=False, alpha=1),
                               edgecolor="black")
        ax.add_patch(colored_cell)
    # Plot Center Points of Each Polygon
    plt.plot([p[0] for p in points], [p[1] for p in points], 'ko', markersize=2)

    unpack_polygons = np.array([c for v in polygons for c in v])
    hull = ConvexHull(points=unpack_polygons, qhull_options='QG6')
    corner_points = []
    for simplex in hull.simplices:
        x, y = unpack_polygons[simplex, 0], unpack_polygons[simplex, 1]
        corner_points.append([x, y])
        plt.plot(x, y, 'k-')
    corner_points = np.array(corner_points)
    # print('corner_points:', corner_points)
    # print('corner points 0:', corner_points[:, 0])
    # print('corner points 1:', corner_points[:, 1])
    plt.plot(corner_points[:, 0], corner_points[:, 1], 'o')

    # 2nd Plot for Walls
    plt.subplot(122)
    plt.xlim(0, max(map_size))
    plt.ylim(0, max(map_size))

    # List Polygon with Vertices and Center Point
    # for polygon, point in zip(polygons, points):
    #     print('Polygon:\n', polygon, '\nCenter:', point, '\n')

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

    # print('unique_vertices:', unique_vertices)
    # plt.plot([v[0] for v in unique_vertices], [v[1] for v in unique_vertices], '.r-')

    # Center
    x = [p[0] for p in unique_vertices]
    y = [p[1] for p in unique_vertices]
    centroid = (sum(x) / len(unique_vertices), sum(y) / len(unique_vertices))
    # print('centroid:', centroid)
    plt.plot(centroid[0], centroid[1], 'o')

    # Re-Order Vertices in Clockwise Around Centroid
    vertex_angles = []
    for vertex in unique_vertices:
        vertex_angles.append((angle_between(centroid, vertex), vertex))
    vertex_angles = sorted(vertex_angles)
    vertex_angles.append(vertex_angles[0])
    # print('vertex_angles:', vertex_angles)
    plt.plot([v[1][0] for v in vertex_angles], [v[1][1] for v in vertex_angles], '.r-')

    for simplex in hull.simplices:
        x, y = unpack_polygons[simplex, 0], unpack_polygons[simplex, 1]
        # corner_points.append([x, y])
        plt.plot(x, y, 'k-')
    plt.plot(corner_points[:, 0], corner_points[:, 1], 'o')
    # Save/Print Figure
    if not saveas is None:
        plt.savefig(saveas)
    if show:
        print('show:', show)
        plt.show()
    return ax


if __name__ == '__main__':
    s = randint(50, 500)
    size = (s, s)
    size = (25, 25)
    plot_polygons(*voronoi_polygons(n=min(size * 3), map_size=size))
