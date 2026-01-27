# Phase 6: PNE Cycle Functions 분석

**작업일**: 2026-01-27  
**원본 파일**: `origin_datatool/BatteryDataTool.py` Lines 1060-1350

---

## 추가된 함수

### PNE Cycle (4개)

| 함수 | 줄 수 | 용도 |
|------|-------|------|
| `pne_cycle_data` | 120 | Cycle 데이터 처리 (DCIR 포함) |
| `pne_cyc_continue_data` | 20 | 전체 Cycle 로딩 |
| `same_add` | 10 | 동일 값 순번 추가 유틸 |

---

## PNE 데이터 컬럼 매핑

```
컬럼 27: Total Cycle
컬럼  2: StepType (1=충전, 2=방전, 3=휴지)
컬럼  6: EndState (64=휴지, 65=전압, 66=전류, 78=용량)
컬럼  8: Voltage (mV)
컬럼  9: Current (μA 또는 mA)
컬럼 10: Chg Capacity (mAh)
컬럼 11: Dchg Capacity (mAh)
컬럼 15: Dchg WattHour (Wh)
컬럼 20: Impedance
컬럼 24: Temperature (°C)
```

---

## DCIR 계산 모드

| 모드 | 플래그 | 설명 |
|------|--------|------|
| 기본 DCIR | `chkir=True` | 10s pulse |
| 연속 DCIR | `chkir2=True` | 연속 측정 |
| 복합 DCIR | `mkdcir=True` | 1s pulse + RSS |

---

## 파일 변경

| 파일 | 변경 |
|------|------|
| `pne_processor.py` | 541줄 (최종) |
| `data_processing/__init__.py` | 22개 함수 export |
