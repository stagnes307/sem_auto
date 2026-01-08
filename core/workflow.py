from .microscope import MicroscopeController
from .ai_engine import YOLODetector
from utils.file_manager import FileManager
from utils.report_generator import ReportGenerator
import time
import os

# ==========================================================
# [내일 여기서 수정하세요!] 샘플 슬롯별 중앙 좌표 (X, Y)
# 현미경에서 확인한 좌표를 아래 숫자 대신 넣으시면 됩니다.
# 단위는 보통 mm 또는 um (장비 세팅에 따라 다름)
# ==========================================================
SLOT_COORDINATES = {
    1:  (10.0, 20.0),  2:  (20.0, 20.0),  3:  (30.0, 20.0),  4:  (40.0, 20.0),  5:  (50.0, 20.0),
    6:  (60.0, 20.0),  7:  (70.0, 20.0),  8:  (80.0, 20.0),  9:  (90.0, 20.0),  10: (100.0, 20.0),
    11: (10.0, 40.0),  12: (20.0, 40.0),  13: (30.0, 40.0),  14: (40.0, 40.0),  15: (50.0, 40.0),
    16: (60.0, 40.0),  17: (70.0, 40.0),  18: (80.0, 40.0),  19: (90.0, 40.0),  20: (100.0, 40.0),
}
# ==========================================================

class AutomationManager:
    def __init__(self, simulation=True, model_path="yolov8n.pt"):
        self.simulation = simulation
        self.sem = MicroscopeController(simulation=simulation)
        self.ai = YOLODetector(model_path=model_path)
        self.file_manager = FileManager()
        
    def run(self, active_slots=None):
        """
        active_slots: GUI에서 넘어온 슬롯 설정 데이터
        예: {1: {'name': 'NCM_01', 'settings': {...}}, 3: {...}}
        """
        print(">>> Starting Automation Workflow")
        
        # 1. Connect
        self.sem.connect()
        
        if not active_slots:
            print("[Error] No active slots provided!")
            return

        for sid, data in active_slots.items():
            sample_name = data['name']
            settings = data['settings']
            
            # SLOT_COORDINATES에서 좌표 가져오기
            if sid not in SLOT_COORDINATES:
                print(f"[Warning] No coordinates defined for Slot #{sid}. Skipping.")
                continue
                
            start_x, start_y = SLOT_COORDINATES[sid]
            
            print(f"\n>>>> Processing Sample: {sample_name} (Slot #{sid}) at ({start_x}, {start_y})")
            
            # --- 1단계: 저배율 촬영 (Search) ---
            # 5000배로 이동
            self.sem.move_stage(start_x, start_y)
            self.sem.set_magnification(settings['low_mag'])
            self.sem.auto_focus()
            
            # 1장 찍고 저장
            low_mag_img = self.sem.acquire_image()
            self.file_manager.save_image(
                low_mag_img, 
                f"Overview_Center.jpg", 
                subdir=os.path.join(sample_name, f"LowMag_x{settings['low_mag']}")
            )
            
            # --- 2단계: AI 탐지 ---
            detections = self.ai.detect_particles(low_mag_img)
            if not detections and self.simulation:
                detections = self.ai.detect_blobs_fallback(low_mag_img) # Fallback for simulation
            
            print(f"[{sample_name}] Found {len(detections)} particles. Selecting top {settings['high_count']}.")
            
            # 좌표 변환을 위한 스케일 계산 (예시: FOV 200um / 1024px)
            # 주의: 실제 장비의 FOV 값에 맞춰야 정확한 이동이 가능합니다.
            img_h, img_w = low_mag_img.shape[:2]
            fov_width = 200000 / settings['low_mag'] # um 단위 추정
            pixel_scale = fov_width / img_w 
            
            # --- 3단계: 고배율 촬영 루프 (High Mag 1 -> High Mag 2) ---
            for j, target in enumerate(detections[:settings['high_count']]):
                
                # 3-1. 타겟 좌표 계산
                dx_px = target['x'] - (img_w / 2)
                dy_px = target['y'] - (img_h / 2)
                
                # (주의: SEM 장비마다 축 방향이 다를 수 있음. +,- 부호 확인 필요)
                target_x = start_x + (dx_px * pixel_scale)
                target_y = start_y + (dy_px * pixel_scale)
                
                print(f"   --> Target #{j+1}: Moving to ({target_x:.3f}, {target_y:.3f})")
                self.sem.move_stage(target_x, target_y)
                
                # 3-2. High Mag 1 (예: x20,000)
                mag1 = settings['high_mag']
                print(f"       [High Mag 1] Shooting x{mag1}")
                self.sem.set_magnification(mag1)
                self.sem.auto_focus() # 고배율일수록 초점 다시 맞춰야 함
                img_high1 = self.sem.acquire_image()
                
                self.file_manager.save_image(
                    img_high1, 
                    f"Particle_{j+1:03d}_x{mag1}.jpg", 
                    subdir=os.path.join(sample_name, f"HighMag_x{mag1}")
                )
                
                # 3-3. High Mag 2 (예: x50,000) - 더 확대!
                # settings에 'high_mag_2'가 있고, 0보다 클 때만 실행
                mag2 = settings.get('high_mag_2', 0)
                if mag2 > mag1:
                    print(f"       [High Mag 2] Zooming in to x{mag2}")
                    self.sem.set_magnification(mag2)
                    self.sem.auto_focus() # 고배율일수록 초점 다시 맞춰야 함
                    img_high2 = self.sem.acquire_image()
                    
                    self.file_manager.save_image(
                        img_high2, 
                        f"Particle_{j+1:03d}_x{mag2}.jpg", 
                        subdir=os.path.join(sample_name, f"SuperHighMag_x{mag2}")
                    )

        print("\n>>> All Samples Completed.")