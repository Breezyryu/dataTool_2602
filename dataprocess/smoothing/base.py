from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class SmoothingStrategy(ABC):
    """
    Abstract Base Class for Smoothing Strategies.
    """
    
    @abstractmethod
    def apply(self, data: pd.Series | np.ndarray) -> np.ndarray:
        """
        Apply smoothing to the data.
        
        Args:
            data: Input data (Series or numpy array)
            
        Returns:
            Smoothed data as numpy array
        """
        pass
