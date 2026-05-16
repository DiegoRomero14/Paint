FINGER_TIPS = {
    "index": 8,
    "middle": 12,
    "ring": 16,
    "pinky": 20,
}
FINGER_PIPS = {
    "index": 6,
    "middle": 10,
    "ring": 14,
    "pinky": 18,
}
FINGER_MCPS = {
    "index": 5,
    "middle": 9,
    "ring": 13,
    "pinky": 17,
}

THUMB_TIP = 4
THUMB_JOINT = 3
THUMB_MCP = 2
FINGER_MARGIN = 0.025


def get_finger_states(landmarks, handedness_label=None):
    states = {
        "thumb": is_thumb_open(landmarks, handedness_label),
    }

    for name in FINGER_TIPS:
        states[name] = is_finger_open(landmarks, name)

    return states


def is_finger_open(landmarks, finger_name):
    tip = landmarks[FINGER_TIPS[finger_name]]
    pip = landmarks[FINGER_PIPS[finger_name]]
    mcp = landmarks[FINGER_MCPS[finger_name]]
    return tip.y < pip.y - FINGER_MARGIN and pip.y < mcp.y + 0.04


def is_thumb_open(landmarks, handedness_label=None):
    tip_x = landmarks[THUMB_TIP].x
    joint_x = landmarks[THUMB_JOINT].x
    tip_y = landmarks[THUMB_TIP].y
    mcp_y = landmarks[THUMB_MCP].y

    if handedness_label == "Left":
        horizontal_open = tip_x > joint_x + FINGER_MARGIN
    elif handedness_label == "Right":
        horizontal_open = tip_x < joint_x - FINGER_MARGIN
    else:
        horizontal_open = abs(tip_x - joint_x) > FINGER_MARGIN

    return horizontal_open and tip_y < mcp_y + 0.08


def count_fingers(landmarks, handedness_label=None):
    return sum(get_finger_states(landmarks, handedness_label).values())


def is_index_only(landmarks, handedness_label=None):
    states = get_finger_states(landmarks, handedness_label)
    return (
        states["index"]
        and not states["thumb"]
        and not states["middle"]
        and not states["ring"]
        and not states["pinky"]
    )


def classify_gesture(landmarks, handedness_label=None):
    states = get_finger_states(landmarks, handedness_label)
    finger_count = sum(states.values())

    if is_index_only(landmarks, handedness_label):
        return "draw"
    if finger_count == 2 and states["index"] and states["middle"]:
        return "red"
    if finger_count == 3 and states["index"] and states["middle"] and states["ring"]:
        return "green"
    if finger_count == 4 and not states["thumb"]:
        return "blue"
    if finger_count == 5:
        return "clear"

    return "idle"
