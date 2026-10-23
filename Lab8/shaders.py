import math
import ctypes
import glfw
import numpy as np
from OpenGL.GL import *

# ============================================================
# EXPERIMENT 8: VERTEX AND FRAGMENT SHADERS
# Interactive 2D transformation laboratory
# Compatible OpenGL 2.1 context for macOS legacy HUD drawing.
# ============================================================

WIDTH, HEIGHT = 1400, 900
TITLE = "Experiment 08 | Vertex and Fragment Shader Studio"

VERTEX_SHADER = """
#version 120
attribute vec2 aPosition;
attribute vec3 aColor;
uniform mat3 uTransform;
varying vec3 vertexColor;

void main()
{
    vec3 p = uTransform * vec3(aPosition, 1.0);
    gl_Position = vec4(p.xy, 0.0, 1.0);
    vertexColor = aColor;
}
"""

FRAGMENT_SHADER = """
#version 120
varying vec3 vertexColor;
uniform float uTime;
uniform int uPulse;
uniform int uColorMode;

void main()
{
    vec3 color = vertexColor;

    if (uColorMode == 1) {
        color = vec3(
            0.20 + 0.70 * abs(sin(uTime)),
            0.20 + 0.70 * abs(sin(uTime + 2.1)),
            0.30 + 0.65 * abs(sin(uTime + 4.2))
        );
    }

    if (uPulse == 1) {
        color *= 0.80 + 0.20 * sin(uTime * 3.0);
    }

    gl_FragColor = vec4(color, 1.0);
}
"""

window_width, window_height = WIDTH, HEIGHT
translation = np.array([0.0, 0.0], dtype=np.float32)
rotation = 0.0
scale_xy = np.array([1.0, 1.0], dtype=np.float32)
shear_xy = np.array([0.0, 0.0], dtype=np.float32)
zoom = 1.0
pivot = np.array([0.0, 0.0], dtype=np.float32)

animation_enabled = False
pulse_enabled = True
color_mode = 0
show_grid = True
show_axes = True
show_outline = True
show_pivot = True
reflection_yx_enabled = False

drag_mode = None
last_mouse_x = 0.0
last_mouse_y = 0.0
current_transform = "IDENTITY"


def compile_shader(source, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        log = glGetShaderInfoLog(shader)
        if isinstance(log, bytes):
            log = log.decode("utf-8", errors="replace")
        glDeleteShader(shader)
        raise RuntimeError("Shader compilation failed:\n" + str(log))
    return shader


def create_shader_program():
    vs = compile_shader(VERTEX_SHADER, GL_VERTEX_SHADER)
    fs = compile_shader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    program = glCreateProgram()
    glAttachShader(program, vs)
    glAttachShader(program, fs)
    glBindAttribLocation(program, 0, "aPosition")
    glBindAttribLocation(program, 1, "aColor")
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
        log = glGetProgramInfoLog(program)
        if isinstance(log, bytes):
            log = log.decode("utf-8", errors="replace")
        glDeleteProgram(program)
        glDeleteShader(vs)
        glDeleteShader(fs)
        raise RuntimeError("Shader linking failed:\n" + str(log))
    glDeleteShader(vs)
    glDeleteShader(fs)
    return program


def identity():
    return np.eye(3, dtype=np.float32)


def translate_matrix(tx, ty):
    m = identity()
    m[0, 2], m[1, 2] = tx, ty
    return m


def rotate_matrix(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float32)


def scale_matrix(sx, sy):
    return np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]], dtype=np.float32)


def shear_matrix(shx, shy):
    return np.array([[1, shx, 0], [shy, 1, 0], [0, 0, 1]], dtype=np.float32)


def reflection_matrix(axis):
    if axis == "yx":
        return np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]], dtype=np.float32)
    m = identity()
    if axis == "x":
        m[1, 1] = -1
    elif axis == "y":
        m[0, 0] = -1
    elif axis == "xy":
        m[0, 0] = -1
        m[1, 1] = -1
    return m


def get_transform():
    model = (
        translate_matrix(translation[0], translation[1])
        @ translate_matrix(pivot[0], pivot[1])
        @ rotate_matrix(rotation)
        @ scale_matrix(scale_xy[0], scale_xy[1])
        @ shear_matrix(shear_xy[0], shear_xy[1])
        @ translate_matrix(-pivot[0], -pivot[1])
    )
    return scale_matrix(zoom, zoom) @ model


def upload_transform(program, matrix):
    loc = glGetUniformLocation(program, "uTransform")
    # PyOpenGL sends the contiguous transposed array as column-major data.
    glUniformMatrix3fv(loc, 1, GL_FALSE, np.ascontiguousarray(matrix.T))


def make_polygon():
    return np.array([
        (-0.42, -0.32, 0.05, 0.85, 1.00),
        (-0.18, -0.43, 0.05, 0.95, 0.70),
        ( 0.18, -0.43, 0.20, 0.85, 1.00),
        ( 0.42, -0.20, 0.25, 1.00, 0.75),
        ( 0.42,  0.20, 0.10, 0.65, 1.00),
        ( 0.18,  0.43, 0.40, 1.00, 0.85),
        (-0.18,  0.43, 0.05, 0.80, 1.00),
        (-0.42,  0.20, 0.20, 1.00, 0.65),
    ], dtype=np.float32)


def make_triangle_fan(polygon):
    center = np.array([0.0, 0.0, 0.25, 0.95, 0.9], dtype=np.float32)
    data = []
    for i in range(len(polygon)):
        data.extend((center, polygon[i], polygon[(i + 1) % len(polygon)]))
    return np.array(data, dtype=np.float32)


def make_grid():
    data = []
    for i in range(-10, 11):
        p = i * 0.1
        data.extend([(p, -1, 0.10, 0.15, 0.19), (p, 1, 0.10, 0.15, 0.19)])
        data.extend([(-1, p, 0.10, 0.15, 0.19), (1, p, 0.10, 0.15, 0.19)])
    return np.array(data, dtype=np.float32)


def make_axes():
    return np.array([
        (-1, 0, 0.85, 0.20, 0.18), (1, 0, 0.85, 0.20, 0.18),
        (0, -1, 0.20, 0.95, 0.40), (0, 1, 0.20, 0.95, 0.40),
    ], dtype=np.float32)


def make_crosshair():
    return np.array([
        (-0.025, 0, 1.0, 0.8, 0.2), (0.025, 0, 1.0, 0.8, 0.2),
        (0, -0.025, 1.0, 0.8, 0.2), (0, 0.025, 1.0, 0.8, 0.2),
    ], dtype=np.float32)


def create_geometry(data, usage=GL_STATIC_DRAW):
    """Create a VBO compatible with an OpenGL 2.1 context."""
    vbo = glGenBuffers(1)
    data = np.ascontiguousarray(data, dtype=np.float32)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, usage)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    return vbo, len(data)


def draw_geometry(program, geometry, mode, matrix=None):
    vbo, count = geometry
    glUseProgram(program)
    upload_transform(program, identity() if matrix is None else matrix)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    stride = 5 * ctypes.sizeof(ctypes.c_float)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(2 * ctypes.sizeof(ctypes.c_float)))
    glDrawArrays(mode, 0, count)
    glDisableVertexAttribArray(0)
    glDisableVertexAttribArray(1)
    glBindBuffer(GL_ARRAY_BUFFER, 0)


FONT = {
    "A":["01110","10001","10001","11111","10001","10001","10001"],
    "B":["11110","10001","10001","11110","10001","10001","11110"],
    "C":["01111","10000","10000","10000","10000","10000","01111"],
    "D":["11110","10001","10001","10001","10001","10001","11110"],
    "E":["11111","10000","10000","11110","10000","10000","11111"],
    "F":["11111","10000","10000","11110","10000","10000","10000"],
    "G":["01111","10000","10000","10111","10001","10001","01111"],
    "H":["10001","10001","10001","11111","10001","10001","10001"],
    "I":["11111","00100","00100","00100","00100","00100","11111"],
    "J":["00111","00010","00010","00010","10010","10010","01100"],
    "K":["10001","10010","10100","11000","10100","10010","10001"],
    "L":["10000","10000","10000","10000","10000","10000","11111"],
    "M":["10001","11011","10101","10101","10001","10001","10001"],
    "N":["10001","11001","10101","10011","10001","10001","10001"],
    "O":["01110","10001","10001","10001","10001","10001","01110"],
    "P":["11110","10001","10001","11110","10000","10000","10000"],
    "Q":["01110","10001","10001","10001","10101","10010","01101"],
    "R":["11110","10001","10001","11110","10100","10010","10001"],
    "S":["01111","10000","10000","01110","00001","00001","11110"],
    "T":["11111","00100","00100","00100","00100","00100","00100"],
    "U":["10001","10001","10001","10001","10001","10001","01110"],
    "V":["10001","10001","10001","10001","10001","01010","00100"],
    "W":["10001","10001","10001","10101","10101","10101","01010"],
    "X":["10001","10001","01010","00100","01010","10001","10001"],
    "Y":["10001","10001","01010","00100","00100","00100","00100"],
    "Z":["11111","00001","00010","00100","01000","10000","11111"],
    "0":["01110","10001","10011","10101","11001","10001","01110"],
    "1":["00100","01100","00100","00100","00100","00100","01110"],
    "2":["01110","10001","00001","00010","00100","01000","11111"],
    "3":["11110","00001","00001","01110","00001","00001","11110"],
    "4":["00010","00110","01010","10010","11111","00010","00010"],
    "5":["11111","10000","10000","11110","00001","00001","11110"],
    "6":["01110","10000","10000","11110","10001","10001","01110"],
    "7":["11111","00001","00010","00100","01000","01000","01000"],
    "8":["01110","10001","10001","01110","10001","10001","01110"],
    "9":["01110","10001","10001","01111","00001","00001","01110"],
    "-":["00000","00000","00000","11111","00000","00000","00000"],
    ":":["00000","00100","00100","00000","00100","00100","00000"],
    ".":["00000","00000","00000","00000","00000","00100","00100"],
    "/":["00001","00010","00010","00100","01000","01000","10000"],
    " ":["00000","00000","00000","00000","00000","00000","00000"],
}


def draw_text(x, y, text, scale=1, color=(0.8, 0.9, 1.0)):
    glUseProgram(0)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window_width, 0, window_height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(*color)
    cursor_x = x
    glBegin(GL_QUADS)
    for char in text.upper():
        for row, pattern in enumerate(FONT.get(char, FONT[" "])):
            for col, bit in enumerate(pattern):
                if bit == "1":
                    px = cursor_x + col * scale
                    py = y + (6 - row) * scale
                    glVertex2f(px, py)
                    glVertex2f(px + scale, py)
                    glVertex2f(px + scale, py + scale)
                    glVertex2f(px, py + scale)
        cursor_x += 6 * scale
    glEnd()
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glDisable(GL_DEPTH_TEST)


def draw_hud():
    glUseProgram(0)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window_width, 0, window_height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(0.015, 0.025, 0.04)
    glBegin(GL_QUADS)
    glVertex2f(0, window_height - 38)
    glVertex2f(window_width, window_height - 38)
    glVertex2f(window_width, window_height)
    glVertex2f(0, window_height)
    glVertex2f(10, 10)
    glVertex2f(345, 10)
    glVertex2f(345, 166)
    glVertex2f(10, 166)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glDisable(GL_DEPTH_TEST)

    draw_text(12, window_height - 25, "EXPERIMENT 08 - VERTEX AND FRAGMENT SHADERS", 1)
    draw_text(20, 145, "SHADER PIPELINE", 1, (0.3, 1.0, 0.75))
    draw_text(20, 128, "VERTEX SHADER: TRANSFORM", 1, (0.5, 0.9, 1.0))
    draw_text(20, 111, "RASTERIZATION: TRIANGLES", 1, (0.8, 0.8, 0.8))
    draw_text(20, 94, "FRAGMENT SHADER: COLOR", 1, (0.5, 0.9, 1.0))
    draw_text(20, 77, "MODE: " + current_transform, 1, (1.0, 0.75, 0.25))
    draw_text(20, 60, "ANIMATION: " + ("ON" if animation_enabled else "OFF"), 1)
    draw_text(20, 43, "LEFT DRAG MOVE RIGHT DRAG ROTATE", 1)
    draw_text(20, 26, "1 ROTATE 2 SCALE 3 REFLECT 4 SHEAR 5 COMPOSITE", 1)
    draw_text(20, 12, "SPACE ANIMATE R RESET ESC EXIT", 1, (0.7, 0.8, 0.9))


def reset_transform():
    global translation, rotation, scale_xy, shear_xy, zoom, pivot
    global current_transform, reflection_yx_enabled
    translation = np.array([0.0, 0.0], dtype=np.float32)
    rotation = 0.0
    scale_xy = np.array([1.0, 1.0], dtype=np.float32)
    shear_xy = np.array([0.0, 0.0], dtype=np.float32)
    zoom = 1.0
    pivot = np.array([0.0, 0.0], dtype=np.float32)
    reflection_yx_enabled = False
    current_transform = "IDENTITY"


def preset_rotation():
    global rotation, pivot, current_transform, reflection_yx_enabled
    rotation = math.radians(45)
    pivot[:] = 0
    reflection_yx_enabled = False
    current_transform = "ROTATION 45 DEG"


def preset_scaling():
    global scale_xy, current_transform, reflection_yx_enabled
    scale_xy = np.array([1.45, 0.65], dtype=np.float32)
    reflection_yx_enabled = False
    current_transform = "NON-UNIFORM SCALE"


def preset_reflection():
    global rotation, scale_xy, shear_xy, current_transform, reflection_yx_enabled
    rotation = 0.0
    scale_xy = np.array([-1.0, 1.0], dtype=np.float32)
    shear_xy[:] = 0
    reflection_yx_enabled = False
    current_transform = "REFLECTION Y-AXIS"


def preset_shear():
    global shear_xy, current_transform, reflection_yx_enabled
    shear_xy = np.array([0.65, 0.0], dtype=np.float32)
    reflection_yx_enabled = False
    current_transform = "SHEARING"


def preset_composite():
    global rotation, scale_xy, shear_xy, translation, pivot
    global current_transform, reflection_yx_enabled
    rotation = math.radians(35)
    scale_xy = np.array([1.15, 0.75], dtype=np.float32)
    shear_xy = np.array([0.25, 0.0], dtype=np.float32)
    pivot[:] = 0
    translation = np.array([0.15, -0.05], dtype=np.float32)
    reflection_yx_enabled = False
    current_transform = "COMPOSITE TRANSFORM"


def framebuffer_size_callback(window, width, height):
    global window_width, window_height
    window_width, window_height = max(width, 1), max(height, 1)
    glViewport(0, 0, window_width, window_height)


def mouse_button_callback(window, button, action, mods):
    global drag_mode, last_mouse_x, last_mouse_y
    if action == glfw.PRESS:
        last_mouse_x, last_mouse_y = glfw.get_cursor_pos(window)
        if button == glfw.MOUSE_BUTTON_LEFT:
            drag_mode = "scale" if mods & glfw.MOD_SHIFT else "translate"
        elif button == glfw.MOUSE_BUTTON_RIGHT:
            drag_mode = "rotate"
    elif action == glfw.RELEASE:
        drag_mode = None


def cursor_position_callback(window, xpos, ypos):
    global last_mouse_x, last_mouse_y, translation, rotation, scale_xy, current_transform
    dx = xpos - last_mouse_x
    dy = ypos - last_mouse_y
    ndc_dx = 2.0 * dx / max(window_width, 1)
    ndc_dy = -2.0 * dy / max(window_height, 1)

    if drag_mode == "translate":
        translation[0] += ndc_dx
        translation[1] += ndc_dy
        current_transform = "MOUSE TRANSLATION"
    elif drag_mode == "rotate":
        rotation += dx * 0.008
        current_transform = "MOUSE ROTATION"
    elif drag_mode == "scale":
        scale_xy[0] *= max(0.2, 1.0 + ndc_dx)
        scale_xy[1] *= max(0.2, 1.0 - ndc_dy)
        current_transform = "MOUSE SCALING"

    last_mouse_x, last_mouse_y = xpos, ypos


def scroll_callback(window, xoffset, yoffset):
    global zoom, current_transform
    zoom = max(0.25, min(2.5, zoom * (1.0 + yoffset * 0.08)))
    current_transform = "SCROLL ZOOM"


def key_callback(window, key, scancode, action, mods):
    global animation_enabled, pulse_enabled, color_mode
    global show_grid, show_axes, show_outline, show_pivot
    global current_transform, translation, rotation, scale_xy
    global reflection_yx_enabled

    if action != glfw.PRESS:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_R:
        reset_transform()
    elif key == glfw.KEY_SPACE:
        animation_enabled = not animation_enabled
    elif key == glfw.KEY_P:
        pulse_enabled = not pulse_enabled
    elif key == glfw.KEY_V:
        color_mode = 1 - color_mode
    elif key == glfw.KEY_G:
        show_grid = not show_grid
    elif key == glfw.KEY_H:
        show_axes = not show_axes
    elif key == glfw.KEY_O:
        show_outline = not show_outline
    elif key == glfw.KEY_C:
        show_pivot = not show_pivot
    elif key == glfw.KEY_1:
        preset_rotation()
    elif key == glfw.KEY_2:
        preset_scaling()
    elif key == glfw.KEY_3:
        preset_reflection()
    elif key == glfw.KEY_4:
        preset_shear()
    elif key == glfw.KEY_5:
        preset_composite()
    elif key == glfw.KEY_LEFT:
        translation[0] -= 0.04
        current_transform = "TRANSLATION"
    elif key == glfw.KEY_RIGHT:
        translation[0] += 0.04
        current_transform = "TRANSLATION"
    elif key == glfw.KEY_UP:
        translation[1] += 0.04
        current_transform = "TRANSLATION"
    elif key == glfw.KEY_DOWN:
        translation[1] -= 0.04
        current_transform = "TRANSLATION"
    elif key == glfw.KEY_Q:
        rotation -= math.radians(5)
        current_transform = "ROTATION"
    elif key == glfw.KEY_E:
        rotation += math.radians(5)
        current_transform = "ROTATION"
    elif key == glfw.KEY_X:
        scale_xy[0] *= 1.1
        current_transform = "SCALING"
    elif key == glfw.KEY_Z:
        scale_xy *= 0.9
        current_transform = "SCALING"
    elif key == glfw.KEY_F:
        reflection_yx_enabled = not reflection_yx_enabled
        current_transform = "REFLECTION Y=X" if reflection_yx_enabled else "IDENTITY"


def main():
    global rotation

    if not glfw.init():
        raise RuntimeError("GLFW initialization failed.")

    # OpenGL 2.1 compatibility context supports the immediate-mode HUD
    # while still allowing GLSL shaders and VBO-backed geometry.
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)

    window = glfw.create_window(WIDTH, HEIGHT, TITLE, None, None)
    if not window:
        glfw.terminate()
        raise RuntimeError("Could not create an OpenGL 2.1 window.")

    glfw.make_context_current(window)
    glViewport(0, 0, WIDTH, HEIGHT)
    glfw.swap_interval(1)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_position_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_key_callback(window, key_callback)

    program = create_shader_program()

    polygon = make_polygon()
    geometries = [
        create_geometry(make_triangle_fan(polygon)),
        create_geometry(polygon),
        create_geometry(make_grid()),
        create_geometry(make_axes()),
        create_geometry(make_crosshair()),
    ]
    triangle_geometry, outline_geometry, grid_geometry, axes_geometry, crosshair_geometry = geometries

    glClearColor(0.025, 0.035, 0.05, 1.0)
    glDisable(GL_DEPTH_TEST)
    glLineWidth(1.0)

    previous_time = glfw.get_time()
    try:
        while not glfw.window_should_close(window):
            now = glfw.get_time()
            dt = min(now - previous_time, 0.05)
            previous_time = now
            glfw.poll_events()

            if animation_enabled:
                rotation += dt * 0.65

            glDisable(GL_DEPTH_TEST)
            glClear(GL_COLOR_BUFFER_BIT)
            glUseProgram(program)
            glUniform1f(glGetUniformLocation(program, "uTime"), now)
            glUniform1i(glGetUniformLocation(program, "uPulse"), int(pulse_enabled))
            glUniform1i(glGetUniformLocation(program, "uColorMode"), color_mode)

            if show_grid:
                glLineWidth(1.0)
                draw_geometry(program, grid_geometry, GL_LINES)

            if show_axes:
                glLineWidth(1.0)
                draw_geometry(program, axes_geometry, GL_LINES)

            model = get_transform()
            if reflection_yx_enabled:
                model = model @ reflection_matrix("yx")

            draw_geometry(program, triangle_geometry, GL_TRIANGLES, model)

            if show_outline:
                glLineWidth(1.0)
                draw_geometry(program, outline_geometry, GL_LINE_LOOP, model)

            if show_pivot:
                draw_geometry(
                    program, crosshair_geometry, GL_LINES,
                    translate_matrix(pivot[0], pivot[1])
                )

            draw_hud()
            glDisable(GL_DEPTH_TEST)
            glfw.swap_buffers(window)
    finally:
        for vbo, count in geometries:
            glDeleteBuffers(1, [vbo])
        glDeleteProgram(program)
        glfw.terminate()


if __name__ == "__main__":
    main()
