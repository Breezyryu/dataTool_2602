from scipy.signal import savgol_filter
import pandas as pd
import numpy as np
from .base import SmoothingStrategy

class SavitzkyGolayStrategy(SmoothingStrategy):
    """
    Smoothing strategy using Savitzky-Golay filter.
    Preserves peak heights and widths better than simple moving averages.
    """
    
    def __init__(self, window_length: int = 51, polyorder: int = 3):
        """
        Args:
            window_length: The length of the filter window. Must be odd.
            polyorder: The order of the polynomial used to fit the samples.
        """
        self.window_length = window_length
        self.polyorder = polyorder
        
        # Ensure window_length is odd
        if self.window_length % 2 == 0:
            self.window_length += 1

    def apply(self, data: pd.Series | np.ndarray) -> np.ndarray:
        # Handle input
        if isinstance(data, pd.Series):
            y = data.to_numpy()
        else:
            y = data
            
        # Handle Quantity if present (strip unit for calculation, assume handling elsewhere or returned as array)
        # Assuming input is just value array for now or handling astropy outside. 
        # But if it's astropy Quantity, numpy functions often handle it or strip it.
        # Let's try to handle NaNs if possible, but SG filter doesn't like NaNs.
        # For now simple implementation.
        
        try:
             # Basic handling for NaN at edges if needed, but scipy might handle or propagate.
            smoothed = savgol_filter(y, self.window_length, self.polyorder)
            return smoothed
        except Exception as e:
            # Fallback or error logging
            print(f"Error in SavitzkyGolayStrategy: {e}")
            return y
