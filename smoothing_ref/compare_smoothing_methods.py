"""
dV/dQ 스무딩 비교: 기존 diff vs 고급 (Wavelet + dMSMCD)
BatteryDataTool.py의 generate_simulation_full 방식과 동일하게 비교
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, './smoothing_ref')

from Lib_LKS_denoise import denoise, dMSMCD as slope

plt.rcParams["font.family"] = "Malgun gothic"
plt.rcParams["axes.unicode_minus"] = False

#########################################################################################
# 데이터 로드
#########################################################################################
def load_data(filepath):
    """CSV 파일 로드 (구분자 자동 감지)"""
    for sep in ["\t", ",", r"\s+"]:
        df = pd.read_csv(filepath, sep=sep, engine='python' if sep == r"\s+" else None,
                         skip_blank_lines=True, on_bad_lines='skip')
        if len(df.columns) >= 2:
            break
    df = df.iloc[:, :2].copy()
    df.columns = ["cap", "volt"]
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    return df

#########################################################################################
# 기존 방식: 단순 diff (BatteryDataTool.py 방식)
#########################################################################################
def calc_dvdq_basic(cap, volt, period=500):
    """기존 방식: diff(periods=period), BatteryDataTool generate_simulation_full과 동일"""
    df = pd.DataFrame({'cap': cap, 'volt': volt})
    dvdq = df.volt.diff(periods=period) / df.cap.diff(periods=period)
    return cap, dvdq.values

#########################################################################################
# 고급 방식: Wavelet + dMSMCD (Lib_LKS_denoise 방식)
#########################################################################################
def calc_dvdq_advanced(cap, volt, denoise_strength=3.5, Crate=0.2, slope_window=2):
    """고급 방식: Wavelet Denoise + dMSMCD slope, Lib_LKS_BatteryData 방식"""
    cap_arr = np.asarray(cap)
    volt_arr = np.asarray(volt)
    
    # dMSMCD 파라미터 계산
    dt = np.median(np.diff(cap_arr))  # cap 간격
    max_window = max(int(slope_window * 12 / Crate / dt), 1)
    
    # 전압 및 용량의 slope 계산
    volt_slope = slope(volt_arr, max_window)['median']
    cap_slope = slope(cap_arr, max_window)['median']
    
    # dV/dQ = dV/dt / dQ/dt
    dvdq = volt_slope / cap_slope
    
    # 디노이즈 적용
    dvdq_denoised = dvdq.copy()
    valid_idx = ~np.isnan(dvdq)
    if np.sum(valid_idx) > 20:
        dvdq_denoised[valid_idx] = denoise(dvdq[valid_idx], denoise_strength)
    
    return cap_arr, dvdq_denoised

#########################################################################################
# 메인: 비교 플롯
#########################################################################################
if __name__ == "__main__":
    # 파일 경로
    real_file = './smoothing_ref/dvdqraw/Gen4P 4905mAh HHP ATL 055CY - 복사본.txt'
    
    print("데이터 로드 중...")
    data = load_data(real_file)
    cap = data['cap'].values
    volt = data['volt'].values
    print(f"데이터 포인트: {len(cap)}")
    
    # 파라미터
    # period는 데이터 크기의 약 10% 또는 최대 500
    period = min(500, max(10, len(cap) // 10))
    print(f"기존 방식 period: {period}")
    
    denoise_strength = 3.5
    Crate = 0.2
    slope_window = 2
    
    print("기존 방식 (diff) 계산 중...")
    cap_basic, dvdq_basic = calc_dvdq_basic(cap, volt, period)
    
    print("고급 방식 (Wavelet+dMSMCD) 계산 중...")
    cap_adv, dvdq_adv = calc_dvdq_advanced(cap, volt, denoise_strength, Crate, slope_window)
    
    # 비교 플롯
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1) 원본 전압 곡선
    ax1 = axes[0, 0]
    ax1.plot(cap, volt, 'b-', linewidth=1)
    ax1.set_xlabel('Capacity (mAh)')
    ax1.set_ylabel('Voltage (V)')
    ax1.set_title('원본 전압 곡선')
    ax1.grid(True, alpha=0.3)
    
    # 2) dV/dQ 전체 비교
    ax2 = axes[0, 1]
    ax2.plot(cap_basic, dvdq_basic, 'b-', alpha=0.7, label=f'기존 diff (period={period})', linewidth=0.8)
    ax2.plot(cap_adv, dvdq_adv, 'r-', label='고급 (Wavelet+dMSMCD)', linewidth=1)
    ax2.set_xlabel('Capacity (mAh)')
    ax2.set_ylabel('dV/dQ (V/mAh)')
    ax2.set_title('dV/dQ 비교: 기존 vs 고급')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Y축 범위 자동 설정 (이상치 제외)
    valid_basic = dvdq_basic[~np.isnan(dvdq_basic)]
    valid_adv = dvdq_adv[~np.isnan(dvdq_adv)]
    
    print(f"기존 방식 유효 데이터: {len(valid_basic)} / {len(dvdq_basic)}")
    print(f"고급 방식 유효 데이터: {len(valid_adv)} / {len(dvdq_adv)}")
    
    if len(valid_basic) > 10 and len(valid_adv) > 10:
        y_min = max(np.percentile(valid_basic, 1), np.percentile(valid_adv, 1))
        y_max = min(np.percentile(valid_basic, 99), np.percentile(valid_adv, 99))
        ax2.set_ylim(y_min * 0.9, y_max * 1.1)
    
    # 3) dV/dQ 중앙 영역 확대
    ax3 = axes[1, 0]
    mid = len(cap) // 2
    rng = len(cap) // 4
    ax3.plot(cap_basic[mid-rng:mid+rng], dvdq_basic[mid-rng:mid+rng], 'b-', alpha=0.7, 
             label=f'기존 diff', linewidth=1)
    ax3.plot(cap_adv[mid-rng:mid+rng], dvdq_adv[mid-rng:mid+rng], 'r-', 
             label='고급 (Wavelet+dMSMCD)', linewidth=1.2)
    ax3.set_xlabel('Capacity (mAh)')
    ax3.set_ylabel('dV/dQ (V/mAh)')
    ax3.set_title('dV/dQ 중앙 영역 확대')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4) 노이즈 레벨 비교 (인접 포인트 차이의 표준편차)
    ax4 = axes[1, 1]
    noise_basic = np.nanstd(np.diff(valid_basic))
    noise_adv = np.nanstd(np.diff(valid_adv))
    
    bars = ax4.bar(['기존 diff', '고급 스무딩'], [noise_basic, noise_adv], 
                   color=['blue', 'red'], alpha=0.7)
    ax4.set_ylabel('노이즈 레벨')
    ax4.set_title('노이즈 비교 (dV/dQ 변동성)')
    
    for bar, val in zip(bars, [noise_basic, noise_adv]):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.02, 
                 f'{val:.2e}', ha='center', fontsize=10)
    
    improvement = (noise_basic - noise_adv) / noise_basic * 100
    ax4.text(0.5, 0.85, f'노이즈 감소율: {improvement:.1f}%', 
             transform=ax4.transAxes, ha='center', fontsize=12, 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('./smoothing_ref/dvdq_comparison_basic_vs_advanced.png', dpi=150)
    print("\n저장 완료: smoothing_ref/dvdq_comparison_basic_vs_advanced.png")
    plt.show()
    
    print(f"\n=== 결과 요약 ===")
    print(f"기존 방식 노이즈: {noise_basic:.6e}")
    print(f"고급 방식 노이즈: {noise_adv:.6e}")
    print(f"노이즈 감소율: {improvement:.1f}%")
