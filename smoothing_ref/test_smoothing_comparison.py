"""
dV/dQ 스무딩 비교 테스트 스크립트
기존 diff 방식 vs 고급 스무딩 (Wavelet + dMSMCD) 비교
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pywt

# 한글 폰트 설정
plt.rcParams["font.family"] = "Malgun gothic"
plt.rcParams["axes.unicode_minus"] = False

#########################################################################################
# Wavelet Denoising 함수
#########################################################################################
def WLD(y, denoise_strength=1.0, wavelet='bior6.8', mode='soft'):
    y_val = np.asarray(y).copy()
    y_val_copy = y_val[1:].copy()
    y_val_pad = np.pad(y_val_copy, 50, mode='edge')

    rolls = []
    for i in range(10):
        y_val_roll = np.roll(y_val_pad, i-5)
        coeffs = pywt.wavedec(y_val_roll, wavelet)
        detail = coeffs[-1]
        sigma = np.median(np.abs(detail - np.median(detail))) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(len(y_val))) * denoise_strength

        new_coeffs = [coeffs[0]]
        for j in range(1, len(coeffs)):
            new_coeffs.append(pywt.threshold(coeffs[j], threshold, mode=mode))

        y_denoised_roll = pywt.waverec(new_coeffs, wavelet)
        if len(y_denoised_roll) > len(y_val_roll):
            y_denoised_roll = y_denoised_roll[:len(y_val_roll)]
        elif len(y_denoised_roll) < len(y_val_roll):
            y_denoised_roll = np.pad(y_denoised_roll, (0, len(y_val_roll)-len(y_denoised_roll)), mode='edge')

        y_val_unroll = np.roll(y_denoised_roll, -(i-5))
        rolls.append(y_val_unroll)

    rolls = np.array(rolls)
    y_denoised = y_val.copy()
    y_denoised[1:] = np.median(rolls, axis=0)[50:-50]
    return y_denoised

def dvdq_denoise(y, denoise_strength=1.0):
    ws1 = ['bior', 'rbio']
    ws2 = ['2.6', '2.8', '3.7', '3.9', '6.8']
    ws = [w1 + w2 for w1 in ws1 for w2 in ws2]
    y_val = np.asarray(y).copy()
    y_denoised = np.nanmedian(np.array([WLD(y_val.copy(), denoise_strength, w) for w in ws]), axis=0)
    return y_denoised

def dMSMCD(y, max_window):
    y_val = np.asarray(y).copy()
    n = len(y_val)
    slopes_list = []
    v_padded = np.pad(y_val, pad_width=1, mode='edge')
    interpolated_values = (v_padded[:-1] + v_padded[1:]) / 2

    for i in range(max_window):
        slope = np.full(n, np.nan, dtype=np.float64)
        if i % 2 == 0:
            j = (i + 1) // 2
            slope[(j+1):-(j+1)] = ((interpolated_values[(i+1):] - interpolated_values[:-(i+1)]) / (i+1))[1:-1]
            slopes_list.append(slope)
    
    slopes_array = np.stack(slopes_list, axis=1)
    median_slope = np.nanmedian(slopes_array, axis=1)
    return {'median': median_slope, 'all': slopes_array}

#########################################################################################
# 데이터 로드
#########################################################################################
def load_dvdq_file(filepath):
    """CSV 파일 로드 (구분자 자동 감지, 헤더 자동 처리)"""
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
# dV/dQ 계산 함수
#########################################################################################
def calc_dvdq_basic(cap, volt, period=500):
    """기존 방식: 단순 diff"""
    dvdq = np.diff(volt, n=1) / np.diff(cap, n=1)
    # period 적용 (rolling average 효과)
    if period > 1:
        from scipy.ndimage import uniform_filter1d
        dvdq_smooth = uniform_filter1d(dvdq, size=period, mode='nearest')
        return cap[:-1], dvdq_smooth
    return cap[:-1], dvdq

def calc_dvdq_advanced(cap, volt, denoise_strength=3.5, Crate=0.2, slope_window=1):
    """고급 방식: Wavelet + dMSMCD"""
    cap_diff = np.median(np.diff(cap))
    max_window = max(int(slope_window * 12 / Crate / cap_diff), 1)
    
    volt_denoised = dvdq_denoise(volt, denoise_strength)
    volt_slope = dMSMCD(volt_denoised, max_window)['median']
    cap_slope = dMSMCD(cap, max_window)['median']
    
    dvdq = volt_slope / cap_slope
    return cap, dvdq

#########################################################################################
# 메인 비교 테스트
#########################################################################################
if __name__ == "__main__":
    # 파일 경로
    real_file = r"C:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dvdqraw\2c 3850mAh 05C 0cy.txt"
    ca_file = r"C:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dvdqraw\S25_291_cathode_dchg_02C.txt"
    an_file = r"C:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dvdqraw\S25_291_anode_dchg_02C.txt"
    
    print("데이터 로드 중...")
    real_data = load_dvdq_file(real_file)
    ca_data = load_dvdq_file(ca_file)
    an_data = load_dvdq_file(an_file)
    
    print(f"Real Cell: {len(real_data)} points")
    print(f"Cathode: {len(ca_data)} points")
    print(f"Anode: {len(an_data)} points")
    
    # 파라미터 설정
    period = 500  # 기존 스무딩 period
    denoise_strength = 3.5
    slope_window = 1
    Crate = 0.2
    
    print("\n기존 스무딩 계산 중...")
    real_cap_basic, real_dvdq_basic = calc_dvdq_basic(real_data['cap'].values, real_data['volt'].values, period)
    
    print("고급 스무딩 계산 중 (Wavelet + dMSMCD)... 약간 시간이 걸릴 수 있습니다.")
    real_cap_adv, real_dvdq_adv = calc_dvdq_advanced(real_data['cap'].values, real_data['volt'].values, 
                                                       denoise_strength, Crate, slope_window)
    
    # 플롯 생성
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1) 전압 원본 vs 디노이즈
    ax1 = axes[0, 0]
    volt_denoised = dvdq_denoise(real_data['volt'].values, denoise_strength)
    ax1.plot(real_data['cap'].values, real_data['volt'].values, 'b-', alpha=0.5, label='원본 전압', linewidth=0.5)
    ax1.plot(real_data['cap'].values, volt_denoised, 'r-', label='디노이즈 전압', linewidth=1)
    ax1.set_xlabel('Capacity (mAh)')
    ax1.set_ylabel('Voltage (V)')
    ax1.set_title('전압 데이터: 원본 vs Wavelet 디노이즈')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2) dV/dQ 비교 (전체)
    ax2 = axes[0, 1]
    ax2.plot(real_cap_basic, real_dvdq_basic, 'b-', alpha=0.7, label=f'기존 (period={period})', linewidth=0.8)
    ax2.plot(real_cap_adv, real_dvdq_adv, 'r-', label='고급 (Wavelet+dMSMCD)', linewidth=1)
    ax2.set_xlabel('Capacity (mAh)')
    ax2.set_ylabel('dV/dQ (V/mAh)')
    ax2.set_title('dV/dQ 비교: 기존 vs 고급 스무딩')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(-0.001, 0.003)
    
    # 3) dV/dQ 비교 (확대)
    ax3 = axes[1, 0]
    mid_idx = len(real_cap_basic) // 2
    range_idx = len(real_cap_basic) // 4
    start_idx = mid_idx - range_idx
    end_idx = mid_idx + range_idx
    ax3.plot(real_cap_basic[start_idx:end_idx], real_dvdq_basic[start_idx:end_idx], 'b-', alpha=0.7, 
             label=f'기존 (period={period})', linewidth=1)
    ax3.plot(real_cap_adv[start_idx:end_idx], real_dvdq_adv[start_idx:end_idx], 'r-', 
             label='고급 (Wavelet+dMSMCD)', linewidth=1.5)
    ax3.set_xlabel('Capacity (mAh)')
    ax3.set_ylabel('dV/dQ (V/mAh)')
    ax3.set_title('dV/dQ 비교 (중앙 영역 확대)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4) 노이즈 레벨 비교
    ax4 = axes[1, 1]
    # 노이즈 = 연속 차이의 표준편차
    noise_basic = np.std(np.diff(real_dvdq_basic[~np.isnan(real_dvdq_basic)]))
    noise_adv = np.std(np.diff(real_dvdq_adv[~np.isnan(real_dvdq_adv)]))
    
    bars = ax4.bar(['기존 스무딩', '고급 스무딩'], [noise_basic, noise_adv], color=['blue', 'red'], alpha=0.7)
    ax4.set_ylabel('노이즈 레벨 (dV/dQ 차이의 표준편차)')
    ax4.set_title('노이즈 레벨 비교')
    for bar, val in zip(bars, [noise_basic, noise_adv]):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{val:.2e}', 
                 ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(r"C:\Users\Ryu\battery\python\dataprocess\smoothing_ref\smoothing_comparison.png", dpi=150)
    plt.show()
    
    print(f"\n노이즈 비교:")
    print(f"  기존 스무딩: {noise_basic:.6e}")
    print(f"  고급 스무딩: {noise_adv:.6e}")
    print(f"  개선율: {(noise_basic - noise_adv) / noise_basic * 100:.1f}%")
    print(f"\n결과 저장: smoothing_ref/smoothing_comparison.png")
