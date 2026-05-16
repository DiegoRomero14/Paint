import cv2
import numpy as np
import re
import time
from collections import deque
from pathlib import Path

from database.drawing_model import save_drawing
from core.camara import initialize_camara
from core.gestures import classify_gesture
from core.painter import draw, get_color, set_color, reset_position



FRAME_WIDTH = 960
FRAME_HEIGHT = 720
WINDOW_NAME = "virtual paint"
DRAWINGS_DIR = Path("drawings")
GESTURE_DELAY = 1
COMMAND_CONFIRM_FRAMES = 5
DRAW_CONFIRM_FRAMES = 2
EDGE_MARGIN = 70
LANDMARK_MARGIN = 0.035

RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)
COLORS_BY_GESTURE = {
    "red": RED,
    "green": GREEN,
    "blue": BLUE,
}
GESTURE_LABELS = {
    "draw": "Dibujando",
    "red": "Color rojo",
    "green": "Color verde",
    "blue": "Color azul",
    "clear": "Limpiar",
    "edge": "Aleja la mano del borde",
    "idle": "Pausa",
}


class PointSmoother:
    def __init__(self):
        self.x = None
        self.y = None

    def reset(self):
        self.x = None
        self.y = None

    def update(self, x, y):
        if self.x is None or self.y is None:
            self.x = x
            self.y = y
            return int(self.x), int(self.y)

        distance = ((x - self.x) ** 2 + (y - self.y) ** 2) ** 0.5
        if distance < 2:
            return int(self.x), int(self.y)

        alpha = 0.22
        if distance > 45:
            alpha = 0.55
        elif distance > 16:
            alpha = 0.38

        self.x += (x - self.x) * alpha
        self.y += (y - self.y) * alpha
        return int(self.x), int(self.y)


def create_canvas():
    return np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)


def sanitize_filename(name):
    clean_name = re.sub(r"[^a-zA-Z0-9 _.-]", "", name).strip()
    clean_name = re.sub(r"\s+", "_", clean_name)
    return clean_name or time.strftime("drawing_%Y%m%d_%H%M%S")


def unique_output_path(name):
    DRAWINGS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(name)
    output_path = DRAWINGS_DIR / f"{safe_name}.png"
    counter = 2

    while output_path.exists():
        output_path = DRAWINGS_DIR / f"{safe_name}_{counter}.png"
        counter += 1

    return output_path


def save_canvas(canvas, drawing_name):
    try:
        output_path = unique_output_path(drawing_name)
        saved = cv2.imwrite(str(output_path), canvas)
    except Exception as error:
        print(f"No se pudo guardar el dibujo: {error}")
        return None

    if saved:
        try:
            save_drawing(
                user_id="1",
                drawing_name=drawing_name,
                image_path=output_path
            )

            print("Metadata guardada en MongoDB Atlas")

        except Exception as error:
         print(f"Error MongoDB: {error}")

        print(f"Dibujo guardado: {output_path}")
        return output_path

    print("No se pudo guardar el dibujo.")
    return None


def default_drawing_name():
    return time.strftime("drawing_%Y%m%d_%H%M%S")


def get_handedness_label(results, hand_index):
    if not results.multi_handedness or hand_index >= len(results.multi_handedness):
        return None

    classifications = results.multi_handedness[hand_index].classification
    if not classifications:
        return None

    return classifications[0].label


def stable_value(values):
    if len(values) < values.maxlen:
        return None

    first = values[0]
    if all(value == first for value in values):
        return first

    return None


def is_inside_safe_area(x, y, width, height):
    return (
        EDGE_MARGIN <= x <= width - EDGE_MARGIN
        and EDGE_MARGIN <= y <= height - EDGE_MARGIN
    )


def is_hand_reliable(landmarks, x, y, width, height):
    if not is_inside_safe_area(x, y, width, height):
        return False

    tracked_tips = [4, 8, 12, 16, 20]
    for tip in tracked_tips:
        landmark = landmarks[tip]
        if not (
            LANDMARK_MARGIN <= landmark.x <= 1 - LANDMARK_MARGIN
            and LANDMARK_MARGIN <= landmark.y <= 1 - LANDMARK_MARGIN
        ):
            return False

    return True


def draw_overlay(frame, gesture, cursor=None):
    color = get_color()
    label = GESTURE_LABELS.get(gesture, "Pausa")

    cv2.rectangle(frame, (0, 0), (FRAME_WIDTH, 54), (20, 20, 20), -1)
    cv2.circle(frame, (28, 27), 12, color, -1, cv2.LINE_AA)
    cv2.putText(
        frame,
        f"{label} | S nombrar y guardar | ESC salir",
        (52, 34),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (245, 245, 245),
        2,
        cv2.LINE_AA,
    )

    if cursor:
        cv2.circle(frame, cursor, 7, color, 2, cv2.LINE_AA)

    cv2.rectangle(
        frame,
        (EDGE_MARGIN, EDGE_MARGIN),
        (FRAME_WIDTH - EDGE_MARGIN, FRAME_HEIGHT - EDGE_MARGIN),
        (80, 160, 255),
        1,
        cv2.LINE_AA,
    )


def draw_save_dialog(frame, name):
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (FRAME_WIDTH, FRAME_HEIGHT), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

    box_width = 620
    box_height = 190
    x1 = (FRAME_WIDTH - box_width) // 2
    y1 = (FRAME_HEIGHT - box_height) // 2
    x2 = x1 + box_width
    y2 = y1 + box_height

    cv2.rectangle(frame, (x1, y1), (x2, y2), (245, 247, 250), -1, cv2.LINE_AA)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 160, 255), 2, cv2.LINE_AA)

    cv2.putText(
        frame,
        "Guardar dibujo",
        (x1 + 26, y1 + 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (25, 25, 25),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "Escribe un nombre. Enter guarda, Esc cancela.",
        (x1 + 26, y1 + 82),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (80, 80, 80),
        1,
        cv2.LINE_AA,
    )

    input_x1 = x1 + 26
    input_y1 = y1 + 104
    input_x2 = x2 - 26
    input_y2 = y1 + 150
    cv2.rectangle(frame, (input_x1, input_y1), (input_x2, input_y2), (255, 255, 255), -1)
    cv2.rectangle(frame, (input_x1, input_y1), (input_x2, input_y2), (190, 196, 205), 1)

    visible_name = name[-42:] if len(name) > 42 else name
    cv2.putText(
        frame,
        visible_name + "_",
        (input_x1 + 12, input_y1 + 31),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (20, 20, 20),
        2,
        cv2.LINE_AA,
    )


def update_save_name(name, key):
    if key in (8, 127):
        return name[:-1]
    if 32 <= key <= 126 and len(name) < 60:
        return name + chr(key)
    return name


def main():
    cap = initialize_camara(width=FRAME_WIDTH, height=FRAME_HEIGHT)

    if not cap.isOpened():
        print("No se pudo abrir la camara.")
        print("Conecta una webcam o revisa el indice usado por OpenCV.")
        return

    from core.hand_tracker import detect_hands, mp_draw, mp_hands

    canvas = create_canvas()
    last_gesture_time = 0
    cursor_smoother = PointSmoother()
    recent_commands = deque(maxlen=COMMAND_CONFIRM_FRAMES)
    draw_frames = 0
    active_gesture = "idle"
    cursor = None
    naming_mode = False
    pending_name = default_drawing_name()

    print("Virtual Paint iniciado.")
    print("Indice: dibujar | indice+medio: rojo | 3 dedos: verde | 4 dedos: azul | mano abierta: limpiar")
    print("Teclas: S guarda el dibujo | ESC cierra la aplicacion")

    try:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, FRAME_WIDTH, FRAME_HEIGHT)

        while True:
            current_time = time.time()
            ret, frame = cap.read()

            if not ret:
                print("No se pudo leer un frame de la camara.")
                break

            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            h, w, _ = frame.shape
            results = detect_hands(frame) if not naming_mode else None

            if results and results.multi_hand_landmarks:
                for hand_index, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                    )

                    landmarks = hand_landmarks.landmark
                    handedness_label = get_handedness_label(results, hand_index)
                    x = int(landmarks[8].x * w)
                    y = int(landmarks[8].y * h)

                    cx, cy = cursor_smoother.update(x, y)
                    cursor = (cx, cy)

                    if not is_hand_reliable(landmarks, x, y, w, h):
                        active_gesture = "edge"
                        draw_frames = 0
                        recent_commands.clear()
                        reset_position()
                        continue

                    gesture = classify_gesture(landmarks, handedness_label)
                    active_gesture = gesture

                    if gesture == "draw":
                        recent_commands.clear()
                        draw_frames += 1
                        if draw_frames == 1:
                            reset_position()
                        if draw_frames >= DRAW_CONFIRM_FRAMES:
                            draw(canvas, cx, cy)
                    else:
                        draw_frames = 0
                        reset_position()
                        recent_commands.append(gesture)
                        stable_command = stable_value(recent_commands)

                        if stable_command in COLORS_BY_GESTURE:
                            if current_time - last_gesture_time > GESTURE_DELAY:
                                set_color(COLORS_BY_GESTURE[stable_command])
                                last_gesture_time = current_time
                        elif stable_command == "clear":
                            if current_time - last_gesture_time > GESTURE_DELAY:
                                canvas = create_canvas()
                                last_gesture_time = current_time
            else:
                cursor_smoother.reset()
                recent_commands.clear()
                draw_frames = 0
                active_gesture = "idle"
                cursor = None
                reset_position()

            frame = cv2.add(frame, canvas)
            draw_overlay(frame, active_gesture, cursor)
            if naming_mode:
                draw_save_dialog(frame, pending_name)
            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF

            if naming_mode:
                if key == 27:
                    naming_mode = False
                    pending_name = default_drawing_name()
                    print("Guardado cancelado.")
                elif key in (10, 13):
                    save_canvas(canvas, pending_name)
                    naming_mode = False
                    pending_name = default_drawing_name()
                elif key != 255:
                    pending_name = update_save_name(pending_name, key)
                continue

            if key == 27:
                break
            if key in (ord("s"), ord("S")):
                naming_mode = True
                pending_name = default_drawing_name()
                reset_position()
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


