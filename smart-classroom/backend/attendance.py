import cv2

def take_attendance():

    camera = cv2.VideoCapture(0)

    ret, frame = camera.read()

    camera.release()

    if not ret:
        return []

    detected = [
        "Harshit",
        "Aman",
        "Riya"
    ]

    return detected