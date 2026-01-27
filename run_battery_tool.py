"""
Battery Data Tool - 직접 실행용 런처

VS Code에서 이 파일을 열고 F5 또는 Run Python File로 실행
"""

import sys
import os

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# battery_tool import
from battery_tool.gui.main import run_app

if __name__ == "__main__":
    run_app(debug=True)
