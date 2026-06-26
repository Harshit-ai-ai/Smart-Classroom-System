"""
CSTPE Session Recovery (Feature 10 - Part 2)
When a student leaves the frame and returns after the gap-threshold,
this module attempts to re-link the new detection to the existing session
using cosine similarity of face embeddings, preventing session fragmentation.
"""

import numpy as np
from embedding_store import get_all_recent_embeddings
from policy_engine import policy


class SessionRecovery:

    def attempt_recovery(self, unknown_embedding):
        """
        Given a face embedding that could not be directly matched,
        compare it against all recently stored embeddings to find
        a possible session to resume.

        Returns (student_name, similarity) if a match is found,
        or (None, 0.0) if no match exceeds the threshold.
        """
        threshold = policy.get_float("session_similarity", 0.85)
        all_embeddings = get_all_recent_embeddings()

        best_match = None
        best_score = 0.0

        for student_name, embeddings in all_embeddings.items():
            for stored_emb in embeddings:
                similarity = self._cosine_similarity(unknown_embedding, stored_emb)
                if similarity > best_score:
                    best_score = similarity
                    best_match = student_name

        if best_score >= threshold:
            return best_match, best_score

        return None, 0.0

    def _cosine_similarity(self, a, b):
        """Compute cosine similarity between two vectors."""
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm < 1e-8:
            return 0.0
        return float(dot / norm)


# Singleton
session_recovery = SessionRecovery()
