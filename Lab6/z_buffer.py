
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import sys


# =========================================================
# GLOBAL VARIABLES
# =========================================================

zoom = 1.0

# Same dark background as Experiment 5
BG_COLOR = (0.03, 0.03, 0.04, 1.0)


# =========================================================
# DRAW CUBE
# =========================================================

def draw_cube(size, color):

    s = size / 2

    vertices = [
        (-s, -s, -s), (s, -s, -s),
        (s, s, -s), (-s, s, -s),
        (-s, -s, s), (s, -s, s),
        (s, s, s), (-s, s, s)
    ]

    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (3, 2, 6, 7),
        (0, 3, 7, 4),
        (1, 5, 6, 2)
    ]

    shades = [1.0, 0.8, 0.7, 0.6, 0.9, 0.5]

    glBegin(GL_QUADS)

    for i, face in enumerate(faces):

        glColor3f(
            color[0] * shades[i],
            color[1] * shades[i],
            color[2] * shades[i]
        )

        for index in face:
            glVertex3f(*vertices[index])

    glEnd()


# =========================================================
# DRAW PYRAMID
# =========================================================

def draw_pyramid(size, color):

    s = size / 2

    vertices = [
        (-s, -s, -s),
        (s, -s, -s),
        (s, -s, s),
        (-s, -s, s),
        (0, s, 0)
    ]

    faces = [
        (0, 1, 2, 3),
        (0, 1, 4),
        (1, 2, 4),
        (2, 3, 4),
        (3, 0, 4)
    ]

    shades = [0.6, 1.0, 0.8, 0.7, 0.9]

    glBegin(GL_QUADS)

    glColor3f(
        color[0] * shades[0],
        color[1] * shades[0],
        color[2] * shades[0]
    )

    for index in faces[0]:
        glVertex3f(*vertices[index])

    glEnd()

    glBegin(GL_TRIANGLES)

    for i in range(1, 5):

        glColor3f(
            color[0] * shades[i],
            color[1] * shades[i],
            color[2] * shades[i]
        )

        for index in faces[i]:
            glVertex3f(*vertices[index])

    glEnd()


# =========================================================
# DRAW SPHERE
# =========================================================

def draw_sphere(size, color):

    glColor3f(*color)

    quadric = gluNewQuadric()

    gluSphere(
        quadric,
        size / 2,
        32,
        24
    )

    gluDeleteQuadric(quadric)


# =========================================================
# DRAW DARK GRID AND AXES
# Grid lies on the XZ plane
# =========================================================

def draw_grid():

    # Dark gray grid, matching Experiment 5
    glColor3f(0.15, 0.15, 0.15)

    glLineWidth(1.0)

    glBegin(GL_LINES)

    for i in range(-20, 21):

        # Lines parallel to Z
        glVertex3f(i, -2, -20)
        glVertex3f(i, -2, 20)

        # Lines parallel to X
        glVertex3f(-20, -2, i)
        glVertex3f(20, -2, i)

    glEnd()

    # Gray coordinate axes
    glColor3f(0.65, 0.65, 0.65)

    glLineWidth(2.0)

    glBegin(GL_LINES)

    # X axis
    glVertex3f(-20, -1.99, 0)
    glVertex3f(20, -1.99, 0)

    # Z axis
    glVertex3f(0, -1.99, -20)
    glVertex3f(0, -1.99, 20)

    glEnd()

    glLineWidth(1.0)


# =========================================================
# DRAW USER-DEFINED OBJECTS
# =========================================================

def draw_objects(objects):

    for obj in objects:

        obj_type, x, y, z, size, color = obj

        glPushMatrix()

        glTranslatef(x, y, z)

        if obj_type == "cube":
            draw_cube(size, color)

        elif obj_type == "pyramid":
            draw_pyramid(size, color)

        elif obj_type == "sphere":
            draw_sphere(size, color)

        glPopMatrix()


# =========================================================
# MOUSE SCROLL ZOOM
# =========================================================

def scroll_callback(window, x_offset, y_offset):

    global zoom

    zoom = max(
        0.2,
        min(5.0, zoom + y_offset * 0.1)
    )


# =========================================================
# INITIALIZE OPENGL
# =========================================================

def initialize_opengl():

    glClearColor(*BG_COLOR)

    # Z-buffer hidden-surface removal
    glEnable(GL_DEPTH_TEST)

    glDepthFunc(GL_LESS)
    glDepthMask(GL_TRUE)


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    global zoom

    print("\n========================================")
    print("   EXPERIMENT 6: Z-BUFFER ALGORITHM")
    print("========================================")

    # -----------------------------------------------------
    # USER INPUT
    # -----------------------------------------------------

    while True:

        try:
            n = int(input("\nEnter number of 3D objects: "))

            if n > 0:
                break

            print("Enter a number greater than zero.")

        except ValueError:
            print("Enter a valid integer.")

    objects = []

    colors = [
        (0.2, 0.6, 1.0),
        (1.0, 0.3, 0.2),
        (0.2, 0.9, 0.3),
        (1.0, 0.8, 0.1),
        (0.8, 0.3, 1.0),
        (0.1, 0.9, 0.9)
    ]

    print("\nAvailable objects: cube, pyramid, sphere")

    for i in range(n):

        print(f"\n--- Object {i + 1} ---")

        while True:

            obj_type = input(
                "Enter type (cube/pyramid/sphere): "
            ).strip().lower()

            if obj_type in ("cube", "pyramid", "sphere"):
                break

            print("Invalid type. Try again.")

        x = float(input("Enter X position: "))
        y = float(input("Enter Y position: "))
        z = float(input("Enter Z position: "))

        size = float(input("Enter object size: "))

        if size <= 0:
            print("Size must be positive.")
            return

        color = colors[i % len(colors)]

        objects.append(
            (obj_type, x, y, z, size, color)
        )

    print("\nObjects entered successfully.")
    print("Z-buffer hidden-surface removal enabled.")

    # -----------------------------------------------------
    # INITIALIZE GLFW
    # -----------------------------------------------------

    if not glfw.init():

        print("Failed to initialize GLFW")
        sys.exit()

    window = glfw.create_window(
        1000,
        800,
        "Experiment 6 - Z-Buffer",
        None,
        None
    )

    if not window:

        glfw.terminate()
        print("Failed to create window")
        sys.exit()

    glfw.make_context_current(window)

    glfw.swap_interval(1)

    glfw.set_scroll_callback(
        window,
        scroll_callback
    )

    initialize_opengl()

    # -----------------------------------------------------
    # AUTOMATIC CAMERA TARGET
    # -----------------------------------------------------

    # Aim at the center of all object positions
    center_x = sum(obj[1] for obj in objects) / n
    center_y = sum(obj[2] for obj in objects) / n
    center_z = sum(obj[3] for obj in objects) / n

    # Estimate a suitable camera distance
    extent = max(
        max(
            abs(obj[1] - center_x),
            abs(obj[2] - center_y),
            abs(obj[3] - center_z)
        ) + obj[4]
        for obj in objects
    )

    camera_distance = max(12.0, extent * 3.0)

    rotation = 0.0

    # -----------------------------------------------------
    # RENDERING LOOP
    # -----------------------------------------------------

    while not glfw.window_should_close(window):

        width, height = glfw.get_framebuffer_size(window)

        if height == 0:
            height = 1

        glViewport(0, 0, width, height)

        # Keyboard zoom
        if (
            glfw.get_key(window, glfw.KEY_EQUAL) == glfw.PRESS
            or glfw.get_key(window, glfw.KEY_KP_ADD) == glfw.PRESS
        ):
            zoom = max(0.2, zoom - 0.02)

        if (
            glfw.get_key(window, glfw.KEY_MINUS) == glfw.PRESS
            or glfw.get_key(window, glfw.KEY_KP_SUBTRACT) == glfw.PRESS
        ):
            zoom = min(5.0, zoom + 0.02)

        if glfw.get_key(window, glfw.KEY_R) == glfw.PRESS:
            zoom = 1.0

        # Projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        gluPerspective(
            45.0 / zoom,
            width / height,
            0.1,
            max(1000.0, camera_distance * 10)
        )

        # Camera
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        gluLookAt(
            center_x + camera_distance,
            center_y + camera_distance * 0.65,
            center_z + camera_distance,
            center_x,
            center_y,
            center_z,
            0, 1, 0
        )

        # Clear both color and depth buffers
        glClear(
            GL_COLOR_BUFFER_BIT |
            GL_DEPTH_BUFFER_BIT
        )

        # Rotate the objects together
        glPushMatrix()

        glTranslatef(center_x, center_y, center_z)
        glRotatef(rotation, 0, 1, 0)
        glTranslatef(-center_x, -center_y, -center_z)

        # Grid and axes
        draw_grid()

        # User-defined objects
        draw_objects(objects)

        glPopMatrix()

        rotation += 0.15

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()
