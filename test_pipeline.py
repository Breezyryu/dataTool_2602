import pandas as pd
import numpy as np
import os
from dataprocess.pipeline import DataProcessPipeline

def create_dummy_data(filename="dummy_battery_data.csv"):
    t = np.linspace(0, 3600, 1000)
    # Voltage: 3.0 to 4.2 (Charge) then 4.2 to 3.0 (Discharge)
    v_charge = np.linspace(3.0, 4.2, 500)
    v_discharge = np.linspace(4.2, 3.0, 500)
    v = np.concatenate([v_charge, v_discharge])
    
    # Current: +1A (Charge) then -1A (Discharge) w/ noise
    i_charge = np.ones(500) + np.random.normal(0, 0.01, 500)
    i_discharge = -np.ones(500) + np.random.normal(0, 0.01, 500)
    i = np.concatenate([i_charge, i_discharge])
    
    # Capacity: Integrating I * dt
    q = np.cumsum(i) * (t[1]-t[0]) / 3600 # Ah
    
    df = pd.DataFrame({'Time(s)': t, 'Voltage(V)': v, 'Current(A)': i, 'Capacity(Ah)': q})
    df.to_csv(filename, index=False)
    print(f"Created {filename}")
    return filename

def test_pipeline():
    filename = create_dummy_data()
    
    pipeline = DataProcessPipeline()
    print("Running Pipeline...")
    bd = pipeline.process_file(filename, smoothing_method='sg', window_length=21, polyorder=3)
    
    if bd:
        print("Pipeline finished successfully.")
        print("Columns:", bd.df.columns)
        print("Head:\n", bd.df[['t', 'V', 'I', 'Cycle', 'Step_Type', 'dV/dQ']].head())
        print("Tail:\n", bd.df[['t', 'V', 'I', 'Cycle', 'Step_Type', 'dV/dQ']].tail())
        
        # Check if Cycle 1 is detected
        cycles = bd.df['Cycle'].unique()
        print("Detected Cycles:", cycles)
        
        if 'dV/dQ' in bd.df.columns:
            print("dV/dQ calculated.")
        else:
            print("Error: dV/dQ not calculated.")
            
    else:
        print("Pipeline failed.")
        
    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)

if __name__ == "__main__":
    test_pipeline()
