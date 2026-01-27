"""
Battery Data Tool - DCIR Graphs Module

DC 내부저항(DC-IR) 그래프 시각화 함수
원본: origin_datatool/BatteryDataTool.py (Lines 275-290)

📌 활용 스킬: matplotlib, scientific-critical-thinking
"""

import numpy as np
from matplotlib.axes import Axes
from typing import Sequence

from .graph_base import graph_base_parameter


def graph_dcir(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    xlabel: str,
    ylabel: str,
    tlabel: str,
    marker_type: str = "-"
) -> None:
    """OCV 기반 DCIR 그래프.
    
    전기화학적 맥락:
        DC-IR (Direct Current Internal Resistance)는 배터리 열화의 
        주요 지표입니다. 전압 강하와 전류로 계산됩니다.
        
        DCIR = ΔV / ΔI
        
        DCIR 증가 원인:
        - SEI 성장 (Li 소모)
        - 활물질 열화 (구조 변화)
        - 전해액 분해
        - 전극/집전체 접촉 저항 증가
    
    Args:
        x: X축 데이터 (Cycle 또는 시간)
        y: Y축 데이터 (DCIR, mΩ)
        ax: matplotlib Axes 객체
        xlabel: X축 라벨
        ylabel: Y축 라벨
        tlabel: 범례 라벨
        marker_type: "-"이면 선만, 그 외는 마커 포함
    """
    if marker_type == "-":
        ax.plot(x, y, label=tlabel)
    else:
        ax.plot(x, y, label=tlabel, marker='o', markersize=3)
    
    graph_base_parameter(ax, xlabel, ylabel)


def graph_soc_dcir(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    xlabel: str,
    ylabel: str,
    tlabel: str,
    marker_type: str = "-"
) -> None:
    """SOC별 DCIR 그래프.
    
    전기화학적 맥락:
        SOC에 따른 DCIR 변화를 보여줍니다.
        일반적으로:
        - 낮은 SOC: 음극 전위 상승으로 저항 증가
        - 높은 SOC: 양극 구조 변화로 저항 증가
        - 중간 SOC: 상대적으로 낮은 저항
    
    Args:
        x: X축 데이터 (SOC, 0-100%)
        y: Y축 데이터 (DCIR, mΩ)
        ax: matplotlib Axes 객체
        xlabel: X축 라벨
        ylabel: Y축 라벨
        tlabel: 범례 라벨
        marker_type: "-"이면 선만, 그 외는 마커 포함
    """
    if marker_type == "-":
        ax.plot(x, y, label=tlabel)
    else:
        ax.plot(x, y, label=tlabel, marker='o', markersize=3)
    
    ax.set_xticks(np.arange(0, 110, 10))
    graph_base_parameter(ax, xlabel, ylabel)
