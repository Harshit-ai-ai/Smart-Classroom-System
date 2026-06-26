import os
import cv2
import numpy as np

INPUT_FOLDER = "students"
OUTPUT_FOLDER = "augmented"

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)

def augment_image(
    image
):

    images=[]

    images.append(
        image
    )

    brighter = cv2.convertScaleAbs(
        image,
        alpha=1.2,
        beta=30
    )

    darker = cv2.convertScaleAbs(
        image,
        alpha=0.8,
        beta=-20
    )

    images.append(
        brighter
    )

    images.append(
        darker
    )

    h,w = image.shape[:2]

    M1 = cv2.getRotationMatrix2D(
        (
            w//2,
            h//2
        ),
        10,
        1
    )

    M2 = cv2.getRotationMatrix2D(
        (
            w//2,
            h//2
        ),
        -10,
        1
    )

    r1 = cv2.warpAffine(
        image,
        M1,
        (w,h)
    )

    r2 = cv2.warpAffine(
        image,
        M2,
        (w,h)
    )

    images.append(r1)

    images.append(r2)

    blur = cv2.GaussianBlur(
        image,
        (5,5),
        0
    )

    images.append(
        blur
    )

    return images


for student in os.listdir(
    INPUT_FOLDER
):

    src_folder = os.path.join(
        INPUT_FOLDER,
        student
    )

    out_folder = os.path.join(
        OUTPUT_FOLDER,
        student
    )

    os.makedirs(
        out_folder,
        exist_ok=True
    )

    for file in os.listdir(
        src_folder
    ):

        path = os.path.join(
            src_folder,
            file
        )

        img = cv2.imread(
            path
        )

        if img is None:
            continue

        generated = augment_image(
            img
        )

        for i,g in enumerate(
            generated
        ):

            save_path = os.path.join(
                out_folder,
                f"{i}.jpg"
            )

            cv2.imwrite(
                save_path,
                g
            )

print(
    "Augmentation done"
)