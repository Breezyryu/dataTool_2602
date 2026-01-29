import numpy as np
import pandas as pd
import xlwings as xw
from openpyxl.utils import get_column_letter as get_char
import matplotlib.pyplot as plt
from glob2 import glob
import time

from Lib_LKS_common import ActCell, from_excel2
from Lib_LKS_units import UNIT_check; import astropy.units as u
from scipy.ndimage import gaussian_filter1d
from Lib_LKS_denoise import denoise, dMSMCD as slope
from Lib_LKS_BatteryData import BatteryData, example
import warnings
warnings.simplefilter("ignore", category=RuntimeWarning)

UNIT = UNIT_check() # {'t': u.sec, 'V': u.V, 'I': u.A, 'Q': u.Ah, 'T': u.deg_C3}

FILE_Fullcell = './smoothing_ref/dvdqraw/Gen4P 4905mAh HHP ATL 055CY - 복사본.txt'
FILE_Anode    = './smoothing_ref/dvdqraw/S25_291_anode_dchg_02C - 복사본.txt'
FILE_Cathode  = './smoothing_ref/dvdqraw/S25_291_cathode_dchg_02C - 복사본.txt'

DATA_Fullcell = example(FILE_Fullcell, denoise_strength=3.5, Crate=0.2, slope_window=2)
DATA_Anode    = example(FILE_Anode, denoise_strength=3.5, Crate=0.2, slope_window=120)
DATA_Cathode  = example(FILE_Cathode, denoise_strength=3.5, Crate=0.2, slope_window=2)
