def check_vertices(list_of_verts, bounding_box, buffer):
    """
    Takes the list of verts from a word, and the bounding box to check it against. Also takes in a buffer size.
    Returns true if the vertices are to the right and on the same plane as the bounding box.
    """
    up, right, down, left = bounding_box
    check_x, check_y = get_bounding_average(list_of_verts)
    if right + buffer < check_x:
        if up <= check_y <= down + buffer:
            return True
    return False


def get_bounding_range(vertices):
    """
    Takes in a list of vertices and returns the upper and lower bounds of the box it creates.
    """
    x_values = [vertex.x for vertex in vertices]
    y_values = [vertex.y for vertex in vertices]

    # Returns the range in the order [Up, Right, Down, Left]
    return [min(y_values), max(x_values), max(y_values), min(x_values)]


def get_bounding_average(vertices):
    """Returns the average x and y value from a bounding range"""
    bounding_box = get_bounding_range(vertices)
    average_x = (bounding_box[1] + bounding_box[3]) / 2
    average_y = (bounding_box[0] + bounding_box[2]) / 2
    return [average_x, average_y]
