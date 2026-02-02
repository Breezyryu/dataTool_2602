from scipy.ndimage import gaussian_filter1d
import pandas as pd
import numpy as np
from .base import SmoothingStrategy

class GaussianStrategy(SmoothingStrategy):
    """
    Smoothing strategy using Gaussian filter.
    """
    
    def __init__(self, sigma: float = 1.0):
        """
        Args:
            sigma: Standard deviation for Gaussian kernel.
        """
        self.sigma = sigma

    def apply(self, data: pd.Series | np.ndarray) -> np.ndarray:
         # Handle input
        if isinstance(data, pd.Series):
            y = data.to_numpy()
        else:
            y = data
            
        try:
            smoothed = gaussian_filter1d(y, self.sigma)
            return smoothed
        except Exception as e:
            # Fallback
            print(f"Error in GaussianStrategy: {e}")
            return y
