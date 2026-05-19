import cv2

DEFAULT_CAMERA_INDEX = 0


def initialize_camara(camera_index=DEFAULT_CAMERA_INDEX, width=None, height=None):
    cap = cv2.VideoCapture(camera_index)

    if width is not None:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height is not None:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    return cap
