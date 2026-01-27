# Phase 7: GUI Handlers 분리

**작업일**: 2026-01-27  
**원본 파일**: `origin_datatool/BatteryDataTool.py` Lines 8059-14144

---

## 접근 방식

GUI 클래스(`Ui_sitool`, `WindowClass`)는 PyQt Designer 생성 코드로 직접 분리하기 어려움.
대신 **비즈니스 로직**만 별도 모듈로 추출.

---

## 생성된 패키지 구조

```
battery_tool/gui/
├── __init__.py
└── handlers/
    ├── __init__.py
    ├── cycle_logic.py      # 4개 함수
    ├── profile_logic.py    # 4개 함수
    └── dvdq_logic.py       # 4개 함수
```

---

## 추가된 함수

### cycle_logic.py

| 함수 | 용도 |
|------|------|
| `process_cycle_data` | Toyo/PNE 자동 감지 후 처리 |
| `process_folder_cycles` | 폴더 내 전체 채널 처리 |
| `create_cycle_plot` | 6-panel 그래프 생성 |
| `extract_cycle_summary` | 요약 데이터 추출 |

### profile_logic.py

| 함수 | 용도 |
|------|------|
| `process_charge_profile` | 충전 Profile 통합 |
| `process_discharge_profile` | 방전 Profile 통합 |
| `process_step_charge_profile` | Step 충전 통합 |
| `create_profile_plot` | Profile 그래프 생성 |

### dvdq_logic.py

| 함수 | 용도 |
|------|------|
| `analyze_dvdq` | dV/dQ 분석 수행 |
| `fit_dvdq_curve` | 곡선 피팅 |
| `create_dvdq_plot` | 분석 그래프 생성 |
| `calculate_degradation_metrics` | 열화 지표 계산 |

---

## 사용 예시

```python
from battery_tool.gui import process_cycle_data, create_cycle_plot

cap, df = process_cycle_data("path/to/data", mincapacity=0)
fig = create_cycle_plot(df, cap, title="Sample")
```

---

## 최종 현황

| 패키지 | 모듈 수 | 함수 수 |
|--------|---------|---------|
| utils | 2 | 17 |
| visualization | 5 | 21 |
| data_processing | 2 | 22 |
| analysis | 1 | 2 |
| gui | 3 | 12 |
| **합계** | **13** | **74+** |
