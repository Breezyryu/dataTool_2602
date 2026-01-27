"""
Battery Data Tool - Profile Logic Module

Profile 데이터 분석 비즈니스 로직

📌 활용 스킬: scientific-critical-thinking
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, List, Optional, Any

from battery_tool.data_processing import (
    toyo_chg_Profile_data,
    toyo_dchg_Profile_data,
    toyo_step_Profile_data,
    toyo_rate_Profile_data,
    pne_step_Profile_data,
    pne_rate_Profile_data,
)
from battery_tool.visualization import (
    graph_profile,
    graph_step,
)
from battery_tool.utils import check_cycler


def process_charge_profile(
    raw_file_path: str,
    cycle: int,
    mincapacity: float = 0,
    cutoff: float = 2.5,
    ini_rate: float = 0.2,
    smooth_degree: int = 0
) -> Tuple[float, Any]:
    """충전 Profile 처리.
    
    Args:
        raw_file_path: 데이터 경로
        cycle: 분석할 cycle 번호
        mincapacity: 정격 용량
        cutoff: 전압 하한
        ini_rate: 초기 C-rate
        smooth_degree: 평활화 정도
    
    Returns:
        (mincapacity, df) 튜플
    """
    is_pne = check_cycler(raw_file_path)
    
    if is_pne:
        # PNE는 충전 Profile 함수가 별도로 없어 step 사용
        return pne_step_Profile_data(raw_file_path, cycle, mincapacity, 
                                     cutoff, ini_rate)
    else:
        return toyo_chg_Profile_data(raw_file_path, cycle, mincapacity,
                                     cutoff, ini_rate, smooth_degree)


def process_discharge_profile(
    raw_file_path: str,
    cycle: int,
    mincapacity: float = 0,
    cutoff: float = 2.5,
    ini_rate: float = 0.2,
    smooth_degree: int = 0
) -> Tuple[float, Any]:
    """방전 Profile 처리.
    
    Args:
        raw_file_path: 데이터 경로
        cycle: 분석할 cycle 번호
        mincapacity: 정격 용량
        cutoff: 전압 하한
        ini_rate: 초기 C-rate
        smooth_degree: 평활화 정도
    
    Returns:
        (mincapacity, df) 튜플
    """
    is_pne = check_cycler(raw_file_path)
    
    if not is_pne:
        return toyo_dchg_Profile_data(raw_file_path, cycle, mincapacity,
                                       cutoff, ini_rate, smooth_degree)
    else:
        # PNE는 별도 구현 필요
        return (mincapacity, pd.DataFrame())


def process_step_charge_profile(
    raw_file_path: str,
    cycle: int,
    mincapacity: float = 0,
    cutoff: float = 0.05,
    ini_rate: float = 0.2
) -> Tuple[float, Any]:
    """Step 충전 Profile 처리.
    
    Args:
        raw_file_path: 데이터 경로
        cycle: 분석할 cycle 번호
        mincapacity: 정격 용량
        cutoff: 전류 하한 (C-rate)
        ini_rate: 초기 C-rate
    
    Returns:
        (mincapacity, df) 튜플
    """
    is_pne = check_cycler(raw_file_path)
    
    if is_pne:
        return pne_step_Profile_data(raw_file_path, cycle, mincapacity,
                                     cutoff, ini_rate)
    else:
        return toyo_step_Profile_data(raw_file_path, cycle, mincapacity,
                                      cutoff, ini_rate)


def create_profile_plot(
    df: Any,
    profile_type: str = "charge",
    title: str = ""
) -> plt.Figure:
    """Profile 그래프 생성.
    
    Args:
        df: Profile 데이터
        profile_type: 'charge' 또는 'discharge'
        title: 그래프 제목
    
    Returns:
        matplotlib Figure 객체
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
        nrows=2, ncols=2, figsize=(12, 8)
    )
    
    attr_name = 'Profile' if profile_type == 'charge' else 'Profile'
    if profile_type == 'step':
        attr_name = 'stepchg'
    
    if hasattr(df, attr_name):
        profile = getattr(df, attr_name)
        
        if not profile.empty and 'Vol' in profile.columns:
            # SOC vs Voltage
            ax1.plot(profile['SOC'], profile['Vol'], '-')
            ax1.set_xlabel('SOC')
            ax1.set_ylabel('Voltage (V)')
            ax1.grid(True, alpha=0.3)
            
            # Time vs Voltage
            ax2.plot(profile['TimeMin'], profile['Vol'], '-')
            ax2.set_xlabel('Time (min)')
            ax2.set_ylabel('Voltage (V)')
            ax2.grid(True, alpha=0.3)
            
            # dQ/dV (if available)
            if 'dQdV' in profile.columns:
                ax3.plot(profile['Vol'], profile['dQdV'], '-')
                ax3.set_xlabel('Voltage (V)')
                ax3.set_ylabel('dQ/dV')
                ax3.grid(True, alpha=0.3)
            
            # dV/dQ (if available)
            if 'dVdQ' in profile.columns:
                ax4.plot(profile['SOC'], profile['dVdQ'], '-')
                ax4.set_xlabel('SOC')
                ax4.set_ylabel('dV/dQ')
                ax4.grid(True, alpha=0.3)
    
    plt.suptitle(title, fontsize=12, fontweight='bold')
    plt.tight_layout()
    
    return fig
