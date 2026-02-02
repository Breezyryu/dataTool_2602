
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# Add current directory to path to import BatteryDataTool
sys.path.append(os.getcwd())
from BatteryDataTool import generate_simulation_full

# Define file paths
real_path = r"C:\Users\Ryu\battery\Rawdata\!dvdqraw\dvdqraw\2c 3850mAh 05C 0cy.txt"
anode_path = r"C:\Users\Ryu\battery\Rawdata\!dvdqraw\dvdqraw\S25_291_anode_dchg_02C.txt"
cathode_path = r"C:\Users\Ryu\battery\Rawdata\!dvdqraw\dvdqraw\S25_291_cathode_dchg_02C.txt"

def load_and_prep():
    # Load Real Data
    print("Loading Real Data...")
    real_df = pd.read_csv(real_path, sep='\t')
    real_df.columns = ["real_cap", "real_volt"]
    
    # Load Anode Data
    print("Loading Anode Data...")
    anode_df = pd.read_csv(anode_path, sep='\t')
    anode_df.columns = ["an_cap", "an_volt"]
    
    # Load Cathode Data
    print("Loading Cathode Data...")
    cathode_df = pd.read_csv(cathode_path, sep='\t')
    cathode_df.columns = ["ca_cap", "ca_volt"]
    
    return real_df, anode_df, cathode_df

def run_verification():
    real_df, anode_df, cathode_df = load_and_prep()
    
    # Dummy parameters for mass/slip (assuming 1.0 and 0 for raw test if not provided)
    # The user provided files but not mass/slip parameters. 
    # We will try to guess or use 1/0 to see dV/dQ shape.
    ca_mass = 1.0
    ca_slip = 0.0
    an_mass = 1.0
    an_slip = 0.0
    full_cell_max_cap = 4000 # Guessing based on "3850mAh" filename
    rated_cap = 3850
    full_period = 1 # Period for diff
    
    print("Running simulation WITHOUT smoothing...")
    sim_raw = generate_simulation_full(
        cathode_df.copy(), anode_df.copy(), real_df.copy(),
        ca_mass, ca_slip, an_mass, an_slip,
        full_cell_max_cap, rated_cap, full_period,
        enable_smoothing=False
    )
    
    print("Running simulation WITH smoothing...")
    sim_smooth = generate_simulation_full(
        cathode_df.copy(), anode_df.copy(), real_df.copy(),
        ca_mass, ca_slip, an_mass, an_slip,
        full_cell_max_cap, rated_cap, full_period,
        enable_smoothing=True, smooth_window=51, smooth_poly=3 # Using stronger smoothing for visibility
    )
    
    # Plotting
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Full Cell dV/dQ
    axes[0, 0].plot(sim_raw.full_cap, sim_raw.full_dvdq, label='Raw', alpha=0.5)
    axes[0, 0].plot(sim_smooth.full_cap, sim_smooth.full_dvdq, label='Smoothed', linewidth=2)
    axes[0, 0].set_title("Full Cell dV/dQ")
    axes[0, 0].legend()
    axes[0, 0].set_ylim(-0.002, 0.002) # Adjust limits if needed
    
    # 2. Anode dV/dQ
    axes[0, 1].plot(sim_raw.full_cap, sim_raw.an_dvdq, label='Raw', alpha=0.5)
    axes[0, 1].plot(sim_smooth.full_cap, sim_smooth.an_dvdq, label='Smoothed', linewidth=2)
    axes[0, 1].set_title("Anode dV/dQ")
    
    # 3. Cathode dV/dQ
    axes[1, 0].plot(sim_raw.full_cap, sim_raw.ca_dvdq, label='Raw', alpha=0.5)
    axes[1, 0].plot(sim_smooth.full_cap, sim_smooth.ca_dvdq, label='Smoothed', linewidth=2)
    axes[1, 0].set_title("Cathode dV/dQ")
    
    # 4. Real dV/dQ
    axes[1, 1].plot(sim_raw.full_cap, sim_raw.real_dvdq, label='Raw', alpha=0.5)
    axes[1, 1].plot(sim_smooth.full_cap, sim_smooth.real_dvdq, label='Smoothed', linewidth=2)
    axes[1, 1].set_title("Real Data dV/dQ")
    
    output_path = "verification_plot.png"
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    run_verification()
