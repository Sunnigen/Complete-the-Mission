import numpy as np


from loader_functions import JsonReader

IMPACT_TECH = JsonReader.obtain_json_data("impact_tech")


def get_blocking_entity_at_location(entities, destination_x, destination_y):
    # Check if Entity is "Blocking" at X, Y Location Specified
    for entity in entities:
        if entity.blocks and entity.position.x == destination_x and entity.position.y == destination_y:
            return entity

    return None


def get_blocking_entities_at_location(entities, target_x, target_y, origin_x, origin_y, technique_name=None):
    # print('\nget_blocking_entities_at_location')
    opposite_x = target_x - origin_x
    opposite_y = target_y - origin_y
    targetable_positions = [(target_x, target_y)]

    # print('\n\nopposite_x/opposite_y:', opposite_x, opposite_y)
    """
    opposite_x | opposite_y values:
    -1 -1 = top left       rotate (1) times
     1 -1 = top right      do not rotate
    -1  1 = bottom left    rotate (2) times
     1  1 = bottom right   rotate (3) times
     
     -1  0 = left          rotate (2) times
      1  0 = right         do not rotate
      0 -1 = top           rotate (1) times
      0  1 = bottom        rotate (3) times

    """
    if technique_name:
        technique_dict = IMPACT_TECH.get(technique_name)


        diagonal_vars = {(-1, -1): 3, (1, -1): 2, (-1, 1): 4, (1, 1): 1}
        straight_vars = {(-1, 0): 3, (1, 0): 1, (0, -1): 2, (0, 1): 4}


        if opposite_x != 0 and opposite_y != 0:
            mat = technique_dict.get("diagonal")
            num_of_rotations = diagonal_vars.get((opposite_x, opposite_y))
        else:
            # Rotate Matrix for Correct Target Locations
            mat = technique_dict.get("straight")
            num_of_rotations = straight_vars.get((opposite_x, opposite_y))
        try:
            mat = np.rot90(mat, k=num_of_rotations, axes=(1, 0))
        except TypeError:
            print("TypeError for matrix : ")
            print("k : ", num_of_rotations)
            print("mat : ", mat)

        # Find Coordinates for Beginning of Target Matrix
        dist_to_center = technique_dict.get("center")
        mat_start_x = origin_x - dist_to_center
        mat_start_y = origin_y - dist_to_center
        # print("mat_start_x : ", mat_start_x)
        # print("mat_start_y : ", mat_start_y)

        # Obtain World Target Positions from Matrix
        mat = np.nonzero(mat)

        for x, y in zip(*mat):
            targetable_positions.append((x+mat_start_x, y+mat_start_y))
        # print('targetable_positions:', targetable_positions)




            # targetable_positions = [(origin_x - 1, origin_y - 1),
            #                         (origin_x - 1, origin_y    ),
            #                         (origin_x - 1, origin_y + 1),
            #                         (origin_x + 1, origin_y - 1),
            #                         (origin_x + 1, origin_y    ),
            #                         (origin_x + 1, origin_y + 1),
            #                         (origin_x    , origin_y - 1),
            #                         (origin_x    , origin_y + 1)]


    if (origin_x, origin_y) in targetable_positions:
        targetable_positions.remove((origin_x, origin_y))

    # print('\norigin_x, origin_y:', origin_x, origin_y)
    # print('targetable_positions:', targetable_positions)

    # Check if Entity is "Blocking" at X, Y Location Specified
    main_target = []
    targetable_entities = []
    for entity in entities:

        # Place Main Target to front
        if entity.blocks and (entity.position.x, entity.position.y) == (target_x, target_y) and entity.name != "Player":
            main_target = [entity]
            continue

        if entity.blocks and (entity.position.x, entity.position.y) in targetable_positions:
            targetable_entities.append(entity)
            targetable_positions.remove((entity.position.x, entity.position.y))

    # if not main_target:
    #     return [], targetable_positions

    # Return targetted entities and all rest of tiles
    # print('Technique Used:', technique_name)
    # print("[main_target] + targetable_entities:", [main_target] + targetable_entities)
    # print("targetable_positions:", targetable_positions)
    return main_target + targetable_entities, targetable_positions


def get_map_object_at_location(map_objects, destination_x, destination_y):
    # Check if Object is "Blocking" at X, Y Location Specified
    for map_object in map_objects:
        if map_object.position.x == destination_x and map_object.position.y == destination_y:
            return map_object
    return None
