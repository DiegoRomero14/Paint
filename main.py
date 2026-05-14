import cv2
import numpy as np
import time
from pathlib import Path

from core.camara import initialize_camara
from core.gestures import count_fingers
from core.painter import draw, set_color, reset_position


FRAME_WIDTH = 640
FRAME_HEIGHT = 480
WINDOW_NAME = "virtual paint"
DRAWINGS_DIR = Path("drawings")
GESTURE_DELAY = 1
SMOOTHING = 5

RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)
COLORS_BY_FINGER_COUNT = {
    2: RED,
    3: GREEN,
    4: BLUE,
}


def create_canvas():
    return np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)


def save_canvas(canvas):
    DRAWINGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = DRAWINGS_DIR / f"drawing_{timestamp}.png"

    if cv2.imwrite(str(output_path), canvas):
        print(f"Dibujo guardado: {output_path}")
        return output_path

    print("No se pudo guardar el dibujo.")
    return None


def main():
    cap = initialize_camara(width=FRAME_WIDTH, height=FRAME_HEIGHT)

    if not cap.isOpened():
        print("No se pudo abrir la camara.")
        print("Conecta una webcam o revisa el indice usado por OpenCV.")
        return

    from core.hand_tracker import detect_hands, mp_draw, mp_hands

    canvas = create_canvas()
    last_gesture_time = 0
    smooth_x, smooth_y = 0, 0

    print("Virtual Paint iniciado.")
    print("1 dedo: dibujar | 2: rojo | 3: verde | 4: azul | 5: limpiar")
    print("Teclas: S guarda el dibujo | ESC cierra la aplicacion")

    try:
        while True:
            current_time = time.time()
            ret, frame = cap.read()

            if not ret:
                print("No se pudo leer un frame de la camara.")
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            results = detect_hands(frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                    )

                    landmarks = hand_landmarks.landmark
                    x = int(landmarks[8].x * w)
                    y = int(landmarks[8].y * h)

                    smooth_x = smooth_x + (x - smooth_x) / SMOOTHING
                    smooth_y = smooth_y + (y - smooth_y) / SMOOTHING

                    cx = int(smooth_x)
                    cy = int(smooth_y)
                    finger_count = count_fingers(landmarks)

                    if finger_count == 1:
                        draw(canvas, cx, cy)
                    elif finger_count in COLORS_BY_FINGER_COUNT:
                        if current_time - last_gesture_time > GESTURE_DELAY:
                            set_color(COLORS_BY_FINGER_COUNT[finger_count])
                            last_gesture_time = current_time
                        reset_position()
                    elif finger_count == 5:
                        if current_time - last_gesture_time > GESTURE_DELAY:
                            canvas = create_canvas()
                            last_gesture_time = current_time
                        reset_position()
            else:
                reset_position()

            frame = cv2.add(frame, canvas)
            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break
            if key in (ord("s"), ord("S")):
                save_canvas(canvas)
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


