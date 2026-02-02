import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

plt.rcParams["font.family"] = "Malgun gothic"
plt.rcParams["axes.unicode_minus"] = False

def load_data(filepath):
    # Try different encodings/separators
    try:
        # First try detecting separator
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Check first few lines for separator
        header_line = lines[1] if len(lines) > 1 else lines[0]
        if '\t' in header_line:
            sep = '\t'
        elif ',' in header_line:
            sep = ','
        else:
            sep = r'\s+'
            
        df = pd.read_csv(filepath, sep=sep, engine='python' if sep == r'\s+' else 'c',
                         skip_blank_lines=True, on_bad_lines='skip')
                         
        # If columns are not named 'capacity' and 'voltage', try to infer or rename
        if len(df.columns) >= 2:
            # Assuming 1st col is Capacity, 2nd is Voltage
            df = df.iloc[:, :2]
            df.columns = ["Capacity", "Voltage"]
            df = df.apply(pd.to_numeric, errors='coerce').dropna()
            return df
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None
    return None

files = [
    r"c:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dVdQ\2c 3850mAh 05C 0cy.txt",
    r"c:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dVdQ\2c 3850mAh 05c 400cy.txt",
    r"c:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dVdQ\2c 3850mAh 05c 950cy.txt",
    r"c:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dVdQ\2c 3850mAh 10c 0cy.txt",
    r"c:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dVdQ\2c 3850mAh 10c 400cy.txt",
    r"c:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dVdQ\2c 3850mAh 10c 950cy.txt",
    r"c:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dVdQ\S25_291_anode_dchg_02C_gen4 수정.txt",
    r"c:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dVdQ\S25_291_anode_dchg_02C.txt",
    r"c:\Users\Ryu\battery\python\dataprocess\smoothing_ref\!dvdqraw\dVdQ\S25_291_cathode_dchg_02C.txt"
]

# Separate groups
full_cells = [f for f in files if "mAh" in f and "anode" not in f and "cathode" not in f]
anodes = [f for f in files if "anode" in f]
cathodes = [f for f in files if "cathode" in f]

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

def get_style(filename):
    ls = '-'
    if "400cy" in filename: ls = '--'
    elif "950cy" in filename: ls = '-.'
    elif "gen4" in filename: ls = ':'
    
    if "05C" in filename or "05c" in filename: color = 'tab:blue'
    elif "10C" in filename or "10c" in filename: color = 'tab:orange'
    elif "anode" in filename: color = 'tab:green'
    elif "cathode" in filename: color = 'tab:red'
    else: color = 'black'
    return ls, color

# Plot Full Cells
for filepath in full_cells:
    if not os.path.exists(filepath): continue
    df = load_data(filepath)
    if df is not None:
        filename = os.path.basename(filepath)
        label = filename.replace(".txt", "")
        ls, color = get_style(filename)
        ax1.plot(df["Capacity"], df["Voltage"], label=label, linestyle=ls, color=color, linewidth=1.5)
ax1.set_title("Full Cell")
ax1.set_xlabel("Capacity (mAh)")
ax1.set_ylabel("Voltage (V)")
ax1.grid(True, alpha=0.3)
ax1.legend()

# Plot Anode
for filepath in anodes:
    if not os.path.exists(filepath): continue
    df = load_data(filepath)
    if df is not None:
        filename = os.path.basename(filepath)
        label = filename.replace(".txt", "")
        ls, color = get_style(filename)
        ax2.plot(df["Capacity"], df["Voltage"], label=label, linestyle=ls, color=color, linewidth=1.5)
ax2.set_title("Anode (Half Cell)")
ax2.set_xlabel("Capacity (mAh)")
ax2.set_ylabel("Voltage (V)")
ax2.grid(True, alpha=0.3)
ax2.legend()

# Plot Cathode
for filepath in cathodes:
    if not os.path.exists(filepath): continue
    df = load_data(filepath)
    if df is not None:
        filename = os.path.basename(filepath)
        label = filename.replace(".txt", "")
        ls, color = get_style(filename)
        ax3.plot(df["Capacity"], df["Voltage"], label=label, linestyle=ls, color=color, linewidth=1.5)
ax3.set_title("Cathode (Half Cell)")
ax3.set_xlabel("Capacity (mAh)")
ax3.set_ylabel("Voltage (V)")
ax3.grid(True, alpha=0.3)
ax3.legend()

plt.tight_layout()
output_path = r"c:\Users\Ryu\battery\python\dataprocess\smoothing_ref\cap_volt_plot.png"
plt.savefig(output_path, dpi=300)
print(f"Saved plot to {output_path}")
plt.show()
