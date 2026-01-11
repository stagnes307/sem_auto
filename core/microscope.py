import time
import numpy as np
import cv2

class MicroscopeController:
    def __init__(self, simulation=False):
        self.simulation = simulation
        if self.simulation:
            self.adapter = MockAdapter()
        else:
            self.adapter = RealAdapter()

    def connect(self):
        print("[Microscope] Connecting...")
        self.adapter.connect()

    def set_magnification(self, mag):
        print(f"[Microscope] Setting magnification to x{mag}")
        self.adapter.set_magnification(mag)

    def move_stage(self, x, y):
        print(f"[Microscope] Moving stage to X={x}, Y={y}")
        self.adapter.move_stage(x, y)

    def auto_focus(self):
        print("[Microscope] Performing Auto-Focus...")
        self.adapter.auto_focus()

    def acquire_image(self):
        print("[Microscope] Acquiring image...")
        return self.adapter.acquire_image()

    def get_stage_position(self):
        return self.adapter.get_stage_position()

class MockAdapter:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.mag = 500
        # Canvas size for simulation (World space)
        self.world_size = 2000 
        self.particles = [
            (1000, 1000), (950, 950), (1050, 1020), # Center cluster
            (200, 200), (300, 250),                 # Top-left cluster
            (1800, 1800), (1750, 1850),             # Bottom-right cluster
            (500, 1500), (1500, 500)                # Scattered
        ]

    def connect(self):
        print("[MockAdapter] Connected to Virtual SEM.")

    def set_magnification(self, mag):
        self.mag = mag
        time.sleep(0.5)

    def move_stage(self, x, y):
        self.x = x
        self.y = y
        time.sleep(1) # Simulate movement time

    def get_stage_position(self):
        return self.x, self.y

    def auto_focus(self):
        time.sleep(1) # Simulate AF

    def acquire_image(self):
        # Generate a synthetic image based on current position and mag
        height, width = 1024, 1024
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Draw background noise
        noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
        img = cv2.add(img, noise)

        # Draw particles if they are in view
        fov_size = 200000 / self.mag # Simple relationship between mag and FOV
        
        # Current view bounds (centered on x, y)
        view_x_min = self.x - fov_size / 2
        view_x_max = self.x + fov_size / 2
        view_y_min = self.y - fov_size / 2
        view_y_max = self.y + fov_size / 2

        for px, py in self.particles:
            if view_x_min < px < view_x_max and view_y_min < py < view_y_max:
                # Map world coordinate to image coordinate
                # normalized 0-1
                norm_x = (px - view_x_min) / fov_size
                norm_y = (py - view_y_min) / fov_size
                
                screen_x = int(norm_x * width)
                screen_y = int(norm_y * height)
                
                # Draw particle (white circle)
                cv2.circle(img, (screen_x, screen_y), 30, (255, 255, 255), -1)
                
        time.sleep(2) # Simulate scan time
        return img

import time
import cv2
import os

class RealAdapter:
    def __init__(self):
        self.atom = None 
        self.sem = None  

    def connect(self):
        try:
            # 분석실 PC에 있는 라이브러리 로드
            from tescanautomation import Automation
            self.atom = Automation('localhost')
            self.sem = self.atom.Client()
            print("✅ [RealAdapter] Tescan MIRA4 장비와 연결되었습니다.")
        except ImportError:
            print("❌ [Error] tescanautomation 라이브러리를 찾을 수 없습니다.")
            print("   -> 분석실 PC의 Essence Python 환경에서 실행해야 합니다.")
            raise

    def set_magnification(self, mag):
        # Tescan은 배율 대신 ViewField(mm)를 사용합니다.
        # 공식: ViewField ≈ 200.0 / 배율 (장비마다 다를 수 있어 확인 필요)
        if mag < 10: mag = 10
        viewfield_mm = 200.0 / float(mag)
        print(f"[Real] 배율 x{mag} 설정 (ViewField: {viewfield_mm:.4f} mm)")
        self.sem.Optics.SetViewfield(viewfield_mm)

    def move_stage(self, x, y):
        print(f"[Real] 스테이지 이동: X={x:.3f}, Y={y:.3f}")
        self.sem.Stage.MoveTo(x, y)
        time.sleep(0.5) # 진동 대기

    def auto_focus(self):
        print("[Real] 오토 포커스 실행...")
        self.sem.Optics.AutoFocus()
        time.sleep(1.0) # 포커스 안정화 대기

    def acquire_image(self):
        print("[Real] 촬영 중...")
        # 1. Tescan 명령어로 촬영 (Detector='SE', 해상도=1024)
        # 인자 순서: Detector, BitDepth, Width, Height, DwellTime, Accumulation...
        img_obj = self.sem.Scan.AcquireImage("SE", 8, 1024, 1024, 10.0, 1, "Frame")
        
        # 2. 호환성을 위해 임시 저장 후 OpenCV로 다시 읽기
        temp_path = "temp_capture.tif"
        img_obj.save(temp_path)
        img_cv = cv2.imread(temp_path)
        return img_cv

    def get_stage_position(self):
        return self.sem.Stage.X, self.sem.Stage.Y
