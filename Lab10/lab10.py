
import math
import random
import glfw

from OpenGL.GL import *
from OpenGL.GLU import *


# ============================================================
# EXPERIMENT 10 - 3D VIEWING PIPELINE
# Fixed top-down orthographic view on the right.
# Interactive perspective view on the left.
# ============================================================

WIDTH = 1520
HEIGHT = 900

BG = (0.015, 0.025, 0.04, 1.0)

ISLAND_RADIUS = 12.0
CAMERA_DISTANCE = 14.0

# Player position
player_x = 0.0
player_z = 4.0
player_y = 0.0
player_angle = 0.0
player_speed = 5.0
player_vertical_speed = 0.0
jumping = False

# Interactive left camera
camera_yaw = 0.0
camera_pitch = 38.0
camera_distance = CAMERA_DISTANCE

# Input state
left_drag = False
right_drag = False
last_mouse_x = 0.0
last_mouse_y = 0.0

# Display options
show_grid = True
show_axes = True
show_boxes = False
show_crystals = True
animate_monument = True
split_screen = True

# Animation
scene_time = 0.0

# OpenGL quadric
quadric = None

# Collectibles
crystals = [
    [-7.0,  1.0, -5.0, False],
    [-3.0,  1.0, -8.0, False],
    [ 3.0,  1.0, -8.0, False],
    [ 7.0,  1.0, -4.0, False],
    [-7.0,  1.0,  1.0, False],
    [ 7.0,  1.0,  2.0, False],
    [-5.0,  1.0,  7.0, False],
    [ 5.0,  1.0,  7.0, False],
]

# Trees and rocks are placed around the island.
trees = [
    (-9, -6), (-5, -9), (0, -9), (5, -9), (9, -6),
    (-10, -1), (10, 0), (-9, 4), (9, 5),
    (-6, 9), (-1, 10), (4, 9), (7, 7), (0, 6)
]

rocks = [
    (-10, -4), (-7, -8), (-3, -10), (3, -10),
    (8, -8), (10, -3), (10, 3), (8, 7),
    (3, 10), (-3, 10), (-8, 7), (-10, 2),
    (-6, 2), (-8, 4), (7, -1), (5, 6)
]


# ============================================================
# BASIC DRAWING HELPERS
# ============================================================

def set_material(r, g, b, shininess=16):
    glColor3f(r, g, b)
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE,
                 (r, g, b, 1.0))
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shininess)


def draw_cube(x, y, z, sx, sy, sz, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    set_material(*color)

    glBegin(GL_QUADS)

    # Front
    glNormal3f(0, 0, 1)
    glVertex3f(-0.5, -0.5, 0.5)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(-0.5, 0.5, 0.5)

    # Back
    glNormal3f(0, 0, -1)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(-0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)

    # Left
    glNormal3f(-1, 0, 0)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(-0.5, -0.5, 0.5)
    glVertex3f(-0.5, 0.5, 0.5)
    glVertex3f(-0.5, 0.5, -0.5)

    # Right
    glNormal3f(1, 0, 0)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, 0.5)

    # Top
    glNormal3f(0, 1, 0)
    glVertex3f(-0.5, 0.5, 0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(-0.5, 0.5, -0.5)

    # Bottom
    glNormal3f(0, -1, 0)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(-0.5, -0.5, 0.5)

    glEnd()
    glPopMatrix()


def draw_sphere(x, y, z, radius, color, slices=14, stacks=10):
    glPushMatrix()
    glTranslatef(x, y, z)
    set_material(*color)
    gluSphere(quadric, radius, slices, stacks)
    glPopMatrix()


def draw_cylinder(x, y, z, radius, height, color,
                  slices=16, top_radius=None):
    if top_radius is None:
        top_radius = radius

    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(-90, 1, 0, 0)
    set_material(*color)
    gluCylinder(quadric, radius, top_radius, height, slices, 2)
    gluDisk(quadric, 0, radius, slices, 1)
    glTranslatef(0, 0, height)
    gluDisk(quadric, 0, top_radius, slices, 1)
    glPopMatrix()


def draw_cone(x, y, z, radius, height, color):
    draw_cylinder(
        x, y, z, radius, height, color,
        slices=18, top_radius=0.0
    )


# ============================================================
# GRID AND AXES
# ============================================================

def draw_grid():
    if not show_grid:
        return

    glDisable(GL_LIGHTING)
    glLineWidth(1.0)
    glColor3f(0.10, 0.15, 0.19)

    glBegin(GL_LINES)
    for i in range(-18, 19):
        glVertex3f(i, -1.12, -18)
        glVertex3f(i, -1.12, 18)
        glVertex3f(-18, -1.12, i)
        glVertex3f(18, -1.12, i)
    glEnd()

    glEnable(GL_LIGHTING)


def draw_axes():
    if not show_axes:
        return

    glDisable(GL_LIGHTING)
    glLineWidth(2.0)

    glBegin(GL_LINES)
    # X axis: red
    glColor3f(1.0, 0.15, 0.12)
    glVertex3f(-15, -0.95, 0)
    glVertex3f(15, -0.95, 0)

    # Y axis: green
    glColor3f(0.1, 1.0, 0.25)
    glVertex3f(0, -1.0, 0)
    glVertex3f(0, 5, 0)

    # Z axis: blue
    glColor3f(0.1, 0.45, 1.0)
    glVertex3f(0, -0.95, -15)
    glVertex3f(0, -0.95, 15)
    glEnd()

    glEnable(GL_LIGHTING)


# ============================================================
# ISLAND ENVIRONMENT
# ============================================================

def draw_water():
    glDisable(GL_LIGHTING)
    glColor3f(0.008, 0.055, 0.09)

    glBegin(GL_QUADS)
    glVertex3f(-40, -1.4, -40)
    glVertex3f(40, -1.4, -40)
    glVertex3f(40, -1.4, 40)
    glVertex3f(-40, -1.4, 40)
    glEnd()

    glEnable(GL_LIGHTING)


def draw_island():
    # Brown outer edge of the island.
    draw_cylinder(
        0, -1.0, 0, ISLAND_RADIUS, 1.0,
        (0.25, 0.12, 0.07), slices=48
    )

    # Green top surface.
    draw_cylinder(
        0, -0.05, 0, ISLAND_RADIUS - 0.65, 0.15,
        (0.035, 0.34, 0.11), slices=48
    )


def draw_path():
    # Stepping stones lead toward the monument.
    for z in range(7, -7, -2):
        draw_cube(
            0, 0.13, z,
            2.2, 0.22, 1.45,
            (0.48, 0.34, 0.22)
        )


def draw_tree(x, z):
    glPushMatrix()
    glTranslatef(x, 0.0, z)

    draw_cylinder(
        0, 0.0, 0, 0.20, 1.15,
        (0.24, 0.12, 0.055), slices=10
    )

    draw_cone(0, 0.85, 0, 0.85, 1.5, (0.005, 0.20, 0.065))
    draw_cone(0, 1.55, 0, 0.62, 1.3, (0.005, 0.15, 0.045))
    draw_cone(0, 2.10, 0, 0.40, 1.0, (0.005, 0.12, 0.035))

    glPopMatrix()


def draw_rock(x, z, index):
    random.seed(index + 30)
    radius = random.uniform(0.30, 0.62)
    scale_x = random.uniform(0.9, 1.5)
    scale_z = random.uniform(0.8, 1.35)

    glPushMatrix()
    glTranslatef(x, -0.02, z)
    glScalef(scale_x, 0.72, scale_z)
    set_material(0.24, 0.26, 0.30)
    gluSphere(quadric, radius, 12, 8)
    glPopMatrix()


def draw_monument():
    glPushMatrix()

    if animate_monument:
        glRotatef(scene_time * 15.0, 0, 1, 0)

    # Base platform.
    draw_cube(0, 0.30, -5.0, 2.5, 0.50, 2.5, (0.48, 0.34, 0.20))

    # Gold circular pedestal.
    draw_cylinder(
        0, 0.55, -5.0, 1.25, 0.35,
        (0.95, 0.43, 0.015), slices=28
    )

    # Central pillar.
    draw_cylinder(
        0, 0.90, -5.0, 0.40, 1.45,
        (0.30, 0.28, 0.36), slices=18
    )

    glPopMatrix()


# ============================================================
# PLAYER AND COLLECTIBLES
# ============================================================

def draw_player():
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z)
    glRotatef(player_angle, 0, 1, 0)

    # Legs
    draw_cube(-0.18, 0.28, 0, 0.22, 0.55, 0.25, (0.95, 0.65, 0.02))
    draw_cube(0.18, 0.28, 0, 0.22, 0.55, 0.25, (0.95, 0.65, 0.02))

    # Body
    draw_cylinder(
        0, 0.85, 0, 0.42, 0.85,
        (0.55, 0.08, 0.025), slices=18
    )

    # Orange collar
    draw_cylinder(
        0, 1.48, 0, 0.43, 0.18,
        (1.0, 0.20, 0.015), slices=18
    )

    # Head
    draw_sphere(0, 1.85, 0, 0.40, (1.0, 0.57, 0.31), 18, 12)

    if show_boxes:
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.85, 0.1)
        glBegin(GL_LINES)

        x1, x2 = -0.5, 0.5
        y1, y2 = 0.0, 2.25
        z1, z2 = -0.4, 0.4

        for y in (y1, y2):
            for z in (z1, z2):
                glVertex3f(x1, y, z)
                glVertex3f(x2, y, z)
            for x in (x1, x2):
                glVertex3f(x, y, z1)
                glVertex3f(x, y, z2)

        for x in (x1, x2):
            for z in (z1, z2):
                glVertex3f(x, y1, z)
                glVertex3f(x, y2, z)

        glEnd()
        glEnable(GL_LIGHTING)

    glPopMatrix()


def draw_crystal(x, y, z, phase):
    bob = math.sin(scene_time * 2.5 + phase) * 0.18

    glPushMatrix()
    glTranslatef(x, y + bob, z)
    glRotatef(scene_time * 50 + phase * 40, 0, 1, 0)

    glDisable(GL_LIGHTING)
    glColor3f(0.0, 0.8, 1.0)

    # Octahedron
    size = 0.62
    glBegin(GL_TRIANGLES)

    top = (0, size, 0)
    bottom = (0, -size, 0)
    points = [
        (size * 0.7, 0, 0),
        (0, 0, size * 0.7),
        (-size * 0.7, 0, 0),
        (0, 0, -size * 0.7),
    ]

    for i in range(4):
        a = points[i]
        b = points[(i + 1) % 4]

        glVertex3f(*top)
        glVertex3f(*a)
        glVertex3f(*b)

        glVertex3f(*bottom)
        glVertex3f(*b)
        glVertex3f(*a)

    glEnd()
    glEnable(GL_LIGHTING)
    glPopMatrix()


def collect_crystals():
    for crystal in crystals:
        if crystal[3]:
            continue

        dx = player_x - crystal[0]
        dz = player_z - crystal[2]

        if math.sqrt(dx * dx + dz * dz) < 1.15:
            crystal[3] = True


def draw_environment():
    draw_water()
    draw_grid()
    draw_axes()
    draw_island()
    draw_path()

    for i, (x, z) in enumerate(trees):
        draw_tree(x, z)

    for i, (x, z) in enumerate(rocks):
        draw_rock(x, z, i)

    draw_monument()

    if show_crystals:
        for i, crystal in enumerate(crystals):
            if not crystal[3]:
                draw_crystal(crystal[0], crystal[1], crystal[2], i)


# ============================================================
# CAMERA AND PROJECTION
# ============================================================

def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glLightfv(GL_LIGHT0, GL_POSITION, (8.0, 18.0, 8.0, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.34, 0.34, 0.34, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.95, 0.95, 0.95, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.45, 0.45, 0.45, 1.0))

    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glShadeModel(GL_SMOOTH)


def setup_camera(width, height, top_view=False):
    aspect = max(width / max(height, 1), 0.01)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    if top_view:
        # FIXED TOP-DOWN ORTHOGRAPHIC CAMERA.
        # It does not use camera_yaw, camera_pitch or camera_distance.
        view_size = 15.0
        glOrtho(
            -view_size * aspect,
            view_size * aspect,
            -view_size,
            view_size,
            0.1,
            100.0
        )
    else:
        # Interactive perspective projection for the left viewport.
        gluPerspective(55.0, aspect, 0.1, 100.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if top_view:
        # Looking vertically down at the centre of the island.
        # Negative Z is the camera's up direction on screen.
        gluLookAt(
            0.0, 32.0, 0.0,
            0.0,  0.0, 0.0,
            0.0,  0.0, -1.0
        )
    else:
        # Mouse-responsive orbit camera follows the player.
        yaw = math.radians(camera_yaw)
        pitch = math.radians(camera_pitch)

        target_x = player_x
        target_y = 0.5
        target_z = player_z

        eye_x = target_x + camera_distance * math.cos(pitch) * math.sin(yaw)
        eye_y = target_y + camera_distance * math.sin(pitch)
        eye_z = target_z + camera_distance * math.cos(pitch) * math.cos(yaw)

        gluLookAt(
            eye_x, eye_y, eye_z,
            target_x, target_y, target_z,
            0.0, 1.0, 0.0
        )


# ============================================================
# SIMPLE HUD TEXT
# ============================================================

FONT = {
    "A": ["01110","10001","10001","11111","10001","10001","10001"],
    "B": ["11110","10001","10001","11110","10001","10001","11110"],
    "C": ["01111","10000","10000","10000","10000","10000","01111"],
    "D": ["11110","10001","10001","10001","10001","10001","11110"],
    "E": ["11111","10000","10000","11110","10000","10000","11111"],
    "F": ["11111","10000","10000","11110","10000","10000","10000"],
    "G": ["01111","10000","10000","10111","10001","10001","01111"],
    "H": ["10001","10001","10001","11111","10001","10001","10001"],
    "I": ["11111","00100","00100","00100","00100","00100","11111"],
    "J": ["00111","00010","00010","00010","10010","10010","01100"],
    "K": ["10001","10010","10100","11000","10100","10010","10001"],
    "L": ["10000","10000","10000","10000","10000","10000","11111"],
    "M": ["10001","11011","10101","10101","10001","10001","10001"],
    "N": ["10001","11001","10101","10011","10001","10001","10001"],
    "O": ["01110","10001","10001","10001","10001","10001","01110"],
    "P": ["11110","10001","10001","11110","10000","10000","10000"],
    "Q": ["01110","10001","10001","10001","10101","10010","01101"],
    "R": ["11110","10001","10001","11110","10100","10010","10001"],
    "S": ["01111","10000","10000","01110","00001","00001","11110"],
    "T": ["11111","00100","00100","00100","00100","00100","00100"],
    "U": ["10001","10001","10001","10001","10001","10001","01110"],
    "V": ["10001","10001","10001","10001","10001","01010","00100"],
    "W": ["10001","10001","10001","10101","10101","10101","01010"],
    "X": ["10001","10001","01010","00100","01010","10001","10001"],
    "Y": ["10001","10001","01010","00100","00100","00100","00100"],
    "Z": ["11111","00001","00010","00100","01000","10000","11111"],
    "0": ["01110","10001","10011","10101","11001","10001","01110"],
    "1": ["00100","01100","00100","00100","00100","00100","01110"],
    "2": ["01110","10001","00001","00010","00100","01000","11111"],
    "3": ["11110","00001","00001","01110","00001","00001","11110"],
    "4": ["00010","00110","01010","10010","11111","00010","00010"],
    "5": ["11111","10000","10000","11110","00001","00001","11110"],
    "6": ["01110","10000","10000","11110","10001","10001","01110"],
    "7": ["11111","00001","00010","00100","01000","01000","01000"],
    "8": ["01110","10001","10001","01110","10001","10001","01110"],
    "9": ["01110","10001","10001","01111","00001","00001","01110"],
    "-": ["00000","00000","00000","11111","00000","00000","00000"],
    ":": ["00000","00100","00100","00000","00100","00100","00000"],
    ".": ["00000","00000","00000","00000","00000","00100","00100"],
    "/": ["00001","00010","00010","00100","01000","01000","10000"],
    " ": ["00000","00000","00000","00000","00000","00000","00000"],
}


def draw_text(x, y, text, scale=1, color=(0.8, 0.9, 1.0)):
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WIDTH, 0, HEIGHT, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(*color)
    cursor_x = x

    for char in text.upper():
        glyph = FONT.get(char, FONT[" "])

        for row, pattern in enumerate(glyph):
            for col, bit in enumerate(pattern):
                if bit == "1":
                    px = cursor_x + col * scale
                    py = y + (6 - row) * scale
                    glBegin(GL_QUADS)
                    glVertex2f(px, py)
                    glVertex2f(px + scale, py)
                    glVertex2f(px + scale, py + scale)
                    glVertex2f(px, py + scale)
                    glEnd()

        cursor_x += 6 * scale

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)


def draw_hud():
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WIDTH, 0, HEIGHT, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Top title strip
    glColor3f(0.015, 0.025, 0.04)
    glBegin(GL_QUADS)
    glVertex2f(0, HEIGHT - 34)
    glVertex2f(WIDTH, HEIGHT - 34)
    glVertex2f(WIDTH, HEIGHT)
    glVertex2f(0, HEIGHT)
    glEnd()

    # Viewport header strips
    split_x = WIDTH // 2

    glColor3f(0.02, 0.20, 0.16)
    glBegin(GL_QUADS)
    glVertex2f(0, HEIGHT - 57)
    glVertex2f(split_x, HEIGHT - 57)
    glVertex2f(split_x, HEIGHT - 35)
    glVertex2f(0, HEIGHT - 35)
    glEnd()

    glColor3f(0.28, 0.15, 0.02)
    glBegin(GL_QUADS)
    glVertex2f(split_x, HEIGHT - 57)
    glVertex2f(WIDTH, HEIGHT - 57)
    glVertex2f(WIDTH, HEIGHT - 35)
    glVertex2f(split_x, HEIGHT - 35)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

    draw_text(12, HEIGHT - 23, "EXPERIMENT 10 - 3D VIEWING PIPELINE", 1,
              (0.8, 0.9, 1.0))
    draw_text(10, HEIGHT - 49, "VIEW A - PERSPECTIVE", 1,
              (0.2, 1.0, 0.7))
    draw_text(split_x + 10, HEIGHT - 49, "VIEW B - TOP ORTHOGRAPHIC", 1,
              (1.0, 0.7, 0.2))

    # Status panel
    panel_x, panel_y = 8, 8
    panel_w, panel_h = 275, 116

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WIDTH, 0, HEIGHT, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(0.015, 0.025, 0.035)
    glBegin(GL_QUADS)
    glVertex2f(panel_x, panel_y)
    glVertex2f(panel_x + panel_w, panel_y)
    glVertex2f(panel_x + panel_w, panel_y + panel_h)
    glVertex2f(panel_x, panel_y + panel_h)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

    collected = sum(1 for c in crystals if c[3])

    draw_text(16, 106, "PIPELINE INSPECTOR", 1, (0.8, 0.9, 1.0))
    draw_text(16, 89, "LEFT: PERSPECTIVE", 1, (0.2, 1.0, 0.7))
    draw_text(16, 74, "RIGHT: ORTHOGRAPHIC", 1, (1.0, 0.7, 0.2))
    draw_text(16, 59, "CRYSTALS: " + str(collected) + "/8", 1, (0.1, 0.9, 1.0))
    draw_text(16, 44, "WASD MOVE  SPACE JUMP", 1, (0.8, 0.8, 0.8))
    draw_text(16, 29, "DRAG OR SCROLL TO ROTATE LEFT", 1, (0.8, 0.8, 0.8))
    draw_text(16, 14, "G GRID  H AXES  B BOXES  R RESET", 1, (0.8, 0.8, 0.8))


# ============================================================
# VIEWPORT RENDERING
# ============================================================

def render_viewport(x, y, width, height, top_view=False):
    glViewport(x, y, width, height)

    glEnable(GL_SCISSOR_TEST)
    glScissor(x, y, width, height)
    glClearColor(*BG)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    setup_camera(width, height, top_view=top_view)

    draw_environment()
    draw_player()


# ============================================================
# INPUT CALLBACKS
# ============================================================

def mouse_button_callback(window, button, action, mods):
    global left_drag, right_drag, last_mouse_x, last_mouse_y

    if button == glfw.MOUSE_BUTTON_LEFT:
        left_drag = action == glfw.PRESS

    if button == glfw.MOUSE_BUTTON_RIGHT:
        right_drag = action == glfw.PRESS

    if action == glfw.PRESS:
        last_mouse_x, last_mouse_y = glfw.get_cursor_pos(window)


def cursor_position_callback(window, xpos, ypos):
    global last_mouse_x, last_mouse_y, camera_yaw, camera_pitch

    dx = xpos - last_mouse_x
    dy = ypos - last_mouse_y

    # Only the left viewport responds to drag.
    window_width, _ = glfw.get_window_size(window)
    left_width = window_width // 2

    in_left_view = xpos < left_width

    if in_left_view and (left_drag or right_drag):
        camera_yaw += dx * 0.35
        camera_pitch -= dy * 0.25
        camera_pitch = max(8.0, min(78.0, camera_pitch))

    last_mouse_x = xpos
    last_mouse_y = ypos


def scroll_callback(window, xoffset, yoffset):
    global camera_yaw, camera_pitch

    # Trackpad two-finger scrolling rotates only the left camera.
    cursor_x, _ = glfw.get_cursor_pos(window)
    window_width, _ = glfw.get_window_size(window)

    if cursor_x < window_width // 2:
        camera_yaw += xoffset * 4.0
        camera_pitch -= yoffset * 2.5
        camera_pitch = max(8.0, min(78.0, camera_pitch))


def key_callback(window, key, scancode, action, mods):
    global show_grid, show_axes, show_boxes, show_crystals
    global animate_monument, split_screen
    global player_x, player_z, player_y, player_angle
    global camera_yaw, camera_pitch, camera_distance
    global player_vertical_speed, jumping

    if action != glfw.PRESS:
        return

    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)

    elif key == glfw.KEY_G:
        show_grid = not show_grid

    elif key == glfw.KEY_H:
        show_axes = not show_axes

    elif key == glfw.KEY_F:
        show_boxes = not show_boxes

    elif key == glfw.KEY_C:
        show_crystals = not show_crystals

    elif key == glfw.KEY_M:
        animate_monument = not animate_monument

    elif key == glfw.KEY_B:
        split_screen = not split_screen

    elif key == glfw.KEY_R:
        player_x = 0.0
        player_z = 4.0
        player_y = 0.0
        player_angle = 0.0
        camera_yaw = 0.0
        camera_pitch = 38.0
        camera_distance = CAMERA_DISTANCE
        player_vertical_speed = 0.0
        jumping = False

        for crystal in crystals:
            crystal[3] = False


def update_player(window, dt):
    global player_x, player_z, player_angle
    global player_y, player_vertical_speed, jumping

    dx = 0.0
    dz = 0.0

    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        dz -= 1.0

    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        dz += 1.0

    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        dx -= 1.0

    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS or \
       glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        dx += 1.0

    sprint = glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS
    speed = player_speed * (1.7 if sprint else 1.0)

    length = math.sqrt(dx * dx + dz * dz)

    if length > 0:
        dx /= length
        dz /= length

        player_x += dx * speed * dt
        player_z += dz * speed * dt
        player_angle = math.degrees(math.atan2(dx, dz))

    # Keep the player within the island.
    max_radius = ISLAND_RADIUS - 1.6
    distance = math.sqrt(player_x * player_x + player_z * player_z)

    if distance > max_radius:
        player_x *= max_radius / distance
        player_z *= max_radius / distance

    # Jump physics
    if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS and not jumping:
        player_vertical_speed = 6.0
        jumping = True

    if jumping:
        player_y += player_vertical_speed * dt
        player_vertical_speed -= 15.0 * dt

        if player_y <= 0:
            player_y = 0
            player_vertical_speed = 0
            jumping = False

    collect_crystals()


# ============================================================
# MAIN
# ============================================================

def main():
    global quadric, scene_time

    if not glfw.init():
        raise RuntimeError("Could not initialize GLFW.")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)

    window = glfw.create_window(
        WIDTH, HEIGHT,
        "Experiment 10 - 3D Viewing Pipeline",
        None, None
    )

    if not window:
        glfw.terminate()
        raise RuntimeError("Could not create the OpenGL window.")

    glfw.make_context_current(window)
    glfw.swap_interval(1)

    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_position_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_key_callback(window, key_callback)

    glClearColor(*BG)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)

    setup_lighting()
    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)

    previous_time = glfw.get_time()

    while not glfw.window_should_close(window):
        current_time = glfw.get_time()
        dt = min(current_time - previous_time, 0.05)
        previous_time = current_time

        scene_time = current_time

        glfw.poll_events()
        update_player(window, dt)

        width, height = glfw.get_framebuffer_size(window)

        if split_screen:
            left_width = width // 2
            right_width = width - left_width

            # LEFT: mouse-responsive perspective view
            render_viewport(
                0, 0,
                left_width, height,
                top_view=False
            )

            # RIGHT: fixed top-down orthographic view
            render_viewport(
                left_width, 0,
                right_width, height,
                top_view=True
            )
        else:
            # Single view remains interactive perspective.
            render_viewport(
                0, 0, width, height,
                top_view=False
            )

        draw_hud()
        glfw.swap_buffers(window)

    gluDeleteQuadric(quadric)
    glfw.terminate()


if __name__ == "__main__":
    main()
