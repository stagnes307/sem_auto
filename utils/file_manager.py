import os
import datetime
import cv2

class FileManager:
    def __init__(self, base_dir="results"):
        self.base_dir = base_dir
        self.current_session_dir = None
        self._create_session_dir()

    def _create_session_dir(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_dir = os.path.join(self.base_dir, f"Session_{timestamp}")
        os.makedirs(self.current_session_dir, exist_ok=True)
        print(f"[FileManager] Session directory created: {self.current_session_dir}")

    def save_image(self, image, filename, subdir=None):
        if subdir:
            save_path = os.path.join(self.current_session_dir, subdir)
            os.makedirs(save_path, exist_ok=True)
        else:
            save_path = self.current_session_dir
            
        full_path = os.path.join(save_path, filename)
        cv2.imwrite(full_path, image)
        return full_path
        
    def log(self, message):
        log_file = os.path.join(self.current_session_dir, "session_log.txt")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
