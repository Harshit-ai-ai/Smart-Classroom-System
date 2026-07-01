import cv2


class EngagementEngine:

    def detect_gaze(self, face_img):

        gray = cv2.cvtColor(
            face_img,
            cv2.COLOR_BGR2GRAY
        )

        h, w = gray.shape

        eye_region = gray[
            0:int(h / 2),
            :
        ]

        _, thresh = cv2.threshold(
            eye_region,
            30,
            255,
            cv2.THRESH_BINARY_INV
        )

        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if len(contours) == 0:
            return "UNKNOWN"

        cnt = max(
            contours,
            key=cv2.contourArea
        )

        M = cv2.moments(cnt)

        if M["m00"] == 0:
            return "UNKNOWN"

        cx = int(
            M["m10"] / M["m00"]
        )

        if cx < w * 0.4:
            return "LEFT"

        elif cx > w * 0.6:
            return "RIGHT"

        return "CENTER"

    def attention_score(self, gaze):

        scores = {

            "CENTER": 1.0,

            "LEFT": 0.5,

            "RIGHT": 0.5,

            "UNKNOWN": 0.2

        }

        return scores.get(
            gaze,
            0.2
        )


engagement_engine = EngagementEngine()