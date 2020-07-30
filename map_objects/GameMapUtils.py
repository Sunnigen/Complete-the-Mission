def get_blocking_entities_at_location(entities, destination_x, destination_y):
    # Check if Entity is "Blocking" at X, Y Location Specified
    for entity in entities:
        if entity.blocks and entity.position.x == destination_x and entity.position.y == destination_y:
            return entity

    return None


def get_map_object_at_location(map_objects, destination_x, destination_y):
    # Check if Object is "Blocking" at X, Y Location Specified
    for map_object in map_objects:
        if map_object.position.x == destination_x and map_object.position.y == destination_y:
            return map_object
    return None
