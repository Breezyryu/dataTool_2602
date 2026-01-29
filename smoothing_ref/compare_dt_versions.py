"""
dV/dQ 스무딩 비교: 4가지 방식
1. 기본 diff (dMSMCD 없음)
2. dt 포함 + dMSMCD
3. dt 제외 + dMSMCD (직접 계산)
4. 전체 파이프라인 (dMSMCD + denoise + Gaussian + Savgol)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, './smoothing_ref')

from Lib_LKS_denoise import denoise, dMSMCD as slope_func
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter, find_peaks

plt.rcParams["font.family"] = "Malgun gothic"
plt.rcParams["axes.unicode_minus"] = False

#########################################################################################
# 데이터 로드
#########################################################################################
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

#########################################################################################
# 방법 1: 기본 diff (dMSMCD 없음)
#########################################################################################
def calc_dvdq_basic_diff(cap, volt, period=500):
    df = pd.DataFrame({'cap': cap, 'volt': volt})
    dvdq = df.volt.diff(periods=period) / df.cap.diff(periods=period)
    return cap, dvdq.values

#########################################################################################
# 방법 2: dt 포함 + dMSMCD
#########################################################################################
def calc_dvdq_dt_dMSMCD(cap, volt, denoise_strength=3.5, Crate=0.2, slope_window=2):
    cap_arr = np.asarray(cap)
    volt_arr = np.asarray(volt)
    
    dQ_median = np.nanmedian(np.diff(cap_arr))
    t_pseudo = cap_arr / dQ_median
    dt_vals = np.diff(t_pseudo)
    dt_vals = np.insert(dt_vals, 0, dt_vals[0])
    
    dt_median = np.nanmedian(dt_vals)
    max_window = max(int(slope_window * 12 / Crate / dt_median), 1)
    
    dV_slope = slope_func(volt_arr, max_window)['median']
    dV_dt = dV_slope / dt_vals
    
    dQ = np.diff(cap_arr)
    dQ = np.insert(dQ, 0, dQ[0])
    dQ_dt = dQ / dt_vals
    
    dvdq = dV_dt / dQ_dt
    return cap_arr, dvdq

#########################################################################################
# 방법 3: dt 제외 + dMSMCD
#########################################################################################
def calc_dvdq_direct_dMSMCD(cap, volt, denoise_strength=3.5, Crate=0.2, slope_window=2):
    cap_arr = np.asarray(cap)
    volt_arr = np.asarray(volt)
    
    max_window = max(int(slope_window * 12 / Crate), 1)
    
    dV = slope_func(volt_arr, max_window)['median']
    dQ = np.diff(cap_arr)
    dQ = np.insert(dQ, 0, dQ[0])
    
    dvdq = dV / dQ
    return cap_arr, dvdq

#########################################################################################
# 방법 4: 전체 파이프라인 (dMSMCD + denoise + Gaussian + Savgol)
#########################################################################################
def calc_dvdq_full_pipeline(cap, volt, denoise_strength=3.5, Crate=0.2, slope_window=2, is_charge=True):
    """Lib_LKS_BatteryData.run()의 전체 파이프라인 구현"""
    cap_arr = np.asarray(cap)
    volt_arr = np.asarray(volt)
    n = len(cap_arr)
    
    # pseudo-time
    dQ_median = np.nanmedian(np.diff(cap_arr))
    dt_vals = np.ones(n) * 1.0  # dt = 1로 정규화
    dt_median = 1.0
    
    max_window = max(int(slope_window * 12 / Crate / dt_median), 1)
    
    # Step 1: dMSMCD로 slope 계산
    dV_slope = slope_func(volt_arr, max_window)['median']
    dQ = np.diff(cap_arr)
    dQ = np.insert(dQ, 0, dQ[0])
    
    dV_dt = dV_slope / dt_vals
    dQ_dt = dQ / dt_vals
    
    # Step 2: dV/dt, dQ/dt 각각 denoise
    valid_dV = ~np.isnan(dV_dt)
    valid_dQ = ~np.isnan(dQ_dt)
    if np.sum(valid_dV) > 20:
        dV_dt_denoise = dV_dt.copy()
        dV_dt_denoise[valid_dV] = denoise(dV_dt[valid_dV], denoise_strength)
    else:
        dV_dt_denoise = dV_dt
        
    if np.sum(valid_dQ) > 20:
        dQ_dt_denoise = dQ_dt.copy()
        dQ_dt_denoise[valid_dQ] = denoise(dQ_dt[valid_dQ], denoise_strength)
    else:
        dQ_dt_denoise = dQ_dt
    
    # Step 3: dV/dQ 계산
    dvdq = dV_dt_denoise / dQ_dt_denoise
    
    # Step 4: dV/dQ에 denoise
    valid = ~np.isnan(dvdq) & ~np.isinf(dvdq)
    if np.sum(valid) > 20:
        dvdq_denoised = dvdq.copy()
        dvdq_denoised[valid] = denoise(dvdq[valid], denoise_strength)
    else:
        dvdq_denoised = dvdq
    
    # Step 5: Gaussian filter
    dvdq_g = dvdq_denoised.copy()
    if n > 20:
        sigma = max(int(1 * 12 / Crate / dt_median), 1)
        try:
            valid_mid = ~np.isnan(dvdq_g[10:-10])
            temp = dvdq_g[10:-10].copy()
            temp[valid_mid] = denoise(temp[valid_mid], denoise_strength)
            dvdq_g[10:-10] = gaussian_filter1d(temp, sigma)
        except:
            pass
    
    # Step 6: Savitzky-Golay filter - small window
    dvdq_m1 = dvdq_denoised.copy()
    if n > 50:
        dvdq_ls1 = [dvdq_m1[10:-10]]
        for order in [3]:
            for win_frac in [0.02, 0.03, 0.04]:
                win_len = int(n * win_frac)
                if win_len % 2 == 0:
                    win_len += 1
                if win_len > order:
                    try:
                        dvdq_ls1.append(savgol_filter(dvdq_m1[10:-10], win_len, order))
                        dvdq_ls1.append(1/savgol_filter(1/dvdq_m1[10:-10], win_len, order))
                    except:
                        pass
        if len(dvdq_ls1) > 1:
            dvdq_m1[10:-10] = np.nanmedian(dvdq_ls1, axis=0)
    
    # Step 7: filtering range reset
    dVdQ_sign = 1 if is_charge else -1
    dVdQ_cut_ids = np.where(dvdq_denoised * dVdQ_sign > 0)[0]
    if len(dVdQ_cut_ids) > 20:
        dVdQ_cut_ids_cont = np.where(np.diff(dVdQ_cut_ids) == 1)[0] + 1
        dVdQ_cut_ids = dVdQ_cut_ids[dVdQ_cut_ids_cont]
        if len(dVdQ_cut_ids) > 20:
            id_s = max(dVdQ_cut_ids[10], 10)
            id_e = min(dVdQ_cut_ids[-10] - n, -10)
        else:
            id_s, id_e = 10, -10
    else:
        id_s, id_e = 10, -10
    
    # Step 8: Savitzky-Golay filter - large window
    dvdq_m2 = dvdq_denoised.copy()
    if n > 50 and id_s < abs(id_e):
        dvdq_ls2 = [dvdq_m2[id_s:id_e]]
        for order in [3]:
            for win_frac in [0.03, 0.04, 0.05, 0.06, 0.07]:
                win_len = int(n * win_frac)
                if win_len % 2 == 0:
                    win_len += 1
                if win_len > order:
                    try:
                        dvdq_ls2.append(savgol_filter(dvdq_m2[id_s:id_e], win_len, order))
                        dvdq_ls2.append(1/savgol_filter(1/dvdq_m2[id_s:id_e], win_len, order))
                    except:
                        pass
        if len(dvdq_ls2) > 1:
            dvdq_m2[id_s:id_e] = np.nanmedian(dvdq_ls2, axis=0)
    
    return cap_arr, dvdq_m2

#########################################################################################
# 메인
#########################################################################################
if __name__ == "__main__":
    files = {
        'Fullcell': ('./smoothing_ref/dvdqraw/Gen4P 4905mAh HHP ATL 055CY - 복사본.txt', 2, True),
        'Anode': ('./smoothing_ref/dvdqraw/S25_291_anode_dchg_02C - 복사본.txt', 20, False),
        'Cathode': ('./smoothing_ref/dvdqraw/S25_291_cathode_dchg_02C - 복사본.txt', 5, True)
    }
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 14))
    
    for idx, (name, (filepath, slope_window, is_charge)) in enumerate(files.items()):
        print(f"\n=== {name} (slope_window={slope_window}) ===")
        data = load_data(filepath)
        cap = data['cap'].values
        volt = data['volt'].values
        print(f"데이터 포인트: {len(cap)}")
        
        period = 500
        
        # 4가지 방식 계산
        cap1, dvdq1 = calc_dvdq_basic_diff(cap, volt, period)
        cap2, dvdq2 = calc_dvdq_dt_dMSMCD(cap, volt, slope_window=slope_window)
        cap3, dvdq3 = calc_dvdq_direct_dMSMCD(cap, volt, slope_window=slope_window)
        cap4, dvdq4 = calc_dvdq_full_pipeline(cap, volt, slope_window=slope_window, is_charge=is_charge)
        
        # 플롯 (왼쪽 y축: dV/dQ)
        ax = axes[idx]
        ax.plot(cap1, dvdq1, 'b-', alpha=0.5, label=f'1. 기본 diff (period={period})', linewidth=0.8)
        ax.plot(cap2, dvdq2, 'r-', alpha=0.6, label='2. dt 포함 + dMSMCD', linewidth=0.8)
        ax.plot(cap3, dvdq3, 'g--', alpha=0.6, label='3. dt 제외 + dMSMCD', linewidth=0.8)
        ax.plot(cap4, dvdq4, 'm-', alpha=0.9, label='4. 전체 파이프라인', linewidth=1.2)
        
        ax.set_xlabel('Capacity')
        ax.set_ylabel('dV/dQ')
        ax.set_title(f'{name}: 4가지 스무딩 방식 비교 (slope_window={slope_window})')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # 우측 y축: Voltage
        ax2 = ax.twinx()
        ax2.plot(cap, volt, 'k-', alpha=0.4, linewidth=1.5, label='Voltage')
        ax2.set_ylabel('Voltage (V)', color='black')
        ax2.tick_params(axis='y', labelcolor='black')
        ax2.legend(loc='upper right')
        
        # dV/dQ 피크 검출 (전체 파이프라인 결과 사용)
        dvdq_clean = np.nan_to_num(dvdq4, nan=0, posinf=0, neginf=0)
        if len(dvdq_clean) > 20:
            # 피크 검출 (prominence로 유의미한 피크만)
            prominence = np.abs(np.percentile(dvdq_clean, 95) - np.percentile(dvdq_clean, 5)) * 0.1
            peaks_idx, props = find_peaks(np.abs(dvdq_clean), prominence=prominence, distance=len(dvdq_clean)//20)
            
            if len(peaks_idx) > 0:
                # 피크 위치에 마커 표시 (dV/dQ 곡선)
                ax.scatter(cap4[peaks_idx], dvdq4[peaks_idx], c='red', s=80, zorder=10, 
                           marker='v', edgecolors='black', linewidth=1, label=f'Peak ({len(peaks_idx)}개)')
                
                # 같은 위치의 전압에도 마커 표시
                ax2.scatter(cap[peaks_idx], volt[peaks_idx], c='red', s=80, zorder=10,
                            marker='o', edgecolors='black', linewidth=1)
                
                # 피크 정보 출력
                print(f"  검출된 피크: {len(peaks_idx)}개")
                for i, pk in enumerate(peaks_idx[:5]):  # 최대 5개만 출력
                    print(f"    Peak {i+1}: Cap={cap4[pk]:.1f}, dV/dQ={dvdq4[pk]:.4f}, V={volt[pk]:.3f}V")
                
                ax.legend(loc='upper left')
        
        # Y축 범위
        all_vals = np.concatenate([dvdq1, dvdq2, dvdq3, dvdq4])
        valid_vals = all_vals[~np.isnan(all_vals) & ~np.isinf(all_vals)]
        if len(valid_vals) > 10:
            y_min, y_max = np.percentile(valid_vals, [2, 98])
            ax.set_ylim(y_min * 0.9, y_max * 1.1)
        
        # 노이즈 비교
        for label, dvdq in [('기본 diff', dvdq1), ('dt+dMSMCD', dvdq2), 
                            ('직접 dMSMCD', dvdq3), ('전체 파이프라인', dvdq4)]:
            valid = dvdq[~np.isnan(dvdq) & ~np.isinf(dvdq)]
            if len(valid) > 10:
                noise = np.std(np.diff(valid))
                print(f"  {label} 노이즈: {noise:.6e}")
    
    plt.tight_layout()
    plt.savefig('./smoothing_ref/dvdq_4methods_comparison.png', dpi=150)
    print("\n저장 완료: smoothing_ref/dvdq_4methods_comparison.png")
    plt.show()
