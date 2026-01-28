"""
Battery Data Tool - dV/dQ Analysis Module

dV/dQ (Incremental Voltage) 분석 함수
원본: origin_datatool/BatteryDataTool.py (Lines 409-441)

    dV/dQ 분석은 배터리 열화 메커니즘을 정량적으로 분석하는 핵심 기법입니다.
    
    - dV/dQ = 전압의 미분값 / 용량의 미분값
    - 피크 위치: 전극 material의 상전이 반영
    - 피크 이동: Li 손실 (slip parameter)
    - 피크 강도 변화: 활물질 손실 (mass parameter)
"""

import numpy as np
import pandas as pd
from typing import Tuple


def generate_params(
    ca_mass_min: float,
    ca_mass_max: float,
    ca_slip_min: float,
    ca_slip_max: float,
    an_mass_min: float,
    an_mass_max: float,
    an_slip_min: float,
    an_slip_max: float
) -> Tuple[float, float, float, float]:
    """랜덤 열화 파라미터 생성.
    
    Monte Carlo 시뮬레이션을 위한 랜덤 파라미터 세트 생성.
    
    전기화학적 맥락:
        - ca_mass: 양극 활물질 잔여량 (1.0 = 초기 상태)
        - ca_slip: 양극 슬립 (Li 손실로 인한 전위 이동)
        - an_mass: 음극 활물질 잔여량 (1.0 = 초기 상태)
        - an_slip: 음극 슬립 (Li 손실로 인한 전위 이동)
    
    Args:
        ca_mass_min, ca_mass_max: 양극 mass 범위
        ca_slip_min, ca_slip_max: 양극 slip 범위
        an_mass_min, an_mass_max: 음극 mass 범위
        an_slip_min, an_slip_max: 음극 slip 범위
    
    Returns:
        (ca_mass, ca_slip, an_mass, an_slip) 튜플
    """
    ca_mass = np.random.uniform(ca_mass_min, ca_mass_max)
    ca_slip = np.random.uniform(ca_slip_min, ca_slip_max)
    an_mass = np.random.uniform(an_mass_min, an_mass_max)
    an_slip = np.random.uniform(an_slip_min, an_slip_max)
    return ca_mass, ca_slip, an_mass, an_slip


def generate_simulation_full(
    ca_ccv_raw: pd.DataFrame,
    an_ccv_raw: pd.DataFrame,
    real_raw: pd.DataFrame,
    ca_mass: float,
    ca_slip: float,
    an_mass: float,
    an_slip: float,
    full_cell_max_cap: float,
    rated_cap: float,
    full_period: int
) -> pd.DataFrame:
    """Full cell dV/dQ 시뮬레이션 데이터 생성.
    
    전기화학적 맥락:
        Full cell 전압은 양극/음극 전위의 차이입니다:
        V_cell = V_cathode(Q) - V_anode(Q)
        
        열화에 따른 전극 변화를 시뮬레이션합니다:
        
        1. Mass 파라미터 (활물질 손실):
           - ca_mass < 1.0: 양극 용량 감소 → 피크 강도 감소
           - an_mass < 1.0: 음극 용량 감소 → 피크 강도 감소
           
        2. Slip 파라미터 (Li 손실):
           - ca_slip > 0: 양극 곡선 좌측 이동
           - an_slip > 0: 음극 곡선 좌측 이동
        
        물리적 해석:
        - SEI 성장: 주로 an_slip 증가 (Li 소모)
        - 양극 구조 붕괴: ca_mass 감소
        - 음극 리튬 도금: an_mass, an_slip 모두 영향
    
    Args:
        ca_ccv_raw: 양극 half cell 데이터 (ca_cap, ca_volt 컬럼)
        an_ccv_raw: 음극 half cell 데이터 (an_cap, an_volt 컬럼)
        real_raw: 실측 full cell 데이터 (real_cap, real_volt 컬럼)
        ca_mass: 양극 질량 보정 계수 (1.0 = 초기 상태)
        ca_slip: 양극 슬립 (mAh)
        an_mass: 음극 질량 보정 계수 (1.0 = 초기 상태)
        an_slip: 음극 슬립 (mAh)
        full_cell_max_cap: Full cell 최대 용량 (mAh)
        rated_cap: 정격 용량 (mAh)
        full_period: 미분 계산 주기
    
    Returns:
        시뮬레이션 결과 DataFrame:
        - full_cap: 용량 (%)
        - an_volt: 음극 전압
        - ca_volt: 양극 전압
        - full_volt: 시뮬레이션 full cell 전압
        - real_volt: 실측 full cell 전압
        - an_dvdq: 음극 dV/dQ
        - ca_dvdq: 양극 dV/dQ
        - real_dvdq: 실측 dV/dQ
        - full_dvdq: 시뮬레이션 full cell dV/dQ
    
    Example:
        >>> simul = generate_simulation_full(
        ...     ca_data, an_data, real_data,
        ...     ca_mass=0.95, ca_slip=5.0,
        ...     an_mass=0.98, an_slip=10.0,
        ...     full_cell_max_cap=4500, rated_cap=4500, full_period=5
        ... )
        >>> # 열화 후 dV/dQ 피크 이동 확인
        >>> peak_shift = simul['ca_dvdq'].idxmax() - initial_peak
    """
    # 용량 보정: 활물질 손실 및 Li 손실 반영
    ca_ccv_raw = ca_ccv_raw.copy()
    an_ccv_raw = an_ccv_raw.copy()
    
    ca_ccv_raw['ca_cap_new'] = ca_ccv_raw['ca_cap'] * ca_mass - ca_slip
    an_ccv_raw['an_cap_new'] = an_ccv_raw['an_cap'] * an_mass - an_slip
    
    # 공통 용량 기준으로 전압 interpolation
    simul_full_cap = np.arange(0, full_cell_max_cap, 0.1)
    simul_full_ca_volt = np.interp(simul_full_cap, ca_ccv_raw['ca_cap_new'], ca_ccv_raw['ca_volt'])
    simul_full_an_volt = np.interp(simul_full_cap, an_ccv_raw['an_cap_new'], an_ccv_raw['an_volt'])
    simul_full_real_volt = np.interp(simul_full_cap, real_raw['real_cap'], real_raw['real_volt'])
    
    # Full cell 전압 = 양극 - 음극
    simul_full_volt = simul_full_ca_volt - simul_full_an_volt
    
    # 결과 DataFrame 생성
    simul_full = pd.DataFrame({
        "full_cap": simul_full_cap,
        "an_volt": simul_full_an_volt,
        "ca_volt": simul_full_ca_volt,
        "full_volt": simul_full_volt,
        "real_volt": simul_full_real_volt
    })
    simul_full = simul_full.drop(simul_full.index[-1])
    
    # 용량을 백분율로 변환
    simul_full['full_cap'] = simul_full['full_cap'] / rated_cap * 100
    
    # dV/dQ 미분값 계산
    simul_full["an_dvdq"] = (simul_full['an_volt'].diff(periods=full_period) / 
                             simul_full['full_cap'].diff(periods=full_period))
    simul_full["ca_dvdq"] = (simul_full['ca_volt'].diff(periods=full_period) / 
                             simul_full['full_cap'].diff(periods=full_period))
    simul_full["real_dvdq"] = (simul_full['real_volt'].diff(periods=full_period) / 
                               simul_full['full_cap'].diff(periods=full_period))
    simul_full["full_dvdq"] = simul_full["ca_dvdq"] - simul_full["an_dvdq"]
    
    return simul_full
