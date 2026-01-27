"""
Battery Data Tool - Output Module

그래프 및 데이터 출력 함수
원본: origin_datatool/BatteryDataTool.py (Lines 354-407)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Sequence, Any
import pandas as pd

from .graph_base import graph_base_parameter


def graph_simulation(
    ax: Axes,
    x: Sequence,
    y: Sequence,
    pltcolor: str,
    pltlabel: str,
    x_limit: float,
    y_min: float,
    y_limit: float,
    xlabel: str,
    ylabel: str
) -> None:
    """시뮬레이션 그래프.
    
    전기화학적 맥락:
        수명 예측 시뮬레이션 결과를 시각화합니다.
        실측 데이터와 예측 모델을 비교할 때 사용.
    
    Args:
        ax: matplotlib Axes 객체
        x: X축 데이터
        y: Y축 데이터
        pltcolor: 선 색상
        pltlabel: 범례 라벨
        x_limit: X축 최대값 (0이면 자동)
        y_min, y_limit: Y축 범위
        xlabel, ylabel: 축 라벨
    """
    ax.plot(x, y, pltcolor, label=pltlabel)
    
    if x_limit != 0:
        ax.set_xlim(0, x_limit)
    ax.set_ylim(y_min, y_limit)
    ax.legend()
    
    graph_base_parameter(ax, xlabel, ylabel)


def graph_eu_set(ax: Axes, y_min: float, y_max: float) -> None:
    """EU 규정 기반 수명 예측 그래프 설정.
    
    EU 배터리 규정 (2023/1542)에 따른 수명 표시 형식.
    
    Args:
        ax: matplotlib Axes 객체
        y_min, y_max: Y축 범위
    """
    ax.set_ylim(y_min, y_max)
    ax.set_ylabel('capacity ratio', fontsize=20, fontweight='bold')
    ax.set_xlabel('cycle', fontsize=20, fontweight='bold')
    ax.tick_params(direction='in')
    ax.tick_params(axis='x', labelsize=16)
    ax.tick_params(axis='y', labelsize=16)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.legend(prop={"size": 16})


def graph_default(
    ax: Axes,
    x: Sequence,
    y: Sequence,
    x_llimit: float,
    x_hlimit: float,
    x_gap: float,
    y_llimit: float,
    y_hlimit: float,
    y_gap: float,
    xlabel: str,
    ylabel: str,
    lgnd: str,
    size: float,
    graphcolor: int,
    facecolor: str,
    graphmarker: str
) -> None:
    """기본 그래프 (scatter).
    
    Args:
        ax: matplotlib Axes 객체
        x, y: 데이터
        x_llimit, x_hlimit, x_gap: X축 범위 및 간격
        y_llimit, y_hlimit, y_gap: Y축 범위 및 간격
        xlabel, ylabel: 축 라벨
        lgnd: 범례 라벨
        size: 마커 크기
        graphcolor: 색상 인덱스 (0-4)
        facecolor: 마커 채우기 색상
        graphmarker: 마커 모양
    """
    colors = {0: 'red', 1: 'blue', 2: 'green', 3: 'magenta', 4: 'cyan'}
    
    if graphcolor in colors:
        ax.scatter(x, y, label=lgnd, s=size, color=colors[graphcolor],
                   edgecolors=colors[graphcolor], facecolors=colors[graphcolor], 
                   marker=graphmarker)
    else:
        ax.scatter(x, y, label=lgnd, s=size)
    
    if x_gap != 0:
        ax.set_xticks(np.arange(x_llimit, x_hlimit, x_gap))
        ax.set_xlim(x_llimit, x_hlimit - x_gap)
    if y_gap != 0:
        ax.set_yticks(np.arange(y_llimit, y_hlimit, y_gap))
        ax.set_ylim(y_llimit, y_hlimit - y_gap)
    
    graph_base_parameter(ax, xlabel, ylabel)


def output_data(
    df: pd.DataFrame,
    writer,
    sheetname: str,
    start_col: int,
    start_row: int,
    colname: str,
    head: bool,
    use_index: bool = False
) -> None:
    """DataFrame을 엑셀로 출력.
    
    Args:
        df: 출력할 DataFrame
        writer: ExcelWriter 객체
        sheetname: 시트 이름 (최대 30자)
        start_col, start_row: 시작 위치
        colname: 출력할 컬럼명
        head: 헤더 출력 여부
        use_index: 인덱스 출력 여부
    """
    df.to_excel(writer, sheet_name=sheetname[:30], startcol=start_col, startrow=start_row,
                columns=[colname], header=head, index=use_index)


def output_para_fig(figsaveokchk: Any, filename: str) -> None:
    """현재 figure를 파라미터 그래프로 저장.
    
    Args:
        figsaveokchk: 저장 여부 체크박스 위젯
        filename: 저장할 파일명 (확장자 제외)
    """
    if figsaveokchk.isChecked():
        filepath = f'd:/{filename}.png'
        if os.path.isfile(filepath):
            os.remove(filepath)
        fig = plt.gcf()
        fig.savefig(filepath)


def output_fig(figsaveokchk: Any, filename: str) -> None:
    """현재 plot을 그림 파일로 저장.
    
    D 드라이브에 PNG 파일로 저장합니다.
    
    Args:
        figsaveokchk: 저장 여부 체크박스 위젯
        filename: 저장할 파일명 (확장자 제외)
    """
    if figsaveokchk.isChecked():
        filepath = f'd:/{filename}.png'
        if os.path.isfile(filepath):
            os.remove(filepath)
        plt.savefig(filepath)
