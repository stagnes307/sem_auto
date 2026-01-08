# 🚀 SEM Automation: 현장 적용 가이드 (D-Day)

이 문서는 AI 지원 없이 오프라인 환경(SEM PC)에서 자동화 시스템을 구축하기 위한 단계별 가이드입니다.

---

## 1. 준비물 (USB 담아가기)
- [ ] **전체 프로젝트 폴더** (`sem_auto`)
- [ ] **Python 설치 파일** (SEM PC에 파이썬이 없을 경우 대비, 3.9~3.11 권장)
- [ ] **YOLO 모델 파일**: `yolov8n.pt` (필수), `yolov8n-seg.pt` (선택/예비용)

---

## 2. 현장 도착 후 환경 설정
1. **파일 복사**: 프로젝트 폴더를 SEM PC의 바탕화면이나 `C:\Work` 등 편한 곳에 복사합니다.
2. **Python 확인**:
   ```cmd
   python --version
   ```
3. **라이브러리 설치**:
   ```cmd
   cd sem_auto
   pip install -r requirements.txt
   ```

---

## 3. 핵심 미션: SDK 연결 (Code Connecting)
**목표**: `core/microscope.py` 파일을 수정하여 실제 장비와 대화하게 만듭니다.

1. **SDK 찾기**:
   - `C:\Program Files\Tescan` 또는 제조사 폴더 탐색.
   - `SharkSEM`, `Python SDK`, `Examples` 키워드 찾기.
   - **설치**: `.whl` 파일이 있다면 `pip install 파일명.whl` 로 설치.

2. **코드 수정 (`core/microscope.py`)**:
   - 아래 내용을 참고하여 `RealAdapter` 클래스를 채웁니다.

```python
# core/microscope.py

# 1. 라이브러리 임포트
import sharksem  # (제조사에 맞는 이름으로 변경)

class RealAdapter:
    def __init__(self):
        print("Connecting...")
        self.sem = sharksem.SemApi()
        self.sem.connect() # 연결 명령어 확인 필요

    def move_stage(self, x, y):
        # ★주의: 단위 확인 (mm vs um)
        self.sem.stage.move_to(x=x, y=y)

    def set_magnification(self, mag):
        self.sem.optics.set_mag(mag)

    def acquire_image(self):
        # 이미지 데이터(Numpy array) 리턴
        return self.sem.detector.grab_frame()
```

---

## 4. 좌표 입력 (Teaching)
**목표**: `core/workflow.py` 파일에 샘플 20개의 위치를 알려줍니다.

1. **조이스틱 조작**: 1번 슬롯(좌측 상단)의 중앙으로 이동 -> 화면의 X, Y 값 메모.
2. **코드 수정 (`core/workflow.py`)**:
   - 파일 상단의 `SLOT_COORDINATES` 딕셔너리를 수정합니다.

```python
SLOT_COORDINATES = {
    # 1번 줄 (Row 1)
    1:  (10.5, 20.0),  2:  (20.5, 20.0), ...
    
    # 2번 줄 (Row 2)
    11: (10.5, 40.0), 12: (20.5, 40.0), ...
}
```

3. **FOV(시야각) 보정**:
   - `core/workflow.py` 중간의 `fov_width = 200000` 부분 확인.
   - 5,000배율일 때 화면 가로 길이가 몇 um인지 확인 후 수정 (정확한 이동을 위해 필요).

---

## 5. 실행 및 안전 수칙 (Run & Safety)

1. **Z축 고정**: 
   - 스터브를 넣고 물리적인 높이(WD)를 안전한 곳(예: 10mm)에 고정합니다.
   - **절대 자동화 도중에 스테이지 Z축을 움직이는 코드를 넣지 마세요.**
2. **GUI 실행**:
   ```cmd
   python ui/gui.py
   ```
   또는
   ```cmd
   python main.py --gui
   ```
3. **비상 대기**:
   - 첫 이동 시 **비상 정지(Emergency Stop)** 버튼 위에 손을 올리고, 스테이지가 엉뚱한 곳으로 튀지 않는지 감시합니다.

---

## 6. 문제 해결 (Troubleshooting)
- **ImportError: No module named 'sharksem'**: SDK 설치가 안 된 것입니다. `pip list`로 확인하세요.
- **이미지가 검게 나옴**: 빔(Beam)이 켜져 있는지 확인하세요 (`Beam On`).
- **좌표가 엉뚱한 곳으로 감**: mm 단위를 um로 넣었거나 그 반대일 수 있습니다. (1mm = 1000um)
