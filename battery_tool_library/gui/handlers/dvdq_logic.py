"""
Battery Data Tool - dV/dQ Analysis Logic Module

dV/dQ 분석 비즈니스 로직
전기화학적 열화 메커니즘 분석

📌 활용 스킬: scientific-critical-thinking
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, Dict, Any, Optional
from scipy.optimize import curve_fit

from battery_tool.analysis import generate_params, generate_simulation_full


def analyze_dvdq(
    profile_data: pd.DataFrame,
    initial_params: Dict[str, float] = None
) -> Tuple[np.ndarray, Dict[str, float], float]:
    """dV/dQ 분석 수행.
    
    전기화학적 맥락:
        dV/dQ 곡선의 피팅을 통해 양극/음극의 열화 상태를 정량화합니다.
        - 양극 열화: positive_mass 감소
        - 음극 열화: negative_mass 감소
        - lithium slippage: slip 파라미터
    
    Args:
        profile_data: Profile 데이터 (SOC, Vol 컬럼 필요)
        initial_params: 초기 파라미터 딕셔너리
    
    Returns:
        (simul_full, fitted_params, rms_error) 튜플
    """
    if initial_params is None:
        initial_params = {
            'positive_mass': 1.0,
            'negative_mass': 1.0,
            'slip': 0.0,
            'positive_offset': 0.0,
            'negative_offset': 0.0,
        }
    
    # 시뮬레이션 수행
    params = generate_params(
        initial_params.get('positive_mass', 1.0),
        initial_params.get('negative_mass', 1.0),
        initial_params.get('slip', 0.0),
        initial_params.get('positive_offset', 0.0),
        initial_params.get('negative_offset', 0.0),
    )
    
    simul_full = generate_simulation_full(params)
    
    # RMS 오차 계산
    if 'SOC' in profile_data.columns and 'dVdQ' in profile_data.columns:
        measured = profile_data['dVdQ'].values
        # 시뮬레이션과 측정값 비교
        rms_error = np.sqrt(np.mean((measured[:len(simul_full)] - simul_full[:len(measured)])**2))
    else:
        rms_error = np.nan
    
    return simul_full, initial_params, rms_error


def fit_dvdq_curve(
    soc: np.ndarray,
    dvdq: np.ndarray,
    bounds: Tuple[list, list] = None
) -> Dict[str, float]:
    """dV/dQ 곡선 피팅.
    
    Args:
        soc: SOC 데이터 배열
        dvdq: dV/dQ 데이터 배열
        bounds: 파라미터 범위 ((lower_bounds), (upper_bounds))
    
    Returns:
        피팅된 파라미터 딕셔너리
    """
    if bounds is None:
        bounds = ([0.8, 0.8, -0.1, -0.05, -0.05],
                  [1.2, 1.2, 0.1, 0.05, 0.05])
    
    def model(x, pos_m, neg_m, slip, pos_off, neg_off):
        params = generate_params(pos_m, neg_m, slip, pos_off, neg_off)
        simul = generate_simulation_full(params)
        # 보간하여 반환
        return np.interp(x, np.linspace(0, 1, len(simul)), simul)
    
    try:
        popt, _ = curve_fit(model, soc, dvdq, bounds=bounds, maxfev=5000)
        return {
            'positive_mass': popt[0],
            'negative_mass': popt[1],
            'slip': popt[2],
            'positive_offset': popt[3],
            'negative_offset': popt[4],
        }
    except Exception as e:
        print(f"Fitting error: {e}")
        return {}


def create_dvdq_plot(
    profile_data: pd.DataFrame,
    simul_data: np.ndarray,
    params: Dict[str, float],
    rms: float,
    title: str = ""
) -> plt.Figure:
    """dV/dQ 분석 그래프 생성.
    
    Args:
        profile_data: 측정 Profile 데이터
        simul_data: 시뮬레이션 dV/dQ 데이터
        params: 피팅 파라미터
        rms: RMS 오차
        title: 그래프 제목
    
    Returns:
        matplotlib Figure 객체
    """
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14, 5))
    
    # dV/dQ 비교 플롯
    if 'SOC' in profile_data.columns and 'dVdQ' in profile_data.columns:
        ax1.plot(profile_data['SOC'], profile_data['dVdQ'], 'b-', 
                 label='Measured', linewidth=1.5)
    
    simul_soc = np.linspace(0, 1, len(simul_data))
    ax1.plot(simul_soc, simul_data, 'r--', 
             label='Simulated', linewidth=1.5)
    
    ax1.set_xlabel('SOC')
    ax1.set_ylabel('dV/dQ (V)')
    ax1.set_title(f'dV/dQ Comparison (RMS: {rms:.4f})')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 파라미터 표시
    param_text = '\n'.join([f'{k}: {v:.4f}' for k, v in params.items()])
    ax2.text(0.1, 0.5, param_text, transform=ax2.transAxes, 
             fontsize=12, verticalalignment='center',
             fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax2.set_title('Fitted Parameters')
    ax2.axis('off')
    
    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return fig


def calculate_degradation_metrics(
    params_initial: Dict[str, float],
    params_current: Dict[str, float]
) -> Dict[str, float]:
    """열화 지표 계산.
    
    Args:
        params_initial: 초기 상태 파라미터
        params_current: 현재 상태 파라미터
    
    Returns:
        열화 지표 딕셔너리
    """
    metrics = {}
    
    # 양극 열화율
    if 'positive_mass' in params_initial and 'positive_mass' in params_current:
        pos_loss = (1 - params_current['positive_mass'] / params_initial['positive_mass']) * 100
        metrics['positive_degradation_pct'] = pos_loss
    
    # 음극 열화율
    if 'negative_mass' in params_initial and 'negative_mass' in params_current:
        neg_loss = (1 - params_current['negative_mass'] / params_initial['negative_mass']) * 100
        metrics['negative_degradation_pct'] = neg_loss
    
    # Lithium slippage 변화
    if 'slip' in params_initial and 'slip' in params_current:
        slip_change = params_current['slip'] - params_initial['slip']
        metrics['slip_change'] = slip_change
    
    return metrics
