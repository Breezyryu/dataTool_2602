from ..core.battery_data import BatteryData
from ..smoothing.base import SmoothingStrategy
import numpy as np
import pandas as pd

class DVDQAnalyzer:
    """
    Analyzer for dV/dQ and dQ/dV calculations.
    """

    def __init__(self, smoothing_strategy: SmoothingStrategy = None):
        self.smoothing_strategy = smoothing_strategy

    def calculate(self, bd: BatteryData, window: int = 5) -> BatteryData:
        """
        Calculate dV/dQ and dQ/dV for the battery data.
        Updates the BatteryData object with new columns.
        """
        
        # Ensure dt is available
        dt = bd.dt
        
        # Calculate derivatives w.r.t time (simple gradient or windowed)
        # Here we use simple gradient for initial implementation, 
        # but could key off 'slope' logic from reference if needed.
        
        # Calculate dV/dt and dQ/dt
        t_vals = bd.df['t'].values
        v_vals = bd.df['V'].values
        q_vals = bd.df['Q'].values

        # Use numpy gradient for better numerical stability than diff
        # But reference uses simple diff/dt or windowed slope.
        # Let's use simple diff for now as baseline
        
        dv = np.gradient(v_vals, t_vals)
        dq = np.gradient(q_vals, t_vals)
        
        # Apply smoothing to derivatives if strategy provided
        if self.smoothing_strategy:
            dv = self.smoothing_strategy.apply(dv)
            dq = self.smoothing_strategy.apply(dq)
            
        # Calculate dV/dQ = (dV/dt) / (dQ/dt)
        # Handle division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            dvdq = dv / dq
            dqdv = dq / dv
            
        dvdq[np.isinf(dvdq)] = np.nan
        dqdv[np.isinf(dqdv)] = np.nan
        
        # Update BatteryData
        bd.update('dV/dt', dv)
        bd.update('dQ/dt', dq)
        bd.update('dV/dQ', dvdq)
        bd.update('dQ/dV', dqdv)
        
        return bd
