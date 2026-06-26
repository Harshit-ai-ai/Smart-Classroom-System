"""
CSTPE Voice Engine (Feature 1 - Multi-Modal Biometrics)
Voice Activity Detection (VAD) and speaker verification.
In production, this interfaces with a classroom microphone array.
For the prototype, we provide a software simulation layer.
"""

import hashlib
import numpy as np
import time


class VoiceEngine:
    """
    Voice activity and speaker verification engine.
    In hardware mode, this captures audio from a microphone array,
    runs Voice Activity Detection (VAD), and extracts speaker embeddings
    using a pre-trained model (e.g., ECAPA-TDNN).

    For the software prototype, we simulate voice embeddings and VAD
    results to demonstrate the multi-modal fusion pipeline.
    """

    def __init__(self):
        self._enrolled = {}  # name -> voice_embedding
        self._last_activity = {}  # name -> timestamp of last voice detection

    def enroll(self, student_name):
        """
        Enroll a student's voice profile.
        In hardware mode, this records a 5-second audio sample.
        """
        embedding = self._simulate_voice_embedding(student_name)
        self._enrolled[student_name] = embedding
        return embedding

    def detect_activity(self, student_name):
        """
        Check if the student has recent voice activity.
        Returns (is_active, confidence).
        """
        # Simulate voice activity detection
        # In production, this would process real-time audio samples
        now = time.time()
        last = self._last_activity.get(student_name, 0)

        # Simulate periodic voice activity (e.g., answering questions)
        simulated_active = (int(now) % 30) < 20  # active 2/3 of the time
        confidence = 0.85 if simulated_active else 0.2

        if simulated_active:
            self._last_activity[student_name] = now

        return simulated_active, confidence

    def verify_speaker(self, student_name):
        """
        Verify that the detected voice matches the enrolled speaker.
        Returns (match_score, is_match).
        """
        if student_name not in self._enrolled:
            self.enroll(student_name)
            return 0.9, True

        enrolled = self._enrolled[student_name]
        current = self._simulate_voice_embedding(student_name)

        # Cosine similarity
        dot = np.dot(enrolled, current)
        norm = np.linalg.norm(enrolled) * np.linalg.norm(current)
        similarity = dot / (norm + 1e-8)

        return float(similarity), similarity > 0.7

    def _simulate_voice_embedding(self, student_name):
        """
        Generate a deterministic 128-dim voice embedding from the student name.
        """
        seed = int(hashlib.md5(student_name.encode()).hexdigest(), 16) % (2**31)
        rng = np.random.RandomState(seed)
        embedding = rng.randn(128).astype(np.float32)
        embedding /= np.linalg.norm(embedding)
        return embedding

    def get_enrolled_count(self):
        return len(self._enrolled)


# Singleton
voice_engine = VoiceEngine()
