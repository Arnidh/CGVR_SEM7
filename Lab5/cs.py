from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys


# ============================================================
# GLOBAL VARIABLES
# ============================================================

x_min = -8
x_max = 8
y_min = -8
y_max = 8

original_line = []
clipped_line = None


# ============================================================
# REGION CODES
# ============================================================

INSIDE = 0
LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8


# ============================================================
# CALCULATE REGION CODE
# ============================================================

def compute_code(x, y):

    code = INSIDE

    if x < x_min:
        code |= LEFT

    elif x > x_max:
        code |= RIGHT

    if y < y_min:
        code |= BOTTOM

    elif y > y_max:
        code |= TOP

    return code


# ============================================================
# COHEN-SUTHERLAND LINE CLIPPING
# ============================================================

def cohen_sutherland_clip(x1, y1, x2, y2):

    code1 = compute_code(x1, y1)
    code2 = compute_code(x2, y2)

    accept = False

    while True:

        # ----------------------------------------------------
        # CASE 1: Both points are inside
        # ----------------------------------------------------

        if code1 == 0 and code2 == 0:

            accept = True
            break

        # ----------------------------------------------------
        # CASE 2: Both points are outside
        # ----------------------------------------------------

        elif (code1 & code2) != 0:

            break

        # ----------------------------------------------------
        # CASE 3: Line needs clipping
        # ----------------------------------------------------

        else:

            if code1 != 0:
                code_out = code1
            else:
                code_out = code2

            # ------------------------------------------------
            # TOP boundary
            # ------------------------------------------------

            if code_out & TOP:

                x = x1 + (x2 - x1) * \
                    (y_max - y1) / (y2 - y1)

                y = y_max

            # ------------------------------------------------
            # BOTTOM boundary
            # ------------------------------------------------

            elif code_out & BOTTOM:

                x = x1 + (x2 - x1) * \
                    (y_min - y1) / (y2 - y1)

                y = y_min

            # ------------------------------------------------
            # RIGHT boundary
            # ------------------------------------------------

            elif code_out & RIGHT:

                y = y1 + (y2 - y1) * \
                    (x_max - x1) / (x2 - x1)

                x = x_max

            # ------------------------------------------------
            # LEFT boundary
            # ------------------------------------------------

            elif code_out & LEFT:

                y = y1 + (y2 - y1) * \
                    (x_min - x1) / (x2 - x1)

                x = x_min

            # ------------------------------------------------
            # Replace outside point
            # ------------------------------------------------

            if code_out == code1:

                x1 = x
                y1 = y

                code1 = compute_code(x1, y1)

            else:

                x2 = x
                y2 = y

                code2 = compute_code(x2, y2)

    if accept:

        return (x1, y1), (x2, y2)

    return None


# ============================================================
# DRAW TEXT
# ============================================================

def draw_text(x, y, text):

    glRasterPos2f(x, y)

    for character in text:

        glutBitmapCharacter(
            GLUT_BITMAP_HELVETICA_12,
            ord(character)
        )


# ============================================================
# DRAW GRID
# ============================================================

def draw_grid():

    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    glColor3f(0.85, 0.85, 0.85)

    glBegin(GL_LINES)

    for i in range(-20, 21):

        # Vertical
        glVertex2f(i, -20)
        glVertex2f(i, 20)

        # Horizontal
        glVertex2f(-20, i)
        glVertex2f(20, i)

    glEnd()

    # --------------------------------------------------------
    # Axes
    # --------------------------------------------------------

    glColor3f(0, 0, 0)

    glLineWidth(2)

    glBegin(GL_LINES)

    # X-axis
    glVertex2f(-20, 0)
    glVertex2f(20, 0)

    # Y-axis
    glVertex2f(0, -20)
    glVertex2f(0, 20)

    glEnd()

    glLineWidth(1)

    # --------------------------------------------------------
    # Axis labels
    # --------------------------------------------------------

    draw_text(19, 0.3, "X")
    draw_text(0.3, 19, "Y")


# ============================================================
# DRAW CLIPPING WINDOW
# ============================================================

def draw_clipping_window():

    glColor3f(0, 0, 0)

    glLineWidth(3)

    glBegin(GL_LINE_LOOP)

    glVertex2f(x_min, y_min)
    glVertex2f(x_max, y_min)
    glVertex2f(x_max, y_max)
    glVertex2f(x_min, y_max)

    glEnd()

    glLineWidth(1)

    # --------------------------------------------------------
    # Window labels
    # --------------------------------------------------------

    draw_text(x_min + 0.2, y_max + 0.3, "CLIPPING WINDOW")


# ============================================================
# DRAW LINE
# ============================================================

def draw_line(p1, p2):

    glBegin(GL_LINES)

    glVertex2f(
        p1[0],
        p1[1]
    )

    glVertex2f(
        p2[0],
        p2[1]
    )

    glEnd()


# ============================================================
# DRAW POINT
# ============================================================

def draw_point(x, y):

    glPointSize(8)

    glBegin(GL_POINTS)

    glVertex2f(x, y)

    glEnd()

    glPointSize(1)


# ============================================================
# DISPLAY
# ============================================================

def display():

    glClear(GL_COLOR_BUFFER_BIT)

    glLoadIdentity()

    # --------------------------------------------------------
    # GRID
    # --------------------------------------------------------

    draw_grid()

    # --------------------------------------------------------
    # CLIPPING WINDOW
    # --------------------------------------------------------

    draw_clipping_window()

    # --------------------------------------------------------
    # ORIGINAL LINE
    # --------------------------------------------------------

    glColor3f(0, 0, 1)

    glLineWidth(2)

    draw_line(
        original_line[0],
        original_line[1]
    )

    # --------------------------------------------------------
    # ORIGINAL END POINTS
    # --------------------------------------------------------

    draw_point(
        original_line[0][0],
        original_line[0][1]
    )

    draw_point(
        original_line[1][0],
        original_line[1][1]
    )

    # --------------------------------------------------------
    # CLIPPED LINE
    # --------------------------------------------------------

    if clipped_line is not None:

        glColor3f(1, 0, 0)

        glLineWidth(4)

        draw_line(
            clipped_line[0],
            clipped_line[1]
        )

        glLineWidth(1)

        # ----------------------------------------------------
        # Clipped endpoints
        # ----------------------------------------------------

        draw_point(
            clipped_line[0][0],
            clipped_line[0][1]
        )

        draw_point(
            clipped_line[1][0],
            clipped_line[1][1]
        )

        # ----------------------------------------------------
        # Coordinates
        # ----------------------------------------------------

        draw_text(
            clipped_line[0][0] + 0.2,
            clipped_line[0][1] + 0.2,
            f"({clipped_line[0][0]:.2f},"
            f"{clipped_line[0][1]:.2f})"
        )

        draw_text(
            clipped_line[1][0] + 0.2,
            clipped_line[1][1] + 0.2,
            f"({clipped_line[1][0]:.2f},"
            f"{clipped_line[1][1]:.2f})"
        )

    # --------------------------------------------------------
    # LEGEND
    # --------------------------------------------------------

    glColor3f(0, 0, 1)

    draw_text(
        -19,
        19,
        "BLUE = ORIGINAL LINE"
    )

    glColor3f(1, 0, 0)

    draw_text(
        -19,
        18,
        "RED = CLIPPED LINE"
    )

    glColor3f(0, 0, 0)

    draw_text(
        -19,
        17,
        "BLACK = CLIPPING WINDOW"
    )

    glFlush()


# ============================================================
# INITIALIZATION
# ============================================================

def init():

    glClearColor(
        1,
        1,
        1,
        1
    )

    glMatrixMode(
        GL_PROJECTION
    )

    glLoadIdentity()

    gluOrtho2D(
        -20,
        20,
        -20,
        20
    )

    glMatrixMode(
        GL_MODELVIEW
    )


# ============================================================
# INPUT
# ============================================================

def get_input():

    global original_line
    global clipped_line

    print("\n======================================")
    print(" COHEN-SUTHERLAND LINE CLIPPING")
    print("======================================")

    # --------------------------------------------------------
    # CLIPPING WINDOW
    # --------------------------------------------------------

    print("\nClipping Window:")
    print(
        f"X: {x_min} to {x_max}"
    )
    print(
        f"Y: {y_min} to {y_max}"
    )

    # --------------------------------------------------------
    # FIRST POINT
    # --------------------------------------------------------

    print("\nEnter first point:")

    x1 = float(
        input("x1: ")
    )

    y1 = float(
        input("y1: ")
    )

    # --------------------------------------------------------
    # SECOND POINT
    # --------------------------------------------------------

    print("\nEnter second point:")

    x2 = float(
        input("x2: ")
    )

    y2 = float(
        input("y2: ")
    )

    original_line = [
        (x1, y1),
        (x2, y2)
    ]

    # --------------------------------------------------------
    # DISPLAY REGION CODES
    # --------------------------------------------------------

    code1 = compute_code(x1, y1)
    code2 = compute_code(x2, y2)

    print("\n======================================")
    print("REGION CODES")
    print("======================================")

    print(
        f"Point 1 ({x1:.2f}, {y1:.2f})"
        f" -> {code1:04b}"
    )

    print(
        f"Point 2 ({x2:.2f}, {y2:.2f})"
        f" -> {code2:04b}"
    )

    # --------------------------------------------------------
    # APPLY CLIPPING
    # --------------------------------------------------------

    clipped_line = cohen_sutherland_clip(
        x1,
        y1,
        x2,
        y2
    )

    # --------------------------------------------------------
    # DISPLAY RESULT
    # --------------------------------------------------------

    print("\n======================================")
    print("CLIPPING RESULT")
    print("======================================")

    if clipped_line is None:

        print("Line is completely outside.")
        print("Line rejected.")

    else:

        print("Line accepted.")

        print(
            "\nClipped Line:"
        )

        print(
            f"({clipped_line[0][0]:.2f}, "
            f"{clipped_line[0][1]:.2f})"
        )

        print(
            f"({clipped_line[1][0]:.2f}, "
            f"{clipped_line[1][1]:.2f})"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    get_input()

    glutInit(sys.argv)

    glutInitDisplayMode(
        GLUT_SINGLE | GLUT_RGB
    )

    glutInitWindowSize(
        900,
        700
    )

    glutInitWindowPosition(
        100,
        50
    )

    glutCreateWindow(
        b"Cohen-Sutherland Line Clipping - OpenGL"
    )

    init()

    glutDisplayFunc(
        display
    )

    glutMainLoop()


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    main()