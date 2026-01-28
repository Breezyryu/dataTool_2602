"""
Battery Data Tool - GUI Main Entry Point

battery_tool에서 GUI를 직접 실행하기 위한 진입점

사용법:
    python -m battery_tool
"""

import sys
import os


def run_app(debug: bool = False) -> int:
    """GUI 앱 실행.
    
    Args:
        debug: 디버그 모드 활성화 여부
    
    Returns:
        앱 종료 코드
    """
    # PyQt6 import (런타임에만 필요)
    from PyQt6.QtWidgets import QApplication
    
    # 디버그 모드 설정
    if debug:
        os.environ["QT_DEBUG_PLUGINS"] = "1"
        print("Debug mode enabled")
    
    # battery_tool의 WindowClass import
    from battery_tool.gui.window_class import WindowClass
    
    # 앱 생성 및 실행
    app = QApplication(sys.argv)
    
    # 메인 윈도우 생성
    window = WindowClass()
    window.setWindowTitle("Battery Data Tool (battery_tool)")
    window.show()
    
    print("Battery Data Tool GUI 시작")
    print("battery_tool 패키지에서 실행 중")
    
    return app.exec()


def main():
    """CLI 진입점."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Battery Data Tool - GUI 실행"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="디버그 모드 활성화"
    )
    
    args = parser.parse_args()
    
    sys.exit(run_app(debug=args.debug))


if __name__ == "__main__":
    main()
