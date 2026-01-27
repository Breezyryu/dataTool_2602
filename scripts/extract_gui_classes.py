"""
GUI 클래스 추출 스크립트
Ui_sitool 및 WindowClass를 battery_tool/gui/로 복사
"""

import os

# 원본 파일 읽기
origin_path = "origin_datatool/BatteryDataTool.py"
with open(origin_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Ui_sitool 클래스 추출 (2018-8057, 1-indexed → 2017-8056, 0-indexed)
ui_start = 2017
ui_end = 8057
ui_lines = lines[ui_start:ui_end]

# WindowClass 클래스 추출 (8059-14144, 1-indexed → 8058-14143, 0-indexed)
wc_start = 8058
wc_end = 14144
wc_lines = lines[wc_start:wc_end]

# ui_sitool.py 생성
ui_header = '''"""
Battery Data Tool - UI Definition

PyQt6 UI 위젯 정의 클래스 (PyQt Designer 생성)

📌 활용 스킬: pyqt6
"""

from PyQt6 import QtCore, QtGui, QtWidgets


'''

ui_path = "battery_tool/gui/ui_sitool.py"
with open(ui_path, "w", encoding="utf-8") as f:
    f.write(ui_header)
    f.writelines(ui_lines)

print(f"✅ ui_sitool.py 생성: {len(ui_lines)} 줄")

# window_class.py 생성
wc_header = '''"""
Battery Data Tool - Main Window Class

메인 윈도우 클래스 및 이벤트 핸들러

📌 활용 스킬: pyqt6
"""

import os
import sys
import re
import bisect
import warnings
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit, root_scalar
from scipy.stats import linregress
from tkinter import Tk, filedialog

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# battery_tool 모듈 import
from battery_tool.utils import (
    to_timestamp, progress, multi_askopendirnames,
    extract_text_in_brackets, separate_series, name_capacity,
    binary_search, remove_end_comma, check_cycler, convert_steplist,
    same_add, err_msg, connect_change, disconnect_change,
)
from battery_tool.visualization import (
    graph_base_parameter, graph_cycle_base, graph_cycle, graph_cycle_empty,
    graph_output_cycle, graph_step, graph_continue, graph_soc_continue,
    graph_profile, output_fig,
)
from battery_tool.data_processing import (
    toyo_read_csv, toyo_Profile_import, toyo_cycle_import, toyo_min_cap,
    toyo_cycle_data, toyo_chg_Profile_data, toyo_dchg_Profile_data,
    toyo_step_Profile_data, toyo_rate_Profile_data, toyo_Profile_continue_data,
    pne_search_cycle, pne_data, pne_continue_data, pne_min_cap,
    pne_cycle_data, pne_step_Profile_data, pne_rate_Profile_data,
)
from battery_tool.analysis import generate_params, generate_simulation_full

from .ui_sitool import Ui_sitool

# 경고 무시
warnings.simplefilter("ignore")
# 한글 설정
plt.rcParams["font.family"] = "Malgun gothic"
plt.rcParams["axes.unicode_minus"] = False


'''

wc_path = "battery_tool/gui/window_class.py"
with open(wc_path, "w", encoding="utf-8") as f:
    f.write(wc_header)
    f.writelines(wc_lines)

print(f"✅ window_class.py 생성: {len(wc_lines)} 줄")
print(f"📁 총 {len(ui_lines) + len(wc_lines)} 줄 이전 완료")
