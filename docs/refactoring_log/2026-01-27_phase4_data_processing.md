# 작업 로그: Phase 4 데이터 처리 함수 모듈화

> **작업일**: 2026-01-27  
> **대상 파일**: [BatteryDataTool.py](file:///c:/Users/Ryu/!battery/python/dataprocess/origin_datatool/BatteryDataTool.py)  
> **작업 범위**: Lines 409-950 (dV/dQ 분석, Toyo/PNE 데이터 처리)

📌 **활용 스킬**: `scientific-critical-thinking`

---

## 1. 생성된 모듈

| 모듈 | 함수 수 | 설명 |
|------|--------|------|
| `analysis/dvdq_analysis.py` | 2 | dV/dQ 시뮬레이션 |
| `data_processing/toyo_processor.py` | 5 | Toyo 충방전기 |
| `data_processing/pne_processor.py` | 4 | PNE 충방전기 |

---

## 2. dV/dQ 분석 (analysis/dvdq_analysis.py)

### 2.1 전기화학적 배경

```
dV/dQ 분석 = 전극 열화 메커니즘의 정량적 분석

Full cell 전압:
V_cell = V_cathode(Q) - V_anode(Q)

열화 파라미터:
┌─────────────┬─────────────────────────────────────┐
│ 파라미터     │ 물리적 의미                          │
├─────────────┼─────────────────────────────────────┤
│ ca_mass     │ 양극 활물질 잔량 (1.0=초기)           │
│ ca_slip     │ 양극 Li 손실 (mAh)                   │
│ an_mass     │ 음극 활물질 잔량 (1.0=초기)           │
│ an_slip     │ 음극 Li 손실 (mAh)                   │
└─────────────┴─────────────────────────────────────┘

열화 메커니즘 해석:
- SEI 성장 → an_slip 증가 (주요 Li 소모원)
- 양극 구조 붕괴 → ca_mass 감소
- 음극 리튬 도금 → an_mass, an_slip 모두 영향
```

### 2.2 `generate_simulation_full()` 함수

```python
# 입력
ca_ccv_raw: 양극 half cell 데이터 (ca_cap, ca_volt)
an_ccv_raw: 음극 half cell 데이터 (an_cap, an_volt)
real_raw: 실측 full cell 데이터 (real_cap, real_volt)

# 출력 컬럼
full_cap, an_volt, ca_volt, full_volt, real_volt
an_dvdq, ca_dvdq, full_dvdq, real_dvdq
```

---

## 3. Toyo 데이터 처리 (toyo_processor.py)

### 3.1 데이터 구조

```
Toyo 충방전기 데이터 폴더 구조:
├── capacity.log      # Cycle 요약 데이터
├── 000001            # Cycle 1 상세 profile
├── 000002            # Cycle 2 상세 profile
└── ...
```

### 3.2 주요 함수

| 함수 | 용도 |
|------|------|
| `toyo_read_csv()` | CSV 파일 읽기 |
| `toyo_cycle_import()` | capacity.log 로딩 |
| `toyo_Profile_import()` | 개별 cycle profile 로딩 |
| `toyo_min_cap()` | 정격 용량 산정 |
| `toyo_cycle_data()` | Cycle 데이터 전처리 (핵심) |

### 3.3 `toyo_cycle_data()` 출력 컬럼

| 컬럼 | 설명 | 전기화학적 의미 |
|------|------|----------------|
| Dchg | 방전 용량 비율 | 열화 지표 (capacity fade) |
| Chg | 충전 용량 비율 | - |
| Eff | 쿨롱 효율 | Dchg/Chg, 부반응 지표 |
| Eff2 | 역방향 효율 | Chg2/Dchg |
| RndV | 휴지 전압 | OCV 변화 |
| AvgV | 평균 방전 전압 | 에너지 효율 관련 |
| Temp | 최고 온도 | 발열 지표 |
| dcir | DC 내부저항 | 저항 성장 추적 |

---

## 4. PNE 데이터 처리 (pne_processor.py)

### 4.1 데이터 구조

```
PNE 충방전기 데이터 폴더 구조:
├── Pattern/                   # 테스트 패턴 정의
└── Restore/                   # 실측 데이터
    ├── SaveData_0001.csv
    ├── SaveData_0002.csv
    ├── SaveEndData.csv        # Cycle 인덱스
    └── savingFileIndex_start.csv
```

### 4.2 주요 함수

| 함수 | 용도 |
|------|------|
| `pne_search_cycle()` | Cycle-파일 매핑 찾기 |
| `pne_data()` | 단일 cycle 로딩 |
| `pne_continue_data()` | 연속 cycle 로딩 |
| `pne_min_cap()` | 정격 용량 산정 |

---

## 5. 검증 결과

```bash
$ uv run python -c "from battery_tool import utils, visualization, data_processing, analysis; print('OK')"
All modules imported successfully!
```

---

## 6. 다음 단계

- [x] dV/dQ 분석 모듈 완료
- [x] Toyo 처리 모듈 완료
- [x] PNE 처리 모듈 완료
- [ ] Phase 5: Toyo/PNE Profile 함수 추가 모듈화
- [ ] Phase 6: GUI 클래스 분리 (대규모 작업)
