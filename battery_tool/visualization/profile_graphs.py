"""
Battery Data Tool - Profile Graphs Module

Profile(충방전 곡선) 데이터 시각화 함수
원본: origin_datatool/BatteryDataTool.py (Lines 247-352)

📌 활용 스킬: matplotlib
"""

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from typing import Sequence, Union

from .graph_base import graph_base_parameter


def graph_step(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    lowlimit: float,
    highlimit: float,
    limitgap: float,
    xlabel: str,
    ylabel: str,
    tlabel: str
) -> None:
    """Step charge Profile 그래프.
    
    전기화학적 맥락:
        CC-CV 충전의 CV 구간에서 전류 감소 프로파일을 시각화합니다.
        X축: 시간 또는 용량
        Y축: 전류 (C-rate)
    
    Args:
        x: X축 데이터
        y: Y축 데이터
        ax: matplotlib Axes 객체
        lowlimit, highlimit: Y축 범위
        limitgap: Y축 눈금 간격
        xlabel, ylabel: 축 라벨
        tlabel: 범례 라벨
    """
    ax.plot(x, y, label=tlabel)
    ax.set_yticks(np.arange(lowlimit, highlimit, limitgap))
    ax.set_ylim(lowlimit, highlimit - limitgap)
    graph_base_parameter(ax, xlabel, ylabel)


def graph_continue(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    lowlimit: float,
    highlimit: float,
    limitgap: float,
    xlabel: str,
    ylabel: str,
    tlabel: str,
    marker_type: str = "-"
) -> None:
    """연속 그래프 (선/마커 선택).
    
    Args:
        x: X축 데이터
        y: Y축 데이터
        ax: matplotlib Axes 객체
        lowlimit, highlimit: Y축 범위
        limitgap: Y축 눈금 간격
        xlabel, ylabel: 축 라벨
        tlabel: 범례 라벨
        marker_type: "-"이면 선만, 그 외는 마커 포함
    """
    if marker_type == "-":
        ax.plot(x, y, label=tlabel)
    else:
        ax.plot(x, y, label=tlabel, marker='o', markersize=3)
    ax.set_yticks(np.arange(lowlimit, highlimit, limitgap))
    ax.set_ylim(lowlimit, highlimit - limitgap)
    graph_base_parameter(ax, xlabel, ylabel)


def graph_soc_continue(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    lowlimit: float,
    highlimit: float,
    limitgap: float,
    xlabel: str,
    ylabel: str,
    tlabel: str,
    marker_type: str = "-"
) -> None:
    """SOC 기준 연속 그래프.
    
    전기화학적 맥락:
        X축이 SOC(0-100%)로 고정된 그래프.
        SOC별 전압, 저항 등을 비교할 때 사용.
    
    Args:
        x: X축 데이터 (SOC, 0-100)
        y: Y축 데이터
        ax: matplotlib Axes 객체
        lowlimit, highlimit: Y축 범위
        limitgap: Y축 눈금 간격
        xlabel, ylabel: 축 라벨
        tlabel: 범례 라벨
        marker_type: "-"이면 선만, 그 외는 마커 포함
    """
    if marker_type == "-":
        ax.plot(x, y, label=tlabel)
    else:
        ax.plot(x, y, label=tlabel, marker='o', markersize=3)
    ax.set_xticks(np.arange(0, 110, 10))
    ax.set_yticks(np.arange(lowlimit, highlimit, limitgap))
    ax.set_ylim(lowlimit, highlimit - limitgap)
    graph_base_parameter(ax, xlabel, ylabel)


def graph_profile(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    xlowlimit: float,
    xhighlimit: float,
    xlimitgap: float,
    ylowlimit: float,
    yhighlimit: float,
    ylimitgap: float,
    xlabel: str,
    ylabel: str,
    tlabel: str
) -> None:
    """충방전 Profile 그래프.
    
    전기화학적 맥락:
        전압-용량 곡선 (V-Q curve)을 시각화합니다.
        - 충전: 용량 증가에 따른 전압 상승
        - 방전: 용량 증가에 따른 전압 하강
    
    Args:
        x: X축 데이터 (용량 또는 SOC)
        y: Y축 데이터 (전압)
        ax: matplotlib Axes 객체
        xlowlimit, xhighlimit: X축 범위
        xlimitgap: X축 눈금 간격
        ylowlimit, yhighlimit: Y축 범위
        ylimitgap: Y축 눈금 간격
        xlabel, ylabel: 축 라벨
        tlabel: 범례 라벨
    """
    ax.plot(x, y, label=tlabel)
    ax.set_xticks(np.arange(xlowlimit, xhighlimit, xlimitgap))
    ax.set_xlim(xlowlimit, xhighlimit - xlimitgap)
    ax.set_yticks(np.arange(ylowlimit, yhighlimit, ylimitgap))
    ax.set_ylim(ylowlimit, yhighlimit - ylimitgap)
    graph_base_parameter(ax, xlabel, ylabel)


def graph_soc_set(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    lowlimit: float,
    highlimit: float,
    limitgap: float,
    xlabel: str,
    ylabel: str,
    tlabel: str,
    xlimit: int
) -> None:
    """SOC 설정 Profile 그래프 (scatter).
    
    Args:
        x: X축 데이터
        y: Y축 데이터
        ax: matplotlib Axes 객체
        lowlimit, highlimit: Y축 범위
        limitgap: Y축 눈금 간격
        xlabel, ylabel: 축 라벨
        tlabel: 범례 라벨
        xlimit: 색상 선택 키
    """
    colors = {3: 'red', 4: 'blue', 5: 'green', 6: 'magenta', 7: 'cyan', 8: 'red', 9: 'red'}
    
    if xlimit == {0, 1, 2}:
        ax.scatter(x, y, label=tlabel, s=1)
    elif xlimit in colors:
        ax.scatter(x, y, label=tlabel, s=1, color=colors[xlimit])
    else:
        ax.scatter(x, y, label=tlabel, s=1)
    
    if limitgap != 0:
        ax.set_yticks(np.arange(lowlimit, highlimit, limitgap))
        ax.set_ylim(lowlimit, highlimit - limitgap)
    
    graph_base_parameter(ax, xlabel, ylabel)


def graph_soc_err(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    lowlimit: float,
    highlimit: float,
    limitgap: float,
    xlabel: str,
    ylabel: str,
    tlabel: str,
    xlimit: int
) -> None:
    """ECT SOC 에러 확인 그래프 (bar chart).
    
    전기화학적 맥락:
        ECT(Electronic Charge Tracker) 알고리즘의 SOC 추정 오차를
        SOC 구간별로 평균하여 시각화합니다.
    
    Args:
        x: SOC 값
        y: 오차 값
        ax: matplotlib Axes 객체
        lowlimit, highlimit: Y축 범위
        limitgap: Y축 눈금 간격
        xlabel, ylabel: 축 라벨
        tlabel: 범례 라벨
        xlimit: 색상 선택 키
    """
    colors = {3: 'red', 4: 'blue', 5: 'green', 6: 'magenta', 7: 'cyan', 8: 'red', 9: 'red'}
    
    # 5% 구간별 평균 계산
    df = pd.DataFrame({'x': x, 'y': abs(y)})
    grouped = df.groupby(df['x'] // 5).mean()
    index_x = grouped.index * 5
    
    ax.bar(index_x, grouped['y'], width=4, align='center', 
           label=tlabel, color=colors[xlimit], alpha=0.5)
    ax.set_yticks(np.arange(lowlimit, highlimit, limitgap))
    ax.set_ylim(lowlimit, highlimit - limitgap)
    ax.set_xlim(105, -5)
    ax.set_xticks(range(-5, 106, 5))
    
    graph_base_parameter(ax, xlabel, ylabel)


def graph_set_profile(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    y_llimit: float,
    y_hlimit: float,
    y_gap: float,
    xlabel: str,
    ylabel: str,
    tlabel: str,
    graphcolor: int,
    x_llimit: float,
    x_hlimit: float,
    x_gap: float
) -> None:
    """Set Profile 그래프 (scatter).
    
    Args:
        x: X축 데이터
        y: Y축 데이터
        ax: matplotlib Axes 객체
        y_llimit, y_hlimit: Y축 범위
        y_gap: Y축 눈금 간격
        xlabel, ylabel: 축 라벨
        tlabel: 범례 라벨
        graphcolor: 색상 인덱스 (1-5)
        x_llimit, x_hlimit: X축 범위
        x_gap: X축 눈금 간격
    """
    colors = {1: 'red', 2: 'blue', 3: 'green', 4: 'magenta', 5: 'cyan'}
    
    if graphcolor in colors:
        ax.scatter(x, y, label=tlabel, s=1, color=colors[graphcolor])
    else:
        ax.scatter(x, y, label=tlabel, s=1)
    
    if x_gap != 0:
        ax.set_xticks(np.arange(x_llimit, x_hlimit, x_gap))
        ax.set_xlim(x_llimit, x_hlimit - x_gap)
    if y_gap != 0:
        ax.set_yticks(np.arange(y_llimit, y_hlimit, y_gap))
        ax.set_ylim(y_llimit, y_hlimit - y_gap)
    
    graph_base_parameter(ax, xlabel, ylabel)


def graph_set_guide(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    y_llimit: float,
    y_hlimit: float,
    y_gap: float,
    xlabel: str,
    ylabel: str,
    tlabel: str,
    x_llimit: float,
    x_hlimit: float,
    x_gap: float
) -> None:
    """SOC 가이드 그래프 (점선).
    
    전기화학적 맥락:
        SOC 추정에 사용되는 참조 곡선 (OCV-SOC 관계)을
        점선으로 표시하여 실측 데이터와 비교합니다.
    
    Args:
        x: X축 데이터
        y: Y축 데이터
        ax: matplotlib Axes 객체
        y_llimit, y_hlimit: Y축 범위
        y_gap: Y축 눈금 간격
        xlabel, ylabel: 축 라벨
        tlabel: 범례 라벨
        x_llimit, x_hlimit: X축 범위
        x_gap: X축 눈금 간격
    """
    ax.plot(x, y, linestyle='dotted', color='red', label=tlabel)
    
    if x_gap != 0:
        ax.set_xticks(np.arange(x_llimit, x_hlimit, x_gap))
        ax.set_xlim(x_llimit, x_hlimit - x_gap)
    if y_gap != 0:
        ax.set_yticks(np.arange(y_llimit, y_hlimit, y_gap))
        ax.set_ylim(y_llimit, y_hlimit - y_gap)
    
    graph_base_parameter(ax, xlabel, ylabel)
