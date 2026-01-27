# Phase 9: GUI 클래스 완전 이전

**작업일**: 2026-01-27  
**원본 참조**: `origin_datatool/BatteryDataTool.py` Lines 2018-14144

📌 **활용 스킬**: `scientific-writing`, `pyqt6`

---

## 추가된 파일

| 파일 | 줄 수 | 용도 |
|------|-------|------|
| `gui/ui_sitool.py` | 6,040 | Ui_sitool 클래스 (UI 정의) |
| `gui/window_class.py` | 6,086 | WindowClass 클래스 (메인 윈도우) |

---

## 이전 상세

### Ui_sitool (2018-8057줄)
- PyQt Designer로 생성된 UI 위젯 정의
- tabWidget, layoutWidget 등 ~200개 위젯
- setupUi(), retranslateUi() 메서드

### WindowClass (8059-14144줄)
- QMainWindow 상속
- ~85개 이벤트 핸들러
- Cycle, Profile, dV/dQ, EU 수명예측 등 탭별 로직

---

## 변경된 Import 구조

```python
# Before (origin_datatool 의존)
from BatteryDataTool import WindowClass

# After (battery_tool 독립)
from battery_tool.gui.window_class import WindowClass
```

---

## 검증 결과

```bash
$ uv run python -c "from battery_tool.gui.window_class import WindowClass"
WindowClass import OK!
```

---

## 최종 구조

```
battery_tool/gui/
├── __init__.py
├── main.py              # run_app()
├── ui_sitool.py         # 6,040줄 (NEW)
├── window_class.py      # 6,086줄 (NEW)
└── handlers/
    ├── cycle_logic.py
    ├── profile_logic.py
    └── dvdq_logic.py
```

---

## 총 이전 현황

| 항목 | 줄 수 |
|------|-------|
| GUI 클래스 | 12,126줄 |
| 비즈니스 로직 | 3,414줄 |
| **합계** | **15,540줄** |
