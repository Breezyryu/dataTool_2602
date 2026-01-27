# 작업 로그: Phase 2 유틸리티 함수 분석

> **작업일**: 2026-01-27  
> **대상 파일**: [BatteryDataTool.py](file:///c:/Users/Ryu/!battery/python/dataprocess/origin_datatool/BatteryDataTool.py)  
> **작업 범위**: Lines 1-180 (유틸리티 함수)

📌 **활용 스킬**: `scientific-critical-thinking`

---

## 1. Import 분석 (Lines 1-20)

### 사용 라이브러리
| 라이브러리 | 용도 |
|-----------|------|
| `os`, `sys` | 파일/시스템 조작 |
| `re` | 정규표현식 (용량 파싱 등) |
| `bisect` | 이진 탐색 |
| `warnings` | 경고 무시 |
| `json` | JSON 처리 |
| `pyodbc` | 데이터베이스 연결 |
| `pandas` | 데이터프레임 처리 |
| `numpy` | 수치 연산 |
| `matplotlib` | 그래프 시각화 |
| `scipy.optimize` | curve_fit, root_scalar (피팅) |
| `scipy.stats` | linregress (선형 회귀) |
| `PyQt6` | GUI 프레임워크 |
| `tkinter` | 디렉토리 선택 다이얼로그 |
| `xlwings` | 엑셀 연동 |

### 전역 설정 (Lines 25-29)
```python
warnings.simplefilter("ignore")  # 경고 무시
plt.rcParams["font.family"] = "Malgun gothic"  # 한글 폰트
plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 처리
```

---

## 2. 유틸리티 함수 상세 분석

### 2.1 `to_timestamp(date_str)` (Lines 32-48)

**목적**: 날짜 문자열을 Unix timestamp로 변환

**입력 형식**: `"YYMMDD HH:MM:SS.msec"` (예: `"170102 12:30:45.123"`)

**전기화학적 맥락**:
- 배터리 충방전 데이터의 시간 동기화에 사용
- Toyo 충방전기 데이터 파일의 타임스탬프 파싱

**코드 분석**:
```python
def to_timestamp(date_str):
    year = int(date_str[:2])      # YY
    month = int(date_str[2:4])    # MM
    day = int(date_str[4:6])      # DD
    hour = int(date_str[7:9])     # HH
    minute = int(date_str[10:12]) # MM
    second = int(date_str[13:15]) # SS
    millisecond = int(date_str[16:19])  # msec
    
    year += 2000  # 2000년대 가정
    
    dt = datetime(year, month, day, hour, minute, second, 
                  millisecond * 1000, tzinfo=timezone.utc)
    return int(dt.timestamp() - 9 * 3600)  # KST → UTC 보정
```

**고도화 제안**:
- 예외 처리 추가 (잘못된 형식 대응)
- 타입 힌트 추가

---

### 2.2 `progress(count1, max1, count2, max2, count3, max3)` (Lines 51-53)

**목적**: 3단계 중첩 루프의 진행률 계산 (0-100%)

**수식**:
```
progress = ((count1 + ((count2 + (count3/max3) - 1) / max2) - 1) / max1) * 100
```

**용도**: GUI에서 데이터 처리 진행 상황 표시

---

### 2.3 `multi_askopendirnames()` (Lines 56-72)

**목적**: 여러 디렉토리를 연속으로 선택

**동작**:
1. 초기 디렉토리: `d://`
2. 이후 선택: 이전 선택의 상위 폴더에서 시작
3. 빈 선택 시 종료

**활용**: 여러 배터리 셀 데이터 폴더 일괄 선택

---

### 2.4 `extract_text_in_brackets(input_string)` (Lines 75-78)

**목적**: 대괄호 `[]` 안의 텍스트 추출

**예시**:
```python
extract_text_in_brackets("[45V 4470mAh]") → "45V 4470mAh"
extract_text_in_brackets("NoMatch") → "NoMatch" (3자리 zfill)
```

**활용**: 폴더명에서 배터리 스펙 파싱

---

### 2.5 `name_capacity(data_file_path)` (Lines 100-114)

**목적**: 파일 경로에서 배터리 용량(mAh) 추출

**전기화학적 맥락**:
- 정격 용량은 C-rate 계산의 기준
- C-rate = 전류(mA) / 용량(mAh)
- 예: 4500mAh 배터리에서 4500mA = 1C

**파싱 예시**:
| 입력 | 출력 |
|------|------|
| `"Cell_3500mAh_001"` | 3500.0 |
| `"M1 ATL [45V 4175mAh]"` | 4175.0 |
| `"4-187mAh_half"` | 4.187 |

**정규식**: `r'(\d+([\-\.]\d+)?)mAh'`
- `-`를 `.`으로 변환 (소수점 용량 지원)

---

### 2.6 `check_cycler(raw_file_path)` (Lines 156-159)

**목적**: 충방전기 타입 구분 (PNE vs Toyo)

**전기화학적 맥락**:
- **PNE 충방전기**: Pattern 폴더 기반 테스트 스케줄
- **Toyo 충방전기**: capacity.log 파일 기반 cycle 데이터

**판별 기준**:
```python
# Pattern 폴더 존재 → PNE (True)
# Pattern 폴더 없음 → Toyo (False)
cycler = os.path.isdir(raw_file_path + "\\Pattern")
```

**중요**: 이 함수는 이후 데이터 로딩 로직 분기의 핵심

---

### 2.7 `convert_steplist(input_str)` (Lines 162-170)

**목적**: 문자열을 스텝 번호 리스트로 변환

**예시**:
```python
convert_steplist("1 3-5 7") → [1, 3, 4, 5, 7]
```

**활용**: 사용자가 입력한 스텝 범위를 파싱하여 Profile 데이터 필터링

---

### 2.8 `same_add(df, column_name)` (Lines 173-179)

**목적**: 동일 값에 대해 순차적으로 1씩 증가하는 새 컬럼 생성

**활용**: Cycle 데이터에서 중복된 인덱스 처리

---

## 3. UI 유틸리티 함수

### 3.1 `err_msg(title, msg)` (Lines 134-143)

**목적**: 에러 메시지 박스 표시 (PyQt6)

### 3.2 `connect_change(button)` / `disconnect_change(button)` (Lines 146-153)

**목적**: 연결 상태에 따른 버튼 색상 변경
- 연결됨: 파란색 (RGB 0,0,200)
- 연결 안됨: 빨간색 (RGB 200,0,0)

---

## 4. 다음 단계

- [x] 유틸리티 함수 분석 완료 (14개 함수)
- [ ] `battery_tool/utils/helpers.py` 모듈 생성
- [ ] 그래프 함수 분석 (Lines 181-420)
