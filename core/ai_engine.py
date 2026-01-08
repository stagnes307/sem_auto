from ultralytics import YOLO
import cv2
import numpy as np

class YOLODetector:
    def __init__(self, model_path="yolov8n.pt"):
        print(f"[AI] Loading YOLO model from {model_path}...")
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            print(f"[AI] Error loading model: {e}")
            self.model = None

    def detect_particles(self, image_path_or_array):
        """
        Runs detection.
        Returns a list of dicts: {'x': center_x, 'y': center_y, 'w': width, 'h': height, 'conf': confidence}
        """
        if self.model is None:
            print("[AI] No model loaded. Returning empty detections.")
            return []

        # Run inference
        results = self.model(image_path_or_array, verbose=False) 
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # box.xywh returns center_x, center_y, width, height
                x, y, w, h = box.xywh[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                
                # For this specific project, if we are using an untrained model on synthetic blobs,
                # it might not detect anything. 
                # To verify the workflow, if confidence is very low, we might skip.
                # But typically we trust the model output.
                
                detections.append({
                    'x': float(x),
                    'y': float(y),
                    'w': float(w),
                    'h': float(h),
                    'conf': conf
                })
        
        print(f"[AI] Detected {len(detections)} objects.")
        return detections

    def detect_blobs_fallback(self, image):
        """
        Fallback using simple CV2 blob detection for simulation if YOLO Model is not yet trained.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Center
            saved_x = x + w/2
            saved_y = y + h/2
            detections.append({
                'x': saved_x,
                'y': saved_y,
                'w': float(w),
                'h': float(h),
                'conf': 1.0 # Fake confidence
            })
        print(f"[AI] (Fallback) Detected {len(detections)} objects using thresholding.")
        return detections
