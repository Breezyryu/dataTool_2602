# Phase 8: GUI 통합

**작업일**: 2026-01-27  
**원본 참조**: `origin_datatool/BatteryDataTool.py`

📌 **활용 스킬**: `scientific-writing`, `matplotlib`, `pyqt6`

---

## 추가된 파일

| 파일 | 용도 |
|------|------|
| `battery_tool/gui/main.py` | GUI 실행 함수 (`run_app()`) |
| `battery_tool/__main__.py` | 모듈 진입점 |

---

## 실행 방법

```bash
# 방법 1: 모듈로 실행
python -m battery_tool

# 방법 2: 디버그 모드
python -m battery_tool --debug

# 방법 3: Python 코드에서
from battery_tool.gui import run_app
run_app()
```

---

## 검증 결과

```bash
$ uv run python -m battery_tool --help
usage: __main__.py [-h] [--debug]

Battery Data Tool - GUI 실행

options:
  -h, --help  show this help message and exit
  --debug     디버그 모드 활성화
```

---

## 구현 세부사항

### run_app() 함수
- origin_datatool의 `WindowClass` 재활용
- sys.path에 origin_datatool 경로 동적 추가
- 디버그 모드 지원 (`--debug` 플래그)

### 패키지 구조 변경

```
battery_tool/
├── __init__.py
├── __main__.py          # 🆕 모듈 진입점
├── gui/
│   ├── __init__.py      # run_app export 추가
│   ├── main.py          # 🆕 GUI 실행 함수
│   └── handlers/
└── ...
```
