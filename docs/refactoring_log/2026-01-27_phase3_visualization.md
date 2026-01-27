# 작업 로그: Phase 3 그래프 함수 모듈화

> **작업일**: 2026-01-27  
> **대상 파일**: [BatteryDataTool.py](file:///c:/Users/Ryu/!battery/python/dataprocess/origin_datatool/BatteryDataTool.py)  
> **작업 범위**: Lines 181-407 (그래프 함수)

📌 **활용 스킬**: `matplotlib`

---

## 1. 생성된 모듈

| 모듈 | 함수 수 | 설명 |
|------|--------|------|
| `graph_base.py` | 2 | 기본 설정, Cycle 베이스 |
| `cycle_graphs.py` | 3 | Cycle 데이터 시각화 |
| `profile_graphs.py` | 8 | Profile 데이터 시각화 |
| `dcir_graphs.py` | 2 | DC-IR 시각화 |
| `output.py` | 6 | 출력, 시뮬레이션 그래프 |

---

## 2. 주요 함수 분석

### 2.1 기본 설정 함수

**`graph_base_parameter(ax, xlabel, ylabel)`**
- 모든 그래프의 공통 스타일 설정
- 폰트: 12pt, bold
- 그리드: 점선, 선 두께 1.0
- 눈금: 안쪽 방향

**`graph_cycle_base(x_data, ax, ...)`**
- Cycle 그래프 X축 범위 자동 계산
- 400/800/1200/2000 cycle 기준으로 눈금 간격 조정

### 2.2 Cycle 그래프

**`graph_cycle(x, y, ax, ...)`** - 채워진 마커
**`graph_cycle_empty(x, y, ax, ...)`** - 빈 마커

두 함수를 조합하여 동일 축에 두 데이터 시리즈를 구분 표시:
- 채워진 마커: 주 데이터 (예: 방전 용량)
- 빈 마커: 보조 데이터 (예: 평균 전압)

**`graph_output_cycle(...)`**
Cycle 분석의 핵심 6개 지표를 한 번에 시각화:
| 축 | 지표 | 전기화학적 의미 |
|----|------|----------------|
| ax1 | Dchg | 방전 용량 비율 (열화 지표) |
| ax2 | Eff | 쿨롱 효율 (부반응 지표) |
| ax3 | Temp | 온도 (발열 지표) |
| ax4 | DCIR | 내부저항 (열화 지표) |
| ax5 | Eff2 | 충전/방전 효율 |
| ax6 | RndV, AvgV | 휴지 전압, 평균 전압 |

### 2.3 DCIR 그래프

**전기화학적 맥락**
```
DCIR = ΔV / ΔI (직류 내부저항)

구성 요소:
- 오믹 저항 (Rohmic): 전해질, 집전체, 접촉 저항
- 전하 이동 저항 (Rct): 전극/전해질 계면 반응
- 확산 저항 (Rdiff): 리튬 이온 확산

DCIR 증가 원인:
1. SEI 성장 → Rohmic, Rct 증가
2. 전해액 분해 → Rohmic 증가
3. 활물질 구조 변화 → Rct 증가
4. 기공 막힘 → Rdiff 증가
```

**`graph_soc_dcir(x, y, ax, ...)`**
- X축: SOC (0-100%)
- 일반적 패턴: 낮은 SOC와 높은 SOC에서 저항 증가

---

## 3. task.md 업데이트 필요

- [x] `visualization/graph_base.py` 생성
- [x] `visualization/cycle_graphs.py` 생성
- [x] `visualization/profile_graphs.py` 생성
- [x] `visualization/dcir_graphs.py` 생성
- [x] `visualization/output.py` 생성
- [ ] Phase 4: 데이터 처리 함수 분석 시작
