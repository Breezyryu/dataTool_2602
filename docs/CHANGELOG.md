# battery_tool 변경 로그

## 2026-01-28

### 버그 수정

#### `window_class.py` 수정

1. **`pyodbc` import 누락 수정** (라인 15)
   - **문제**: 패턴 리스트 Load 기능 실행 시 프로그램 종료
   - **원인**: Access 데이터베이스 연결에 필요한 `pyodbc` 모듈 미import
   - **수정**: `import pyodbc` 추가

2. **visualization 함수 11개 import 누락 수정** (라인 35-41)
   - **문제**: 현황 탭의 'R5 15F' 및 '전체' 메뉴 선택 시 프로그램 종료
   - **원인**: `battery_tool.visualization` 모듈에서 함수들이 누락됨
   - **추가된 함수**:
     - `graph_soc_set`, `graph_soc_err`, `graph_set_profile`, `graph_set_guide`
     - `graph_dcir`, `graph_soc_dcir`, `graph_simulation`, `graph_eu_set`
     - `graph_default`, `output_data`, `output_para_fig`

3. **`toyo_base_data_make` 함수 예외 처리 추가** (라인 2386-2429)
   - **문제**: 'R5 15F'/'전체' 선택 후 Toyo 사이클러 선택 시 프로그램 종료
   - **원인**: 네트워크 드라이브(Z:) 파일 미존재 시 `UnboundLocalError` 발생
   - **수정**: `else` 분기 추가 - 에러 메시지 표시 및 빈 DataFrame 반환

4. **`toyo_base_data_make` 함수 TypeError 수정** (라인 2419)
   - **문제**: `TypeError: Invalid value '완료' for type 'int64'`
   - **원인**: `int64` 타입 컬럼에 문자열 할당 시도
   - **수정**: `used_chnl` 계산 후 `toyo_data["use"].astype(object)` 타입 변환

---

## 2026-01-27

### PNE 함수 구현

#### `pne_processor.py` 수정

8개 PNE 함수 신규 구현:

**Profile 함수 (4개)**:
- `pne_chg_Profile_data`: 충전 Profile 처리 (dQ/dV 분석 포함)
- `pne_dchg_Profile_data`: 방전 Profile 처리 (dV/dQ 분석 포함)
- `pne_continue_profile_scale_change`: 연속 Profile 스케일 변환
- `pne_Profile_continue_data`: 연속 Profile 데이터 처리

**DCIR 함수 (2개)**:
- `pne_dcir_chk_cycle`: DCIR 측정 가능 사이클 확인
- `pne_dcir_Profile_data`: DCIR Profile 데이터 처리

**시뮬레이션 함수 (2개)**:
- `pne_simul_cycle_data`: 수명 예측용 사이클 데이터 처리
- `pne_simul_cycle_data_file`: 파일 기반 시뮬레이션 데이터 처리

#### `data_processing/__init__.py` 수정

- 8개 PNE 함수 export 추가
