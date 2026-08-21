from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import sys


# ============================================================
# GLOBAL VARIABLES
# ============================================================

object_type = 0

points = []
transformed_points = []


# ============================================================
# MATRIX FUNCTIONS
# ============================================================

def identity_matrix():
    return [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ]


def multiply_matrix(A, B):

    result = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]

    for i in range(3):
        for j in range(3):
            for k in range(3):
                result[i][j] += A[i][k] * B[k][j]

    return result


def apply_matrix(M, x, y):

    new_x = M[0][0] * x + M[0][1] * y + M[0][2]
    new_y = M[1][0] * x + M[1][1] * y + M[1][2]

    return new_x, new_y


# ============================================================
# TRANSFORMATION MATRICES
# ============================================================

def translation_matrix(tx, ty):

    return [
        [1, 0, tx],
        [0, 1, ty],
        [0, 0, 1]
    ]


def rotation_matrix(angle):

    rad = math.radians(angle)

    return [
        [math.cos(rad), -math.sin(rad), 0],
        [math.sin(rad),  math.cos(rad), 0],
        [0, 0, 1]
    ]


def scaling_matrix(sx, sy):

    return [
        [sx, 0, 0],
        [0, sy, 0],
        [0, 0, 1]
    ]


def reflection_matrix(choice):

    # Reflection about X-axis
    if choice == 1:
        return [
            [1, 0, 0],
            [0, -1, 0],
            [0, 0, 1]
        ]

    # Reflection about Y-axis
    elif choice == 2:
        return [
            [-1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ]

    # Reflection about origin
    elif choice == 3:
        return [
            [-1, 0, 0],
            [0, -1, 0],
            [0, 0, 1]
        ]

    # Reflection about y = x
    elif choice == 4:
        return [
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, 1]
        ]

    return identity_matrix()


# ============================================================
# PRINT MATRIX
# ============================================================

def print_matrix(M):

    for row in M:
        print(
            "[",
            "  ".join(f"{value:8.3f}" for value in row),
            "]"
        )


# ============================================================
# APPLY COMPOSITE TRANSFORMATION
# ============================================================

def apply_transformation():

    global transformed_points

    transformed_points = []

    # Start with identity matrix
    composite_matrix = identity_matrix()

    print("\n======================================")
    print("     COMPOSITE TRANSFORMATION")
    print("======================================")

    print("\nHow many transformations do you want?")
    print("2. Two transformations")
    print("3. Three transformations")
    print("4. Four transformations")

    number = int(input("\nEnter number: "))

    if number < 2 or number > 4:
        print("Invalid number!")
        sys.exit()

    # --------------------------------------------------------
    # TRANSFORMATION MENU
    # --------------------------------------------------------

    print("\nTransformation types:")
    print("1. Translation")
    print("2. Rotation")
    print("3. Scaling")
    print("4. Reflection")

    # --------------------------------------------------------
    # GET TRANSFORMATIONS
    # --------------------------------------------------------

    for i in range(number):

        print("\n--------------------------------------")
        print(f"Transformation {i + 1}")
        print("--------------------------------------")

        choice = int(input("Enter transformation choice: "))

        # ----------------------------------------------------
        # TRANSLATION
        # ----------------------------------------------------

        if choice == 1:

            tx = float(input("Enter tx: "))
            ty = float(input("Enter ty: "))

            matrix = translation_matrix(tx, ty)

        # ----------------------------------------------------
        # ROTATION
        # ----------------------------------------------------

        elif choice == 2:

            angle = float(input("Enter rotation angle: "))

            matrix = rotation_matrix(angle)

        # ----------------------------------------------------
        # SCALING
        # ----------------------------------------------------

        elif choice == 3:

            sx = float(input("Enter sx: "))
            sy = float(input("Enter sy: "))

            matrix = scaling_matrix(sx, sy)

        # ----------------------------------------------------
        # REFLECTION
        # ----------------------------------------------------

        elif choice == 4:

            print("\nReflection:")
            print("1. X-axis")
            print("2. Y-axis")
            print("3. Origin")
            print("4. y = x")

            reflection_choice = int(
                input("Enter choice: ")
            )

            matrix = reflection_matrix(
                reflection_choice
            )

        else:

            print("Invalid transformation!")
            sys.exit()

        # ----------------------------------------------------
        # DISPLAY CURRENT MATRIX
        # ----------------------------------------------------

        print("\nTransformation Matrix:")

        print_matrix(matrix)

        # ----------------------------------------------------
        # COMPOSITE MATRIX
        # ----------------------------------------------------

        composite_matrix = multiply_matrix(
            matrix,
            composite_matrix
        )

    # --------------------------------------------------------
    # DISPLAY FINAL COMPOSITE MATRIX
    # --------------------------------------------------------

    print("\n======================================")
    print("FINAL COMPOSITE MATRIX")
    print("======================================")

    print_matrix(composite_matrix)

    # --------------------------------------------------------
    # APPLY MATRIX TO ALL POINTS
    # --------------------------------------------------------

    transformed_points = []

    for x, y in points:

        new_point = apply_matrix(
            composite_matrix,
            x,
            y
        )

        transformed_points.append(new_point)

    # --------------------------------------------------------
    # DISPLAY COORDINATES
    # --------------------------------------------------------

    print("\nOriginal Coordinates:")

    for point in points:
        print(
            f"({point[0]:.2f}, {point[1]:.2f})"
        )

    print("\nTransformed Coordinates:")

    for point in transformed_points:
        print(
            f"({point[0]:.2f}, {point[1]:.2f})"
        )


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

    # Grid
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

    # Axes
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

    # Axis labels
    draw_text(19, 0.3, "X")
    draw_text(0.3, 19, "Y")

    # Coordinate numbers
    for i in range(-20, 21):

        if i != 0:

            draw_text(
                i + 0.1,
                0.2,
                str(i)
            )

            draw_text(
                0.2,
                i + 0.1,
                str(i)
            )


# ============================================================
# DRAW POINT
# ============================================================

def draw_point(x, y):

    glPointSize(10)

    glBegin(GL_POINTS)

    glVertex2f(x, y)

    glEnd()

    glPointSize(1)

    draw_text(
        x + 0.2,
        y + 0.2,
        f"({x:.1f},{y:.1f})"
    )


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

    draw_text(
        p1[0] + 0.2,
        p1[1] + 0.2,
        f"({p1[0]:.1f},{p1[1]:.1f})"
    )

    draw_text(
        p2[0] + 0.2,
        p2[1] + 0.2,
        f"({p2[0]:.1f},{p2[1]:.1f})"
    )


# ============================================================
# DRAW TRIANGLE
# ============================================================

def draw_triangle(p1, p2, p3):

    glBegin(GL_LINE_LOOP)

    glVertex2f(
        p1[0],
        p1[1]
    )

    glVertex2f(
        p2[0],
        p2[1]
    )

    glVertex2f(
        p3[0],
        p3[1]
    )

    glEnd()

    draw_text(
        p1[0] + 0.2,
        p1[1] + 0.2,
        f"({p1[0]:.1f},{p1[1]:.1f})"
    )

    draw_text(
        p2[0] + 0.2,
        p2[1] + 0.2,
        f"({p2[0]:.1f},{p2[1]:.1f})"
    )

    draw_text(
        p3[0] + 0.2,
        p3[1] + 0.2,
        f"({p3[0]:.1f},{p3[1]:.1f})"
    )


# ============================================================
# DISPLAY
# ============================================================

def display():

    glClear(GL_COLOR_BUFFER_BIT)

    glLoadIdentity()

    draw_grid()

    # --------------------------------------------------------
    # ORIGINAL OBJECT - BLUE
    # --------------------------------------------------------

    glColor3f(0, 0, 1)

    if object_type == 1:

        draw_point(
            points[0][0],
            points[0][1]
        )

    elif object_type == 2:

        draw_line(
            points[0],
            points[1]
        )

    elif object_type == 3:

        draw_triangle(
            points[0],
            points[1],
            points[2]
        )

    # --------------------------------------------------------
    # TRANSFORMED OBJECT - RED
    # --------------------------------------------------------

    glColor3f(1, 0, 0)

    if object_type == 1:

        draw_point(
            transformed_points[0][0],
            transformed_points[0][1]
        )

    elif object_type == 2:

        draw_line(
            transformed_points[0],
            transformed_points[1]
        )

    elif object_type == 3:

        draw_triangle(
            transformed_points[0],
            transformed_points[1],
            transformed_points[2]
        )

    # --------------------------------------------------------
    # LEGEND
    # --------------------------------------------------------

    glColor3f(0, 0, 1)

    draw_text(
        -19,
        19,
        "BLUE = ORIGINAL"
    )

    glColor3f(1, 0, 0)

    draw_text(
        -19,
        18,
        "RED = TRANSFORMED"
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

    global object_type
    global points

    print("\n======================================")
    print("     2D COMPOSITE TRANSFORMATION")
    print("======================================")

    # --------------------------------------------------------
    # OBJECT
    # --------------------------------------------------------

    print("\nChoose object:")

    print("1. Point")
    print("2. Line")
    print("3. Triangle")

    object_type = int(
        input("\nEnter choice: ")
    )

    # --------------------------------------------------------
    # POINT
    # --------------------------------------------------------

    if object_type == 1:

        x = float(
            input("Enter x: ")
        )

        y = float(
            input("Enter y: ")
        )

        points = [
            (x, y)
        ]

    # --------------------------------------------------------
    # LINE
    # --------------------------------------------------------

    elif object_type == 2:

        print("\nEnter first point:")

        x1 = float(
            input("x1: ")
        )

        y1 = float(
            input("y1: ")
        )

        print("\nEnter second point:")

        x2 = float(
            input("x2: ")
        )

        y2 = float(
            input("y2: ")
        )

        points = [
            (x1, y1),
            (x2, y2)
        ]

    # --------------------------------------------------------
    # TRIANGLE
    # --------------------------------------------------------

    elif object_type == 3:

        print("\nEnter first point:")

        x1 = float(
            input("x1: ")
        )

        y1 = float(
            input("y1: ")
        )

        print("\nEnter second point:")

        x2 = float(
            input("x2: ")
        )

        y2 = float(
            input("y2: ")
        )

        print("\nEnter third point:")

        x3 = float(
            input("x3: ")
        )

        y3 = float(
            input("y3: ")
        )

        points = [
            (x1, y1),
            (x2, y2),
            (x3, y3)
        ]

    else:

        print("Invalid choice!")
        sys.exit()

    apply_transformation()


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
        b"2D Composite Transformations - OpenGL"
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