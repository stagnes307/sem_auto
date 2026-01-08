# Smart-SEM Deployment Guide

## 1. Installation on SEM PC
1.  **Transfer Files**: Copy the entire `sem_auto` folder to the computer connected to the Tescan MIRA4.
2.  **Install Python**: Ensure Python 3.8+ is installed.
3.  **Install Dependencies**:
    ```powershell
    cd sem_auto
    pip install -r requirements.txt
    ```
4.  **Install Manufacturer SDK**: You must install the `SharkSEM` Python package provided by Tescan. (Usually comes with the microscope installation CD or support portal).

## 2. Code Integration (Critical)
You need to connect my code to the real microscope. I have left a "Placeholder" for you.

**File to Edit**: `core/microscope.py`

Find the `class RealAdapter:` and fill in the methods using the SharkSEM manual.

### Example (Conceptual):
```python
# In core/microscope.py

import sharksem # <--- Import the real library

class RealAdapter:
    def __init__(self):
        self.sem_api = sharksem.SemApi()

    def connect(self):
        self.sem_api.connect("127.0.0.1", 5555) # Example IP/Port

    def move_stage(self, x, y):
        # The API might use microns, mm, or nanometers. Check the units!
        self.sem_api.stage.move_to(x=x, y=y) 

    def set_magnification(self, mag):
        self.sem_api.optics.set_mag(mag)

    def acquire_image(self):
        # Should return a numpy array (OpenCV format)
        img_data = self.sem_api.detector.grab_frame()
        return img_data
```

## 3. Fine-Tuning YOLO
1.  **Collect Data**: Run the system in "Manual" or "Semi-Auto" to save images of real particles.
2.  **Labeling**: Use tools like `LabelImg` or `Roboflow` to draw boxes around particles.
3.  **Training**:
    ```bash
    yolo detect train data=my_dataset.yaml model=yolov8n.pt epochs=100
    ```
4.  **Update Model**: Copy the new `best.pt` to the project folder and run:
    ```bash
    python main.py --model best.pt
    ```

## 4. Safety First!
> [!WARNING]
> **Collisions**: When testing `move_stage` for the first time, keep your hand on the Emergency Stop. The coordinates might be inverted or scaled differently (e.g., mm vs um).

## 5. Launch
Run the specific command to disable simulation mode:
```bash
python main.py
```
(Without the `--simulation` flag, it defaults to `RealAdapter`).
