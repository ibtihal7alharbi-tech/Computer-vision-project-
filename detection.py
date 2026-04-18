import numpy as np
import base64
import cv2
from PIL import Image
from ultralytics import YOLO
import io

print("Loading body model...")
body_model = YOLO("models/body_best.pt")
print("Loading face model...")
face_model = YOLO("models/face_best.pt")
print("Models loaded successfully ✅")


def decode_image(base64_string: str) -> np.ndarray:
    img_bytes = base64.b64decode(base64_string)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    return np.array(img)


def analyze_frame(base64_image: str) -> dict:
    frame = decode_image(base64_image)
    body_results = body_model(frame, verbose=False, conf=0.25)[0]
    face_results = face_model(frame, verbose=False, conf=0.25)[0]
    body_labels = [body_model.names[int(c)].lower() for c in body_results.boxes.cls]
    face_labels = [face_model.names[int(c)].lower() for c in face_results.boxes.cls]
    print(f"Body detected: {body_labels}")
    print(f"Face detected: {face_labels}")
    has_stomach = any("stomach" in l or "tummy" in l or "lying-on-stomach" in l or "belly" in l for l in body_labels)
    has_back = any("back" in l for l in body_labels)
    has_nose = any("nose" in l for l in face_labels)
    # DANGER always takes priority
    if has_stomach:
        status = "DANGER"
    elif has_back and has_nose:
        status = "SAFE"
    elif has_back and not has_nose:
        status = "FACE_COVERED"
    else:
        status = "SCANNING"
    print(f"Status: {status}")
    return {
        "status": status,
        "has_stomach": has_stomach,
        "has_back": has_back,
        "has_nose": has_nose,
        "body_detected": body_labels,
        "face_detected": face_labels,
    }


def analyze_video_frame(video_bytes: bytes) -> dict:
    try:
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(video_bytes)
            temp_path = f.name

        cap = cv2.VideoCapture(temp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        positions = [0.1, 0.3, 0.5, 0.7, 0.9]
        best_result = {"status": "SCANNING", "has_stomach": False, "has_back": False, "has_nose": False, "body_detected": [], "face_detected": []}

        for pos in positions:
            frame_idx = int(total_frames * pos)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue
            _, buffer = cv2.imencode('.jpg', frame)
            base64_image = base64.b64encode(buffer).decode('utf-8')
            result = analyze_frame(base64_image)
            # DANGER always wins
            if result['status'] == 'DANGER':
                cap.release()
                os.unlink(temp_path)
                return result
            if result['status'] != 'SCANNING':
                best_result = result

        cap.release()
        os.unlink(temp_path)
        return best_result

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "ERROR", "message": str(e)}
