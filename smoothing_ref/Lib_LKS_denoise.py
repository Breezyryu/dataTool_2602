import numpy as np
import pywt
from Lib_LKS_units import UNIT_check; import astropy.units as u

#########################################################################################
### Wavelet Denoising (pip install PyWavelet, final)
#########################################################################################
def WLD(y, denoise_strength: float = 1.0, wavelet: str = 'bior6.8', mode: str = 'soft'):
    """
    Wavelet Denoising (WLD). VisuShrink 임계값을 사용하여 노이즈를 제거합니다.
    denoise_strength : threshold multiplier
    wavelet options : 'db4','db8','bior3.5','bior6.8','sym5' etc
    """
    y_val, y_unit = (y.value, y.unit) if isinstance(y, u.Quantity) else (y, None)
    y_val_copy = y_val[1:].copy()
    y_val_pad = np.pad(y_val_copy,50,mode='edge')

    rolls = []
    for i in range(10):
        y_val_roll = np.roll(y_val_pad, i-5)
        coeffs = pywt.wavedec(y_val_roll, wavelet)
        detail = coeffs[-1]

        # MAD 기반 노이즈 추정
        sigma = np.median(np.abs(detail - np.median(detail))) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(len(y_val))) * denoise_strength

        new_coeffs = [coeffs[0]]
        for i in range(1, len(coeffs)):
            new_coeffs.append(pywt.threshold(coeffs[i], threshold, mode=mode))

        y_denoised_roll = pywt.waverec(new_coeffs, wavelet)

        if len(y_denoised_roll) > len(y_val_roll):
            y_denoised_roll = y_denoised_roll[:len(y_val_roll)]
        elif len(y_denoised_roll) < len(y_val_roll):
            y_denoised_roll = np.pad(y_denoised_roll,(0,len(y_val_roll)-len(y_denoised_roll)),mode='edge')

        y_val_unroll = np.roll(y_denoised_roll, -(i-5))
        rolls.append(y_val_unroll)

    rolls = np.array(rolls)
    y_denoised = y_val
    y_denoised[1:] = np.median(rolls,axis=0)[50:-50]

    return y_denoised * y_unit if y_unit else y_denoised

def denoise(y, denoise_strength: float = 1.0):
    """
    Wavelet Denoising (WLD). VisuShrink 임계값을 사용하여 노이즈를 제거합니다.
    denoise_strength : threshold multiplier
    """
    ws1 = ['bior', 'rbio']
    ws2 = ['2.6', '2.8', '3.7', '3.9', '6.8']
    ws = [w1 + w2 for w1 in ws1 for w2 in ws2]
    y_val, y_unit = (y.value, y.unit) if isinstance(y, u.Quantity) else (y, None)
    y_denoised = np.nanmedian(np.array([WLD(y_val.copy(), denoise_strength, w) for w in ws]),axis=0)
    return y_denoised * y_unit if y_unit else y_denoised

#########################################################################################
### (임시 가칭) Multi-Scale Median Centered Difference (ver.2)
#########################################################################################
def dMSMCD(y, max_window: int):
    y_val, y_unit = (y.value, y.unit) if isinstance(y, u.Quantity) else (y, None)
    n = len(y_val)
    slopes_list = []
    v_padded = np.pad(y_val, pad_width=1, mode='edge')
    interpolated_values = (v_padded[:-1] + v_padded[1:]) / 2

    for i in range(max_window):
        slope = np.full(n, np.nan, dtype=np.float64)
        if i%2 == 0:
            j = (i+1)//2
            slope[(j+1):-(j+1)] = ((interpolated_values[(i+1):]-interpolated_values[:-(i+1)])/(i+1))[1:-1]
            slopes_list.append(slope)
    slopes_array = np.stack(slopes_list, axis=1)
    median_slope = np.nanmedian(slopes_array, axis=1)

    if y_unit:
        slopes_array = slopes_array * y_unit
        median_slope = median_slope * y_unit

    return {'median': median_slope, 'all': slopes_array}