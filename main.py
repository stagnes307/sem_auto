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

    # 1. GUI 실행
    if args.gui:
        from ui.gui import launch_gui
        launch_gui() # GUI 창이 닫힐 때까지 여기서 대기함
        return # GUI 종료 시 프로그램 종료

    # --- 아래는 CLI(명령줄) 모드일 때만 실행됩니다 ---
    print("==========================================")
    print("   Smart-SEM Automation System v1.0       ")
    print("==========================================")
    
    if args.simulation:
        print("[INFO] Running in SIMULATION MODE")
    else:
        print("[INFO] Running in REAL HARDWARE MODE")
        
    try:
        app = AutomationManager(simulation=args.simulation, model_path=args.model)
        
        # CLI 테스트용 데이터
        print("[INFO] GUI 모드가 아니므로 기본 설정으로 실행합니다.")
        dummy_data = {1: {'name': 'CLI_Test_Sample', 'settings': {'low_mag': 1000, 'high_count': 3, 'high_mag': 5000}}}
        app.run(active_slots=dummy_data)

    except KeyboardInterrupt:
        print("\n[INFO] Process interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
