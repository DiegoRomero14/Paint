import cv2
from mediapipe.python.solutions import drawing_utils as mp_draw
from mediapipe.python.solutions import hands as mp_hands


hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)


def detect_hands(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return hands.process(rgb)
