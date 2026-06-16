<div align="center">

# CSTPE: Continuous Spatial-Temporal Presence Engine

### Proprietary Smart Classroom Attendance Architecture (v2.0)

**A 10-module patent-ready Computer Vision attendance system combining YOLOv8 liveness detection, multi-modal biometric fusion, zero-knowledge proofs, and blockchain-anchored audit trails.**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-3178C6?style=for-the-badge)](https://ultralytics.com/)
[![React](https://img.shields.io/badge/React_Vite-6366f1?style=for-the-badge&logo=react)](https://reactjs.org/)
[![SQLite](https://img.shields.io/badge/SQLite-4169E1?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)

[Architecture](#architecture-overview) | [10 Novel Modules](#the-10-novel-modules) | [Dashboard & Reporting](#teacher-and-student-dashboard) | [Patent Claims](#patent-claims) | [Setup](#setup-instructions)

</div>

---

## Architecture Overview

This system introduces a continuous spatial-temporal methodology for strict physical attendance tracking in educational institutions. We replace static snapshot-based facial recognition with a multi-layered, continuously accumulating presence engine that integrates ten distinct technical innovations into a single pipeline.

The core pipeline operates as follows: a video frame is captured, validated against environmental sensors, passed through a YOLOv8 body-detection liveness gate, processed by a facial recognition layer, fused with iris and voice biometric signals via a Kalman filter, and finally credited to an Accumulated Active Presence (AAP) counter that enforces contiguous attendance. Every state change is logged to a tamper-evident blockchain audit trail and accompanied by a zero-knowledge proof of presence.

![Dashboard Tab](docs/screenshots/dashboard_tab.png)

---

## Teacher and Student Dashboard

The system provides a comprehensive React-based UI for both teachers and students, enabling real-time tracking, historical analysis, and official reporting.

### For Teachers

*   **Live Tracking Dashboard:** View real-time Accumulated Active Presence (AAP) for all students. A progress bar visualizes progression towards the required 40-minute threshold.
*   **Continuous Camera Tracking:** Start and stop 3-second interval continuous tracking directly from the UI, with live YOLO vision output.
*   **End-of-Day Finalization:** A single click freezes the daily record, converting "In Progress" statuses to "Present", "Partial", or "Absent" based on the accumulated time.
*   **Multi-Sheet Excel Export:** Generate comprehensive official reports containing:
    *   Today's Session stats.
    *   Full Attendance History.
    *   Per-Student Summaries (total classes, attendance rate, avg biometric score).
    *   Daily Class Summaries.
    *   Blockchain Audit Trail.

![Teacher Camera Tab](docs/screenshots/camera_tab.png)

### For Students

*   **Student Profile Lookup:** Search for a student name to view their complete attendance history, attendance rate, and biometric scores.
*   **Personal Excel Reports:** Students can download their own localized `.xlsx` attendance history for their records.

![Student Tab](docs/screenshots/student_tab.png)

---

## The 10 Novel Modules

Here is a detailed breakdown of how each patented feature is practically applied in the system:

| Module | Feature | Technical Implementation & Application |
|--------|---------|--------------------------------------|
| **1. Two-Stage YOLO Liveness** | Anti-spoofing body-gated face detection | **Application:** Prevents "photo-to-camera" spoofing. YOLOv8n first detects a human person and checks aspect-ratio constraints. A face is only recognized if it is dimensionally bound *inside* a verified human torso. |
| **2. Adaptive Gap Threshold** | Entropy-driven temporal sensitivity | **Application:** Adjusts the "leave gap" dynamically. MediaPipe Pose extracts 33 body keypoints. A sliding-window entropy computation maps movement patterns to per-student dynamic gap thresholds (e.g., 5s for still students, 15s for active ones). |
| **3. Model Hash Attestation** | Tamper-proof model loading | **Application:** Guarantees inference integrity. SHA-256 cryptographic hashes of all model weights (e.g., `yolov8n.pt`) are verified at startup against a sealed registry, preventing unauthorized model substitution. |
| **4. Zero-Knowledge Proofs** | Privacy-preserving presence verification | **Application:** Privacy-compliant attendance. A Pedersen commitment scheme generates ZK proofs for each 5-second presence window. Third-party auditors can verify attendance without ever seeing raw video data. |
| **5. Edge-Only Inference** | Hardware camera deployment | **Application:** Low-power edge deployment. Includes an ONNX export script with INT8 quantization, allowing the heavy YOLO/dlib pipeline to run on Jetson Nanos or Coral TPUs directly. |
| **6. Policy-as-Code DSL** | Runtime-configurable attendance rules | **Application:** Zero-downtime policy updates. A domain-specific language parser loads `policy.dsl` at startup, enabling administrators to hot-reload time thresholds, confidence levels, and environmental bounds without restarting servers. |
| **7. Federated Learning** | On-device anti-spoof improvement | **Application:** Privacy-preserving model training. Edge devices locally train a logistic classifier on genuine/spoof detections and upload only weight deltas. The central server aggregates these via Federated Averaging (FedAvg). |
| **8. Blockchain Audit Log** | Immutable event ledger | **Application:** Non-repudiation of attendance records. An append-only SHA-256 hash-chain records every state change (e.g., "session_start", "attendance_update"). Any retrospective tampering breaks the chain. |
| **9. Environmental Gating** | Context-aware validation | **Application:** Prevents dark-room or manipulated-environment spoofing. Ambient light (lux) and temperature (Celsius) sensor readings gate AAP accumulation. Out-of-range conditions automatically suspend attendance credits. |
| **10. Session Recovery** | Biometric continuity after gaps | **Application:** Handles occlusion and network drops gracefully. When a student leaves the frame and returns beyond the gap threshold, cosine similarity of stored face embeddings re-links the new detection to the existing session, preventing fragmented records. |

### Module Visualizations

````carousel
![Blockchain Audit Trail](docs/screenshots/audit_tab.png)
<!-- slide -->
![Environmental Gating & System Telemetry](docs/screenshots/environment_tab.png)
<!-- slide -->
![Model Attestation System Report](docs/screenshots/system_tab.png)
````

---

## Patent Claims

**What is claimed is:**

1. **A system for continuous spatial-temporal state accumulation**, comprising a primary object detection layer utilizing bounding-box aspect ratio filtering to enforce human biological structure, a secondary facial recognition layer bound dimensionally inside the primary detection coordinates, and a state-machine database that strictly measures active physical presence accumulation with automatic pause heuristics upon spatial departure.

2. **The system of claim 1**, further comprising a multi-modal biometric fusion module that combines face, iris, and voice confidence scores through a Kalman filter, producing a single gated acceptance signal.

3. **The system of claim 1**, wherein the temporal gap threshold is dynamically computed per entity based on a movement entropy metric derived from body keypoint variance over a sliding window.

4. **The system of claim 1**, further comprising a cryptographic model attestation module that verifies SHA-256 hashes of inference model weights against a sealed registry at service startup.

5. **The system of claim 1**, further comprising a zero-knowledge proof generator that produces Pedersen commitments for each presence window, enabling privacy-preserving auditability.

6. **The system of claim 1**, further comprising a domain-specific language interpreter that loads attendance policy parameters at runtime from a declarative configuration file.

7. **The system of claim 1**, further comprising a federated learning subsystem wherein edge devices train local anti-spoof classifiers and transmit weight deltas to a central aggregation server.

8. **The system of claim 1**, further comprising an append-only hash-chain audit log wherein each attendance event is linked to the previous event via SHA-256, forming a tamper-evident ledger.

9. **The system of claim 1**, further comprising an environmental context gating module that suspends attendance accumulation when ambient light or temperature readings fall outside calibrated sensor bounds.

10. **The system of claim 1**, further comprising a session recovery module that re-links post-gap detections to existing sessions using cosine similarity of stored face embeddings exceeding a configurable threshold.

---

## System Diagram

```mermaid
graph TB
    subgraph Edge ["Edge Hardware Camera"]
        Feed["Video Feed"]
        ENV["Light + Temp Sensors"]
        CV["YOLOv8 + dlib + Pose"]
    end

    subgraph Biometrics ["Multi-Modal Fusion"]
        FACE["Face Recognition"]
        IRIS["Iris Verification"]
        VOICE["Voice Activity"]
        KALMAN["Kalman Filter Fusion"]
    end

    subgraph Core ["CSTPE Core"]
        POLICY["Policy DSL Engine"]
        ENTROPY["Adaptive Entropy Engine"]
        AAP["AAP State Machine"]
        RECOVERY["Session Recovery"]
    end

    subgraph Security ["Security Layer"]
        ATTEST["Model Attestation"]
        ZK["ZK Proof Generator"]
        CHAIN["Blockchain Audit"]
    end

    subgraph ML ["ML Layer"]
        FED_C["Fed Client"]
        FED_S["Fed Server"]
    end

    subgraph Dashboard ["Teacher Dashboard"]
        UI["React/Vite UI"]
        WS["WebSocket Stream"]
    end

    Feed --> CV
    ENV --> AAP
    CV --> FACE
    CV --> IRIS
    CV --> VOICE
    FACE --> KALMAN
    IRIS --> KALMAN
    VOICE --> KALMAN
    KALMAN --> AAP
    POLICY --> AAP
    ENTROPY --> AAP
    AAP --> RECOVERY
    AAP --> ZK
    AAP --> CHAIN
    ATTEST --> CV
    FED_C --> FED_S
    AAP --> WS
    WS --> UI

    style Edge fill:#1e1b4b,stroke:#6366f1,color:#e0e7ff
    style Biometrics fill:#312e81,stroke:#818cf8,color:#e0e7ff
    style Core fill:#064e3b,stroke:#10b981,color:#d1fae5
    style Security fill:#7f1d1d,stroke:#f87171,color:#fee2e2
    style ML fill:#78350f,stroke:#f59e0b,color:#fef3c7
    style Dashboard fill:#1c1917,stroke:#f59e0b,color:#fef3c7
```

---

## Test Results

All 53 automated tests pass across all 10 modules:

```
RESULTS: 53 passed, 0 failed out of 53 tests
ALL TESTS PASSED
```

Tested subsystems: Policy Engine, Config Module, Model Attestation, Entropy Engine, Pose Engine, Iris Engine, Voice Engine, Biometric Fusion, Session Recovery, ZK Prover, Blockchain Audit, Environmental Sensors, Federated Learning, Attendance DB Integration, Edge Export.

---

## Setup Instructions

### 1. Backend Setup
```bash
cd smart-classroom/backend
python -m venv venv
source venv/Scripts/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### 2. Frontend Setup
```bash
cd smart-classroom/frontend
npm install
npm run dev
```

### 3. Usage
Navigate to `http://localhost:5173` in a browser. The dashboard provides comprehensive tabs for Live Attendance, Camera Tracking, Student Lookup, Audit Trails, Environment Sensors, and System Attestation.

---

## License and Intellectual Property

Proprietary and Confidential.
Patent Pending. CSTPE Architecture (2026).
