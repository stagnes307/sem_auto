import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import math
import threading
import sys
import os

# 현재 파일(gui.py)의 부모 디렉토리(ui/)의 부모(sem_auto/)를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from core.workflow import AutomationManager

class StubMap(tk.Canvas):
    def __init__(self, master, size=400, on_slot_click=None):
        super().__init__(master, width=size, height=size, bg="#f0f0f0", highlightthickness=0)
        self.size = size
        self.center = size / 2
        self.radius = (size / 2) - 20
        self.on_slot_click = on_slot_click
        
        # 슬롯 데이터: {id: {x, y, active, settings}}
        self.slots = {}
        self.selected_slot_id = None
        
        self.draw_stub_base()
        self.create_slots()

    def draw_stub_base(self):
        # Draw rectangular base (Tape strips)
        # Strip 1
        self.create_rectangle(10, 40, self.size-10, 140, fill="#e0e0e0", outline="#a0a0a0", width=2)
        self.create_text(30, 30, text="Row 1", anchor="w", font=("Arial", 10, "bold"), fill="gray")
        
        # Strip 2
        self.create_rectangle(10, 200, self.size-10, 300, fill="#e0e0e0", outline="#a0a0a0", width=2)
        self.create_text(30, 190, text="Row 2", anchor="w", font=("Arial", 10, "bold"), fill="gray")

    def create_slots(self):
        # 20 Slots: 2 Rows x 10 Columns
        rows = 2
        cols = 10
        
        margin_x = 35
        start_y_row1 = 90
        start_y_row2 = 250
        spacing_x = (self.size - 2 * margin_x) / (cols - 1)
        
        slot_radius = 12
        
        # Row 1 (Slots 1-10)
        for i in range(cols):
            x = margin_x + i * spacing_x
            y = start_y_row1
            self.add_slot(i+1, x, y, slot_radius)
            
        # Row 2 (Slots 11-20)
        for i in range(cols):
            x = margin_x + i * spacing_x
            y = start_y_row2
            self.add_slot(i+11, x, y, slot_radius)

    def add_slot(self, slot_id, x, y, r):
        # 기본 설정값
        default_settings = {
            "low_mag": 5000, "low_count": 5,
            "high_mag": 20000, "high_count": 5,
            "high_mag_2": 50000, "high_count_2": 5 # 3rd step
        }
        
        # 캔버스에 원 그리기
        tag = f"slot_{slot_id}"
        oval = self.create_oval(x-r, y-r, x+r, y+r, fill="white", outline="gray", tags=(tag, "slot"))
        text = self.create_text(x, y, text=str(slot_id), font=("Arial", 9, "bold"), tags=(tag, "text"))
        
        self.slots[slot_id] = {
            "oval": oval, "text": text,
            "active": False,
            "name": f"Sample_{slot_id:02d}",  # Default Name
            "settings": default_settings.copy()
        }
        
        # 이벤트 바인딩
        self.tag_bind(tag, "<Button-1>", lambda e, sid=slot_id: self.handle_click(sid))

    def handle_click(self, slot_id):
        # 1. 활성/비활성 토글 (선택 로직과 분리할 수도 있지만, 여기선 클릭=활성화+선택)
        slot = self.slots[slot_id]
        
        if self.selected_slot_id == slot_id:
            # 토글
            slot['active'] = not slot['active']
        else:
            # 새로운 선택 (만약 꺼져있다면 켬)
            self.selected_slot_id = slot_id
            if not slot['active']:
                slot['active'] = True
        
        self.update_visuals()
        
        # 콜백 호출 (우측 패널 업데이트용)
        if self.on_slot_click:
            # Pass 'name' as well
            self.on_slot_click(slot_id, slot['active'], slot['name'], slot['settings'])

    def update_visuals(self):
        for sid, data in self.slots.items():
            color = "white"
            outline = "gray"
            width = 1
            
            if data['active']:
                color = "#4caf50" # Green
                
            if sid == self.selected_slot_id:
                outline = "#ff9800" # Orange selection ring
                width = 3
            
            self.itemconfig(data['oval'], fill=color, outline=outline, width=width)

    def update_settings(self, slot_id, new_name, new_settings):
        if slot_id in self.slots:
            self.slots[slot_id]['settings'] = new_settings
            self.slots[slot_id]['name'] = new_name

    def get_active_slots(self):
        return {sid: data for sid, data in self.slots.items() if data['active']}


class BatchRenamingWindow(tk.Toplevel):
    def __init__(self, parent, slots_data, callback):
        super().__init__(parent)
        self.title("Batch Sample Renaming")
        self.geometry("500x700")
        self.slots_data = slots_data
        self.callback = callback
        self.entries = {}
        self.vars_active = {}
        
        # 1. Auto-Fill Section
        frame_auto = ttk.LabelFrame(self, text="Auto-Fill Names", padding="10")
        frame_auto.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(frame_auto, text="Prefix:").pack(side=tk.LEFT)
        self.var_prefix = tk.StringVar(value="Sample")
        ttk.Entry(frame_auto, textvariable=self.var_prefix, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_auto, text="Apply Auto-Numbering", command=self.apply_auto_fill).pack(side=tk.LEFT, padx=10)
        
        # 2. Scrollable List Area
        frame_list_container = ttk.Frame(self)
        frame_list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(frame_list_container)
        scrollbar = ttk.Scrollbar(frame_list_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Headers
        ttk.Label(self.scrollable_frame, text="Slot", font="Arial 9 bold").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(self.scrollable_frame, text="Active", font="Arial 9 bold").grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(self.scrollable_frame, text="Sample Name", font="Arial 9 bold").grid(row=0, column=2, padx=5, pady=5)
        
        # Rows
        row = 1
        for sid, data in self.slots_data.items():
            ttk.Label(self.scrollable_frame, text=f"#{sid}").grid(row=row, column=0, padx=5, pady=2)
            
            # Active Checkbox
            var_active = tk.BooleanVar(value=data['active'])
            self.vars_active[sid] = var_active
            ttk.Checkbutton(self.scrollable_frame, variable=var_active).grid(row=row, column=1, padx=5)
            
            # Name Entry
            entry = ttk.Entry(self.scrollable_frame, width=30)
            entry.insert(0, data['name'])
            entry.grid(row=row, column=2, padx=5, pady=2)
            self.entries[sid] = entry
            
            row += 1
            
        # 3. Action Buttons
        frame_actions = ttk.Frame(self, padding="10")
        frame_actions.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(frame_actions, text="Save & Close", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(frame_actions, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def apply_auto_fill(self):
        prefix = self.var_prefix.get()
        if not prefix:
            return
        
        for sid, entry in self.entries.items():
            new_name = f"{prefix}_{sid:02d}"
            entry.delete(0, tk.END)
            entry.insert(0, new_name)
            self.vars_active[sid].set(True)

    def save(self):
        new_data = {}
        for sid in self.entries:
            new_data[sid] = {
                "name": self.entries[sid].get(),
                "active": self.vars_active[sid].get()
            }
        self.callback(new_data)
        self.destroy()


class SmartSEMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart-SEM Stub Manager")
        self.root.geometry("1300x650") # 가로로 더 넓게 조정
        
        # Main Layout (Horizontal)
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. Left Panel (Stub Map)
        left_panel = ttk.LabelFrame(main_frame, text=" 1. Visual Stub Map ", padding="10")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.stub_map = StubMap(left_panel, size=400, on_slot_click=self.on_slot_selected)
        self.stub_map.pack(anchor=tk.CENTER, pady=20)
        
        # 2. Middle Panel (Controls)
        right_panel = ttk.LabelFrame(main_frame, text=" 2. Control Panel ", padding="20")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10)
        
        self.create_controls(right_panel)
        
        # 3. Right Panel (Real-time Logs) - 세로로 길게 배치
        log_panel = ttk.LabelFrame(main_frame, text=" 3. Real-time Logs ", padding="10")
        log_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.log_widget = scrolledtext.ScrolledText(log_panel, width=40, state='disabled', font=("Consolas", 10))
        self.log_widget.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready. Click a slot to configure.")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def log_message(self, message):
        """Append message to the log widget in a thread-safe way."""
        def _append():
            self.log_widget.config(state='normal')
            self.log_widget.insert(tk.END, message + "\n")
            self.log_widget.see(tk.END) # Auto-scroll
            self.log_widget.config(state='disabled')
        
        self.root.after(0, _append)

    def create_controls(self, parent):
        # Batch Edit Button
        ttk.Button(parent, text="📝 Edit All Sample Names (List View)", command=self.open_batch_naming_window).pack(fill=tk.X, pady=(0, 20))
        
        # Title
        self.lbl_selected = ttk.Label(parent, text="No Slot Selected", font=("Arial", 14, "bold"))
        self.lbl_selected.pack(pady=(0, 20))
        
        # Settings Form
        frame_form = ttk.Frame(parent)
        frame_form.pack(fill=tk.X, pady=10)
        
        # Sample Name
        ttk.Label(frame_form, text="Sample Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.var_sample_name = tk.StringVar()
        ttk.Entry(frame_form, textvariable=self.var_sample_name, width=25).grid(row=0, column=1, columnspan=3, sticky="w", padx=5)

        # 1. Low Mag
        ttk.Label(frame_form, text="1. Low Mag (Search)").grid(row=1, column=0, sticky="w", pady=5)
        self.var_low_mag = tk.IntVar(value=5000)
        ttk.Entry(frame_form, textvariable=self.var_low_mag, width=10).grid(row=1, column=1, padx=5)
        
        ttk.Label(frame_form, text="Count:").grid(row=1, column=2, padx=5)
        self.var_low_count = tk.IntVar(value=5)
        ttk.Entry(frame_form, textvariable=self.var_low_count, width=5).grid(row=1, column=3)

        # 2. High Mag 1
        ttk.Label(frame_form, text="2. High Mag (Capture)").grid(row=2, column=0, sticky="w", pady=5)
        self.var_high_mag = tk.IntVar(value=20000)
        ttk.Entry(frame_form, textvariable=self.var_high_mag, width=10).grid(row=2, column=1, padx=5)
        
        ttk.Label(frame_form, text="Count:").grid(row=2, column=2, padx=5)
        self.var_high_count = tk.IntVar(value=5)
        ttk.Entry(frame_form, textvariable=self.var_high_count, width=5).grid(row=2, column=3)
        
        # 3. High Mag 2 (New!)
        ttk.Label(frame_form, text="3. Super High Mag (Detail)").grid(row=3, column=0, sticky="w", pady=5)
        self.var_high_mag_2 = tk.IntVar(value=50000)
        ttk.Entry(frame_form, textvariable=self.var_high_mag_2, width=10).grid(row=3, column=1, padx=5)
        
        ttk.Label(frame_form, text="Count:").grid(row=3, column=2, padx=5)
        self.var_high_count_2 = tk.IntVar(value=5)
        ttk.Entry(frame_form, textvariable=self.var_high_count_2, width=5).grid(row=3, column=3)
        
        # Apply Buttons
        frame_btns = ttk.Frame(parent)
        frame_btns.pack(fill=tk.X, pady=20)
        
        self.btn_apply = ttk.Button(frame_btns, text="Apply Name & Settings to Current", command=self.apply_to_current, state=tk.DISABLED)
        self.btn_apply.pack(fill=tk.X, pady=2)
        
        ttk.Button(frame_btns, text="Apply Settings to ALL Active (Keep Names)", command=self.apply_to_all).pack(fill=tk.X, pady=2)
        
        # Separator
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        
        # Run Button
        self.btn_run = ttk.Button(parent, text="START AUTOMATION", command=self.start_automation)
        self.btn_run.pack(fill=tk.X, pady=10, ipady=10)

    def open_batch_naming_window(self):
        # Open the popup
        BatchRenamingWindow(self.root, self.stub_map.slots, self.on_batch_update)

    def on_batch_update(self, new_data):
        # Update StubMap with new names and active status
        count = 0
        for sid, data in new_data.items():
            self.stub_map.slots[sid]['name'] = data['name']
            self.stub_map.slots[sid]['active'] = data['active']
            count += 1
            
        self.stub_map.update_visuals()
        # Refresh current selection if any
        if self.stub_map.selected_slot_id:
            sid = self.stub_map.selected_slot_id
            self.on_slot_selected(sid, self.stub_map.slots[sid]['active'], 
                                  self.stub_map.slots[sid]['name'], 
                                  self.stub_map.slots[sid]['settings'])
            
        messagebox.showinfo("Updated", f"Updated names for {count} slots.")

    def on_slot_selected(self, slot_id, active, name, settings):
        state_text = "Active" if active else "Inactive"
        self.lbl_selected.config(text=f"Slot #{slot_id} ({state_text})")
        
        if active:
            self.btn_apply.config(state=tk.NORMAL)
            # Load settings into fields
            self.var_sample_name.set(name)
            self.var_low_mag.set(settings['low_mag'])
            self.var_low_count.set(settings['low_count'])
            self.var_high_mag.set(settings['high_mag'])
            self.var_high_count.set(settings['high_count'])
            # New fields
            self.var_high_mag_2.set(settings.get('high_mag_2', 50000))
            self.var_high_count_2.set(settings.get('high_count_2', 5))
        else:
            self.btn_apply.config(state=tk.DISABLED)
            
        self.status_var.set(f"Selected Slot {slot_id}. Configure settings on the right.")

    def get_current_settings_from_ui(self):
        return {
            "low_mag": self.var_low_mag.get(),
            "low_count": self.var_low_count.get(),
            "high_mag": self.var_high_mag.get(),
            "high_count": self.var_high_count.get(),
            "high_mag_2": self.var_high_mag_2.get(),
            "high_count_2": self.var_high_count_2.get()
        }

    def apply_to_current(self):
        sid = self.stub_map.selected_slot_id
        if sid:
            name = self.var_sample_name.get().strip()
            if not name:
                messagebox.showerror("Error", "Sample Name cannot be empty!")
                return
            settings = self.get_current_settings_from_ui()
            self.stub_map.update_settings(sid, name, settings)
            self.status_var.set(f"Settings saved for {name} (Slot {sid}).")
            messagebox.showinfo("Success", f"Saved: {name}")

    def apply_to_all(self):
        settings = self.get_current_settings_from_ui()
        active_slots = self.stub_map.get_active_slots()
        
        if not active_slots:
            messagebox.showwarning("Warning", "No active slots selected!")
            return
            
        count = 0
        for sid, data in active_slots.items():
            # Keep original name, only update settings
            current_name = data['name']
            self.stub_map.update_settings(sid, current_name, settings)
            count += 1
            
        self.status_var.set(f"Settings applied to all {count} active slots (Names preserved).")
        messagebox.showinfo("Batch Apply", f"Applied settings to {count} slots.\n(Sample names were kept as is)")

    def start_automation(self):
        active_slots = self.stub_map.get_active_slots()
        if not active_slots:
            messagebox.showerror("Error", "Please select at least one sample slot!")
            return
            
        # Summary
        summary = "Automation Plan:\n\n"
        for sid, data in active_slots.items():
            s = data['settings']
            name = data['name']
            summary += f"[{name}] Slot {sid}\n   Search: x{s['low_mag']} -> High1: x{s['high_mag']} -> High2: x{s['high_mag_2']}\n"
            
        confirm = messagebox.askyesno("Confirm Start", summary + "\nStart SEM Automation now?")
        
        if confirm:
            self.btn_run.config(state=tk.DISABLED, text="Running...")
            self.log_message(">>> Initializing Automation Thread...")
            
            # Start in a separate thread to prevent GUI freezing
            thread = threading.Thread(target=self.run_workflow_thread, args=(active_slots,))
            thread.daemon = True # Exit thread when main app closes
            thread.start()

    def run_workflow_thread(self, active_slots):
        try:
            # Instantiate AutomationManager with the GUI log callback
            # Note: simulation=True by default. In real usage, this should be toggled via CLI arg or Checkbox.
            # For now, let's assume simulation=False if we are "Starting Automation" (or pass a flag).
            # Let's keep it safe: Simulation=True unless changed in code.
            # *Ideally, add a Checkbox "Simulation Mode" in GUI*
            
            # For this deployment, I will hardcode simulation=False so it works on real hardware,
            # BUT wrapped in try-except so it doesn't crash if sharksem is missing.
            
            # Or better: Check if sharksem is importable.
            try:
                import sharksem
                sim_mode = False
            except ImportError:
                sim_mode = True
                self.log_message("[System] SharkSEM not found. Running in SIMULATION MODE.")

            manager = AutomationManager(simulation=sim_mode, log_callback=self.log_message)
            manager.run(active_slots)
            
            self.log_message(">>> Automation Workflow Finished.")
            
        except Exception as e:
            self.log_message(f"[GUI Error] Thread failed: {e}")
        finally:
            # Re-enable button (needs to be done in main thread)
            self.root.after(0, lambda: self.btn_run.config(state=tk.NORMAL, text="START AUTOMATION"))

def launch_gui():
    root = tk.Tk()
    # High DPI support for Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    app = SmartSEMApp(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
