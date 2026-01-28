import numpy as np
import pandas as pd
import xlwings as xw
from openpyxl.utils import get_column_letter as get_char
import matplotlib.pyplot as plt
from glob2 import glob
import time

from Lib_LKS_common import ActCell, from_excel2, init_excel
from Lib_LKS_units import UNIT_check; import astropy.units as u
from scipy.ndimage import gaussian_filter1d
from Lib_LKS_denoise import WLD as denoise, dMSMCD as slope
from Lib_LKS_BatteryData import BatteryData
import warnings
warnings.simplefilter("ignore", category=RuntimeWarning)

UNIT = UNIT_check() # {'t': u.sec, 'V': u.V, 'I': u.A, 'Q': u.Ah, 'T': u.deg_C3}

path_part1 = 'D:/work/26/Lib_LKS/260107) Lib_LKS_matching & sample/Converted/AN_SDI_PA2/3.12/'
Cases = ['An','Cat']
Types = ['CHG','DCH']
Cells = [1,2,3]

# Cases = ['An',]
# Types = ['CHG',]
# Cells = [1,]

#### Test History ###
# 260119_01 : [m1] 0.02-0.04, [m2] 0.03-0.09, [m3] 섞는 비율 제곱으로 변경
# 260119_02 : [m1] 0.02-0.04, [m2] 0.05-0.09, [m3] 섞는 비율 제곱으로 변경
# 260119_03 : [m1] 0.02-0.04, [m2] (0.03-0.07)+Crate/10, [m3] 섞는 비율 제곱으로 변경 -> 개선 확인
# 260119_04 : [m1] 0.02-0.04, [m2] 0.03-(0.07+Crate/10), [m3] 섞는 비율 제곱으로 변경 -> X
# 260119_05 : [m1] 0.02-0.04, [m2] (0.03-0.07)+Crate/10, [m3] 섞는 비율 원복 -> ???
# 260119_06 : [m1] 0.02-0.04, [m2] (0.03-0.07)+Crate/10, [m3] 섞는 비율 원복, 필터링 범위 dV 반대 방향 제외 -> 개선 확인
# 260119_07 : slope3/slope2(평균기울기 O/X) 비교
#             -> slope2 사용시 노이즈는 많으나 전체적인 추세로는 잘 겹침을 확인
#             -> 단, slope2의 경우 denoise 시 왜곡 발생
#             -> slope3 사용시 전압 급락/급등하는 부분은 노이즈가 발생
#             -> 단, 분석을 위한 peak 부근의 노이즈는 획기적으로 감소
#             -> slope3+denoise 조합을 이용할 것
# 260119_08 : [m1] 0.02-0.04, [m2] (0.03-0.07)+Crate/10, [m3] 섞는 비율 제곱으로 변경, 필터링 범위 dV 반대 방향 제외 -> 제곱으로 변경한 효과 미미 원복
# 260119_09 : [m1] 0.02-0.04, [m2] 0.05-(0.09+Crate/10), [m3] 섞는 비율 원복 -> 1.0C 물결치는 부분 완화X
# 260120_01 : [m1] 0.02-0.04, [m2] (0.03-0.07)+Crate/10, denoise O/X, slope_window 0.0 ~ 2.0
#             -> PPT 중간 공유 자료 제작 / 메일 작성 예정 [~ 26/01/21 (수)]

prefix1 = f'260120_01_denoise_O_slope_2.0'
prefix2 = f'3.12'

for Case in Cases:
    for Type in Types:
        # i = 0
        # bk = xw.Book(path_part1+f'0. form_{prefix2}_{Case}_{Type}.xlsx')
        for Cell in Cells:
            paths = [path.replace('\\','/') for path in glob(path_part1+f'{Case}_{Type}_#{Cell}*.dat')]
            # print(paths)
            for path in paths:
                path_part2 = path.split('/')[-1]
                print(path_part2)
                Crate = float(path_part2.split('_')[-1].replace('.dat',''))
                df = pd.read_csv(path)
                if (Type == 'CHG') & (len(np.where(np.round(df.iloc[2:,2],2) < np.round(np.mean(df.iloc[2:12,2]),2))[0]) > 0):
                    df = df.iloc[:np.where(np.round(df.iloc[2:,2],2) < np.round(np.mean(df.iloc[2:12,2]),2))[0][0],:]
                BD = BatteryData(df)
                BD.run(3.5,Crate,2)
                # BD.run(3.5,Crate,1)
                BD.df.to_excel(path.split('.dat')[0]+'.xlsx',index=False)
                # sh = bk.sheets[i]
                # sh.range('A1').value = BD.df.T.reset_index(drop=False).T.to_numpy()
                # i += 1
        bk.save(path_part1+f'{prefix1}_{prefix2}_{Case}_{Type}.xlsx')
        bk.close()
init_excel()

# for loop_ in range(20):
#     prefix1 = f'260120_01_denoise_△_slope_{(loop_+1)/10}'
# #     prefix1 = f'260120_01_denoise_O_slope_0.0'
#     prefix2 = f'3.12'
#
#     for Case in Cases:
#         for Type in Types:
#             i = 0
#             bk = xw.Book(path_part1+f'0. form_{prefix2}_{Case}_{Type}.xlsx')
#             for Cell in Cells:
#                 paths = [path.replace('\\','/') for path in glob(path_part1+f'{Case}_{Type}_#{Cell}*.dat')]
#                 # print(paths)
#                 for path in paths:
#                     path_part2 = path.split('/')[-1]
#                     print(path_part2)
#                     Crate = float(path_part2.split('_')[-1].replace('.dat',''))
#                     df = pd.read_csv(path)
#                     if (Type == 'CHG') & (len(np.where(np.round(df.iloc[2:,2],2) < np.round(np.mean(df.iloc[2:12,2]),2))[0]) > 0):
#                         df = df.iloc[:np.where(np.round(df.iloc[2:,2],2) < np.round(np.mean(df.iloc[2:12,2]),2))[0][0],:]
#                     BD = BatteryData(df)
#                     BD.run(3.5,Crate,(loop_+1)/10)
#                     # BD.run(3.5,Crate,1)
#                     # BD.df.to_excel(path.split('.dat')[0]+'.xlsx',index=False)
#                     sh = bk.sheets[i]
#                     sh.range('A1').value = BD.df.T.reset_index(drop=False).T.to_numpy()
#                     i += 1
#             bk.save(path_part1+f'{prefix1}_{prefix2}_{Case}_{Type}.xlsx')
#             bk.close()
#     init_excel()
