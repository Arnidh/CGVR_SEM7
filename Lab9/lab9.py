
import math
import random
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

# ============================================================
# EXPERIMENT 9: INTERACTIVE 3D SCENE USING PYTHON + OPENGL
# ============================================================

random.seed(7)

BG_COLOR = (0.03, 0.03, 0.04, 1.0)

player_x = 0.0
player_z = -4.0
player_y = 0.0

yaw = 0.0
pitch = 20.0
camera_distance = 9.0

move_speed = 5.0
vertical_velocity = 0.0
grounded = True

score = 0
total_crystals = 8
elapsed_time = 0.0

right_dragging = False
last_mouse_x = 0.0
last_mouse_y = 0.0

crystals = []
tree_positions = []
rock_positions = []

quadric = None
window = None


# ============================================================
# MATERIALS AND LIGHTING
# ============================================================

def set_material(color, emission=None):
    glColor3f(*color)

    if emission is not None:
        glMaterialfv(
            GL_FRONT_AND_BACK, GL_EMISSION,
            [*emission, 1.0]
        )
    else:
        glMaterialfv(
            GL_FRONT_AND_BACK, GL_EMISSION,
            [0.0, 0.0, 0.0, 1.0]
        )


def setup_lighting():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glLightfv(
        GL_LIGHT0, GL_POSITION,
        [ -8.0, 14.0, -5.0, 1.0 ]
    )
    glLightfv(
        GL_LIGHT0, GL_DIFFUSE,
        [1.0, 0.88, 0.72, 1.0]
    )
    glLightfv(
        GL_LIGHT0, GL_SPECULAR,
        [1.0, 1.0, 1.0, 1.0]
    )

    glLightModelfv(
        GL_LIGHT_MODEL_AMBIENT,
        [0.28, 0.30, 0.38, 1.0]
    )

    glEnable(GL_NORMALIZE)
    glShadeModel(GL_SMOOTH)


# ============================================================
# BASIC 3D PRIMITIVES
# ============================================================

def draw_cube(size, color):
    h = size / 2.0

    faces = [
        ((0, 0, 1),  [(-h,-h,h), (h,-h,h), (h,h,h), (-h,h,h)]),
        ((0, 0,-1),  [(h,-h,-h), (-h,-h,-h), (-h,h,-h), (h,h,-h)]),
        ((1, 0, 0),  [(h,-h,h), (h,-h,-h), (h,h,-h), (h,h,h)]),
        ((-1,0, 0),  [(-h,-h,-h), (-h,-h,h), (-h,h,h), (-h,h,-h)]),
        ((0, 1, 0),  [(-h,h,h), (h,h,h), (h,h,-h), (-h,h,-h)]),
        ((0,-1, 0),  [(-h,-h,-h), (h,-h,-h), (h,-h,h), (-h,-h,h)])
    ]

    set_material(color)
    glBegin(GL_QUADS)

    for normal, vertices in faces:
        glNormal3f(*normal)
        for vertex in vertices:
            glVertex3f(*vertex)

    glEnd()


def draw_sphere(radius, color, slices=18, stacks=12):
    set_material(color)
    gluSphere(quadric, radius, slices, stacks)


def draw_cylinder(radius, height, color, top_radius=None):
    if top_radius is None:
        top_radius = radius

    set_material(color)

    # GLU cylinders extend along +Z; rotate to make them vertical.
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)

    gluCylinder(
        quadric, radius, top_radius,
        height, 16, 3
    )

    gluDisk(quadric, 0, radius, 16, 1)

    glTranslatef(0, 0, height)
    gluDisk(quadric, 0, top_radius, 16, 1)

    glPopMatrix()


def draw_octahedron(size, color):
    s = size

    points = [
        np.array([0.0, s, 0.0]),
        np.array([0.0, -s, 0.0]),
        np.array([s, 0.0, 0.0]),
        np.array([-s, 0.0, 0.0]),
        np.array([0.0, 0.0, s]),
        np.array([0.0, 0.0, -s])
    ]

    triangles = [
        (0, 2, 4), (0, 4, 3),
        (0, 3, 5), (0, 5, 2),
        (1, 4, 2), (1, 3, 4),
        (1, 5, 3), (1, 2, 5)
    ]

    set_material(color)
    glBegin(GL_TRIANGLES)

    for ia, ib, ic in triangles:
        a, b, c = points[ia], points[ib], points[ic]
        normal = np.cross(b - a, c - a)

        length = np.linalg.norm(normal)
        if length > 0:
            normal = normal / length

        # Ensure the normal points outward.
        center = (a + b + c) / 3.0
        if np.dot(normal, center) < 0:
            normal = -normal
            b, c = c, b

        glNormal3f(*normal)

        for point in (a, b, c):
            glVertex3f(*point)

    glEnd()


# ============================================================
# WORLD GENERATION
# ============================================================

def create_world_data():
    global crystals, tree_positions, rock_positions

    crystals = [
        [-5, 1.2, -5],
        [ 5, 1.2, -5],
        [-7, 1.2,  1],
        [ 7, 1.2,  1],
        [-5, 1.2,  7],
        [ 5, 1.2,  8],
        [ 0, 1.2, 10],
        [ 0, 1.2, -10]
    ]

    tree_positions = []

    for i in range(14):
        a = 2 * math.pi * i / 14
        r = random.uniform(9.0, 11.0)

        tree_positions.append((
            math.cos(a) * r,
            math.sin(a) * r,
            random.uniform(0.8, 1.2)
        ))

    rock_positions = []

    for i in range(25):
        a = random.uniform(0, 2 * math.pi)
        r = random.uniform(7.5, 11.8)

        rock_positions.append((
            math.cos(a) * r,
            math.sin(a) * r,
            random.uniform(0.35, 0.85)
        ))


def draw_water():
    glDisable(GL_LIGHTING)
    glColor3f(0.025, 0.12, 0.19)

    glBegin(GL_QUADS)
    glVertex3f(-100, -1.3, -100)
    glVertex3f(100, -1.3, -100)
    glVertex3f(100, -1.3, 100)
    glVertex3f(-100, -1.3, 100)
    glEnd()

    # Water ripple lines.
    glColor3f(0.05, 0.22, 0.29)
    glBegin(GL_LINES)

    for z in range(-45, 46, 5):
        for x in range(-45, 46, 10):
            glVertex3f(x, -1.28, z)
            glVertex3f(x + 3, -1.28, z)

    glEnd()
    glEnable(GL_LIGHTING)


def draw_island():
    # Island body.
    glPushMatrix()
    glTranslatef(0, -0.8, 0)
    draw_cylinder(12.0, 0.8, (0.27, 0.20, 0.13), 10.5)
    glPopMatrix()

    # Grass surface.
    glPushMatrix()
    glTranslatef(0, -0.02, 0)
    draw_cylinder(10.5, 0.12, (0.17, 0.36, 0.19), 10.5)
    glPopMatrix()


def draw_tree(x, z, scale):
    glPushMatrix()
    glTranslatef(x, 0, z)
    glScalef(scale, scale, scale)

    # Trunk.
    glPushMatrix()
    glTranslatef(0, 0.85, 0)
    draw_cylinder(0.23, 1.7, (0.32, 0.17, 0.08))
    glPopMatrix()

    # Three overlapping foliage layers.
    for y, radius in [(2.0, 1.1), (2.8, 0.85), (3.5, 0.58)]:
        glPushMatrix()
        glTranslatef(0, y, 0)
        draw_cylinder(radius, 1.45, (0.08, 0.27, 0.13), 0.0)
        glPopMatrix()

    glPopMatrix()


def draw_environment():
    draw_water()
    draw_island()

    # Stone path.
    for i in range(9):
        z = -9 + i * 2.1

        glPushMatrix()
        glTranslatef(0, 0.12, z)
        glRotatef(math.sin(i) * 4, 0, 1, 0)
        draw_cube(1.0, (0.44, 0.39, 0.31))
        glScalef(2.0, 0.12, 1.35)
        draw_cube(1.0, (0.44, 0.39, 0.31))
        glPopMatrix()

    for x, z, scale in tree_positions:
        draw_tree(x, z, scale)

    # Rocks around the island.
    for x, z, size in rock_positions:
        glPushMatrix()
        glTranslatef(x, size * 0.45, z)
        glRotatef((x * z) % 360, 0, 1, 0)
        glScalef(size * 1.3, size * 0.8, size)
        draw_sphere(1.0, (0.32, 0.34, 0.37), 10, 8)
        glPopMatrix()

    # Monument.
    glPushMatrix()
    glTranslatef(0, 0, 7)

    draw_cylinder(1.3, 0.4, (0.65, 0.43, 0.14))

    glPushMatrix()
    glTranslatef(0, 0.4, 0)
    draw_cylinder(0.38, 2.1, (0.42, 0.43, 0.48))
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 3.0 + math.sin(elapsed_time * 2) * 0.15, 0)
    glRotatef(elapsed_time * 65, 0, 1, 0)
    draw_octahedron(0.65, (0.05, 0.8, 1.0))
    glPopMatrix()

    glPopMatrix()


# ============================================================
# COLLECTIBLES AND PLAYER
# ============================================================

def draw_crystals():
    for i, p in enumerate(crystals):
        if p is None:
            continue

        x, y, z = p

        glPushMatrix()
        glTranslatef(x, y + math.sin(elapsed_time * 2 + i) * 0.2, z)
        glRotatef(elapsed_time * 75 + i * 35, 0, 1, 0)
        draw_octahedron(0.65, (0.0, 0.8, 1.0))
        glPopMatrix()


def draw_player():
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z)

    # Body.
    glPushMatrix()
    glTranslatef(0, 0.9, 0)
    draw_cylinder(0.38, 0.85, (0.94, 0.32, 0.12))
    glPopMatrix()

    # Head.
    glPushMatrix()
    glTranslatef(0, 1.95, 0)
    draw_sphere(0.34, (0.95, 0.68, 0.48))
    glPopMatrix()

    # Backpack.
    glPushMatrix()
    glTranslatef(0, 0.95, -0.38)
    draw_cube(0.45, (0.95, 0.63, 0.12))
    glPopMatrix()

    # Feet.
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side * 0.2, 0.12, 0.05)
        draw_sphere(0.18, (0.12, 0.15, 0.2), 10, 8)
        glPopMatrix()

    glPopMatrix()


def check_collection():
    global score, crystals

    for i, p in enumerate(crystals):
        if p is None:
            continue

        distance = math.sqrt(
            (player_x - p[0]) ** 2
            + (player_y + 1.0 - p[1]) ** 2
            + (player_z - p[2]) ** 2
        )

        if distance < 1.5:
            crystals[i] = None
            score += 1
            glfw.set_window_title(
                window,
                f"Experiment 9 - Crystals: {score}/{total_crystals}"
            )

            print(f"Crystal collected! Score: {score}/{total_crystals}")

            if score == total_crystals:
                print("MISSION COMPLETE! All crystals collected.")


# ============================================================
# CAMERA AND INPUT
# ============================================================

def update_camera():
    target_x = player_x
    target_y = player_y + 1.2
    target_z = player_z

    yaw_r = math.radians(yaw)
    pitch_r = math.radians(pitch)

    horizontal = camera_distance * math.cos(pitch_r)

    cam_x = target_x + math.sin(yaw_r) * horizontal
    cam_y = target_y + camera_distance * math.sin(pitch_r)
    cam_z = target_z - math.cos(yaw_r) * horizontal

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    gluLookAt(
        cam_x, cam_y, cam_z,
        target_x, target_y, target_z,
        0, 1, 0
    )


def mouse_button_callback(win, button, action, mods):
    global right_dragging, last_mouse_x, last_mouse_y

    if button == glfw.MOUSE_BUTTON_RIGHT:
        right_dragging = action == glfw.PRESS
        last_mouse_x, last_mouse_y = glfw.get_cursor_pos(win)


def cursor_callback(win, xpos, ypos):
    global yaw, pitch, last_mouse_x, last_mouse_y

    if right_dragging:
        dx = xpos - last_mouse_x
        dy = ypos - last_mouse_y

        yaw += dx * 0.35
        pitch = max(8.0, min(65.0, pitch - dy * 0.25))

    last_mouse_x, last_mouse_y = xpos, ypos


def scroll_callback(win, xoffset, yoffset):
    global camera_distance
    camera_distance = max(
        4.0, min(18.0, camera_distance - yoffset * 0.8)
    )


def key_callback(win, key, scancode, action, mods):
    global score, crystals, player_x, player_z, player_y
    global vertical_velocity, grounded, elapsed_time

    if action != glfw.PRESS:
        return

    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(win, True)

    elif key == glfw.KEY_R:
        score = 0
        crystals = [
            [-5, 1.2, -5], [5, 1.2, -5],
            [-7, 1.2, 1], [7, 1.2, 1],
            [-5, 1.2, 7], [5, 1.2, 8],
            [0, 1.2, 10], [0, 1.2, -10]
        ]

        player_x, player_z, player_y = 0.0, -4.0, 0.0
        vertical_velocity = 0.0
        grounded = True
        elapsed_time = 0.0

        glfw.set_window_title(
            win, "Experiment 9 - Interactive 3D Island"
        )

        print("Scene restarted.")


def handle_movement(dt):
    global player_x, player_z, player_y
    global vertical_velocity, grounded

    forward = 0.0
    side = 0.0

    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        forward += 1

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        forward -= 1

    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        side += 1

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        side -= 1

    speed = move_speed

    if glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
        speed *= 1.7

    length = math.sqrt(forward * forward + side * side)

    if length > 0:
        forward /= length
        side /= length

    angle = math.radians(yaw)

    dx = math.sin(angle) * forward + math.cos(angle) * side
    dz = math.cos(angle) * forward - math.sin(angle) * side

    player_x += dx * speed * dt
    player_z += dz * speed * dt

    # Keep the explorer on the island.
    radius = math.sqrt(player_x * player_x + player_z * player_z)

    if radius > 10.0:
        player_x *= 10.0 / radius
        player_z *= 10.0 / radius

    if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS and grounded:
        vertical_velocity = 7.0
        grounded = False

    vertical_velocity -= 18.0 * dt
    player_y += vertical_velocity * dt

    if player_y <= 0:
        player_y = 0
        vertical_velocity = 0
        grounded = True


# ============================================================
# HUD USING WINDOW TITLE AND TERMINAL
# ============================================================

def print_controls():
    print("""
====================================================
 EXPERIMENT 9: INTERACTIVE 3D SCENE USING OPENGL
====================================================
W / A / S / D or Arrow keys : Move
Left Shift                  : Sprint
Space                       : Jump
Right mouse button + drag   : Rotate camera
Mouse wheel                 : Zoom camera
R                           : Restart scene
Esc                         : Exit

Objective: Explore the island and collect all 8
glowing energy crystals.
====================================================
""")


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    global window, quadric, elapsed_time

    if not glfw.init():
        raise RuntimeError("Could not initialize GLFW.")

    # Compatibility context for immediate-mode OpenGL and GLU.
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)

    window = glfw.create_window(
        1100, 800,
        "Experiment 9 - Interactive 3D Island",
        None, None
    )

    if not window:
        glfw.terminate()
        raise RuntimeError("Could not create OpenGL window.")

    glfw.make_context_current(window)
    glfw.swap_interval(1)

    glfw.set_key_callback(window, key_callback)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_callback)
    glfw.set_scroll_callback(window, scroll_callback)

    glClearColor(*BG_COLOR)
    setup_lighting()

    global quadric
    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)

    create_world_data()
    print_controls()

    previous_time = glfw.get_time()

    while not glfw.window_should_close(window):
        current_time = glfw.get_time()
        dt = min(current_time - previous_time, 0.05)
        previous_time = current_time
        elapsed_time += dt

        handle_movement(dt)
        check_collection()

        width, height = glfw.get_framebuffer_size(window)

        if height == 0 or width == 0:
            glfw.poll_events()
            continue

        glViewport(0, 0, width, height)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        gluPerspective(
            65.0,
            width / float(height),
            0.1,
            250.0
        )

        update_camera()

        draw_environment()
        draw_crystals()
        draw_player()

        glfw.swap_buffers(window)
        glfw.poll_events()

    gluDeleteQuadric(quadric)
    glfw.terminate()


if __name__ == "__main__":
    main()
