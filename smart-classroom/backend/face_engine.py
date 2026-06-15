import os
import face_recognition
import pickle
import cv2
import numpy as np
import base64
import torch
from ultralytics import YOLO

# Fix for PyTorch 2.6 weights_only unpickling error with older ultralytics
_original_load = torch.load
def _custom_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _custom_load

ENCODING_FILE = "encodings.pkl"

# Load YOLO model for person detection (anti-spoofing)
# It will download yolov8n.pt automatically on first run
yolo_model = YOLO("yolov8n.pt")

def load_encodings():
    if os.path.exists(ENCODING_FILE):
        with open(ENCODING_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_encodings(data):
    with open(ENCODING_FILE, "wb") as f:
        pickle.dump(data, f)

def enroll_student(name, image_path):
    image = face_recognition.load_image_file(image_path)
    faces = face_recognition.face_encodings(image, num_jitters=1)
    if len(faces) == 0:
        print("No face:", image_path)
        return False
    encodings = load_encodings()
    if name not in encodings:
        encodings[name] = []
    encodings[name].append(faces[0])
    save_encodings(encodings)
    print("Added:", name, image_path)
    return True

def recognize(base64_image):
    try:
        print("START RECOGNITION WITH YOLO + LIVENESS")
        db = load_encodings()
        if len(db) == 0:
            print("Database empty")
            return []

        if "," in base64_image:
            base64_image = base64_image.split(",")[1]

        image_bytes = base64.b64decode(base64_image)
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if image is None:
            print("Image decode failed")
            return []

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 1. Advanced YOLO Detection for Body/Context (Anti-Spoofing)
        results = yolo_model(image)
        persons = []
        for r in results:
            for box in r.boxes:
                # Class 0 is 'person' in COCO dataset
                if int(box.cls[0]) == 0 and float(box.conf[0]) > 0.6:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # Liveness Check 1: Aspect ratio of person should be roughly vertical
                    h = y2 - y1
                    w = x2 - x1
                    if h > w * 0.8: # Person isn't a horizontal 2D floating cutout
                        persons.append((x1, y1, x2, y2))

        # 2. Face Detection
        face_locations = face_recognition.face_locations(image_rgb, model="hog")
        face_encs = face_recognition.face_encodings(image_rgb, face_locations, num_jitters=1)

        detected = []
        used_students = set()

        for (top, right, bottom, left), face in zip(face_locations, face_encs):
            
            # Anti-Spoofing Check: Is this face inside a detected human body?
            is_real_person = False
            for (px1, py1, px2, py2) in persons:
                # relaxed check to handle slightly out-of-box faces
                if left >= px1 - 50 and right <= px2 + 50 and top >= py1 - 50 and bottom <= py2 + 50:
                    is_real_person = True
                    break
            
            if not is_real_person:
                print("Spoof detected: Face found but no corresponding YOLO person body.")
                # We can skip or mark as spoof
                # For now, we skip marking attendance for floating faces
                continue

            best_name = None
            best_distance = 999

            for student_name, saved_list in db.items():
                if len(saved_list) == 0:
                    continue
                distances = face_recognition.face_distance(saved_list, face)
                distance = float(np.min(distances))

                if distance < best_distance:
                    best_distance = distance
                    best_name = student_name

            if best_name and best_distance < 0.55 and best_name not in used_students:
                label = best_name
                detected.append(best_name)
                used_students.add(best_name)
                print("Matched:", best_name, best_distance)
            else:
                label = "Unknown"
                detected.append(label)

            cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(image, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        os.makedirs("static", exist_ok=True)
        cv2.imwrite("static/result.jpg", image)

        return detected

    except Exception as e:
        print("Recognition Error:", str(e))
        return []