def check_vertices(list_of_verts, bounding_box, buffer, height, width):
    """
    Takes the list of verts from a word, and the bounding box to check it against. Also takes in a buffer size.
    Returns true if the vertices are to the right and on the same plane as the bounding box.
    """
    # print("verts: ", list_of_verts, "box: ", bounding_box)
    up, right, down, left = bounding_box
    check_x, check_y = get_bounding_average(list_of_verts, height, width)
    if right + buffer < check_x:
        if up <= check_y <= down + buffer:
            return True
    return False


def get_bounding_range(vertices, height, width):
    """
    Takes in a list of vertices and returns the upper and lower bounds of the box it creates.
    """
    x_values = [vertex["x"] * width if "x" in vertex else 0 for vertex in vertices]
    y_values = [vertex["y"] * height if "y" in vertex else 0 for vertex in vertices]

    # Returns the range in the order [Up, Right, Down, Left]
    return [min(y_values), max(x_values), max(y_values), min(x_values)]


def get_bounding_average(vertices, height, width):
    """Returns the average x and y value from a bounding range"""
    bounding_box = get_bounding_range(vertices, height, width)
    average_x = (bounding_box[1] + bounding_box[3]) / 2
    average_y = (bounding_box[0] + bounding_box[2]) / 2
    return [average_x, average_y]
