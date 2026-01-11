import argparse
import sys
import os
from core.workflow import AutomationManager

def main():
    parser = argparse.ArgumentParser(description="Smart-SEM Automation System")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode (Mock Hardware)")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Path to YOLO model or model name")
    parser.add_argument("--gui", action="store_true", help="Launch Graphical User Interface")
    
    args = parser.parse_args()

    # 1. GUI 실행 및 데이터 받기
    config_data = None
    if args.gui:
        from ui.gui import launch_gui
        config_data = launch_gui() # GUI에서 설정값 받아옴
        
        if not config_data:
            print("[INFO] GUI에서 설정을 완료하지 않고 종료했습니다.")
            return
        print(f"[INFO] GUI 설정 수신 완료: {len(config_data)}개 슬롯")

    print("==========================================")
    print("   Smart-SEM Automation System v1.0       ")
    print("==========================================")
    
    if args.simulation:
        print("[INFO] Running in SIMULATION MODE")
    else:
        print("[INFO] Running in REAL HARDWARE MODE")
        
    try:
        app = AutomationManager(simulation=args.simulation, model_path=args.model)
        
        # 2. 데이터가 있으면 그걸로 실행, 없으면 기본 실행
        if config_data:
            print(">>> 설정된 데이터로 자동화를 시작합니다...")
            app.run(active_slots=config_data) # active_slots 인자 전달!
        else:
            # CLI 모드 등 (필요하면 구현)
            print("[INFO] GUI 모드가 아니므로 기본 설정으로 실행합니다.")
            # 테스트용 더미 데이터 예시
            dummy_data = {1: {'name': 'Test_Sample', 'settings': {'low_mag': 1000, 'high_count': 3, 'high_mag': 5000}}}
            app.run(active_slots=dummy_data)

    except KeyboardInterrupt:
        print("\n[INFO] Process interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
