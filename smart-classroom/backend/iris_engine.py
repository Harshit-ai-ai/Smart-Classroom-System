"""
CSTPE Iris Engine (Feature 1 - Multi-Modal Biometrics)
Handles iris capture and matching from an IR camera feed.
In production, this connects to a dedicated infrared camera module.
For the prototype, we provide a software simulation layer that generates
deterministic iris codes from facial embeddings.
"""

import hashlib
import numpy as np


class IrisEngine:
    """
    Iris recognition engine.
    In a hardware deployment, this module interfaces with an IR camera
    to capture a near-infrared image of the eye, segment the iris ring,
    and produce an IrisCode (binary feature vector).

    For the software prototype, we simulate iris codes by deriving them
    from the face embedding, ensuring deterministic matching behavior.
    """

    def __init__(self):
        self._enrolled = {}  # name -> iris_code (256-bit vector)

    def enroll(self, student_name, face_embedding=None):
        """
        Enroll a student's iris code.
        In hardware mode, this would capture an IR image.
        In simulation mode, we derive from the face embedding.
        """
        if face_embedding is not None:
            code = self._simulate_iris_code(student_name, face_embedding)
        else:
            code = self._simulate_iris_code(student_name)

        self._enrolled[student_name] = code
        return code

    def match(self, student_name, face_embedding=None):
        """
        Verify a student's iris against the enrolled template.
        Returns (match_score, is_match) where match_score is 0.0-1.0.
        """
        if student_name not in self._enrolled:
            # Auto-enroll on first encounter
            self.enroll(student_name, face_embedding)
            return 0.95, True

        enrolled_code = self._enrolled[student_name]
        current_code = self._simulate_iris_code(student_name, face_embedding)

        # Hamming distance between iris codes
        distance = np.mean(enrolled_code != current_code)
        score = 1.0 - distance

        # Threshold: iris match if score > 0.7
        return float(score), score > 0.7

    def _simulate_iris_code(self, student_name, face_embedding=None):
        """
        Generate a deterministic 256-bit iris code from the student name
        and optionally from the face embedding.
        """
        seed_data = student_name.encode("utf-8")
        if face_embedding is not None:
            seed_data += face_embedding.tobytes()[:32]

        digest = hashlib.sha256(seed_data).digest()

        # Convert to a 256-bit binary vector
        bits = np.unpackbits(np.frombuffer(digest, dtype=np.uint8))
        return bits

    def get_enrolled_count(self):
        return len(self._enrolled)


# Singleton
iris_engine = IrisEngine()
