# CSTPE Attendance Policy DSL
# This file defines runtime-configurable attendance rules.
# The policy engine parses this file at startup and exposes
# the values to the AAP controller without requiring a code redeploy.

# Temporal thresholds
threshold_minutes = 40
gap_seconds = 10
heartbeat_interval = 3

# Vision confidence
face_confidence = 0.55
yolo_confidence = 0.6
aspect_ratio_min = 0.8

# Session recovery
session_similarity = 0.85
max_stored_embeddings = 5

# Environmental bounds (for sensor gating)
light_min_lux = 100
light_max_lux = 2000
temp_min_celsius = 15
temp_max_celsius = 40

# Biometric fusion weights (must sum to 1.0)
weight_face = 0.5
weight_iris = 0.3
weight_voice = 0.2
fusion_threshold = 0.7

# Federated learning
fed_min_samples = 50
fed_learning_rate = 0.001
fed_aggregation_hours = 24

# Adaptive entropy mapping
entropy_low = 0.2
entropy_high = 0.8
gap_when_low_entropy = 5
gap_when_high_entropy = 15
