import pandas as pd
import numpy as np
from ..core.battery_data import BatteryData

class CycleCategorizer:
    """
    Class to categorize battery data into cycles and steps (Charge/Discharge).
    """

    def __init__(self, current_threshold: float = 0.001):
        self.current_threshold = current_threshold

    def categorize(self, bd: BatteryData) -> pd.DataFrame:
        """
        Categorize the data into cycles.
        Adds 'Cycle' and 'Step_Type' columns to the dataframe.
        
        Step_Type: 
            1: Charge
            -1: Discharge
            0: Rest
        """
        df = bd.df.copy()
        
        if 'I' not in df.columns:
            print("Warning: 'I' (Current) column not found. Cannot categorize.")
            return df

        # Determine Step Type based on Current
        conditions = [
            (df['I'] > self.current_threshold),
            (df['I'] < -self.current_threshold)
        ]
        choices = [1, -1] # 1: Charge, -1: Discharge
        df['Step_Type'] = np.select(conditions, choices, default=0)

        # Calculate Cycle Number
        # Logic: Increment cycle count when transitioning from Discharge to Charge (or Rest to Charge) 
        # based on user preference, but here let's assume simple logic: 
        # A cycle is a full charge-discharge loop.
        
        # Detect state changes
        df['State_Change'] = df['Step_Type'].diff().ne(0)
        
        # Simple cycle counting: Count passing through a full charge phase
        # This is a naive implementation, can be improved with advanced logic
        
        # Identify start of charge events
        charge_starts = (df['Step_Type'] == 1) & (df['Step_Type'].shift(1) != 1)
        
        # Cumulative sum to assign cycle numbers
        df['Cycle'] = charge_starts.cumsum()
        
        # If data starts with discharge/rest before first charge, it might be Cycle 0 or 1.
        # Ensure minimum cycle is 1
        df['Cycle'] = df['Cycle'].replace(0, 1)

        return df

    def split_cycles(self, bd: BatteryData) -> dict:
        """
        Split the BatteryData into a dictionary of DataFrames by Cycle.
        Returns: {cycle_num: pd.DataFrame}
        """
        df_categorized = self.categorize(bd)
        cycles = {}
        for cycle_num, group in df_categorized.groupby('Cycle'):
            cycles[cycle_num] = group
        return cycles
