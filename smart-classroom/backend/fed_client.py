"""
CSTPE Federated Learning Client (Feature 7 - Part 1)
On-device federated learning stub for continuous improvement of
the anti-spoof classifier. Each edge device trains locally and
sends weight deltas to the aggregation server, preserving privacy.
"""

import numpy as np
import json
import os
import hashlib
from datetime import datetime

DELTAS_DIR = os.path.join(os.path.dirname(__file__), "fed_deltas")


class FederatedClient:
    """
    Federated learning client that runs on each edge camera device.
    It collects local training samples (spoof vs. genuine detections),
    trains a lightweight local classifier, and produces weight deltas
    for server-side aggregation.
    """

    def __init__(self, device_id=None):
        self.device_id = device_id or self._generate_device_id()
        self._local_samples = []
        self._model_weights = self._initialize_weights()
        os.makedirs(DELTAS_DIR, exist_ok=True)

    def collect_sample(self, features, is_genuine):
        """
        Collect a local training sample.
        features: numpy array of detection features
        is_genuine: boolean indicating if the detection was genuine
        """
        self._local_samples.append({
            "features": features.tolist() if isinstance(features, np.ndarray) else features,
            "label": 1 if is_genuine else 0,
            "timestamp": datetime.now().isoformat(),
        })

    def train_local(self, learning_rate=0.001, epochs=5):
        """
        Train the local model on collected samples.
        Uses a simple logistic regression for the prototype.
        Returns the weight delta.
        """
        if len(self._local_samples) < 10:
            return None  # Not enough data

        # Extract features and labels
        features = np.array([s["features"] for s in self._local_samples])
        labels = np.array([s["label"] for s in self._local_samples])

        # Simple gradient descent on logistic regression
        weights_before = self._model_weights.copy()

        for epoch in range(epochs):
            # Forward pass
            logits = features @ self._model_weights
            predictions = self._sigmoid(logits)

            # Gradient
            error = predictions - labels
            gradient = features.T @ error / len(labels)

            # Update
            self._model_weights -= learning_rate * gradient

        # Compute delta
        delta = self._model_weights - weights_before

        return delta

    def export_delta(self):
        """
        Export the weight delta to a file for server aggregation.
        """
        delta = self.train_local()
        if delta is None:
            return None

        delta_record = {
            "device_id": self.device_id,
            "timestamp": datetime.now().isoformat(),
            "delta": delta.tolist(),
            "sample_count": len(self._local_samples),
        }

        filename = f"delta_{self.device_id}_{int(datetime.now().timestamp())}.json"
        filepath = os.path.join(DELTAS_DIR, filename)

        with open(filepath, "w") as f:
            json.dump(delta_record, f)

        # Clear local samples after export
        self._local_samples = []

        return filepath

    def get_sample_count(self):
        return len(self._local_samples)

    def _initialize_weights(self, dim=128):
        """Initialize model weights."""
        return np.zeros(dim)

    def _sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def _generate_device_id(self):
        import platform
        info = f"{platform.node()}-{platform.machine()}"
        return hashlib.md5(info.encode()).hexdigest()[:12]


# Singleton
fed_client = FederatedClient()
