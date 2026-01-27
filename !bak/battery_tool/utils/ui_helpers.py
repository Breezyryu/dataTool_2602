"""
Battery Data Tool - UI Helpers Module

PyQt6 기반 UI 유틸리티 함수
원본: origin_datatool/BatteryDataTool.py (Lines 134-153)
"""

from PyQt6 import QtGui, QtWidgets


def err_msg(title: str, msg: str) -> None:
    """에러 메시지 박스 표시.
    
    Args:
        title: 메시지 박스 제목
        msg: 표시할 메시지 내용
    """
    msg_box = QtWidgets.QMessageBox()
    msg_box.setWindowTitle(title)
    msg_box.setText(msg)
    msg_box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
    
    font = QtGui.QFont()
    font.setFamily("Malgun gothic")
    msg_box.setFont(font)
    msg_box.exec()


def connect_change(button: QtWidgets.QPushButton) -> None:
    """연결 상태 버튼을 파란색으로 변경.
    
    Args:
        button: 상태를 변경할 버튼 위젯
    """
    color = QtGui.QColor(0, 0, 200)  # 파란색
    button.setStyleSheet(f"color: {color.name()}")


def disconnect_change(button: QtWidgets.QPushButton) -> None:
    """비연결 상태 버튼을 빨간색으로 변경.
    
    Args:
        button: 상태를 변경할 버튼 위젯
    """
    color = QtGui.QColor(200, 0, 0)  # 빨간색
    button.setStyleSheet(f"color: {color.name()}")
