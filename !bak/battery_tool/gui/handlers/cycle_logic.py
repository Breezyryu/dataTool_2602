"""
Battery Data Tool - Cycle Logic Module

Cycle 데이터 분석 비즈니스 로직
GUI 핸들러에서 사용되는 핵심 함수들

📌 활용 스킬: scientific-critical-thinking
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, List, Optional, Any

# 상대 import
from battery_tool.data_processing import (
    toyo_cycle_data,
    pne_cycle_data,
)
from battery_tool.visualization import (
    graph_cycle,
    graph_output_cycle,
    output_fig,
)
from battery_tool.utils import check_cycler, name_capacity


def process_cycle_data(
    raw_file_path: str,
    mincapacity: float,
    ini_crate: float = 0.2,
    chkir: bool = False,
    chkir2: bool = False,
    mkdcir: bool = False
) -> Tuple[float, Any]:
    """Cycle 데이터 처리 통합 함수.
    
    충방전기 종류에 따라 적절한 데이터 처리 함수를 호출합니다.
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        mincapacity: 정격 용량 (0이면 자동)
        ini_crate: 첫 cycle C-rate
        chkir: DCIR 체크 여부
        chkir2: 연속 DCIR 체크
        mkdcir: 복합 DCIR 여부
    
    Returns:
        (mincapacity, df) 튜플
    """
    is_pne = check_cycler(raw_file_path)
    
    if is_pne:
        return pne_cycle_data(raw_file_path, mincapacity, ini_crate, 
                             chkir, chkir2, mkdcir)
    else:
        return toyo_cycle_data(raw_file_path, mincapacity, ini_crate, chkir)


def process_folder_cycles(
    folder_path: str,
    mincapacity: float = 0,
    ini_crate: float = 0.2,
    chkir: bool = False
) -> List[Tuple[str, float, Any]]:
    """폴더 내 모든 채널의 Cycle 데이터 처리.
    
    Args:
        folder_path: 상위 폴더 경로
        mincapacity: 정격 용량
        ini_crate: 첫 cycle C-rate
        chkir: DCIR 체크 여부
    
    Returns:
        [(channel_name, mincapacity, df), ...] 리스트
    """
    results = []
    
    if os.path.isdir(folder_path):
        subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir()]
        
        for subfolder in subfolders:
            channel_name = os.path.basename(subfolder)
            try:
                cap, df = process_cycle_data(
                    subfolder, mincapacity, ini_crate, chkir
                )
                results.append((channel_name, cap, df))
            except Exception as e:
                print(f"Error processing {channel_name}: {e}")
                continue
    
    return results


def create_cycle_plot(
    df: Any,
    mincapacity: float,
    xscale: float = 1.0,
    ylimit_low: float = 0.7,
    ylimit_high: float = 1.05,
    irscale: float = 0.01,
    title: str = "",
    graphcolor: List[str] = None,
    colorno: int = 0
) -> plt.Figure:
    """Cycle 데이터 6-panel 그래프 생성.
    
    Args:
        df: 처리된 Cycle 데이터 (df.NewData 포함)
        mincapacity: 정격 용량
        xscale: X축 스케일
        ylimit_low: Y축 하한
        ylimit_high: Y축 상한
        irscale: IR 스케일
        title: 그래프 제목
        graphcolor: 색상 리스트
        colorno: 시작 색상 번호
    
    Returns:
        matplotlib Figure 객체
    """
    if graphcolor is None:
        graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(
        nrows=2, ncols=3, figsize=(14, 8)
    )
    
    if hasattr(df, 'NewData') and not df.NewData.empty:
        dcir = df.NewData.get('dcir', pd.Series([0]))
        
        graph_output_cycle(
            df, xscale, ylimit_low, ylimit_high, irscale,
            title, title, colorno, graphcolor, dcir,
            ax1, ax2, ax3, ax4, ax5, ax6
        )
        
        plt.suptitle(title, fontsize=15, fontweight='bold')
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
    
    return fig


def extract_cycle_summary(df: Any) -> pd.DataFrame:
    """Cycle 데이터 요약 추출.
    
    Args:
        df: 처리된 Cycle 데이터
    
    Returns:
        요약 DataFrame (Cycle, Dchg, Eff, Temp, dcir 컬럼)
    """
    if hasattr(df, 'NewData') and not df.NewData.empty:
        summary_cols = ['Dchg', 'Eff', 'Temp']
        if 'dcir' in df.NewData.columns:
            summary_cols.append('dcir')
        
        summary = df.NewData[summary_cols].copy()
        summary.index.name = 'Cycle'
        return summary
    
    return pd.DataFrame()
