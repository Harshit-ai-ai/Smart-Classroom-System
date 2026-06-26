"""
CSTPE Pose Engine
Height Estimation
Posture Analysis
CSR Calculation
SWR Calculation
"""

import cv2
import math
import numpy as np
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


CAM_HEIGHT = 2.5
CAM_TILT = 15.0
VERTICAL_FOV = 60.0

REF_DISTANCE = 2.0
REF_PIXEL_HEIGHT = 400.0

_prev_height = None


def pixel_to_angle(y_pixel, frame_height):
    return (
        (y_pixel - frame_height / 2)
        / frame_height
    ) * VERTICAL_FOV


def estimate_distance(pixel_height):
    return (
        REF_DISTANCE *
        (REF_PIXEL_HEIGHT / pixel_height)
    )


def estimate_height(head_y, pixel_height, frame_h):

    angle = math.radians(
        CAM_TILT +
        pixel_to_angle(
            head_y,
            frame_h
        )
    )

    return (
        CAM_HEIGHT -
        estimate_distance(pixel_height)
        * math.tan(angle)
    )


def smooth_height(new_h):

    global _prev_height

    if _prev_height is None:
        _prev_height = new_h
    else:
        _prev_height = (
            0.8 * _prev_height +
            0.2 * new_h
        )

    return _prev_height


def calculate_angle(a, b):

    return np.degrees(
        np.arctan2(
            b[1] - a[1],
            b[0] - a[0]
        )
    )


def get_head_top(lm, h):

    eye_mid = (
        lm[2].y +
        lm[5].y
    ) / 2

    return (
        eye_mid - 0.10
    ) * h


def get_pixel_height(lm, h):

    head_y = get_head_top(
        lm,
        h
    )

    ankle_y = max(
        lm[27].y,
        lm[28].y
    ) * h

    return head_y, abs(
        ankle_y - head_y
    )


def head_length(lm, h):

    head_top = get_head_top(
        lm,
        h
    )

    return abs(
        lm[0].y * h -
        head_top
    )


def cranio_shoulder_ratio(lm, h):

    hl = head_length(
        lm,
        h
    )

    if hl == 0:
        return None

    shoulder_y = (
        lm[11].y +
        lm[12].y
    ) / 2 * h

    return abs(
        shoulder_y -
        lm[0].y * h
    ) / hl


def shoulder_width_ratio(lm, w, h):

    hl = head_length(
        lm,
        h
    )

    if hl == 0:
        return None

    width = np.linalg.norm([
        (lm[11].x - lm[12].x) * w,
        (lm[11].y - lm[12].y) * h
    ])

    return width / hl


class PoseEngine:

    def __init__(self):

        base_options = python.BaseOptions(
            model_asset_path="pose_landmarker_lite.task"
        )

        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=5
        )

        self.landmarker = (
            vision.PoseLandmarker.create_from_options(
                options
            )
        )

    def analyze(
        self,
        frame,
        timestamp
    ):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.landmarker.detect_for_video(
            mp_image,
            timestamp
        )

        if not result.pose_landmarks:
            return None

        lm = result.pose_landmarks[0]

        h, w = frame.shape[:2]

        head_y, pixel_height = (
            get_pixel_height(
                lm,
                h
            )
        )

        height = None

        if pixel_height > 50:

            raw_height = estimate_height(
                head_y,
                pixel_height,
                h
            )

            if 1.2 < raw_height < 2.2:

                height = smooth_height(
                    raw_height
                )

        ear = (
            int(lm[7].x * w),
            int(lm[7].y * h)
        )

        shoulder = (
            int(lm[11].x * w),
            int(lm[11].y * h)
        )

        posture = calculate_angle(
            shoulder,
            ear
        )

        csr = cranio_shoulder_ratio(
            lm,
            h
        )

        swr = shoulder_width_ratio(
            lm,
            w,
            h
        )

        return {

            "height": height,

            "posture": posture,

            "csr": csr,

            "swr": swr
        }


pose_engine = PoseEngine()