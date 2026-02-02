import numpy as np
import pandas as pd
import re
import astropy.units as u
from .units import UNITS

class BatteryData:
    """
    Core class for handling Battery Data.
    Manages raw data, unit conversion, and basic time steps.
    """
    
    KEYS = {
        't': [r'(Time|시간)', UNITS['t']],
        'V': [r'(Voltage|전압|전위)', UNITS['V']],
        'I': [r'(Current|전류)', UNITS['I']],
        'Q': [r'(Capacity|용량)', UNITS['Q']],
        'T': [r'(Temp|온도)', UNITS['T']]
    }

    def __init__(self, df: pd.DataFrame):
        self.df_raw = df.copy()
        self.arrays = {}
        self.df = pd.DataFrame(index=df.index)
        self._convert_units(df)
        self.dt = self._calculate_dt()
        self.is_charge_start = self._determine_type()

    def _convert_units(self, df: pd.DataFrame):
        """Convert columns to standard units based on patterns."""
        for key, (pattern, std_unit) in self.KEYS.items():
            for col in df.columns:
                if re.search(pattern, col, re.IGNORECASE):
                    try:
                        # Extract unit from parenthesis e.g. "Voltage(V)"
                        unit_str = re.search(r'\((.*?)\)', col)
                        if unit_str:
                            current_unit = u.Unit(unit_str.group(1))
                        else:
                            current_unit = std_unit
                    except Exception:
                        current_unit = std_unit
                    
                    data_quantity = (df[col].values * current_unit)
                    
                    # Convert to standard unit
                    if std_unit == u.deg_C:
                        converted = data_quantity.to(std_unit, equivalencies=u.temperature())
                    else:
                        converted = data_quantity.to(std_unit)

                    self.arrays[key] = converted
                    self.df[key] = converted.value
                    break # Found the column for this key, move to next key

    def _calculate_dt(self) -> float:
        """Calculate mode of time intervals."""
        if 't' not in self.arrays:
            return 60.0
        
        intervals = np.diff(self.arrays['t'].value)
        if len(intervals) == 0:
            return 1.0
            
        rounded_intervals = np.round(intervals, 3)
        dt_mode = np.nanmedian(rounded_intervals)
        return float(dt_mode) if dt_mode > 0 else 1.0

    def _determine_type(self) -> bool:
        """
        Determine if the data starts with charging or discharging.
        Returns True if charging (Voltage increases or Current > 0), False otherwise.
        """
        v_arr = self.arrays.get('V')
        if v_arr is not None:
            v_valid = v_arr[np.isfinite(v_arr.value)]
            if len(v_valid) >= 2:
                # Check if voltage is increasing at the start
                return (v_valid[-1] - v_valid[0]).value > 0
        
        i_arr = self.arrays.get('I')
        if i_arr is not None:
            i_mean = np.nanmean(i_arr.value)
            if np.abs(i_mean) > 1e-6:
                return i_mean > 0
                
        return True

    def update(self, key: str, data):
        """Update/Add a column to the dataset."""
        if hasattr(data, 'value'): # It's a Quantity
            self.df[key] = data.value
            self.arrays[key] = data
        else:
            self.df[key] = data
            self.arrays[key] = data * u.dimensionless_unscaled
