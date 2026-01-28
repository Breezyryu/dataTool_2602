"""
Battery Data Tool - Graph Base Module

그래프 기본 설정 함수
원본: BatteryDataTool.py (Lines 181-203)

"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, Union, Sequence


def graph_base_parameter(graph_ax: Axes, xlabel: str, ylabel: str) -> None:
    """그래프 축 기본 설정.
    
    그래프의 라벨, 폰트, 그리드를 표준 형식으로 설정합니다.
    
    Args:
        graph_ax: matplotlib Axes 객체
        xlabel: X축 라벨
        ylabel: Y축 라벨
    """
    graph_ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    graph_ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    graph_ax.tick_params(direction='in')
    graph_ax.grid(True, which='both', linestyle='--', linewidth=1.0)


def graph_cycle_base(
    x_data: Sequence,
    ax: Axes,
    lowlimit: float,
    highlimit: float,
    y_gap: float,
    xlabel: str,
    ylabel: str,
    xscale: float,
    overall_xlimit: float
) -> None:
    """Cycle 그래프 기본 설정 (X축, Y축 범위 설정).
    
    전기화학적 맥락:
        Cycle 그래프는 배터리 수명 테스트의 기본 시각화입니다.
        X축: Cycle 수 (충방전 횟수)
        Y축: 용량, 효율, 온도, 저항 등 cycle별 측정값
    
    Args:
        x_data: X축 데이터 (Cycle 번호)
        ax: matplotlib Axes 객체
        lowlimit: Y축 최소값
        highlimit: Y축 최대값
        y_gap: Y축 눈금 간격
        xlabel: X축 라벨
        ylabel: Y축 라벨
        xscale: X축 최대값 (0이면 자동)
        overall_xlimit: 전체 X축 최소 한계
    """
    if xscale == 0 and len(x_data) != 0:
        xlimit = max(x_data)
        if xlimit < overall_xlimit:
            xlimit = overall_xlimit
        xrangemax = (xlimit // 100 + 2) * 100
    else:
        xlimit = xscale
        xrangemax = xscale
    
    # Cycle 수에 따른 X축 눈금 간격 자동 조정
    # 400 이상: 50 추가, 800 이상: 100 추가, 1200 이상: 200 추가, 2000 이상: 100 추가
    xrangegap = ((xlimit >= 400) + (xlimit >= 800) * 2 + 
                 (xlimit >= 1200) * 4 + (xlimit >= 2000) * 2 + 1) * 50
    
    ax.set_xticks(np.arange(0, xrangemax + xrangegap, xrangegap))
    
    if highlimit != 0:
        ax.set_yticks(np.arange(lowlimit, highlimit, y_gap))
        ax.set_ylim(lowlimit, highlimit)
    
    graph_base_parameter(ax, xlabel, ylabel)
