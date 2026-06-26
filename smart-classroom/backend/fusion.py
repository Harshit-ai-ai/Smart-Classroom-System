"""
CSTPE Multi-Modal Biometric Fusion (Feature 1)
Weighted Kalman-filter fusion of face, iris, and voice biometric signals.
The combined confidence score determines whether a detection is accepted.
"""

import numpy as np
from policy_engine import policy


class KalmanBiometricFilter:
    """
    Lightweight Kalman filter for fusing multiple biometric confidence scores.
    State: [face_conf, iris_conf, voice_conf]
    Observation: raw scores from each modality.
    """

    def __init__(self):
        self.state = np.array([0.5, 0.5, 0.5])  # initial estimate
        self.covariance = np.eye(3) * 0.1
        self.process_noise = np.eye(3) * 0.01
        self.measurement_noise = np.eye(3) * 0.05

    def predict(self):
        # State transition: identity (confidence does not drift)
        self.covariance += self.process_noise

    def update(self, measurement):
        """
        measurement: np.array([face_score, iris_score, voice_score])
        """
        self.predict()

        # Kalman gain
        S = self.covariance + self.measurement_noise
        K = self.covariance @ np.linalg.inv(S)

        # Update state
        innovation = measurement - self.state
        self.state = self.state + K @ innovation
        self.covariance = (np.eye(3) - K) @ self.covariance

        # Clamp to [0, 1]
        self.state = np.clip(self.state, 0.0, 1.0)

        return self.state.copy()


class BiometricFusion:
    def __init__(self):
        self._filters = {}  # student_name -> KalmanBiometricFilter

    def fuse(self, student_name, face_score, iris_score, voice_score):
        """
        Fuse three biometric scores into a single confidence value.
        Returns (fused_score, is_accepted, individual_scores).
        """
        if student_name not in self._filters:
            self._filters[student_name] = KalmanBiometricFilter()

        kf = self._filters[student_name]

        # Feed raw measurements through the Kalman filter
        measurement = np.array([face_score, iris_score, voice_score])
        filtered = kf.update(measurement)

        # Weighted combination using policy weights
        w_face = policy.get_float("weight_face", 0.5)
        w_iris = policy.get_float("weight_iris", 0.3)
        w_voice = policy.get_float("weight_voice", 0.2)

        weights = np.array([w_face, w_iris, w_voice])
        weights /= weights.sum()  # normalize

        fused_score = float(np.dot(weights, filtered))
        threshold = policy.get_float("fusion_threshold", 0.7)

        return fused_score, fused_score >= threshold, {
            "face": float(filtered[0]),
            "iris": float(filtered[1]),
            "voice": float(filtered[2]),
            "fused": fused_score,
            "threshold": threshold,
        }

    def reset_student(self, student_name):
        if student_name in self._filters:
            del self._filters[student_name]


# Singleton
biometric_fusion = BiometricFusion()
