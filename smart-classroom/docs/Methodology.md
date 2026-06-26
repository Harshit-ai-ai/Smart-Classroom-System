# Methodology

## System Overview

The proposed Smart Classroom Vision system performs
continuous classroom monitoring through a combination
of computer vision, facial recognition, pose estimation,
gaze analysis, and attendance management.

---

## Stage 1: Frame Acquisition

Video frames are captured continuously from a
classroom camera.

---

## Stage 2: Human Detection

YOLOv8 is used to identify human subjects within
the classroom environment.

Implementation:

main.py

yolo = YOLO("yolov8n.pt")

---

## Stage 3: Face Detection

OpenCV Haar Cascade is used to localize faces.

Implementation:

face_cascade.detectMultiScale()

---

## Stage 4: Face Recognition

FaceNet InceptionResnetV1 generates facial
embeddings.

Implementation:

facenet = InceptionResnetV1(
    pretrained="vggface2"
)

---

## Stage 5: Student Identification

Generated embeddings are matched against
enrolled student embeddings.

Implementation:

student_id = get_student_id(face_embedding)

---

## Stage 6: Gaze Detection

Eye contour analysis determines whether the
student is looking left, right, or center.

Implementation:

detect_gaze()

---

## Stage 7: Pose Estimation

MediaPipe Pose extracts body landmarks.

Implementation:

pose_landmarker.detect_for_video()

---

## Stage 8: Height Estimation

Height is estimated using camera calibration
parameters and geometric projection.

Implementation:

estimate_height()

---

## Stage 9: Posture Analysis

Neck and shoulder alignment angles are calculated.

Implementation:

calculate_angle()

---

## Stage 10: Anthropometric Analysis

The system computes:

- Cranio-Shoulder Ratio
- Shoulder Width Ratio

for behavioral and posture assessment.

Implementation:

cranio_shoulder_ratio()
shoulder_width_ratio()

---

## Stage 11: Attendance Engine

Recognized students are marked present and
their attendance records updated.

Implementation:

update_attendance()

---

## Stage 12: Database Storage

Observations are periodically stored.

Stored Parameters:

- Student ID
- Timestamp
- Height
- Posture Angle
- Gaze Direction
- Cranio-Shoulder Ratio
- Shoulder Width Ratio

Implementation:

insert_observation()