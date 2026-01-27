# Phase 5: Toyo/PNE Profile Functions 분석

**작업일**: 2026-01-27  
**원본 파일**: `origin_datatool/BatteryDataTool.py` Lines 620-950

---

## 추가된 함수

### Toyo Profile (5개)

| 함수 | 줄 수 | 용도 |
|------|-------|------|
| `toyo_chg_Profile_data` | 60 | 충전 Profile (dQ/dV, dV/dQ) |
| `toyo_dchg_Profile_data` | 65 | 방전 Profile (연속 step 병합) |
| `toyo_step_Profile_data` | 55 | Step 충전 패턴 |
| `toyo_rate_Profile_data` | 45 | 율별 충전 특성 |
| `toyo_Profile_continue_data` | 50 | 연속 cycle 병합 |

### PNE Profile (2개)

| 함수 | 줄 수 | 용도 |
|------|-------|------|
| `pne_step_Profile_data` | 55 | Step 충전 Profile |
| `pne_rate_Profile_data` | 45 | 율별 충전 Profile |

---

## 전기화학적 맥락

### dQ/dV 분석
- **피크 위치**: 상변화 전압 반영
- **피크 강도**: 활물질 양 반영
- **피크 이동**: 과전압 증가 (내부저항 증가)

### dV/dQ 분석
- 용량 감소 시 피크 높이 증가
- 열화 메커니즘 정량화에 활용

---

## 파일 변경

| 파일 | 변경 |
|------|------|
| `toyo_processor.py` | 370줄 → 711줄 |
| `pne_processor.py` | 211줄 → 541줄 |
| `data_processing/__init__.py` | export 추가 |
