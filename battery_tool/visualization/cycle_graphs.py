"""
Battery Data Tool - Cycle Graphs Module

Cycle 데이터 시각화 함수
원본: BatteryDataTool.py (Lines 205-245)

"""

import numpy as np
from matplotlib.axes import Axes
from typing import Optional, Sequence, Union

from .graph_base import graph_base_parameter, graph_cycle_base


def graph_cycle(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    lowlimit: float,
    highlimit: float,
    ygap: float,
    xlabel: str,
    ylabel: str,
    tlabel: str,
    xscale: float,
    cyc_color: Union[str, int],
    overall_xlimit: float = 0
) -> None:
    """Cycle 그래프 그리기 (scatter plot, 채워진 마커).
    
    전기화학적 맥락:
        각 cycle의 측정값을 점으로 표시합니다.
        - 용량: 배터리 열화에 따라 감소 추세
        - 효율: 일반적으로 0.995~1.002 범위
        - 저항: 열화에 따라 증가 추세
    
    Args:
        x: X축 데이터 (Cycle 번호)
        y: Y축 데이터 (측정값)
        ax: matplotlib Axes 객체
        lowlimit: Y축 최소값
        highlimit: Y축 최대값
        ygap: Y축 눈금 간격
        xlabel: X축 라벨
        ylabel: Y축 라벨
        tlabel: 범례 라벨
        xscale: X축 최대값 (0이면 자동)
        cyc_color: 마커 색상 (0이면 기본색)
        overall_xlimit: 전체 X축 최소 한계
    """
    if cyc_color != 0:
        ax.scatter(x, y, label=tlabel, s=5, color=cyc_color)
    else:
        ax.scatter(x, y, label=tlabel, s=5)
    
    graph_cycle_base(x, ax, lowlimit, highlimit, ygap, xlabel, ylabel, xscale, overall_xlimit=0)


def graph_cycle_empty(
    x: Sequence,
    y: Sequence,
    ax: Axes,
    lowlimit: float,
    highlimit: float,
    ygap: float,
    xlabel: str,
    ylabel: str,
    tlabel: str,
    xscale: float,
    cyc_color: Union[str, int],
    overall_xlimit: float = 0
) -> None:
    """Cycle 그래프 그리기 (scatter plot, 빈 마커).
    
    채우기 없는 마커로 두 번째 데이터 시리즈를 구분하여 표시합니다.
    예: Eff2 (Charge/Discharge 효율), AvgV (평균 전압)
    
    Args:
        x: X축 데이터 (Cycle 번호)
        y: Y축 데이터 (측정값)
        ax: matplotlib Axes 객체
        lowlimit: Y축 최소값
        highlimit: Y축 최대값
        ygap: Y축 눈금 간격
        xlabel: X축 라벨
        ylabel: Y축 라벨
        tlabel: 범례 라벨
        xscale: X축 최대값 (0이면 자동)
        cyc_color: 마커 테두리 색상 (0이면 기본색)
        overall_xlimit: 전체 X축 최소 한계
    """
    if cyc_color != 0:
        ax.scatter(x, y, label=tlabel, s=8, edgecolors=cyc_color, facecolors='none')
    else:
        ax.scatter(x, y, label=tlabel, s=8, facecolors='none')
    
    graph_cycle_base(x, ax, lowlimit, highlimit, ygap, xlabel, ylabel, xscale, overall_xlimit=0)


def graph_output_cycle(
    df,
    xscale: float,
    ylimitlow: float,
    ylimithigh: float,
    irscale: float,
    lgnd: str,
    temp_lgnd: str,
    colorno: int,
    graphcolor: list,
    dcir,
    ax1: Axes,
    ax2: Axes,
    ax3: Axes,
    ax4: Axes,
    ax5: Axes,
    ax6: Axes
) -> None:
    """Cycle 데이터 전체 출력 (6개 그래프).
    
    전기화학적 맥락:
        배터리 수명 테스트의 핵심 지표들을 한 번에 시각화:
        - ax1: 방전 용량 비율 (Discharge Capacity Ratio)
        - ax2: 방전/충전 효율 (Coulombic Efficiency)
        - ax3: 온도
        - ax4: DC-IR (내부저항)
        - ax5: 충전/방전 효율
        - ax6: 휴지 전압, 평균 전압
    
    Args:
        df: Cycle 데이터가 포함된 DataFrame (df.NewData)
        xscale: X축 최대값
        ylimitlow, ylimithigh: Y축 범위 (용량)
        irscale: 저항 스케일 배율
        lgnd, temp_lgnd: 범례 라벨
        colorno: 색상 인덱스
        graphcolor: 색상 팔레트 리스트
        dcir: DC-IR 체크박스 위젯
        ax1-ax6: matplotlib Axes 객체들
    """
    # 방전 용량 비율
    graph_cycle(df.NewData.index, df.NewData.Dchg, ax1, ylimitlow, ylimithigh, 0.05,
                "Cycle", "Discharge Capacity Ratio", temp_lgnd, xscale, graphcolor[colorno % 9])
    
    # 방전/충전 효율 (쿨롱 효율)
    graph_cycle(df.NewData.index, df.NewData.Eff, ax2, 0.992, 1.004, 0.002,
                "Cycle", "Discharge/Charge Efficiency", temp_lgnd, xscale, graphcolor[colorno % 9])
    
    # 온도
    graph_cycle(df.NewData.index, df.NewData.Temp, ax3, 0, 50, 5,
                "Cycle", "Temperature (℃)", temp_lgnd, xscale, graphcolor[colorno % 9])
    
    # 휴지 종료 전압
    graph_cycle(df.NewData.index, df.NewData.RndV, ax6, 3.00, 4.00, 0.1,
                "Cycle", "Rest End Voltage (V)", "", xscale, graphcolor[colorno % 9])
    
    # 충전/방전 효율 (빈 마커)
    graph_cycle_empty(df.NewData.index, df.NewData.Eff2, ax5, 0.996, 1.008, 0.002,
                      "Cycle", "Charge/Discharge Efficiency", temp_lgnd, xscale, graphcolor[colorno % 9])
    
    # 평균 전압 (빈 마커)
    graph_cycle_empty(df.NewData.index, df.NewData.AvgV, ax6, 3.00, 4.00, 0.1,
                      "Cycle", "Average/Rest Voltage (V)", temp_lgnd, xscale, graphcolor[colorno % 9])
    
    # DC-IR
    if dcir.isChecked() and hasattr(df.NewData, "dcir2"):
        graph_cycle_empty(df.NewData.index, df.NewData.soc70_dcir, ax4, 0, 120.0 * irscale, 20 * irscale,
                          "Cycle", "RSS/ 1s DC-IR (mΩ)", "", xscale, graphcolor[colorno % 9])
        graph_cycle(df.NewData.index, df.NewData.soc70_rss_dcir, ax4, 0, 120.0 * irscale, 20 * irscale,
                    "Cycle", "RSS/ 1s DC-IR (mΩ)", temp_lgnd, xscale, graphcolor[colorno % 9])
    else:
        graph_cycle(df.NewData.index, df.NewData.dcir, ax4, 0, 120.0 * irscale, 20 * irscale,
                    "Cycle", "DC-IR (mΩ)", temp_lgnd, xscale, graphcolor[colorno % 9])
    
    colorno = colorno % 9 + 1
