FINGER_TIPS = [12, 8, 16, 20]
THUMB_TIP = 4
THUMB_JOINT = 3


def count_fingers(landmarks):
    fingers = [landmarks[THUMB_TIP].x < landmarks[THUMB_JOINT].x]

    for tip in FINGER_TIPS:
        fingers.append(landmarks[tip].y < landmarks[tip - 2].y)

    return sum(fingers)
