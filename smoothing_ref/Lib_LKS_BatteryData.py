import numpy as np
import pandas as pd
import re
import time
from openpyxl.utils import get_column_letter as get_char

from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter1d, median_filter

from Lib_LKS_units import UNIT_check; import astropy.units as u
from Lib_LKS_denoise import denoise, dMSMCD as slope
import matplotlib.pyplot as plt

UNIT = UNIT_check()

########################################################################################################################
# BatteryData Class
########################################################################################################################
class BatteryData:
    ### class 초기 기본 설정 ###
    KEYS = {'t': [r'(Time|시간)',u.sec],
            'V': [r'(Voltage|전압|전위)',u.V],
            'I': [r'(Current|전류)',u.A],
            'Q': [r'(Capacity|용량)',u.Ah],
            'T': [r'(Temp|온도)',u.deg_C3]}

    def __init__(self, df: pd.DataFrame):
        self.df_raw = df.copy()
        self.arrays = {}
        self.df = pd.DataFrame(index=df.index)
        self._convert(df)
        self.dt = self._dt()
        self.type = self._type()

    def _convert(self, df):
        for KEY, [PATTERN, STD_UNIT] in self.KEYS.items():
            for COL in df.columns:
                if re.search(PATTERN, COL, re.IGNORECASE):
                    try:
                        UNIT = u.Unit(re.search(r'\((.*?)\)', COL).group(1))
                        # print(UNIT)
                    except:
                        UNIT = STD_UNIT
                    DATA = (df[COL].values * UNIT)
                    DATA = DATA.to(STD_UNIT, equivalencies=u.temperature()) if STD_UNIT == u.deg_C else DATA.to(STD_UNIT)

                    self.arrays[KEY] = DATA
                    self.df[KEY] = DATA.value

    def _dt(self):
        if 't' not in self.arrays: return 60
        intervals = np.diff(self.arrays['t'].value)
        if len(intervals) == 0: return 1
        rounded_intervals = np.round(intervals, 3)
        dt_mode = np.nanmedian(rounded_intervals)
        return dt_mode

    def _type(self):
        V = self.arrays.get('V')
        if V is not None:
            V_valid = V[np.isfinite(V.value)]
            if len(V_valid) >= 2:
                return (V_valid[-1] - V_valid[0]).value > 0
        I = self.arrays.get('I')
        if I is not None:
            I_mean = np.nanmean(I.value)
            if np.abs(I_mean) > 1e-6:
                return I_mean > 0
        return True

    ### update (Data 추가) ###
    def update(self, KEY, DATA):
        try:
            self.df[KEY] = DATA.value
            self.arrays[KEY] = DATA
        except:
            self.df[KEY] = DATA
            self.arrays[KEY] = DATA*u.dimensionless_unscaled

    ### denoise (단일 feature 추가용) ###
    def denoise(self,column_name, denoise_strength = 3.5):
        arr_vals = self.df[f'{column_name}'].copy().to_numpy().copy()
        arr_vals_len = int(len(arr_vals)*0.0025)
        arr_unit = self.arrays.get(f'{column_name}').unit
        try:
            arr_vals[np.where(~np.isnan(arr_vals))[0][(1+arr_vals_len):-(1+arr_vals_len)]] = denoise(arr_vals[np.where(~np.isnan(arr_vals))[0][(1+arr_vals_len):-(1+arr_vals_len)]], denoise_strength)
        except:
            try:
                arr_vals[np.where(~np.isnan(arr_vals))[0][(10):-(10)]] = denoise(arr_vals[np.where(~np.isnan(arr_vals))[0][(10):-(10)]], denoise_strength)
            except:
                arr_vals[np.where(~np.isnan(arr_vals))[0]] = denoise(arr_vals[np.where(~np.isnan(arr_vals))[0]], denoise_strength)
        self.update(f'{column_name}_denoise',arr_vals*arr_unit)

    ### slope (단일 feature 추가용) ###
    def slope(self,column_name, Crate: float = 0.2, slope_window: int = 1):
        try:
            self.update(f'd{column_name}',
                        slope(self.arrays.get(f'{column_name}'), max(int(slope_window*12/Crate/self.dt),1))['median'])
        except:
            print(f"Error : There's no '{column_name}'.")

    def slope2(self,column_name):
        if ('t' in self.arrays):
            t_unit  = u.s
            t_vals  = self.df['t'].copy().to_numpy()
            dt_vals = self.df['t'].copy().diff().to_numpy()
            self.update('dt', dt_vals * t_unit)
        elif ('Q' in self.arrays):
            t_unit  = u.s
            t_vals  = self.df['Q'].copy().to_numpy()/np.nanmedian(self.df['Q'].copy().diff().to_numpy())
            self.update('t', t_vals * t_unit)
            dt_vals = self.df['t'].copy().diff().to_numpy()
            self.update('dt', dt_vals * t_unit)
        else:
            t_unit  = u.s
            t_vals  = 60

        try:
            arr_vals = self.df[f'{column_name}'].copy().diff().to_numpy() / dt_vals
            arr_unit = self.arrays.get(f'{column_name}').unit / t_unit
            self.update(f'd{column_name}/dt', arr_vals * arr_unit)
        except:
            print(f"Error : There's no '{column_name}'.")

    def slope3(self,column_name, Crate: float = 0.2, slope_window: int = 1):
        if ('t' in self.arrays):
            t_unit = u.s
            t_vals  = self.df['t'].copy().to_numpy()
            dt_vals = self.df['t'].copy().diff().to_numpy()
            self.update('dt', dt_vals * t_unit)
        elif ('Q' in self.arrays):
            t_unit = u.s
            t_vals = self.df['Q'].copy().to_numpy()/np.nanmedian(self.df['Q'].copy().diff().to_numpy())
            self.update('t', t_vals * t_unit)
            dt_vals = self.df['t'].copy().diff().to_numpy()
            self.update('dt', dt_vals * t_unit)
        else:
            t_unit = u.s
            t_vals = 60

        try:
            arr_vals = slope(self.arrays.get(f'{column_name}'), max(int(slope_window*12/Crate/self.dt),1))['median'] / dt_vals
            arr_unit = self.arrays.get(f'{column_name}').unit / t_unit
            # self.update(f'd{column_name}/dt_{slope_window:.02f}', arr_vals * arr_unit)
            self.update(f'd{column_name}/dt', arr_vals * arr_unit)
        except:
            print(f"Error : There's no '{column_name}'.")

    ### run (dQdV) ###
    def run(self, denoise_strength: float = 3.5, Crate: float = 0.2, slope_window: int = 1):
        '''
        정상 작동 조건
         - BD.df column ['V','Q'] 필수 포함
        Input Parameter
         - Crate, denoise_strength, slope_window
        Output Results
         - Dictionary 형식 {'dVdQ', 'dQdV'}
        '''

        # self.slope2('V')
        self.slope3('V',Crate,slope_window)
        self.slope2('Q')

        self.denoise('dV/dt',denoise_strength)
# 260120_01_denoise_O
        self.denoise('dQ/dt',denoise_strength)
        self.update('dV/dQ', self.arrays.get('dV/dt_denoise') / self.arrays.get('dQ/dt_denoise'))
        self.update('dQ/dV', self.arrays.get('dQ/dt_denoise') / self.arrays.get('dV/dt_denoise'))
# 260120_01_denoise_X
#         self.denoise('dQ/dt',denoise_strength)
#         self.update('dV/dQ', self.arrays.get('dV/dt') / self.arrays.get('dQ/dt'))
#         self.update('dQ/dV', self.arrays.get('dQ/dt') / self.arrays.get('dV/dt'))
# 260120_01_denoise_△1
#         self.denoise('I',denoise_strength)
#         self.update('dV/dQ', self.arrays.get('dV/dt_denoise').copy() / self.arrays.get('I_denoise').copy() * 3600)
#         self.update('dQ/dV', self.arrays.get('I_denoise').copy() / self.arrays.get('dV/dt_denoise').copy() / 3600)

# 260119_07
#         self.slope2('V')
#         self.slope2('Q')
#
#         self.denoise('dV/dt',denoise_strength)
#         self.denoise('dQ/dt',denoise_strength)
#
#         self.update('dV/dQ', self.arrays.get('dV/dt').copy() / self.arrays.get('dQ/dt_denoise').copy())
#         self.update('dQ/dV', self.arrays.get('dQ/dt_denoise').copy() / self.arrays.get('dV/dt').copy())
#
#         self.slope3('V',Crate,2)
#         self.denoise('dV/dt', denoise_strength)
#
#         self.update('dV/dQ_denoise', self.arrays.get('dV/dt').copy() / self.arrays.get('dQ/dt_denoise').copy())
#         self.update('dQ/dV_denoise', self.arrays.get('dQ/dt_denoise').copy() / self.arrays.get('dV/dt').copy())

# 공통부
        self.denoise('dV/dQ',denoise_strength)
        self.denoise('dQ/dV',denoise_strength)


### run - Gaussian Fileter 보정 #########################################################################################
        dVdQ_g = self.arrays.get('dV/dQ').value.copy()
        # dVdQ_g[10:-10] = gaussian_filter1d(denoise(dVdQ_g[10:-10]), max(int(slope_window*12/Crate/self.dt),1))
        dVdQ_g[10:-10] = gaussian_filter1d(denoise(dVdQ_g[10:-10]), max(int(1*12/Crate/self.dt),1))
        dVdQ_g = dVdQ_g * self.arrays.get('dV/dQ').unit
        self.update('dV/dQ_g', dVdQ_g)
        self.update('dQ/dV_g', 1/dVdQ_g)

### run - 참고용 데이터 ##################################################################################################
### 1. Savitzky-Golay filter - small window ###
        dVdQ_d1 = self.arrays.get('dV/dQ').value.copy()
        dQdV_d1 = self.arrays.get('dQ/dV').value.copy()

        dVdQ_d_ls1 = [dVdQ_d1[10:-10]]
        dQdV_d_ls1 = [dQdV_d1[10:-10]]

        for i in [3]:
            for j in [0.02,0.03,0.04]:
                try:
                    dVdQ_d_ls1.append(  savgol_filter(  dVdQ_d1[10:-10], int(len(dVdQ_d1) * j),i))
                    dQdV_d_ls1.append(  savgol_filter(  dQdV_d1[10:-10], int(len(dQdV_d1) * j),i))
                    dVdQ_d_ls1.append(1/savgol_filter(1/dVdQ_d1[10:-10], int(len(dVdQ_d1) * j),i))
                    dQdV_d_ls1.append(1/savgol_filter(1/dQdV_d1[10:-10], int(len(dQdV_d1) * j),i))
                except:
                    pass

        dVdQ_d1[10:-10] = np.nanmedian(dVdQ_d_ls1,axis=0)
        dQdV_d1[10:-10] = np.nanmedian(dQdV_d_ls1,axis=0)

### 2. filtering range reset
        dVdQ_sign = (self.type*2-1)# * check_anode
        dVdQ_cut_ids = np.where(self.arrays.get('dV/dQ').value.copy() * dVdQ_sign > 0)[0]
        dVdQ_cut_ids_cont_id = np.where(np.diff(dVdQ_cut_ids)==1)[0]+1
        dVdQ_cut_ids = dVdQ_cut_ids[dVdQ_cut_ids_cont_id]

        lines = len(dVdQ_d1)
        id_s = max(dVdQ_cut_ids[10],10)
        id_e = min(dVdQ_cut_ids[-10]-lines,-10)
        # print(id_s, id_e)

### 3. Savitzky-Golay filter - large window ###
        dVdQ_d2 = self.arrays.get('dV/dQ').value.copy()
        dQdV_d2 = self.arrays.get('dQ/dV').value.copy()

        dVdQ_d_ls2 = [dVdQ_d2[id_s:id_e]]
        dQdV_d_ls2 = [dQdV_d2[id_s:id_e]]

        for i in [3]:
            for j in [0.03, 0.04, 0.05, 0.06, 0.07]: # for Full Cell
            # for j in (np.array([0.03, 0.04, 0.05, 0.06, 0.07])+Crate/10):  # for Coin Half Cell
            # for j in np.linspace(0.03,np.round(0.03+0.04+Crate/10,2),int((np.round(0.03+0.04+Crate/10,2)-0.02)/0.01)):  # for Coin Half Cell
            # for j in np.linspace(0.03,np.round(0.03+0.04+Crate/10,2),int((np.round(0.05+0.04+Crate/10,2)-0.04)/0.01)):  # for Coin Half Cell
                try:
                    dVdQ_d_ls2.append(1/savgol_filter(1/dVdQ_d2[id_s:id_e], int(len(dVdQ_d2) * j), i))
                    dQdV_d_ls2.append(1/savgol_filter(1/dQdV_d2[id_s:id_e], int(len(dQdV_d2) * j), i))
                    dVdQ_d_ls2.append(  savgol_filter(  dVdQ_d2[id_s:id_e], int(len(dVdQ_d2) * j),i))
                    dQdV_d_ls2.append(  savgol_filter(  dQdV_d2[id_s:id_e], int(len(dQdV_d2) * j),i))
                except:
                    pass

        dVdQ_d2[id_s:id_e] = np.nanmedian(dVdQ_d_ls2,axis=0)
        dQdV_d2[id_s:id_e] = np.nanmedian(dQdV_d_ls2,axis=0)

        dQdV_d2_scaled = np.abs(dQdV_d2) / np.nanmax(np.abs(dQdV_d2[id_s:id_e]))

        dQdV_d2_scaled = np.minimum(np.maximum(dQdV_d2_scaled,0),1)
        dVdQ_d3 = dVdQ_d1 * (1-dQdV_d2_scaled) + dVdQ_d2 * dQdV_d2_scaled
        dQdV_d3 = dQdV_d1 * (1-dQdV_d2_scaled) + dQdV_d2 * dQdV_d2_scaled
        # dVdQ_d3 = dVdQ_d1 * (1-dQdV_d2_scaled)**2 + dVdQ_d2 * (1-(1-dQdV_d2_scaled)**2)
        # dQdV_d3 = dQdV_d1 * (1-dQdV_d2_scaled)**2 + dQdV_d2 * (1-(1-dQdV_d2_scaled)**2)

        dVdQ_d1 = dVdQ_d1 * self.arrays.get('dV/dQ').unit
        dVdQ_d2 = dVdQ_d2 * self.arrays.get('dV/dQ').unit
        dVdQ_d3 = dVdQ_d3 * self.arrays.get('dV/dQ').unit

        dQdV_d1 = dQdV_d1 * self.arrays.get('dQ/dV').unit
        dQdV_d2 = dQdV_d2 * self.arrays.get('dQ/dV').unit
        dQdV_d3 = dQdV_d3 * self.arrays.get('dQ/dV').unit

        self.update('dV/dQ_m1', dVdQ_d1)
        self.update('dV/dQ_m2', dVdQ_d2)
        self.update('dV/dQ_m3', dVdQ_d3)

        self.update('dQ/dV_m1', dQdV_d1)
        self.update('dQ/dV_m2', dQdV_d2)
        self.update('dQ/dV_m3', dQdV_d3)

def example(path, denoise_strength: float = 3.5, Crate: float = 0.2, slope_window: int = 1):
    print(path)
    df = pd.read_csv(path)
    if df.shape[1] == 0:
        df = pd.read_csv(path,sep='\t')
    BD = BatteryData(df)
    BD.run(denoise_strength,Crate,slope_window)

    BD.df.to_excel(path.split('.dat')[0]+'.xlsx',index=False)
########################################################################################################################
    # bk_xw = xw.books.open(path.split('.dat')[0]+'.xlsx')
    # bk_xw.sheets[0].activate()
########################################################################################################################
    # import openpyxl
    # from openpyxl import Workbook
    # from openpyxl.chart import ScatterChart, Reference, Series
    #
    # bk = openpyxl.load_workbook(path.split('.dat')[0] + '.xlsx')
    # sh = bk.active
    #
    # max_row = BD.df.shape[0] + 1
    # find_col_V_denoise = np.where(BD.df.columns == 'V')[0][0] + 1
    # find_col_Q_denoise = np.where(BD.df.columns == 'Q')[0][0] + 1
    # find_col_dVdQ = np.where(BD.df.columns == 'dV/dQ')[0][0] + 1
    # find_col_dVdQ_g = np.where(BD.df.columns == 'dV/dQ_g')[0][0] + 1
    # find_col_dQdV = np.where(BD.df.columns == 'dQ/dV')[0][0] + 1
    # find_col_dQdV_g = np.where(BD.df.columns == 'dQ/dV_g')[0][0] + 1
    # find_col_dVdQ_m = np.where(BD.df.columns == 'dV/dQ_m3')[0][0] + 1
    # find_col_dQdV_m = np.where(BD.df.columns == 'dQ/dV_m3')[0][0] + 1
    #
    # x_val_chart1 = Reference(sh, min_col=find_col_Q_denoise, min_row=2, max_row=max_row)
    # x_val_chart3 = Reference(sh, min_col=find_col_V_denoise, min_row=2, max_row=max_row)
    #
    # y_val_chart1_series1 = Reference(sh, min_col=find_col_dVdQ, min_row=2, max_row=max_row)
    # y_val_chart1_series2 = Reference(sh, min_col=find_col_dVdQ_g, min_row=2, max_row=max_row)
    # y_val_chart1_series3 = Reference(sh, min_col=find_col_dVdQ_m, min_row=2, max_row=max_row)
    #
    # y_val_chart2_series1 = Reference(sh, min_col=find_col_dQdV, min_row=2, max_row=max_row)
    # y_val_chart2_series2 = Reference(sh, min_col=find_col_dQdV_g, min_row=2, max_row=max_row)
    # y_val_chart2_series3 = Reference(sh, min_col=find_col_dQdV_m, min_row=2, max_row=max_row)
    #
    # chart1 = ScatterChart()
    # # chart1.style = 1
    # chart1.height = 7.8
    # chart1.width = 12.84
    # chart1.auto_axis = True
    # chart1.y_axis.scaling.min = 0.5 * (BD.type - 1)
    # chart1.y_axis.scaling.max = 0.5 * (BD.type)
    # chart1.series.append(Series(y_val_chart1_series1, x_val_chart1, title='dVdQ'))
    # chart1.series.append(Series(y_val_chart1_series2, x_val_chart1, title='dVdQ_g'))
    # chart1.series.append(Series(y_val_chart1_series3, x_val_chart1, title='dVdQ_m'))
    #
    # chart2 = ScatterChart()
    # # chart2.style = 1
    # chart2.height = 7.8
    # chart2.width = 12.84
    # chart2.auto_axis = True
    # chart2.y_axis.scaling.min = 20 * (BD.type - 1)
    # chart2.y_axis.scaling.max = 20 * (BD.type)
    # chart2.series.append(Series(y_val_chart2_series1, x_val_chart1, title='dVdQ'))
    # chart2.series.append(Series(y_val_chart2_series2, x_val_chart1, title='dVdQ_g'))
    # chart2.series.append(Series(y_val_chart2_series3, x_val_chart1, title='dVdQ_m'))
    #
    # chart3 = ScatterChart()
    # # chart3.style = 1
    # chart3.height = 7.8
    # chart3.width = 12.84
    # chart3.x_axis.scaling.min = np.floor(np.min(BD.arrays.get('V').value))
    # chart3.x_axis.scaling.max = np.ceil(np.max(BD.arrays.get('V').value))
    # chart3.x_axis.majorUnit = 0.1
    # chart3.y_axis.scaling.min = 0.5 * (BD.type - 1)
    # chart3.y_axis.scaling.max = 0.5 * (BD.type)
    # chart3.series.append(Series(y_val_chart1_series1, x_val_chart3, title='dQdV'))
    # chart3.series.append(Series(y_val_chart1_series2, x_val_chart3, title='dQdV_g'))
    # chart3.series.append(Series(y_val_chart1_series3, x_val_chart3, title='dQdV_m'))
    #
    # chart4 = ScatterChart()
    # # chart4.style = 1
    # chart4.height = 7.8
    # chart4.width = 12.84
    # chart4.x_axis.scaling.min = np.floor(np.min(BD.arrays.get('V').value))
    # chart4.x_axis.scaling.max = np.ceil(np.max(BD.arrays.get('V').value))
    # chart4.x_axis.majorUnit = 0.1
    # chart4.y_axis.scaling.min = 20 * (BD.type - 1)
    # chart4.y_axis.scaling.max = 20 * (BD.type)
    # chart4.series.append(Series(y_val_chart2_series1, x_val_chart3, title='dQdV'))
    # chart4.series.append(Series(y_val_chart2_series2, x_val_chart3, title='dQdV_g'))
    # chart4.series.append(Series(y_val_chart2_series3, x_val_chart3, title='dQdV_m'))
    #
    # sh.add_chart(chart1, f'{get_char(BD.df.shape[1] + 2)}2')
    # sh.add_chart(chart2, f'{get_char(BD.df.shape[1] + 2)}15')
    # sh.add_chart(chart3, f'{get_char(BD.df.shape[1] + 9)}2')
    # sh.add_chart(chart4, f'{get_char(BD.df.shape[1] + 9)}15')
    # time.sleep(1)
    #
    # bk.save(path.split('.dat')[0] + '.xlsx')
    # bk.close()
    #
    # return BD
