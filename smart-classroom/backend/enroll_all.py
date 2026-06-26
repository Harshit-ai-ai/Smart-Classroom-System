import os

from face_engine import enroll_student

STUDENT_FOLDER = "students"

for student in os.listdir(
    STUDENT_FOLDER
):

    student_path = os.path.join(
        STUDENT_FOLDER,
        student
    )

    if not os.path.isdir(
        student_path
    ):

        continue

    images = os.listdir(
        student_path
    )

    success = 0

    for img in images:

        img_path = os.path.join(
            student_path,
            img
        )

        result = enroll_student(
            student,
            img_path
        )

        if result:

            success += 1

    print(
        student,
        "->",
        success,
        "images enrolled"
    )

print(
    "Enrollment complete"
)