"""
dV/dQ Fitting 스무딩 옵션 비교 (Basic vs Advanced A vs Advanced B)
"""
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, 'origin_datatool_dev')) # BatteryDataTool 경로
sys.path.append(current_dir) # smoothing_ref 경로 (Lib_LKS_denoise)

# BatteryDataTool에서 함수 import
# 주의: BatteryDataTool 내부에서 PyQT 등을 import하므로 GUI 환경이 없으면 에러 날 수 있으나, 
# generate_simulation_full 함수만 필요하므로 try-except로 감싸거나 해당 파일만 import 시도
try:
    from BatteryDataTool import generate_simulation_full, name_capacity
except ImportError:
    # BatteryDataTool.py가 GUI 의존성이 강할 경우, 해당 함수만 복사해서 테스트하거나
    # GUI 의존성 부분을 mock 처리해야 함. 
    # 여기서는 간단히 sys.path 문제일 수 있으므로 다시 시도
    sys.path.append(os.path.join(parent_dir, 'origin_datatool'))
    from BatteryDataTool import generate_simulation_full, name_capacity

plt.rcParams["font.family"] = "Malgun gothic"
plt.rcParams["axes.unicode_minus"] = False

def load_data(filepath):
    for sep in ["\t", ",", r"\s+"]:
        df = pd.read_csv(filepath, sep=sep, engine='python' if sep == r"\s+" else None,
                         skip_blank_lines=True, on_bad_lines='skip')
        if len(df.columns) >= 2:
            break
    df = df.iloc[:, :2].copy()
    df.columns = ["cap", "volt"]
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    return df

def run_comparison():
    # 1. 데이터 로드 (Fullcell, Anode, Cathode)
    print("데이터 로딩 중...")
    try:
        real_raw = load_data('./smoothing_ref/dvdqraw/Gen4P 4905mAh HHP ATL 055CY - 복사본.txt')
        real_raw.columns = ["real_cap", "real_volt"]
        
        an_ccv_raw = load_data('./smoothing_ref/dvdqraw/S25_291_anode_dchg_02C - 복사본.txt')
        an_ccv_raw.columns = ["an_cap", "an_volt"]
        
        ca_ccv_raw = load_data('./smoothing_ref/dvdqraw/S25_291_cathode_dchg_02C - 복사본.txt')
        ca_ccv_raw.columns = ["ca_cap", "ca_volt"]
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        return

    # 2. 파라미터 설정 (임의의 합리적인 값)
    full_cell_max_cap = 4905 # mAh
    rated_cap = 4905
    full_period = 500 # Basic 방식 window
    
    # 초기 파라미터 추정
    ca_mass = full_cell_max_cap / ca_ccv_raw.ca_cap.max()
    an_mass = full_cell_max_cap / an_ccv_raw.an_cap.max()
    ca_slip = 10
    an_slip = 10

    print(f"파라미터: Mass(Ca={ca_mass:.3f}, An={an_mass:.3f}), Slip(Ca={ca_slip}, An={an_slip})")

    # 3. 3가지 모드 실행
    modes = ['basic', 'advanced_A', 'advanced_B']
    results = {}
    
    for mode in modes:
        print(f"실행 중: {mode}...")
        # 원본 데이터 보존을 위해 copy 사용
        simul = generate_simulation_full(
            ca_ccv_raw.copy(), an_ccv_raw.copy(), real_raw.copy(),
            ca_mass, ca_slip, an_mass, an_slip,
            full_cell_max_cap, rated_cap, full_period,
            smoothing_mode=mode, denoise_strength=3.5, slope_window=2
        )
        results[mode] = simul

    # 4. 결과 비교 플롯
    fig, axes = plt.subplots(3, 1, figsize=(14, 15))
    
    # 그래프 1: dV/dQ (Full Cell)
    ax = axes[0]
    ax.plot(results['basic'].full_cap, results['basic'].full_dvdq, 'k-', alpha=0.3, label='Basic (diff)', linewidth=1)
    ax.plot(results['advanced_A'].full_cap, results['advanced_A'].full_dvdq, 'r-', alpha=0.8, label='Option A (Pre-process)', linewidth=1.2)
    ax.plot(results['advanced_B'].full_cap, results['advanced_B'].full_dvdq, 'b--', alpha=0.8, label='Option B (Post-process)', linewidth=1.2)
    ax.set_title("Full Cell dV/dQ Comparison")
    ax.set_ylim(-0.01, 0.01)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 그래프 2: dV/dQ (Anode) - 노이즈가 많은 부분
    ax = axes[1]
    ax.plot(results['basic'].full_cap, results['basic'].an_dvdq, 'k-', alpha=0.3, label='Basic', linewidth=1)
    ax.plot(results['advanced_A'].full_cap, results['advanced_A'].an_dvdq, 'r-', alpha=0.8, label='Option A', linewidth=1.2)
    ax.plot(results['advanced_B'].full_cap, results['advanced_B'].an_dvdq, 'b--', alpha=0.8, label='Option B', linewidth=1.2)
    ax.set_title("Anode dV/dQ Comparison")
    ax.set_ylim(-0.005, 0.005)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 그래프 3: Noise Level 비교 (Bar Chart)
    ax = axes[2]
    noise_levels = []
    for mode in modes:
        dvdq = results[mode].full_dvdq.values
        # NaN 제거 및 미분(노이즈 성분)
        valid = dvdq[~np.isnan(dvdq) & ~np.isinf(dvdq)]
        if len(valid) > 10:
            noise = np.std(np.diff(valid))
            noise_levels.append(noise)
        else:
            noise_levels.append(0)
    
    ax.bar(modes, noise_levels, color=['gray', 'red', 'blue'], alpha=0.7)
    ax.set_title("Noise Level (Std of diff(dV/dQ))")
    for i, v in enumerate(noise_levels):
        ax.text(i, v, f"{v:.2e}", ha='center', va='bottom')

    plt.tight_layout()
    save_path = './smoothing_ref/comparison_fitting_options.png'
    plt.savefig(save_path)
    print(f"저장 완료: {save_path}")
    # plt.show()

if __name__ == "__main__":
    run_comparison()
