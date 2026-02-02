
try:
    with open(r'c:\Users\Ryu\battery\python\dataprocess\BatteryDataTool_Optimized\BatteryDataTool.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
except UnicodeDecodeError:
    with open(r'c:\Users\Ryu\battery\python\dataprocess\BatteryDataTool_Optimized\BatteryDataTool.py', 'r', encoding='cp949') as f:
        lines = f.readlines()

for i, line in enumerate(lines):
    if 'def dvdq_fitting' in line:
        print(f"Found at line {i+1}: {line}")
