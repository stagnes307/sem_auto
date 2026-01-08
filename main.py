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

    if args.gui:
        from ui.gui import launch_gui
        launch_gui()
        return

    print("==========================================")
    print("   Smart-SEM Automation System v1.0       ")
    print("==========================================")
    
    if args.simulation:
        print("[INFO] Running in SIMULATION MODE")
    else:
        print("[INFO] Running in REAL HARDWARE MODE")
        # In real mode, we might need safety checks here
        
    try:
        app = AutomationManager(simulation=args.simulation, model_path=args.model)
        app.run()
    except KeyboardInterrupt:
        print("\n[INFO] Process interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
