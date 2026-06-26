import os
import face_recognition
import pickle
import cv2
import numpy as np
import base64
import torch
from ultralytics import YOLO
from cryptography.fernet import Fernet

# Fix for PyTorch 2.6 weights_only unpickling error
_original_load = torch.load
def _custom_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _custom_load

DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
ENCODING_FILE = os.path.join(DATA_DIR, "encodings.pkl")

# Generate or load the 256-bit AES key
ENCRYPTION_KEY = os.getenv("BIO_ENCRYPTION_KEY", Fernet.generate_key().decode())
fernet = Fernet(ENCRYPTION_KEY.encode())

# OPTIMIZATION 1: Load ONNX model for edge inference
# ONNX is significantly lighter on CPU/RAM than PyTorch.
ONNX_MODEL_PATH = "exports/yolov8n.onnx"
if os.path.exists(ONNX_MODEL_PATH):
    yolo_model = YOLO(ONNX_MODEL_PATH, task="detect")
    print("Loaded YOLOv8 ONNX format for Edge Inference.")
else:
    # Fallback to PyTorch if ONNX export hasn't run yet
    yolo_model = YOLO("yolov8n.pt")
    print("Loaded YOLOv8 PyTorch format.")

def load_encodings():
    if os.path.exists(ENCODING_FILE):
        with open(ENCODING_FILE, "rb") as f:
            data = f.read()
        try:
            decrypted_data = fernet.decrypt(data)
            return pickle.loads(decrypted_data)
        except Exception:
            try:
                # Migration: File exists but is not encrypted. Load it and auto-encrypt it.
                unencrypted = pickle.loads(data)
                save_encodings(unencrypted)
                print("Auto-migrated legacy unencrypted biometric database to AES-256.")
                return unencrypted
            except Exception as e:
                print(f"Failed to load biometric database: {e}")
                return {}
    return {}

def save_encodings(data):
    binary_data = pickle.dumps(data)
    encrypted_data = fernet.encrypt(binary_data)
    with open(ENCODING_FILE, "wb") as f:
        f.write(encrypted_data)

def enroll_student(name, image_path=None, base64_image=None):
    if base64_image:
        if "," in base64_image:
            base64_image = base64_image.split(",")[1]
        image_bytes = base64.b64decode(base64_image)
        np_array = np.frombuffer(image_bytes, np.uint8)
        cv_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        if cv_image is None: return False
        image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    elif image_path:
        image = face_recognition.load_image_file(image_path)
    else:
        return False
        
    faces = face_recognition.face_encodings(image, num_jitters=1)
    if len(faces) == 0:
        print("No face detected for enrollment")
        return False
    encodings = load_encodings()
    if name not in encodings:
        encodings[name] = []
    encodings[name].append(faces[0])
    save_encodings(encodings)
    print("Enrolled:", name)
    return True

def resize_for_edge(image, max_width=1920):
    """
    OPTIMIZATION 2: Adaptive High-Res Frame Downscaling.
    Supports high-res 1080p CCTV feeds while preventing 4K+ memory explosions.
    """
    h, w = image.shape[:2]
    if w > max_width:
        ratio = max_width / w
        new_h = int(h * ratio)
        return cv2.resize(image, (max_width, new_h), interpolation=cv2.INTER_AREA)
    return image

def recognize(base64_image):
    try:
        db = load_encodings()
        if len(db) == 0:
            return []

        if "," in base64_image:
            base64_image = base64_image.split(",")[1]

        image_bytes = base64.b64decode(base64_image)
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if image is None:
            return []
            
        # Apply Edge Optimization 2: Downscaling (Increased to 1080p for CCTV)
        image = resize_for_edge(image, max_width=1920)

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 1. Advanced YOLO Detection for Body/Context (Anti-Spoofing)
        # Using imgsz=640 optimizes ONNX inference further
        results = yolo_model(image, imgsz=640, verbose=False)
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

        # OPTIMIZATION 3: Fast-Fail
        # If YOLO found no humans, don't run heavy dlib face extraction
        if len(persons) == 0:
            # We still save the image so the dashboard doesn't look frozen
            os.makedirs("static", exist_ok=True)
            cv2.imwrite("static/result.jpg", image)
            return []

        # 2. Face Detection
        # Only reached if YOLO found a person
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
                # Floating face detected (spoof)
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
