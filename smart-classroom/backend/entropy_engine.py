"""
CSTPE Entropy Engine (Feature 2 - Part 2)
Computes movement entropy over a sliding window of body keypoints.
Maps the entropy value to a dynamic gap-threshold, replacing the static 10-second rule.

Low entropy (student sitting still) -> tighter gap threshold (e.g., 5s)
High entropy (student moving actively) -> relaxed gap threshold (e.g., 15s)
"""

import numpy as np
from collections import defaultdict
from policy_engine import policy


class EntropyEngine:
    def __init__(self):
        # Per-student sliding window of keypoint frames
        self._history = defaultdict(list)
        self._max_window = 30  # number of frames to retain

    def update(self, student_name, keypoints):
        """
        Add a new keypoint frame for a student and compute their current entropy.
        keypoints: numpy array of shape (33, 3)
        """
        if keypoints is None:
            return self.get_adaptive_gap(student_name)

        self._history[student_name].append(keypoints[:, :2].copy())

        # Trim to window size
        if len(self._history[student_name]) > self._max_window:
            self._history[student_name] = self._history[student_name][-self._max_window:]

        return self.get_adaptive_gap(student_name)

    def compute_entropy(self, student_name):
        """
        Compute the movement entropy for a student based on their keypoint history.
        Entropy is defined as the mean standard deviation of keypoint positions
        over the sliding window, normalized to [0, 1].
        """
        frames = self._history.get(student_name, [])

        if len(frames) < 3:
            return 0.5  # neutral default when insufficient data

        stacked = np.array(frames)  # shape: (num_frames, 33, 2)

        # Compute per-joint standard deviation over time
        joint_std = np.std(stacked, axis=0)  # shape: (33, 2)
        mean_std = np.mean(joint_std)

        # Normalize: empirically, std > 0.05 is high movement
        entropy = min(mean_std / 0.05, 1.0)

        return float(entropy)

    def get_adaptive_gap(self, student_name):
        """
        Map the current entropy to a dynamic gap-threshold in seconds.
        """
        entropy = self.compute_entropy(student_name)

        low_threshold = policy.get_float("entropy_low", 0.2)
        high_threshold = policy.get_float("entropy_high", 0.8)
        gap_low = policy.get_int("gap_when_low_entropy", 5)
        gap_high = policy.get_int("gap_when_high_entropy", 15)

        if entropy <= low_threshold:
            return gap_low
        elif entropy >= high_threshold:
            return gap_high
        else:
            # Linear interpolation
            ratio = (entropy - low_threshold) / (high_threshold - low_threshold)
            return int(gap_low + ratio * (gap_high - gap_low))

    def clear_student(self, student_name):
        if student_name in self._history:
            del self._history[student_name]


# Singleton
entropy_engine = EntropyEngine()
