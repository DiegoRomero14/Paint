import cv2
import numpy  as np
import mediapipe  as mp
import time
import os
import tkinter as tk
from tkinter import simpledialog


from database.drawing_model import save_drawing
from core.camara import initialize_camara
from core.hand_tracker import detect_hands, mp_draw, mp_hands
from core.gestures import count_fingers
from core.painter import draw, set_color, reset_position


cap = initialize_camara()
cap.set(3,640)
cap.set(4,480)

canvas = np.zeros((480,640,3),dtype=np.uint8)
last_gesture_time = 0
gesture_delay = 1

smooth_x, smooth_y = 0, 0
smoothing = 5

current_user = {"_id" : 123456}


def ask_drawing_name():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.update()

    drawing_name = simpledialog.askstring(
        "Guardar dibujo",
        "Nombre del dibujo:",
        parent=root
    )

    root.destroy()
    return drawing_name




while True:

    current_time = time.time()
    ret, frame = cap.read()


    if not ret:
        break

    frame = cv2.flip(frame,1)

    h,w,c = frame.shape

    results = detect_hands(frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            lm = hand_landmarks.landmark

            x = int(lm[8].x*w)
            y = int(lm[8].y*h)

            smooth_x = smooth_x + (x - smooth_x) / smoothing
            smooth_y = smooth_y + (y - smooth_y) / smoothing

            cx = int(smooth_x)
            cy = int(smooth_y)

            finger_count = count_fingers(lm)

            if finger_count == 1:
                draw(canvas, cx, cy)

            elif finger_count ==2:

                if current_time - last_gesture_time > gesture_delay:
                    set_color((0,0,255))
                    last_gesture_time = current_time
                reset_position()

            elif finger_count ==3:
                if current_time - last_gesture_time > gesture_delay:
                    set_color((0,255,0))
                    last_gesture_time = current_time
                reset_position()

            elif finger_count == 4:
                if current_time - last_gesture_time > gesture_delay:
                    set_color((255,0,0))
                    last_gesture_time = current_time
                reset_position()
            
            elif finger_count == 5:
                if current_time - last_gesture_time > gesture_delay:
                    canvas = np.zeros_like(canvas)
                    last_gesture_time = current_time
                reset_position()

    frame = cv2.add(frame, canvas)
    cv2.imshow("virtual paint", frame)
    key = cv2.waitKey(1) & 0xFF 
    if key == 27:
        break

    elif key == ord("s"):
        drawing_name = ask_drawing_name()

        if drawing_name:
            drawing_name = drawing_name.replace(" ", "_")

            if not os.path.exists("saved_drawings"):
                os.makedirs("saved_drawings")

            filename = f"{drawing_name}_{int(time.time())}.png"
            filepath = os.path.join("saved_drawings", filename)

            cv2.imwrite(filepath, canvas)

            save_drawing(current_user["_id"], drawing_name, filepath)

            print("Dibujo guardado correctamente")

        

cap.release()
cv2.destroyAllWindows()

