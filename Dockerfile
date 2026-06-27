# Use Python 3.10 slim as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV, Dlib, and C++ compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libx11-dev \
    libxext6 \
    libsm6 \
    libxrender1 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY smart-classroom/backend/requirements.txt .

# Limit C++ compilation concurrency to prevent 8GB+ OOM crashes on Render
ENV CMAKE_BUILD_PARALLEL_LEVEL=1
ENV MAX_JOBS=1

# Install Python dependencies (this will compile dlib and install onnxruntime)
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY smart-classroom/backend/ .

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
