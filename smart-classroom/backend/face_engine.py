import os
import face_recognition
import pickle
import cv2
import numpy as np
import base64

ENCODING_FILE = "encodings.pkl"


def load_encodings():

    if os.path.exists(ENCODING_FILE):

        with open(
            ENCODING_FILE,
            "rb"
        ) as f:

            return pickle.load(f)

    return {}


def save_encodings(data):

    with open(
        ENCODING_FILE,
        "wb"
    ) as f:

        pickle.dump(
            data,
            f
        )


def enroll_student(
    name,
    image_path
):

    image = face_recognition.load_image_file(
        image_path
    )

    faces = face_recognition.face_encodings(
        image,
        num_jitters=1
    )

    if len(faces) == 0:

        print(
            "No face:",
            image_path
        )

        return False

    encodings = load_encodings()

    if name not in encodings:

        encodings[name] = []

    encodings[name].append(
        faces[0]
    )

    save_encodings(
        encodings
    )

    print(
        "Added:",
        name,
        image_path
    )

    return True


def recognize(base64_image):

    try:

        print("START RECOGNITION")

        db = load_encodings()

        print(
            "DB SIZE:",
            len(db)
        )

        if len(db) == 0:

            print(
                "Database empty"
            )

            return []

        if "," in base64_image:

            base64_image = (
                base64_image.split(",")[1]
            )

        image_bytes = (
            base64.b64decode(
                base64_image
            )
        )

        np_array = np.frombuffer(
            image_bytes,
            np.uint8
        )

        image = cv2.imdecode(
            np_array,
            cv2.IMREAD_COLOR
        )

        if image is None:

            print(
                "Image decode failed"
            )

            return []

        print("IMAGE DECODED")

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        face_locations = (
            face_recognition.face_locations(
                image,
                model="hog"
            )
        )

        print(
            "FACE LOCATIONS COMPLETE:",
            len(face_locations)
        )

        face_encs = (
            face_recognition.face_encodings(
                image,
                face_locations,
                num_jitters=1
            )
        )

        print(
            "FACE ENCODINGS COMPLETE"
        )

        detected = []

        used_students = set()

        for (
            (top, right, bottom, left),
            face
        ) in zip(
            face_locations,
            face_encs
        ):

            best_name = None
            best_distance = 999

            for (
                student_name,
                saved_list
            ) in db.items():

                if len(saved_list) == 0:
                    continue

                distances = (
                    face_recognition.face_distance(
                        saved_list,
                        face
                    )
                )

                distance = float(
                    np.min(
                        distances
                    )
                )

                print(
                    student_name,
                    distance
                )

                if (
                    distance
                    <
                    best_distance
                ):

                    best_distance = distance

                    best_name = student_name

            if (
                best_name
                and
                best_distance < 0.55
                and
                best_name
                not in used_students
            ):

                label = best_name

                detected.append(
                    best_name
                )

                used_students.add(
                    best_name
                )

                print(
                    "Matched:",
                    best_name,
                    best_distance
                )

            else:

                label = "Unknown"

                detected.append(
                    label
                )

                print(
                    "Unknown face"
                )

            cv2.rectangle(
                image,
                (left, top),
                (right, bottom),
                (0, 255, 0),
                2
            )

            cv2.putText(
                image,
                label,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        os.makedirs(
            "static",
            exist_ok=True
        )

        image = cv2.cvtColor(
            image,
            cv2.COLOR_RGB2BGR
        )

        os.makedirs("static", exist_ok=True)

        cv2.imwrite(
            "static/result.jpg",
            image
        )

        print(
            "Detected final:",
            detected
        )

        return detected

    except Exception as e:

        print(
            "Recognition Error:",
            str(e)
        )

        return []