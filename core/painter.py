import cv2

BRUSH_THICKNESS = 5
MIN_DRAW_DISTANCE = 5

prev_x, prev_y = 0, 0
draw_color = (0, 0, 255)


def draw(canvas, x, y):
    global prev_x, prev_y

    distance = ((x - prev_x) ** 2 + (y - prev_y) ** 2) ** 0.5
    if distance < MIN_DRAW_DISTANCE:
        return

    if prev_x == 0 and prev_y == 0:
        prev_x, prev_y = x, y

    cv2.line(canvas, (prev_x, prev_y), (x, y), draw_color, BRUSH_THICKNESS)
    prev_x, prev_y = x, y


def set_color(color):
    global draw_color

    draw_color = color


def reset_position():
    global prev_x, prev_y

    prev_x, prev_y = 0, 0
