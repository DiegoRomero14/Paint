def count_fingers(landmarks):
    tips = [12,8,16,20]
    fingers=[]
    fingers.append(landmarks[4].x<landmarks[3].x)
    for tip in tips:
        fingers.append(landmarks[tip].y < landmarks[tip -2].y)
    return sum(fingers)

