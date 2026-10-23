
import math
import glfw
import numpy as np
from OpenGL.GL import *

# --------------------------------------------------
# EXPERIMENT 7: 2D GEOMETRIC TRANSFORMATIONS
# Using Homogeneous Coordinates and Transformation
# Matrices
# --------------------------------------------------

BG_COLOR = (0.03, 0.03, 0.04, 1.0)

zoom = 1.0
animation = False
last_time = 0.0

# Original polygon vertices (homogeneous coordinates)
polygon = np.array([
    [-4.0, -2.0, 1.0],
    [ 0.0, -4.0, 1.0],
    [ 4.0, -2.0, 1.0],
    [ 3.0,  3.0, 1.0],
    [-3.0,  3.0, 1.0]
], dtype=float)

# Composite transformation matrix
M = np.identity(3)


# --------------------------------------------------
# HOMOGENEOUS TRANSFORMATION MATRICES
# --------------------------------------------------

def translation(tx, ty):
    return np.array([
        [1, 0, tx],
        [0, 1, ty],
        [0, 0,  1]
    ], dtype=float)


def rotation(angle_degrees):
    theta = math.radians(angle_degrees)
    c = math.cos(theta)
    s = math.sin(theta)

    return np.array([
        [c, -s, 0],
        [s,  c, 0],
        [0,  0, 1]
    ], dtype=float)


def scaling(sx, sy):
    return np.array([
        [sx,  0, 0],
        [ 0, sy, 0],
        [ 0,  0, 1]
    ], dtype=float)


def reflection_x():
    # Reflection about the X-axis
    return np.array([
        [1,  0, 0],
        [0, -1, 0],
        [0,  0, 1]
    ], dtype=float)


def reflection_y():
    # Reflection about the Y-axis
    return np.array([
        [-1, 0, 0],
        [ 0, 1, 0],
        [ 0, 0, 1]
    ], dtype=float)


def reflection_y_eq_x():
    # Reflection about the line y = x
    return np.array([
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1]
    ], dtype=float)


def shearing(shx, shy):
    return np.array([
        [1,  shx, 0],
        [shy, 1,  0],
        [0,   0,  1]
    ], dtype=float)


def rotation_about_pivot(angle, px, py):
    # Move pivot to origin, rotate, move it back
    return (
        translation(px, py)
        @ rotation(angle)
        @ translation(-px, -py)
    )


# --------------------------------------------------
# SINGLE MATRIX MULTIPLICATION FUNCTION
# --------------------------------------------------

def apply_transformation(T):
    global M

    # Column-vector convention:
    # New composite matrix = T @ M
    M = T @ M

    print("\nTransformation applied.")
    print("Current composite matrix:")
    print(np.round(M, 3))


def reset():
    global M, animation
    M = np.identity(3)
    animation = False
    print("\nObject reset to original position.")


# --------------------------------------------------
# DRAWING FUNCTIONS
# --------------------------------------------------

def draw_grid():
    glLineWidth(1.0)
    glColor3f(0.15, 0.15, 0.15)

    glBegin(GL_LINES)
    for i in range(-20, 21):
        glVertex2f(i, -20)
        glVertex2f(i, 20)

        glVertex2f(-20, i)
        glVertex2f(20, i)
    glEnd()

    # Coordinate axes
    glLineWidth(2.0)
    glColor3f(0.65, 0.65, 0.65)

    glBegin(GL_LINES)
    glVertex2f(-20, 0)
    glVertex2f(20, 0)

    glVertex2f(0, -20)
    glVertex2f(0, 20)
    glEnd()

    glLineWidth(1.0)


def draw_polygon(vertices, filled, color):
    glColor3f(*color)

    if filled:
        glBegin(GL_TRIANGLE_FAN)
    else:
        glBegin(GL_LINE_LOOP)

    for vertex in vertices:
        glVertex2f(float(vertex[0]), float(vertex[1]))

    glEnd()


def draw_pivot():
    # Arbitrary pivot used for rotation: (3, 2)
    glPointSize(9.0)
    glColor3f(1.0, 0.3, 0.2)

    glBegin(GL_POINTS)
    glVertex2f(3.0, 2.0)
    glEnd()

    glPointSize(1.0)


def transform_vertices():
    # Apply composite matrix to every homogeneous vertex
    result = (M @ polygon.T).T
    return result[:, :2]


# --------------------------------------------------
# INTERACTIVE KEYBOARD MENU
# --------------------------------------------------

def print_menu():
    print("""
=================================================
 EXPERIMENT 7: 2D GEOMETRIC TRANSFORMATIONS
=================================================
 1 : Translation (+2, +1)
 2 : Rotation by 15 degrees about origin
 3 : Non-uniform scaling (1.2, 0.8)
 4 : Reflection about X-axis
 5 : Reflection about Y-axis
 6 : Reflection about line y = x
 7 : Shearing (shx=0.3, shy=0)
 8 : Rotation by 15 degrees about pivot (3, 2)
 9 : Toggle continuous rotation
 0 : Reset all transformations
 R : Reset zoom
 ESC : Exit
=================================================
Transformations are composed using matrix products.
Use the mouse wheel or +/- keys to zoom.
""")


def key_callback(window, key, scancode, action, mods):
    global zoom, animation, last_time, M

    if action != glfw.PRESS:
        return

    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)

    elif key == glfw.KEY_1:
        apply_transformation(translation(2, 1))

    elif key == glfw.KEY_2:
        apply_transformation(rotation(15))

    elif key == glfw.KEY_3:
        apply_transformation(scaling(1.2, 0.8))

    elif key == glfw.KEY_4:
        apply_transformation(reflection_x())

    elif key == glfw.KEY_5:
        apply_transformation(reflection_y())

    elif key == glfw.KEY_6:
        apply_transformation(reflection_y_eq_x())

    elif key == glfw.KEY_7:
        apply_transformation(shearing(0.3, 0.0))

    elif key == glfw.KEY_8:
        apply_transformation(rotation_about_pivot(15, 3, 2))

    elif key == glfw.KEY_9:
        animation = not animation
        last_time = glfw.get_time()
        print("Continuous rotation:", "ON" if animation else "OFF")

    elif key == glfw.KEY_0:
        reset()

    elif key == glfw.KEY_R:
        zoom = 1.0
        print("Zoom reset.")

    elif key in (glfw.KEY_EQUAL, glfw.KEY_KP_ADD):
        zoom = min(zoom * 1.1, 5.0)

    elif key in (glfw.KEY_MINUS, glfw.KEY_KP_SUBTRACT):
        zoom = max(zoom / 1.1, 0.2)


def scroll_callback(window, xoffset, yoffset):
    global zoom

    if yoffset > 0:
        zoom = min(zoom * 1.1, 5.0)
    elif yoffset < 0:
        zoom = max(zoom / 1.1, 0.2)


# --------------------------------------------------
# MAIN OPENGL PROGRAM
# --------------------------------------------------

def main():
    global M, last_time

    if not glfw.init():
        raise RuntimeError("Could not initialize GLFW.")

    window = glfw.create_window(
        1000, 800,
        "Experiment 7 - 2D Transformations",
        None, None
    )

    if not window:
        glfw.terminate()
        raise RuntimeError("Could not create OpenGL window.")

    glfw.make_context_current(window)
    glfw.swap_interval(1)

    glfw.set_key_callback(window, key_callback)
    glfw.set_scroll_callback(window, scroll_callback)

    glClearColor(*BG_COLOR)
    glDisable(GL_DEPTH_TEST)

    print_menu()

    last_time = glfw.get_time()

    while not glfw.window_should_close(window):
        current_time = glfw.get_time()
        delta_time = current_time - last_time
        last_time = current_time

        # Continuous rotation animation
        if animation:
            angle = 60.0 * delta_time
            M = rotation(angle) @ M

        width, height = glfw.get_framebuffer_size(window)
        if height == 0:
            glfw.poll_events()
            continue

        glViewport(0, 0, width, height)
        glClear(GL_COLOR_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        aspect = width / height
        half_height = 20.0 / zoom
        half_width = half_height * aspect

        glOrtho(
            -half_width, half_width,
            -half_height, half_height,
            -1, 1
        )

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        draw_grid()

        # Original polygon shown as a gray outline
        draw_polygon(
            polygon[:, :2],
            False,
            (0.65, 0.65, 0.65)
        )

        # Transformed polygon shown in cyan
        transformed = transform_vertices()
        draw_polygon(
            transformed,
            True,
            (0.0, 0.65, 0.9)
        )

        # Transformed outline for clarity
        draw_polygon(
            transformed,
            False,
            (0.4, 0.9, 1.0)
        )

        draw_pivot()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
