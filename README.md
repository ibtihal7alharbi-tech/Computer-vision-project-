Mahd: AI-Powered Infant Safety Monitoring System
Mahd is a specialized monitoring application designed to enhance infant safety during sleep.

The system utilizes Computer Vision and Deep Learning to analyze video feeds, specifically detecting infant body positions and facial orientation to mitigate risks associated with Sudden Infant Death Syndrome (SIDS).

Project ArchitectureThe system is built using a decoupled architecture consisting of a mobile frontend and a high-performance computer vision backend.

Frontend:

Flutter

FrameworkUser Interface: Developed with Flutter to provide a responsive and intuitive experience across mobile platforms.

Media Handling: Features integrated video selection and processing modules to handle high-resolution media from local storage or live streams.

API Integration: Communication with the backend is handled via asynchronous HTTP requests to ensure a seamless user experience.

Backend: 

FastAPI & YOLOv8API Layer:

Built with FastAPI for high-performance, asynchronous request handling.

Inference Engine: Utilizes the YOLOv8 (You Only Look Once) architecture for real-time object detection.

Models:

Body Detection: Specialized model to identify the infant's physical boundaries and sleeping posture.

Face Analysis: Focused detection to ensure the infant's respiratory pathways are not obstructed.

Technical Specifications

Inference: The YOLOv8 model processes the frame to identify specific classes (e.g., infant, face).Result Extraction: The backend calculates bounding box coordinates and confidence scores.

Response: Data is returned to the frontend in JSON format for visual rendering of detection boxes.

Prerequisites

Flutter SDK (3.x or higher)

Python (3.9 or higher)

Ultralytics YOLO environment

Required Python packages: fastapi, uvicorn, opencv-python-headless, pillowLocal SetupBackend SetupNavigate to the backend directory and install dependencies

Security and PrivacyThe system is designed to prioritize data privacy by focusing on localized inference processing where possible, ensuring that sensitive monitoring data is handled securely within the defined API protocols.
