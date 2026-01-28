"""
Battery Data Tool - Main Window Class

메인 윈도우 클래스 및 이벤트 핸들러
"""

import os
import sys
import re
import bisect
import warnings
import json
import pyodbc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit, root_scalar
from scipy.stats import linregress
from tkinter import Tk, filedialog

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# battery_tool 모듈 import
from battery_tool.utils import (
    to_timestamp, progress, multi_askopendirnames,
    extract_text_in_brackets, separate_series, name_capacity,
    binary_search, remove_end_comma, check_cycler, convert_steplist,
    same_add, err_msg, connect_change, disconnect_change,
)
from battery_tool.visualization import (
    graph_base_parameter, graph_cycle_base, graph_cycle, graph_cycle_empty,
    graph_output_cycle, graph_step, graph_continue, graph_soc_continue,
    graph_profile, graph_soc_set, graph_soc_err, graph_set_profile,
    graph_set_guide, graph_dcir, graph_soc_dcir, graph_simulation,
    graph_eu_set, graph_default, output_data, output_para_fig, output_fig,
)
from battery_tool.data_processing import (
    toyo_read_csv, toyo_Profile_import, toyo_cycle_import, toyo_min_cap,
    toyo_cycle_data, toyo_chg_Profile_data, toyo_dchg_Profile_data,
    toyo_step_Profile_data, toyo_rate_Profile_data, toyo_Profile_continue_data,
    pne_search_cycle, pne_data, pne_continue_data, pne_min_cap,
    pne_cycle_data, pne_step_Profile_data, pne_rate_Profile_data,
)
from battery_tool.analysis import generate_params, generate_simulation_full

from .ui_sitool import Ui_sitool

# 경고 무시
warnings.simplefilter("ignore")
# 한글 설정
plt.rcParams["font.family"] = "Malgun gothic"
plt.rcParams["axes.unicode_minus"] = False


class WindowClass(QtWidgets.QMainWindow, Ui_sitool):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.chnlnow = "default"
        self.tab_no = 0
        # 충방전기 세팅 관련
        self.toyo_blk_list = ['BLK1', 'BLK2', 'BLK3', 'BLK4', 'BLK5']
        self.toyo_column_list = ['chno', 'use', 'testname', 'folder', 'day', 'part', 'name', 'temp', 'cyc', 'vol', 'path']
        self.toyo_cycler_name = ["Toyo #1", "Toyo #2", "Toyo #3", "Toyo #4", "Toyo #5"]
        self.pne_blk_list = ['PNE1', 'PNE2', 'PNE3', 'PNE4', 'PNE5', 'PNE01', 'PNE02', 'PNE03', 'PNE04', 'PNE05', 'PNE06',
                             'PNE07', 'PNE08', 'PNE09', 'PNE10', 'PNE11', 'PNE12', 'PNE13', 'PNE14', 'PNE15', 'PNE16',
                             'PNE17', 'PNE18', 'PNE19', 'PNE20', 'PNE21', 'PNE22', 'PNE23', 'PNE24', 'PNE25']
        self.pne_work_path_list = ['y:\\Working\\PNE1\\','y:\\Working\\PNE2\\',
                               'x:\\Working\\PNE3\\', 'x:\\Working\\PNE4\\', 'x:\\Working\\PNE5\\',
                               'w:\\Working\\PNE1\\', 'w:\\Working\\PNE2\\', 'w:\\Working\\PNE3\\', 'w:\\Working\\PNE4\\',
                               'w:\\Working\\PNE5\\', 'w:\\Working\\PNE6\\', 'w:\\Working\\PNE7\\', 'w:\\Working\\PNE8\\',
                               'v:\\Working\\PNE9\\', 'v:\\Working\\PNE10\\', 'v:\\Working\\PNE11\\', 'v:\\Working\\PNE12\\',
                               'v:\\Working\\PNE13\\', 'v:\\Working\\PNE14\\', 'v:\\Working\\PNE15\\', 'v:\\Working\\PNE16\\',
                               'u:\\Working\\PNE17\\', 'u:\\Working\\PNE18\\', 'u:\\Working\\PNE19\\', 'u:\\Working\\PNE20\\',
                               'u:\\Working\\PNE21\\', 'u:\\Working\\PNE22\\', 'u:\\Working\\PNE23\\', 'u:\\Working\\PNE24\\',
                               'u:\\Working\\PNE25\\']
        self.pne_data_path_list = ['y:\\PNE-1 New\\','y:\\PNE-2 New\\',
                               'x:\\PNE-3 New\\', 'x:\\PNE-4\\', 'x:\\PNE-5\\',
                               'w:\\PNE1\\', 'w:\\PNE2\\', 'w:\\PNE3\\', 'w:\\PNE4\\', 'w:\\PNE5\\',
                               'w:\\PNE6\\', 'w:\\PNE7\\', 'w:\\PNE8\\',
                               'v:\\PNE9\\', 'v:\\PNE10\\', 'v:\\PNE11\\', 'v:\\PNE12\\', 'v:\\PNE13\\',
                               'v:\\PNE14\\', 'v:\\PNE15\\', 'v:\\PNE16\\',
                               'u:\\PNE17\\', 'u:\\PNE18\\', 'u:\\PNE19\\', 'u:\\PNE20\\','u:\\PNE21\\',
                               'u:\\PNE22\\', 'u:\\PNE23\\', 'u:\\PNE24\\', 'u:\\PNE25\\']
        self.pne_cycler_name = ["PNE #1","PNE #2","PNE #3","PNE #4","PNE #5",
                            "PNE 3F - #01","PNE 3F - #02","PNE 3F - #03","PNE 3F - #04","PNE 3F - #05",
                            "PNE 3F - #06","PNE 3F - #07","PNE 3F - #08","PNE 3F - #09","PNE 3F - #10",
                            "PNE 3F - #11","PNE 3F - #12","PNE 3F - #13","PNE 3F - #14","PNE 3F - #15",
                            "PNE 3F - #16","PNE 3F - #17","PNE 3F - #18","PNE 3F - #19","PNE 3F - #20",
                            "PNE 3F - #21", "PNE 3F - #22", "PNE 3F - #23", "PNE 3F - #24", "PNE 3F - #25"]
        # 초기 폴더 경로 설정
        self.an_mat_dvdq_path.setText("d:/!dvdqraw/S25_291_anode_dchg_02C_gen4 수정.txt")
        self.ca_mat_dvdq_path.setText("d:/!dvdqraw/S25_291_cathode_dchg_02C.txt")
        self.pro_dvdq_path.setText("d:/!dvdqraw/Gen4 SDI 4512mAh/Gen4 SDI 450V 13C 4512mAh 45도 100CY.txt")
        self.cycparameter.setText("d:/!cyc_parameter_trend/para_data_Gen4 SDI MP1 업체 02C 수명 241212.txt")
        self.cycparameter2.setText("d:/!cyc_parameter_trend/para_data_Gen4 SDI MP1 업체 05C 수명 241212.txt")
        # UI 기준 초기치 설정 set-up
        self.firstCrate = float(self.ratetext.text())
        if self.inicaprate.isChecked():
            self.mincapacity = 0
        elif self.inicaptype.isChecked():
            self.mincapacity = float(self.capacitytext.text())
        self.xscale = int(self.tcyclerng.text())
        self.setxscale = int(self.setcyclexscale.text())
        self.ylimithigh = float(self.tcyclerngyhl.text())
        self.ylimitlow = float(self.tcyclerngyll.text())
        self.irscale = float(self.dcirscale.text())
        self.CycleNo = convert_steplist(self.stepnum.toPlainText())
        self.smoothdegree = int(self.smooth.text())
        self.mincrate = float(self.cutoff.text())
        self.dqscale = float(self.dqdvscale.text())
        self.dvscale = self.dqscale
        self.vol_y_hlimit = float(self.volrngyhl.text())
        self.vol_y_llimit = float(self.volrngyll.text())
        self.vol_y_gap = float(self.volrnggap.text())
        # 기초 dataframe 생성
        self.df = []
        self.AllchnlData = []
        self.ptn_df_select = []
        self.pne_ptn_merged_df = []
        # 각 버튼에 각각 명령어 할당
        # Combobox set up
        self.tb_info.currentIndexChanged.connect(self.tb_info_combobox)
        self.tb_cycler.currentIndexChanged.connect(self.tb_cycler_combobox)
        self.tb_room.currentIndexChanged.connect(self.tb_room_combobox)
        self.toyosumstate = 0
        self.pnesumstate = 0
        # unmount, mount button에 각각 명령어 할당
        self.mount_toyo.clicked.connect(self.mount_toyo_button)
        self.mount_pne_1.clicked.connect(self.mount_pne1_button)
        self.mount_pne_2.clicked.connect(self.mount_pne2_button)
        self.mount_pne_3.clicked.connect(self.mount_pne3_button)
        self.mount_pne_4.clicked.connect(self.mount_pne4_button)
        self.mount_pne_5.clicked.connect(self.mount_pne5_button)
        self.mount_all.clicked.connect(self.mount_all_button)
        self.unmount_all.clicked.connect(self.unmount_all_button)
        # 충방전기 데이터 보는 버튼
        self.cycle_tab_reset.clicked.connect(self.cycle_tab_reset_confirm_button)
        self.indiv_cycle.clicked.connect(self.indiv_cyc_confirm_button)
        self.overall_cycle.clicked.connect(self.overall_cyc_confirm_button)
        self.link_cycle.clicked.connect(self.link_cyc_confirm_button)
        self.link_cycle_indiv.clicked.connect(self.link_cyc_indiv_confirm_button)
        self.link_cycle_overall.clicked.connect(self.link_cyc_overall_confirm_button)
        self.AppCycConfirm.clicked.connect(self.app_cyc_confirm_button)
        self.StepConfirm.clicked.connect(self.step_confirm_button)
        self.RateConfirm.clicked.connect(self.rate_confirm_button)
        self.ChgConfirm.clicked.connect(self.chg_confirm_button)
        self.DchgConfirm.clicked.connect(self.dchg_confirm_button)
        self.ContinueConfirm.clicked.connect(self.continue_confirm_button)
        self.DCIRConfirm.clicked.connect(self.dcir_confirm_button)
        # SET 관련 버튼
        # self.BMSetProfile.clicked.connect(self.BMSetProfilebutton)
        # self.BMSetCycle.clicked.connect(self.BMSetCyclebutton)
        self.SETTabReset.clicked.connect(self.set_tab_reset_button)
        self.SetlogConfirm.clicked.connect(self.set_log_confirm_button)
        # self.SetlogcycConfirm.clicked.connect(self.SetlogcycConfirmbutton)
        self.SetConfirm.clicked.connect(self.set_confirm_button)
        self.SetCycle.clicked.connect(self.set_cycle_button)
        self.ECTShort.clicked.connect(self.ect_short_button)
        self.ECTSOC.clicked.connect(self.ect_soc_button)
        self.ECTSetProfile.clicked.connect(self.ect_set_profile_button)
        self.ECTSetCycle.clicked.connect(self.ect_set_cycle_button)
        self.ECTSetlog.clicked.connect(self.ect_set_log_button)
        self.ECTSetlog2.clicked.connect(self.ect_set_log2_button)
        # EU 수명 예측 버튼
        self.ParameterReset_eu.clicked.connect(self.eu_parameter_reset_button)
        self.TabReset_eu.clicked.connect(self.eu_tab_reset_button)
        self.load_cycparameter_eu.clicked.connect(self.eu_load_cycparameter_button)
        self.save_cycparameter_eu.clicked.connect(self.eu_save_cycparameter_button)
        self.FitConfirm_eu.clicked.connect(self.eu_fitting_confirm_button)
        self.ConstFitConfirm_eu.clicked.connect(self.eu_constant_fitting_confirm_button)
        self.indivConstFitConfirm_eu.clicked.connect(self.eu_indiv_constant_fitting_confirm_button)
        # 승인 수명 예측 버튼
        self.load_cycparameter.clicked.connect(self.load_cycparameter_button)
        self.AppCycleTabReset.clicked.connect(self.app_cycle_tab_reset_button)
        self.folderappcycestimation.clicked.connect(self.folder_approval_cycle_estimation_button)
        self.pathappcycestimation.clicked.connect(self.path_approval_cycle_estimation_button)
        self.folderappcycestimation.setDisabled(True)
        self.pathappcycestimation.setDisabled(True)
        # 필드 수명 예측 관련 버튼
        self.SimulConfirm.clicked.connect(self.simulation_confirm_button)
        self.SimulTabResetConfirm.clicked.connect(self.simulation_tab_reset_confirm_button)
        # 패턴 수정 버튼
        self.chg_ptn.clicked.connect(self.ptn_change_pattern_button)
        self.chg_ptn_refi.clicked.connect(self.ptn_change_refi_button)
        self.chg_ptn_endi.clicked.connect(self.ptn_change_endi_button)
        self.chg_ptn_chgv.clicked.connect(self.ptn_change_chgv_button)
        self.chg_ptn_dchgv.clicked.connect(self.ptn_change_dchgv_button)
        self.chg_ptn_endv.clicked.connect(self.ptn_change_endv_button)
        self.chg_ptn_step.clicked.connect(self.ptn_change_step_button)
        self.ptn_load.clicked.connect(self.ptn_load_button)
        # dVdQ fitting
        self.min_rms = np.inf
        self.mat_dvdq_btn.clicked.connect(self.dvdq_material_button)
        self.pro_dvdq_btn.clicked.connect(self.dvdq_profile_button)
        self.dvdq_ini_reset.clicked.connect(self.dvdq_ini_reset_button)
        self.dvdq_fitting.clicked.connect(self.dvdq_fitting_button)
        self.dvdq_fitting_2.clicked.connect(self.dvdq_fitting2_button)
        self.fittingdegree = 1
        # cycle 초기 a변수 설정
        parini1 = [0.03, -18, 0.7, 2.3, -782, -0.28, 96, 1]
        # 저장 초기 변수 설정
        parini2 = [0.03, -18, 0.7, 2.3, -782, -0.28, 96, 1]
        # 초기 parameter 설정
        simul_parameter = [self.aTextEdit, self.bTextEdit, self.b1TextEdit, self.cTextEdit, self.dTextEdit, self.eTextEdit,
                           self.fTextEdit, self.fdTextEdit]
        for i, text_edit in enumerate(simul_parameter):
            text_edit.setText(str(parini1[i]))
            text_edit_2 = getattr(self, f"{text_edit.objectName()}_2")
            text_edit_2.setText(str(parini2[i]))
            text_edit_3 = getattr(self, f"{text_edit.objectName()}_3")
            text_edit_3.setText(str(parini1[i]))
            text_edit_4 = getattr(self, f"{text_edit.objectName()}_4")
            text_edit_4.setText(str(parini2[i]))
        if os.path.isdir("z:"):
            connect_change(self.mount_toyo)
        else:
            disconnect_change(self.mount_toyo)
        if os.path.isdir("y:"):
            connect_change(self.mount_pne_1)
        else:
            disconnect_change(self.mount_pne_1)
        if os.path.isdir("x:"):
            connect_change(self.mount_pne_2)
        else:
            disconnect_change(self.mount_pne_2)
        if os.path.isdir("w:"):
            connect_change(self.mount_pne_3)
        else:
            disconnect_change(self.mount_pne_3)
        if os.path.isdir("v:"):
            connect_change(self.mount_pne_4)
        else:
            disconnect_change(self.mount_pne_4)
        if os.path.isdir("u:"):
            connect_change(self.mount_pne_5)
        else:
            disconnect_change(self.mount_pne_5)

    def cyc_ini_set(self):
        # UI 기준 초기 설정 데이터
        firstCrate = float(self.ratetext.text())
        if self.inicaprate.isChecked():
            mincapacity = 0
        elif self.inicaptype.isChecked():
            mincapacity = float(self.capacitytext.text())
        xscale = int(self.tcyclerng.text())
        ylimithigh = float(self.tcyclerngyhl.text())
        ylimitlow = float(self.tcyclerngyll.text())
        irscale = float(self.dcirscale.text())
        return firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale

    def Profile_ini_set(self):
        # UI 기준 초기 설정 데이터
        firstCrate = float(self.ratetext.text())
        if self.inicaprate.isChecked():
            mincapacity = 0
        elif self.inicaptype.isChecked():
            mincapacity = float(self.capacitytext.text())
        CycleNo = convert_steplist(self.stepnum.toPlainText())
        smoothdegree = int(self.smooth.text())
        mincrate = float(self.cutoff.text())
        dqscale = float(self.dqdvscale.text())
        dvscale = dqscale
        self.vol_y_hlimit = float(self.volrngyhl.text())
        self.vol_y_llimit = float(self.volrngyll.text())
        self.vol_y_gap = float(self.volrnggap.text())
        return firstCrate, mincapacity, CycleNo, smoothdegree, mincrate, dqscale, dvscale

    def tab_delete(self, tab):
        while tab.count() > 0:
            tab.removeTab(0)

    #종료이벤트 발생시 종료
    def closeEvent(self, QCloseEvent):
        sys.exit()

    def inicaprate_on(self):
        self.inicaprate.setChecked(True)

    def inicaptype_on(self):
        self.inicaptype.setChecked(True)

    def pne_path_setting(self):
        all_data_name = []
        all_data_folder = []
        datafilepath = []
        # path file이 있을 경우
        if self.chk_cyclepath.isChecked():
            datafilepath = filedialog.askopenfilename(initialdir="d://", title="Choose Test files")
            if datafilepath:
                cycle_path = pd.read_csv(datafilepath, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
                if hasattr(cycle_path,"cyclepath"):
                    all_data_folder = np.array(cycle_path.cyclepath.tolist())
                    if hasattr(cycle_path,"cyclename"):
                        all_data_name = np.array(cycle_path.cyclename.tolist())
                    if (self.inicaprate.isChecked()) and ("mAh" in datafilepath):
                        self.mincapacity = name_capacity(datafilepath)
                        self.capacitytext.setText(str(self.mincapacity))
                else:
                    all_data_folder = multi_askopendirnames()
            else:
                all_data_folder = multi_askopendirnames()
        elif self.stepnum_2.toPlainText() != "":
            datafilepath = list(map(str, self.stepnum_2.toPlainText().split('\n')))
            all_data_folder = np.array(datafilepath)
        else:
            all_data_folder = multi_askopendirnames()
            datafilepath = all_data_folder
        return [all_data_folder, all_data_name, datafilepath]

    def app_pne_path_setting(self):
        all_data_name = []
        all_data_folder = multi_askopendirnames()
        return [all_data_folder, all_data_name]

    def cycle_tab_reset_confirm_button(self):
        self.tab_delete(self.cycle_tab)
        self.tab_no = 0
    
    def app_cyc_confirm_button(self):
        # 버튼 비활성화
        global writer
        self.AppCycState = True
        self.AppCycConfirm.setDisabled(True)
        firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale = self.cyc_ini_set()
        graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22',
                      '#17becf', ]
        filecount,colorno , columncount = 0, 0, 0
        dfoutput = pd.DataFrame()
        col_name_output = []
        root = Tk()
        root.withdraw()
        filename = ""
        all_data_folder = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        self.AppCycConfirm.setEnabled(True)
        fig, ((ax1)) = plt.subplots(nrows=1, ncols=1, figsize=(14, 8))
        tab_no = 0
        for i, datafilepath in enumerate(all_data_folder):
            # tab 그래프 추가
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout(tab)
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, None)
            if (self.inicaprate.isChecked()) and ("mAh" in datafilepath):
                mincapacity = name_capacity(datafilepath)
                self.capacitytext.setText(str(mincapacity))
            else:
                mincapacity = float(self.capacitytext.text())
            filename = datafilepath.split(".x")[-2].split("/")[-1].split("\\")[-1]
            try:
                wb = xw.Book(datafilepath)
                df = wb.sheets("Plot Base Data").used_range.offset(1,0).options(pd.DataFrame, index=False, header=False).value
                xw.apps.active.quit()
                df = df.drop(0)
                df = df.iloc[:,1::2]
                # df = df.dropna(axis=0)
                df.reset_index(drop=True, inplace=True)
                df.index = df.index + 1
                col_name = [filename for i in range(0, len(df.columns))]
                df = df/mincapacity
                # df.index = df.index + 1
                if df.iat[2, 0] < df.iat[0, 0] * 0.5:
                    count = len(df)
                    lastcount = int((count + int(count / 199) + 1) / 2 + 1)
                    index = 0
                    for i in range(lastcount - 1):
                        if (index == 0) or (index == 197):
                            index = index + 1
                        else:
                            if (index > 197) and ((index - 197) % 199 == 0):
                                index = index + 1
                            else:
                                df.loc[index + 1,:] = df.loc[index + 1,:] + df.loc[index + 2,:]
                                df.drop(index + 2, axis=0, inplace=True)
                                index = index + 2
                    df.reset_index(drop=True, inplace=True)
                    df.index = df.index + 1
                columncount = 0
                for col, column in df.items():
                    if columncount == 0:
                        graph_cycle(df.index, column, ax1, ylimitlow, ylimithigh, 0.05, "Cycle", "Discharge Capacity Ratio",
                                    filename, xscale, graphcolor[colorno])
                    else:
                        graph_cycle(df.index, column, ax1, ylimitlow, ylimithigh, 0.05, "Cycle", "Discharge Capacity Ratio",
                                    "" , xscale, graphcolor[colorno])
                    columncount = columncount + 1
                    colorno = (colorno + 1)%10
                filecountmax = len(all_data_folder)
                progressdata = filecount/filecountmax * 100
                filecount = filecount + 1
                self.progressBar.setValue(int(progressdata))
                dfoutput = pd.concat([dfoutput, df], axis=1)
                col_name_output = col_name_output + col_name
            except Exception as e:
                print(f"오류 발생: {e}")
                raise
        if self.saveok.isChecked() and save_file_name:
            dfoutput.to_excel(writer, sheet_name="Approval_cycle", header = col_name_output)
            writer.close()
        if filename != "":
            plt.suptitle(filename, fontsize= 15, fontweight='bold')
            plt.legend(loc="upper right")
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            self.progressBar.setValue(100)
            output_fig(self.figsaveok, filename)
            tab_layout.addWidget(toolbar)
            tab_layout.addWidget(canvas)
            self.cycle_tab.addTab(tab, str(tab_no))
            self.cycle_tab.setCurrentWidget(tab)
            tab_no = tab_no + 1
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        plt.close()

    def indiv_cyc_confirm_button(self):
        firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale = self.cyc_ini_set()
        # 용량 선정 관련
        global writer
        foldercount, chnlcount, writecolno, writerowno, Chnl_num, colorno = 0, 0, 0, 0, 0, 0
        root = Tk()
        root.withdraw()
        self.indiv_cycle.setDisabled(True)
        pne_path = self.pne_path_setting()
        all_data_folder = pne_path[0]
        all_data_name = pne_path[1]
        if pne_path[2]:
            mincapacity = name_capacity(pne_path[2])
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        self.indiv_cycle.setEnabled(True)
        graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        j = 0
        # while self.cycle_tab.count() > 0:
        #     self.cycle_tab.removeTab(0)
        tab_no = 0
        for i, cyclefolder in enumerate(all_data_folder):
            fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3, figsize=(14, 8))
            if os.path.exists(cyclefolder):
                subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                foldercountmax = len(all_data_folder)
                foldercount = foldercount + 1
                for FolderBase in subfolder:
                    # tab 그래프 추가
                    tab = QtWidgets.QWidget()
                    tab_layout = QtWidgets.QVBoxLayout(tab)
                    canvas = FigureCanvas(fig)
                    toolbar = NavigationToolbar(canvas, None)
                    chnlcountmax = len(subfolder)
                    chnlcount = chnlcount + 1
                    progressdata = progress(foldercount, foldercountmax, chnlcount, chnlcountmax, 1, 1)
                    self.progressBar.setValue(int(progressdata))
                    cycnamelist = FolderBase.split("\\")
                    headername = [cycnamelist[-2] + ", " + cycnamelist[-1]]
                    if len(all_data_name) != 0 and j == i:
                        lgnd = all_data_name[i]
                        j = j + 1
                    elif len(all_data_name) != 0 and j != i:
                        lgnd = ""
                    else:
                        lgnd = extract_text_in_brackets(cycnamelist[-1])
                    if not check_cycler(cyclefolder):
                        cyctemp = toyo_cycle_data(FolderBase, mincapacity, firstCrate, self.dcirchk_2.isChecked())
                    else:
                        cyctemp = pne_cycle_data(FolderBase, mincapacity, firstCrate, self.dcirchk.isChecked(),
                                                    self.dcirchk_2.isChecked(), self.mkdcir.isChecked())
                    if hasattr(cyctemp[1], "NewData"):
                        self.capacitytext.setText(str(cyctemp[0]))
                        irscale = float(self.dcirscale.text())
                        if irscale == 0 and cyctemp[0] != 0:
                            irscale = int(1/(cyctemp[0]/5000) + 1)//2 * 2
                        if self.mkdcir.isChecked() and hasattr(cyctemp[1].NewData, "dcir2"):
                            graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, lgnd, lgnd, colorno,
                                                graphcolor, self.mkdcir, ax1, ax2, ax3, ax4, ax5, ax6)
                        else:
                            graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, lgnd, lgnd, colorno,
                                                graphcolor, self.mkdcir, ax1, ax2, ax3, ax4, ax5, ax6)
                        colorno = colorno + 1
                        # # Data output option
                        if self.saveok.isChecked() and save_file_name:
                            output_data(cyctemp[1].NewData, "방전용량", writecolno, 0, "Dchg", headername)
                            output_data(cyctemp[1].NewData, "Rest End", writecolno, 0, "RndV", headername)
                            output_data(cyctemp[1].NewData, "평균 전압", writecolno, 0, "AvgV", headername)
                            output_data(cyctemp[1].NewData, "충방효율", writecolno, 0, "Eff", headername)
                            output_data(cyctemp[1].NewData, "충전용량", writecolno, 0, "Chg", headername)
                            output_data(cyctemp[1].NewData, "방충효율", writecolno, 0, "Eff2", headername)
                            output_data(cyctemp[1].NewData, "방전Energy", writecolno, 0, "DchgEng", headername)
                            cyctempdcir = cyctemp[1].NewData.dcir.dropna(axis=0)
                            if self.mkdcir.isChecked() and hasattr(cyctemp[1].NewData, "dcir2"):
                                cyctempdcir2 = cyctemp[1].NewData.dcir2.dropna(axis=0)
                                cyctemprssocv = cyctemp[1].NewData.rssocv.dropna(axis=0)
                                cyctemprssccv = cyctemp[1].NewData.rssccv.dropna(axis=0)
                                cyctempsoc70dcir = cyctemp[1].NewData.soc70_dcir.dropna(axis=0)
                                cyctempsoc70rssdcir = cyctemp[1].NewData.soc70_rss_dcir.dropna(axis=0)
                                output_data(cyctempsoc70dcir, "SOC70_DCIR", writecolno, 0, "soc70_dcir", headername)
                                output_data(cyctempsoc70rssdcir, "SOC70_RSS", writecolno, 0, "soc70_rss_dcir", headername)
                                output_data(cyctempdcir, "RSS", writecolno, 0, "dcir", headername)
                                output_data(cyctempdcir2, "DCIR", writecolno, 0, "dcir2", headername)
                                output_data(cyctempdcir, "RSS", writecolno, 0, "dcir", headername)
                                output_data(cyctemprssocv, "RSS_OCV", writecolno, 0, "rssocv", headername)
                                output_data(cyctemprssccv, "RSS_CCV", writecolno, 0, "rssccv", headername)
                            else:
                                output_data(cyctempdcir, "DCIR", writecolno, 0, "dcir", headername)
                            output_data(cyctemp[1].NewData, "충방전기CY", writecolno, 0, "OriCyc", headername)
                            writecolno = writecolno + 1
                    # if len(all_data_name) != 0:
                    plt.suptitle(cycnamelist[-2], fontsize= 15, fontweight='bold')
                    ax1.legend(loc="lower left")
                    ax2.legend(loc="lower right")
                    ax3.legend(loc="upper right")
                    ax4.legend(loc="upper right")
                    ax5.legend(loc="upper right")
                    ax6.legend(loc="lower right")
                    # else:
                    #     plt.suptitle(cycnamelist[-2], fontsize= 15, fontweight='bold')
                    #     # plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                    #     ax6.legend(loc="lower right")
                tab_layout.addWidget(toolbar)
                tab_layout.addWidget(canvas)
                self.cycle_tab.addTab(tab, str(tab_no))
                self.cycle_tab.setCurrentWidget(tab)
                tab_no = tab_no + 1
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                output_fig(self.figsaveok, cycnamelist[-2])
                colorno = 0
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()

    def overall_cyc_confirm_button(self):
        firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale = self.cyc_ini_set()
        # 용량 선정 관련
        global writer
        foldercount, chnlcount, writecolno, writerowno, Chnl_num = 0, 0, 0, 0, 0
        root = Tk()
        root.withdraw()
        self.overall_cycle.setDisabled(True)
        pne_path = self.pne_path_setting()
        all_data_folder = pne_path[0]
        all_data_name = pne_path[1]
        mincapacity = name_capacity(pne_path[2])
        if len(pne_path[2]) != 0:
            if ".t" in pne_path[2][0]:
                overall_filename = pne_path[2][0].split(".t")[-2].split("/")[-1]
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        self.overall_cycle.setEnabled(True)
        graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        # Cycle 관련 (그래프통합)
        fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3, figsize=(14, 8))
        writecolno, colorno, j, overall_xlimit = 0, 0, 0, 0
        tab_no = 0
        for i, cyclefolder in enumerate(all_data_folder):
            if os.path.isdir(cyclefolder):
                subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                foldercountmax = len(all_data_folder)
                foldercount = foldercount + 1
                for FolderBase in subfolder:
                    tab = QtWidgets.QWidget()
                    tab_layout = QtWidgets.QVBoxLayout(tab)
                    canvas = FigureCanvas(fig)
                    toolbar = NavigationToolbar(canvas, None)
                    chnlcountmax = len(subfolder)
                    chnlcount = chnlcount + 1
                    progressdata = progress(foldercount, foldercountmax, chnlcount, chnlcountmax, 1, 1)
                    self.progressBar.setValue(int(progressdata))
                    cycnamelist = FolderBase.split("\\")
                    headername = [cycnamelist[-2] + ", " + cycnamelist[-1]]
                    # 중복없이 같은 LOT끼리에서만 legend 추가
                    if len(all_data_name) != 0 and j == i:
                        temp_lgnd = all_data_name[i]
                        j = j + 1
                    elif len(all_data_name) == 0 and j == i:
                        temp_lgnd = cycnamelist[-2].split('_')[-1]
                        j = j + 1
                    else:
                        temp_lgnd = ""
                    if not check_cycler(cyclefolder):
                        cyctemp = toyo_cycle_data(FolderBase, mincapacity, firstCrate, self.dcirchk_2.isChecked())
                    else:
                        cyctemp = pne_cycle_data(FolderBase, mincapacity, firstCrate, self.dcirchk.isChecked(),
                                                    self.dcirchk_2.isChecked(), self.mkdcir.isChecked())
                    if hasattr(cyctemp[1], "NewData"):
                        self.capacitytext.setText(str(cyctemp[0]))
                        if float(self.dcirscale.text()) == 0:
                            irscale_new = int(1/(cyctemp[0]/5000) + 1)//2 * 2
                            irscale = max(irscale, irscale_new)
                        if len(cyctemp[1].NewData.index) > overall_xlimit:
                            overall_xlimit = len(cyctemp[1].NewData.index)
                        if self.mkdcir.isChecked() and hasattr(cyctemp[1].NewData, "dcir2"):
                            graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, temp_lgnd, temp_lgnd,
                                                colorno, graphcolor, self.mkdcir, ax1, ax2, ax3, ax4, ax5, ax6)
                        else:
                            graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, temp_lgnd, temp_lgnd, colorno,
                                                graphcolor, self.mkdcir, ax1, ax2, ax3, ax4, ax5, ax6)
                        # # Data output option
                        if self.saveok.isChecked() and save_file_name:
                            output_data(cyctemp[1].NewData, "방전용량", writecolno, writerowno, "Dchg", headername)
                            output_data(cyctemp[1].NewData, "Rest End", writecolno, writerowno, "RndV", headername)
                            output_data(cyctemp[1].NewData, "평균 전압", writecolno, writerowno, "AvgV", headername)
                            output_data(cyctemp[1].NewData, "충방효율", writecolno, writerowno, "Eff", headername)
                            output_data(cyctemp[1].NewData, "충전용량", writecolno, writerowno, "Chg", headername)
                            output_data(cyctemp[1].NewData, "방충효율", writecolno, writerowno, "Eff2", headername)
                            output_data(cyctemp[1].NewData, "방전Energy", writecolno, writerowno, "DchgEng", headername)
                            cyctempdcir = cyctemp[1].NewData.dcir.dropna(axis=0)
                            if self.mkdcir.isChecked() and hasattr(cyctemp[1].NewData, "dcir2"):
                                cyctempdcir2 = cyctemp[1].NewData.dcir2.dropna(axis=0)
                                cyctemprssocv = cyctemp[1].NewData.rssocv.dropna(axis=0)
                                cyctemprssccv = cyctemp[1].NewData.rssccv.dropna(axis=0)
                                cyctempsoc70dcir = cyctemp[1].NewData.soc70_dcir.dropna(axis=0)
                                cyctempsoc70rssdcir = cyctemp[1].NewData.soc70_rss_dcir.dropna(axis=0)
                                output_data(cyctempsoc70dcir, "SOC70_DCIR", writecolno, 0, "soc70_dcir", headername)
                                output_data(cyctempsoc70rssdcir, "SOC70_RSS", writecolno, 0, "soc70_rss_dcir", headername)
                                output_data(cyctempdcir, "RSS", writecolno, 0, "dcir", headername)
                                output_data(cyctempdcir2, "DCIR", writecolno, 0, "dcir2", headername)
                                output_data(cyctempdcir, "RSS", writecolno, 0, "dcir", headername)
                                output_data(cyctemprssocv, "RSS_OCV", writecolno, 0, "rssocv", headername)
                                output_data(cyctemprssccv, "RSS_CCV", writecolno, 0, "rssccv", headername)
                            else:
                                output_data(cyctempdcir, "DCIR", writecolno, 0, "dcir", headername)
                            writecolno = writecolno + 1
                colorno = colorno % 9 + 1
        if len(all_data_name) != 0:
            ax1.legend(loc="lower left")
            ax2.legend(loc="lower right")
            ax3.legend(loc="upper right")
            ax4.legend(loc="upper right")
            ax5.legend(loc="upper right")
            ax6.legend(loc="lower right")
        else:
            ax6.legend(loc="lower right")
        if "overall_filename" in locals():
            if self.chk_cyclepath.isChecked():
                output_fig(self.figsaveok, overall_filename)
            else:
                output_fig(self.figsaveok, str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        if len(all_data_folder) != 0:
            tab_layout.addWidget(toolbar)
            tab_layout.addWidget(canvas)
            self.cycle_tab.addTab(tab, str(tab_no))
            self.cycle_tab.setCurrentWidget(tab)
            tab_no = tab_no + 1
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()

    def link_cyc_confirm_button(self):
        firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale = self.cyc_ini_set()
        # 용량 선정 관련
        global writer
        foldercount, chnlcount, writecolno, writerowno, Chnl_num = 0, 0, 0, 0, 0
        CycleMax = [0, 0, 0, 0, 0]
        link_writerownum = [0, 0, 0, 0, 0]
        root = Tk()
        root.withdraw()
        self.link_cycle.setDisabled(True)
        pne_path = self.pne_path_setting()
        all_data_folder = pne_path[0]
        all_data_name = pne_path[1]
        mincapacity = name_capacity(pne_path[2])
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        self.link_cycle.setEnabled(True)
        graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        # Cycle 관련 (그래프 연결)
        fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3, figsize=(14, 8))
        writecolno ,colorno, j = 0, 0, 0
        # while self.cycle_tab.count() > 0:
        #     self.cycle_tab.removeTab(0)
        tab_no = 0
        for i, cyclefolder in enumerate(all_data_folder):
        # for cyclefolder in all_data_folder:
            if os.path.exists(cyclefolder):
                subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                foldercountmax = len(all_data_folder)
                foldercount = foldercount + 1
                colorno, writecolno , Chnl_num = 0, 0, 0
                for FolderBase in subfolder:
                    tab = QtWidgets.QWidget()
                    tab_layout = QtWidgets.QVBoxLayout(tab)
                    canvas = FigureCanvas(fig)
                    toolbar = NavigationToolbar(canvas, None)
                    chnlcountmax = len(subfolder)
                    chnlcount = chnlcount + 1
                    # progressdata = (foldercount + chnlcount/chnlcountmax - 1)/foldercountmax * 100
                    progressdata = progress(foldercount, foldercountmax, chnlcount, chnlcountmax, 1, 1)
                    self.progressBar.setValue(int(progressdata))
                    cycnamelist = FolderBase.split("\\")
                    headername = [cycnamelist[-2] + ", " + cycnamelist[-1]]
                    if len(all_data_name) != 0 and j == i:
                        lgnd = all_data_name[i]
                        j = j + 1
                    elif len(all_data_name) != 0 and j != i:
                        lgnd = ""
                    else:
                        lgnd = cycnamelist[-1]
                    if not check_cycler(cyclefolder):
                        cyctemp = toyo_cycle_data(FolderBase, mincapacity, firstCrate, self.dcirchk_2.isChecked())
                    else:
                        cyctemp = pne_cycle_data(FolderBase, mincapacity, firstCrate, self.dcirchk.isChecked(),
                                                 self.dcirchk_2.isChecked(), self.mkdcir.isChecked())
                    if hasattr(cyctemp[1], "NewData") and (len(link_writerownum) > Chnl_num):
                        writerowno = link_writerownum[Chnl_num] + CycleMax[Chnl_num]
                        cyctemp[1].NewData.index = cyctemp[1].NewData.index + writerowno
                        if xscale == 0:
                            xscale = len(cyctemp[1].NewData) * (foldercountmax + 1)
                        self.capacitytext.setText(str(cyctemp[0]))
                        if irscale == 0:
                            irscale = int(1/(cyctemp[0]/5000) + 1)//2 * 2
                        if len(all_data_name) == 0:
                            temp_lgnd = ""
                        else:
                            temp_lgnd = lgnd
                        if self.mkdcir.isChecked() and hasattr(cyctemp[1].NewData, "dcir2"):
                            graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, lgnd, temp_lgnd, colorno,
                                               graphcolor, self.mkdcir, ax1, ax2, ax3, ax4, ax5, ax6)
                        else:
                            graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, lgnd, temp_lgnd, colorno,
                                                graphcolor, self.mkdcir, ax1, ax2, ax3, ax4, ax5, ax6)
                        # # Data output option
                        if self.saveok.isChecked() and save_file_name:
                            output_data(cyctemp[1].NewData, "방전용량", writecolno, writerowno, "Dchg", headername)
                            output_data(cyctemp[1].NewData, "Rest End", writecolno, writerowno, "RndV", headername)
                            output_data(cyctemp[1].NewData, "평균 전압", writecolno, writerowno, "AvgV", headername)
                            output_data(cyctemp[1].NewData, "충방효율", writecolno, writerowno, "Eff", headername)
                            output_data(cyctemp[1].NewData, "충전용량", writecolno, writerowno, "Chg", headername)
                            output_data(cyctemp[1].NewData, "방충효율", writecolno, writerowno, "Eff2", headername)
                            output_data(cyctemp[1].NewData, "방전Energy", writecolno, writerowno, "DchgEng", headername)
                            cyctempdcir = cyctemp[1].NewData.dcir.dropna(axis=0)
                            if self.mkdcir.isChecked() and hasattr(cyctemp[1].NewData, "dcir2"):
                                cyctempdcir2 = cyctemp[1].NewData.dcir2.dropna(axis=0)
                                cyctemprssocv = cyctemp[1].NewData.rssocv.dropna(axis=0)
                                cyctemprssccv = cyctemp[1].NewData.rssccv.dropna(axis=0)
                                output_data(cyctempdcir2, "DCIR", writecolno, 0, "dcir2", headername)
                                output_data(cyctempdcir, "RSS", writecolno, 0, "dcir", headername)
                                output_data(cyctemprssocv, "RSS_OCV", writecolno, 0, "rssocv", headername)
                                output_data(cyctemprssccv, "RSS_CCV", writecolno, 0, "rssccv", headername)
                            else:
                                output_data(cyctempdcir, "DCIR", writecolno, 0, "dcir", headername)
                        colorno = colorno + 1
                        writecolno = writecolno + 1
                        CycleMax[Chnl_num] = len(cyctemp[1].NewData)
                        link_writerownum[Chnl_num] = writerowno
                        Chnl_num = Chnl_num + 1
        if "cycnamelist" in locals():
            if len(all_data_name) != 0:
                plt.suptitle(cycnamelist[-2], fontsize= 15, fontweight='bold')
                ax1.legend(loc="lower left")
                ax2.legend(loc="lower right")
                ax3.legend(loc="upper right")
                ax4.legend(loc="upper right")
                ax5.legend(loc="upper right")
                ax6.legend(loc="lower right")
            else:
                plt.suptitle(cycnamelist[-2],fontsize= 15, fontweight='bold')
                plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(canvas)
        self.cycle_tab.addTab(tab, str(tab_no))
        self.cycle_tab.setCurrentWidget(tab)
        tab_no = tab_no + 1
        if "cycnamelist" in locals():
            output_fig(self.figsaveok, cycnamelist[-2])
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()

    def link_cyc_indiv_confirm_button(self):
        firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale = self.cyc_ini_set()
        # 용량 선정 관련
        global writer
        root = Tk()
        root.withdraw()
        self.link_cycle.setDisabled(True)
        all_data_name = []
        all_data_folder = []
        datafilepath = []
        alldatafilepath = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        self.link_cycle.setEnabled(True)
        graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        # Cycle 관련 (그래프 연결)
        writecolno ,colorno, j, writecolnomax = 0, 0, 0, 0
        tab_no = 0
        for k, datafilepath in enumerate(alldatafilepath):
            fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3, figsize=(14, 8))
            folder_cnt, chnl_cnt, writerowno, Chnl_num = 0, 0, 0, 0
            writecolno = writecolnomax
            colorno, j = 0, 0
            CycleMax = [0, 0, 0, 0, 0]
            link_writerownum = [0, 0, 0, 0, 0]
            cycle_path = pd.read_csv(datafilepath, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
            all_data_folder = np.array(cycle_path.cyclepath.tolist())
            if hasattr(cycle_path,"cyclename"):
                all_data_name = np.array(cycle_path.cyclename.tolist())
            if (self.inicaprate.isChecked()) and ("mAh" in datafilepath):
                mincapacity = name_capacity(datafilepath)
                self.capacitytext.setText(str(self.mincapacity))
            for i, cyclefolder in enumerate(all_data_folder):
            # for cyclefolder in all_data_folder:
                if os.path.exists(cyclefolder):
                    subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                    folder_cnt_max = len(all_data_folder)
                    folder_cnt = folder_cnt + 1
                    colorno, writecolno , Chnl_num = 0, 0, 0
                    for j, FolderBase in enumerate(subfolder):
                        tab = QtWidgets.QWidget()
                        tab_layout = QtWidgets.QVBoxLayout(tab)
                        canvas = FigureCanvas(fig)
                        toolbar = NavigationToolbar(canvas, None)
                        chnl_cnt_max = len(subfolder)
                        chnl_cnt = chnl_cnt + 1
                        filepath_max = len(alldatafilepath)
                        progressdata = progress(1, filepath_max, folder_cnt, folder_cnt_max, chnl_cnt, chnl_cnt_max)
                        self.progressBar.setValue(int(progressdata))
                        cycnamelist = FolderBase.split("\\")
                        headername = [cycnamelist[-2] + ", " + cycnamelist[-1]]
                        if len(all_data_name) != 0 and i == 0 and j == 0:
                            lgnd = all_data_name[i]
                        elif len(all_data_name) != 0:
                            lgnd = ""
                        else:
                            lgnd = cycnamelist[-1]
                        if not check_cycler(cyclefolder):
                            cyctemp = toyo_cycle_data(FolderBase, mincapacity, firstCrate, self.dcirchk_2.isChecked())
                        else:
                            cyctemp = pne_cycle_data(FolderBase, mincapacity, firstCrate, self.dcirchk.isChecked(),
                                                     self.dcirchk_2.isChecked(), self.mkdcir.isChecked())
                        if hasattr(cyctemp[1], "NewData") and (len(link_writerownum) > Chnl_num):
                            writerowno = link_writerownum[Chnl_num] + CycleMax[Chnl_num]
                            cyctemp[1].NewData.index = cyctemp[1].NewData.index + writerowno
                            if xscale == 0:
                                xscale = len(cyctemp[1].NewData) * (folder_cnt_max + 1)
                            self.capacitytext.setText(str(cyctemp[0]))
                            if irscale == 0:
                                irscale = int(1/(cyctemp[0]/5000) + 1)//2 * 2
                            if len(all_data_name) == 0:
                                temp_lgnd = ""
                            else:
                                temp_lgnd = lgnd
                            if self.mkdcir.isChecked() and hasattr(cyctemp[1].NewData, "dcir2"):
                                graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, lgnd, temp_lgnd, colorno,
                                                   graphcolor, self.mkdcir, ax1, ax2, ax3, ax4, ax5, ax6)
                            else:
                                graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, lgnd, temp_lgnd, colorno,
                                                    graphcolor, self.mkdcir, ax1, ax2, ax3, ax4, ax5, ax6)
                            # # Data output option
                            if self.saveok.isChecked() and save_file_name:
                                output_data(cyctemp[1].NewData, "방전용량", writecolno, writerowno, "Dchg", headername)
                                output_data(cyctemp[1].NewData, "Rest End", writecolno, writerowno, "RndV", headername)
                                output_data(cyctemp[1].NewData, "평균 전압", writecolno, writerowno, "AvgV", headername)
                                output_data(cyctemp[1].NewData, "충방효율", writecolno, writerowno, "Eff", headername)
                                output_data(cyctemp[1].NewData, "충전용량", writecolno, writerowno, "Chg", headername)
                                output_data(cyctemp[1].NewData, "방충효율", writecolno, writerowno, "Eff2", headername)
                                output_data(cyctemp[1].NewData, "방전Energy", writecolno, writerowno, "DchgEng", headername)
                                cyctempdcir = cyctemp[1].NewData.dcir.dropna(axis=0)
                                if self.mkdcir.isChecked() and hasattr(cyctemp[1].NewData, "dcir2"):
                                    cyctempdcir2 = cyctemp[1].NewData.dcir2.dropna(axis=0)
                                    cyctemprssocv = cyctemp[1].NewData.rssocv.dropna(axis=0)
                                    cyctemprssccv = cyctemp[1].NewData.rssccv.dropna(axis=0)
                                    output_data(cyctempdcir2, "DCIR", writecolno, 0, "dcir2", headername)
                                    output_data(cyctempdcir, "RSS", writecolno, 0, "dcir", headername)
                                    output_data(cyctemprssocv, "RSS_OCV", writecolno, 0, "rssocv", headername)
                                    output_data(cyctemprssccv, "RSS_CCV", writecolno, 0, "rssccv", headername)
                                else:
                                    output_data(cyctempdcir, "DCIR", writecolno, 0, "dcir", headername)
                                output_data(cyctemp[1].NewData, "충방전기CY", writecolno, 0, "OriCyc", headername)
                                writecolno = writecolno + 1
                            colorno = colorno + 1
                            CycleMax[Chnl_num] = len(cyctemp[1].NewData)
                            link_writerownum[Chnl_num] = writerowno
                            Chnl_num = Chnl_num + 1
                            writecolnomax = max(writecolno, writecolnomax)
            if "cycnamelist" in locals():
                if len(all_data_name) != 0:
                    plt.suptitle(cycnamelist[-2], fontsize= 15, fontweight='bold')
                    ax1.legend(loc="lower left")
                    ax2.legend(loc="lower right")
                    ax3.legend(loc="upper right")
                    ax4.legend(loc="upper right")
                    ax5.legend(loc="upper right")
                    ax6.legend(loc="lower right")
                else:
                    plt.suptitle(cycnamelist[-2],fontsize= 15, fontweight='bold')
                    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
            tab_layout.addWidget(toolbar)
            tab_layout.addWidget(canvas)
            self.cycle_tab.addTab(tab, str(tab_no))
            self.cycle_tab.setCurrentWidget(tab)
            tab_no = tab_no + 1
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            if "cycnamelist" in locals():
                output_fig(self.figsaveok, cycnamelist[-2])
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()

    def link_cyc_overall_confirm_button(self):
        firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale = self.cyc_ini_set()
        # 용량 선정 관련
        global writer
        root = Tk()
        root.withdraw()
        self.link_cycle.setDisabled(True)
        all_data_name = []
        all_data_folder = []
        datafilepath = []
        alldatafilepath = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        self.link_cycle.setEnabled(True)
        graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        # Cycle 관련 (그래프 연결)
        fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3, figsize=(14, 8))
        writecolno ,colorno, j, maxcolor, writecolnomax = 0, 0, 0, 0, 0
        tab_no = 0
        for k, datafilepath in enumerate(alldatafilepath):
            folder_cnt, chnl_cnt, writerowno, Chnl_num = 0, 0, 0, 0
            writecolno = writecolnomax
            CycleMax = [0, 0, 0, 0, 0]
            link_writerownum = [0, 0, 0, 0, 0]
            cycle_path = pd.read_csv(datafilepath, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
            all_data_folder = np.array(cycle_path.cyclepath.tolist())
            if hasattr(cycle_path,"cyclename"):
                all_data_name = np.array(cycle_path.cyclename.tolist())
            if (self.inicaprate.isChecked()) and ("mAh" in datafilepath):
                mincapacity = name_capacity(datafilepath)
                self.capacitytext.setText(str(self.mincapacity))
            for i, cyclefolder in enumerate(all_data_folder):
            # for cyclefolder in all_data_folder:
                if os.path.exists(cyclefolder):
                    subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                    folder_cnt_max = len(all_data_folder)
                    folder_cnt = folder_cnt + 1
                    colorno, writecolno , Chnl_num = maxcolor, 0, 0
                    for j, FolderBase in enumerate(subfolder):
                        tab = QtWidgets.QWidget()
                        tab_layout = QtWidgets.QVBoxLayout(tab)
                        canvas = FigureCanvas(fig)
                        toolbar = NavigationToolbar(canvas, None)
                        chnl_cnt_max = len(subfolder)
                        chnl_cnt = chnl_cnt + 1
                        filepath_max = len(alldatafilepath)
                        progressdata = progress(1, filepath_max, folder_cnt, folder_cnt_max, chnl_cnt, chnl_cnt_max)
                        self.progressBar.setValue(int(progressdata))
                        cycnamelist = FolderBase.split("\\")
                        headername = [cycnamelist[-2] + ", " + cycnamelist[-1]]
                        if len(all_data_name) != 0 and i == 0 and j == 0:
                            lgnd = all_data_name[i]
                        elif len(all_data_name) != 0:
                            lgnd = ""
                        else:
                            lgnd = cycnamelist[-1]
                        if not check_cycler(cyclefolder):
                            cyctemp = toyo_cycle_data(FolderBase, mincapacity, firstCrate, self.dcirchk_2.isChecked())
                        else:
                            cyctemp = pne_cycle_data(FolderBase, mincapacity, firstCrate, self.dcirchk.isChecked(),
                                                     self.dcirchk_2.isChecked(), self.mkdcir.isChecked())
                        if hasattr(cyctemp[1], "NewData") and (len(link_writerownum) > Chnl_num):
                            writerowno = link_writerownum[Chnl_num] + CycleMax[Chnl_num]
                            cyctemp[1].NewData.index = cyctemp[1].NewData.index + writerowno
                            if xscale == 0:
                                xscale = len(cyctemp[1].NewData) * (folder_cnt_max + 1)
                            self.capacitytext.setText(str(cyctemp[0]))
                            if irscale == 0:
                                irscale = int(1/(cyctemp[0]/5000) + 1)//2 * 2
                            if len(all_data_name) == 0:
                                temp_lgnd = ""
                            else:
                                temp_lgnd = lgnd
                            if self.mkdcir.isChecked() and hasattr(cyctemp[1].NewData, "dcir2"):
                                graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, lgnd, temp_lgnd, colorno,
                                                   graphcolor, self.mkdcir, ax1, ax2, ax3, ax4, ax5, ax6)
                            else:
                                graph_output_cycle(cyctemp[1], xscale, ylimitlow, ylimithigh, irscale, lgnd, temp_lgnd, colorno,
                                                    graphcolor, self.mkdcir, ax1, ax2, ax3, ax4, ax5, ax6)
                            # Data output option
                            if self.saveok.isChecked() and save_file_name:
                                output_data(cyctemp[1].NewData, "방전용량", writecolno, writerowno, "Dchg", headername)
                                output_data(cyctemp[1].NewData, "Rest End", writecolno, writerowno, "RndV", headername)
                                output_data(cyctemp[1].NewData, "평균 전압", writecolno, writerowno, "AvgV", headername)
                                output_data(cyctemp[1].NewData, "충방효율", writecolno, writerowno, "Eff", headername)
                                output_data(cyctemp[1].NewData, "충전용량", writecolno, writerowno, "Chg", headername)
                                output_data(cyctemp[1].NewData, "방충효율", writecolno, writerowno, "Eff2", headername)
                                output_data(cyctemp[1].NewData, "방전Energy", writecolno, writerowno, "DchgEng", headername)
                                cyctempdcir = cyctemp[1].NewData.dcir.dropna(axis=0)
                                if self.mkdcir.isChecked() and hasattr(cyctemp[1].NewData, "dcir2"):
                                    cyctempdcir2 = cyctemp[1].NewData.dcir2.dropna(axis=0)
                                    cyctemprssocv = cyctemp[1].NewData.rssocv.dropna(axis=0)
                                    cyctemprssccv = cyctemp[1].NewData.rssccv.dropna(axis=0)
                                    output_data(cyctempdcir2, "DCIR", writecolno, 0, "dcir2", headername)
                                    output_data(cyctempdcir, "RSS", writecolno, 0, "dcir", headername)
                                    output_data(cyctemprssocv, "RSS_OCV", writecolno, 0, "rssocv", headername)
                                    output_data(cyctemprssccv, "RSS_CCV", writecolno, 0, "rssccv", headername)
                                else:
                                    output_data(cyctempdcir, "DCIR", writecolno, 0, "dcir", headername)
                                output_data(cyctemp[1].NewData, "충방전기CY", writecolno, 0, "OriCyc", headername)
                                writecolno = writecolno + 1
                            CycleMax[Chnl_num] = len(cyctemp[1].NewData)
                            link_writerownum[Chnl_num] = writerowno
                            Chnl_num = Chnl_num + 1
                            writecolnomax = max(writecolno, writecolnomax)
                colorno = colorno + 1
            maxcolor = max(colorno, maxcolor)
            if "cycnamelist" in locals():
                if len(all_data_name) != 0:
                    plt.suptitle(cycnamelist[-2], fontsize= 15, fontweight='bold')
                    ax1.legend(loc="lower left")
                    ax2.legend(loc="lower right")
                    ax3.legend(loc="upper right")
                    ax4.legend(loc="upper right")
                    ax5.legend(loc="upper right")
                    ax6.legend(loc="lower right")
                else:
                    plt.suptitle(cycnamelist[-2],fontsize= 15, fontweight='bold')
                    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(canvas)
        self.cycle_tab.addTab(tab, str(tab_no))
        self.cycle_tab.setCurrentWidget(tab)
        tab_no = tab_no + 1
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        if "cycnamelist" in locals():
            output_fig(self.figsaveok, cycnamelist[-2])
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()

    def step_confirm_button(self):
        self.StepConfirm.setDisabled(True)
        firstCrate, mincapacity, CycleNo, smoothdegree, mincrate, dqscale, dvscale = self.Profile_ini_set()
        # 용량 선정 관련
        global writer
        write_column_num, folder_count, chnlcount, cyccount = 0, 0, 0, 0
        root = Tk()
        root.withdraw()
        pne_path = self.pne_path_setting()
        all_data_folder = pne_path[0]
        all_data_name = pne_path[1]
        self.StepConfirm.setEnabled(True)
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        if self.ect_saveok.isChecked():
            # save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".csv")
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name")
        tab_no = 0
        for i, cyclefolder in enumerate(all_data_folder):
            if os.path.isdir(cyclefolder):
                subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                foldercountmax = len(all_data_folder)
                folder_count = folder_count + 1
                if self.CycProfile.isChecked():
                    for FolderBase in subfolder:
                        fig, ((step_ax1, step_ax2, step_ax3) ,(step_ax4, step_ax5, step_ax6)) = plt.subplots(
                            nrows=2, ncols=3, figsize=(14, 10))
                        tab = QtWidgets.QWidget()
                        tab_layout = QtWidgets.QVBoxLayout(tab)
                        canvas = FigureCanvas(fig)
                        toolbar = NavigationToolbar(canvas, None)
                        chnlcount = chnlcount + 1
                        chnlcountmax = len(subfolder)
                        if "Pattern" not in FolderBase:
                            for Step_CycNo in CycleNo:
                                cyccountmax = len(CycleNo)
                                cyccount = cyccount + 1
                                progressdata = progress(folder_count, foldercountmax, chnlcount, chnlcountmax, cyccount, cyccountmax)
                                self.progressBar.setValue(int(progressdata))
                                step_namelist = FolderBase.split("\\")
                                headername = step_namelist[-2] + ", " + step_namelist[-1] + ", " + str(Step_CycNo) + "cy, "
                                lgnd = "%04d" % Step_CycNo
                                if not check_cycler(cyclefolder):
                                    temp = toyo_step_Profile_data( FolderBase, Step_CycNo, mincapacity, mincrate, firstCrate)
                                else:
                                    temp = pne_step_Profile_data( FolderBase, Step_CycNo, mincapacity, mincrate, firstCrate)
                                if len(all_data_name) == 0:
                                    temp_lgnd = ""
                                else:
                                    temp_lgnd = all_data_name[i] +" "+lgnd
                                if hasattr(temp[1], "stepchg"):
                                    if len(temp[1].stepchg) > 2:
                                        self.capacitytext.setText(str(temp[0]))
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.Vol, step_ax1, self.vol_y_hlimit, self.vol_y_llimit,
                                                   self.vol_y_gap, "Time(min)", "Voltage(V)", temp_lgnd)
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.Vol, step_ax3, self.vol_y_hlimit, self.vol_y_llimit,
                                                   self.vol_y_gap, "Time(min)", "Voltage(V)", temp_lgnd)
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.Vol, step_ax2, self.vol_y_hlimit, self.vol_y_llimit,
                                                   self.vol_y_gap, "Time(min)", "Voltage(V)", temp_lgnd)
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.Crate, step_ax5, 0, 3.4, 0.2,
                                                   "Time(min)", "C-rate", temp_lgnd)
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.SOC, step_ax4, 0, 1.2, 0.1,
                                                   "Time(min)", "SOC", temp_lgnd)
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.Temp, step_ax6, -15, 60, 5,
                                                   "Time(min)", "Temperature (℃)", lgnd)
                                        # Data output option
                                        if self.saveok.isChecked() and save_file_name:
                                            temp[1].stepchg.to_excel(writer, startcol=write_column_num, index=False,
                                                                header=[headername + "time(min)",
                                                                        headername + "SOC",
                                                                        headername + "Voltage",
                                                                        headername + "Crate",
                                                                        headername + "Temp."])
                                            write_column_num = write_column_num + 5
                                        if self.ect_saveok.isChecked() and save_file_name:
                                            temp[1].stepchg["TimeSec"] = temp[1].stepchg.TimeMin * 60
                                            temp[1].stepchg["Curr"] = temp[1].stepchg.Crate * temp[0]/ 1000
                                            continue_df = temp[1].stepchg.loc[:,["TimeSec", "Vol", "Curr", "Temp"]]
                                            # 각 열을 소수점 자리수에 맞게 반올림
                                            continue_df['TimeSec'] = continue_df['TimeSec'].round(1)  # 소수점 1자리
                                            continue_df['Vol'] = continue_df['Vol'].round(4)           # 소수점 4자리
                                            continue_df['Curr'] = continue_df['Curr'].round(4)         # 소수점 4자리
                                            continue_df['Temp'] = continue_df['Temp'].round(1)         # 소수점 1자리
                                            continue_df.to_csv(save_file_name + "_" + "%04d" % Step_CycNo + ".csv", index=False, sep=',',
                                                                header=["time(s)",
                                                                        "Voltage(V)",
                                                                        "Current(A)",
                                                                        "Temp."])
                            title = step_namelist[-2] + "=" + step_namelist[-1]
                            plt.suptitle(title, fontsize= 15, fontweight='bold')
                            if len(all_data_name) != 0:
                                step_ax1.legend(loc="lower right")
                                step_ax2.legend(loc="lower right")
                                step_ax4.legend(loc="lower right")
                                step_ax3.legend(loc="lower right")
                                step_ax5.legend(loc="upper right")
                                step_ax6.legend(loc="upper right")
                            else:
                                plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                            tab_layout.addWidget(toolbar)
                            tab_layout.addWidget(canvas)
                            self.cycle_tab.addTab(tab, str(tab_no))
                            self.cycle_tab.setCurrentWidget(tab)
                            tab_no = tab_no + 1
                            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                else:
                    for Step_CycNo in CycleNo:
                        fig, ((step_ax1, step_ax2, step_ax3) ,(step_ax4, step_ax5, step_ax6)) = plt.subplots(
                            nrows=2, ncols=3, figsize=(14, 10))
                        tab = QtWidgets.QWidget()
                        tab_layout = QtWidgets.QVBoxLayout(tab)
                        canvas = FigureCanvas(fig)
                        toolbar = NavigationToolbar(canvas, None)
                        chnlcount = chnlcount + 1
                        chnlcountmax = len(subfolder)
                        for FolderBase in subfolder:
                            if "Pattern" not in FolderBase:
                                cyccountmax = len(CycleNo)
                                cyccount = cyccount + 1
                                progressdata = progress(folder_count, foldercountmax, cyccount, cyccountmax, chnlcount, chnlcountmax)
                                self.progressBar.setValue(int(progressdata))
                                step_namelist = FolderBase.split("\\")
                                headername = step_namelist[-2] + ", " + step_namelist[-1] + ", " + str(Step_CycNo) + "cy, "
                                lgnd = step_namelist[-1]
                                if not check_cycler(cyclefolder):
                                    temp = toyo_step_Profile_data( FolderBase, Step_CycNo, mincapacity, mincrate, firstCrate)
                                else:
                                    temp = pne_step_Profile_data( FolderBase, Step_CycNo, mincapacity, mincrate, firstCrate)
                                if len(all_data_name) == 0:
                                    temp_lgnd = ""
                                else:
                                    temp_lgnd = all_data_name[i] +" "+lgnd
                                if hasattr(temp[1], "stepchg"):
                                    if len(temp[1].stepchg) > 2:
                                        self.capacitytext.setText(str(temp[0]))
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.Vol, step_ax1, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap,
                                                   "Time(min)", "Voltage(V)", temp_lgnd)
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.Vol, step_ax3, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap,
                                                   "Time(min)", "Voltage(V)", temp_lgnd)
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.Vol, step_ax2, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap,
                                                   "Time(min)", "Voltage(V)", temp_lgnd)
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.Crate, step_ax5, 0, 3.4, 0.2,
                                                   "Time(min)", "C-rate", temp_lgnd)
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.SOC, step_ax4, 0, 1.2, 0.1,
                                                   "Time(min)", "SOC", temp_lgnd)
                                        graph_step(temp[1].stepchg.TimeMin, temp[1].stepchg.Temp, step_ax6, -15, 60, 5,
                                                   "Time(min)", "Temperature (℃)", lgnd)
                                        # Data output option
                                        if self.saveok.isChecked() and save_file_name:
                                            temp[1].stepchg.to_excel(writer, startcol=write_column_num, index=False,
                                                                header=[headername + "time(min)",
                                                                        headername + "SOC",
                                                                        headername + "Voltage",
                                                                        headername + "Crate",
                                                                        headername + "Temp."])
                                            write_column_num = write_column_num + 5
                                title = step_namelist[-2] + "=" + "%04d" % Step_CycNo
                                plt.suptitle(title, fontsize= 15, fontweight='bold')
                                if len(all_data_name) != 0:
                                    step_ax1.legend(loc="lower right")
                                    step_ax2.legend(loc="lower right")
                                    step_ax4.legend(loc="lower right")
                                    step_ax3.legend(loc="lower right")
                                    step_ax5.legend(loc="upper right")
                                    step_ax6.legend(loc="upper right")
                                else:
                                    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                        tab_layout.addWidget(toolbar)
                        tab_layout.addWidget(canvas)
                        self.cycle_tab.addTab(tab, str(tab_no))
                        self.cycle_tab.setCurrentWidget(tab)
                        tab_no = tab_no + 1
                        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()

    def rate_confirm_button(self):
        self.RateConfirm.setDisabled(True)
        firstCrate, mincapacity, CycleNo, smoothdegree, mincrate, dqscale, dvscale = self.Profile_ini_set()
        # 용량 선정 관련
        global writer
        writecolno, foldercount, chnlcount, cyccount = 0, 0, 0, 0
        root = Tk()
        root.withdraw()
        pne_path = self.pne_path_setting()
        all_data_folder = pne_path[0]
        all_data_name = pne_path[1]
        self.RateConfirm.setEnabled(True)
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        if self.ect_saveok.isChecked():
            # save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".csv")
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name")
        tab_no = 0
        for i, cyclefolder in enumerate(all_data_folder):
            subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
            foldercountmax = len(all_data_folder)
            foldercount = foldercount + 1
            if self.CycProfile.isChecked():
                for FolderBase in subfolder:
                    fig, ((rate_ax1, rate_ax2, rate_ax3) ,(rate_ax4, rate_ax5, rate_ax6)) = plt.subplots(
                        nrows=2, ncols=3, figsize=(14, 10))
                    tab = QtWidgets.QWidget()
                    tab_layout = QtWidgets.QVBoxLayout(tab)
                    canvas = FigureCanvas(fig)
                    toolbar = NavigationToolbar(canvas, None)
                    chnlcount = chnlcount + 1
                    chnlcountmax = len(subfolder)
                    if "Pattern" not in FolderBase:
                        for CycNo in CycleNo:
                            cyccountmax = len(CycleNo)
                            cyccount = cyccount + 1
                            progressdata = progress(foldercount, foldercountmax, chnlcount, chnlcountmax, cyccount, cyccountmax)
                            self.progressBar.setValue(int(progressdata))
                            Ratenamelist = FolderBase.split("\\")
                            headername = Ratenamelist[-2] + ", " + Ratenamelist[-1] + ", " + str(CycNo) + "cy, "
                            lgnd = "%04d" % CycNo
                            if not check_cycler(cyclefolder):
                                Ratetemp = toyo_rate_Profile_data( FolderBase, CycNo, mincapacity, mincrate, firstCrate)
                            else:
                                Ratetemp = pne_rate_Profile_data( FolderBase, CycNo, mincapacity, mincrate, firstCrate)
                            if len(all_data_name) == 0:
                                temp_lgnd = ""
                            else:	
                                temp_lgnd = all_data_name[i] + " " + lgnd
                            if hasattr(Ratetemp[1], "rateProfile"):
                                if len(Ratetemp[1].rateProfile) > 2:
                                    self.capacitytext.setText(str(Ratetemp[0]))
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.Vol, rate_ax1, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap,
                                               "Time(min)", "Voltage(V)", temp_lgnd)
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.Vol, rate_ax4, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap,
                                               "Time(min)", "Voltage(V)", temp_lgnd)
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.Crate, rate_ax2, 0, 3.4, 0.2,
                                               "Time(min)", "C-rate", temp_lgnd)
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.Crate, rate_ax5, 0, 3.4, 0.2,
                                               "Time(min)", "C-rate", temp_lgnd)
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.SOC, rate_ax3, 0, 1.2, 0.1,
                                               "Time(min)", "SOC", temp_lgnd)
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.Temp, rate_ax6, -15, 60, 5,
                                               "Time(min)", "Temp.", lgnd)
                                    # Data output option
                                    if self.saveok.isChecked() and save_file_name:
                                        Ratetemp[1].rateProfile.to_excel(
                                            writer,
                                            startcol=writecolno,
                                            index=False,
                                            header=[
                                                headername + "time(min)",
                                                headername + "SOC",
                                                headername + "Voltage",
                                                headername + "Crate",
                                                headername + "Temp."
                                            ])
                                        writecolno = writecolno + 5
                                    if self.ect_saveok.isChecked() and save_file_name:
                                        Ratetemp[1].Profile["TimeSec"] = Ratetemp[1].Profile.TimeMin * 60
                                        Ratetemp[1].Profile["Curr"] = Ratetemp[1].Profile.Crate * Ratetemp[0] /1000
                                        continue_df = Ratetemp[1].Profile.loc[:,["TimeSec", "Vol", "Curr", "Temp"]]
                                        # 각 열을 소수점 자리수에 맞게 반올림
                                        continue_df['TimeSec'] = continue_df['TimeSec'].round(1)  # 소수점 1자리
                                        continue_df['Vol'] = continue_df['Vol'].round(4)           # 소수점 4자리
                                        continue_df['Curr'] = continue_df['Curr'].round(4)         # 소수점 4자리
                                        continue_df['Temp'] = continue_df['Temp'].round(1)         # 소수점 1자리
                                        continue_df.to_csv(save_file_name + "_" + "%04d" % CycNo + ".csv", index=False, sep=',',
                                                            header=["time(s)",
                                                                    "Voltage(V)",
                                                                    "Current(A)",
                                                                    "Temp."])
                            title = Ratenamelist[-2] + "=" + Ratenamelist[-1]
                            plt.suptitle(title, fontsize= 15, fontweight='bold')
                            if len(all_data_name) != 0:
                                rate_ax1.legend(loc="lower right")
                                rate_ax2.legend(loc="upper right")
                                rate_ax3.legend(loc="lower right")
                                rate_ax4.legend(loc="lower right")
                                rate_ax5.legend(loc="upper right")
                                rate_ax6.legend(loc="upper right")
                            else:
                                plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                        tab_layout.addWidget(toolbar)
                        tab_layout.addWidget(canvas)
                        self.cycle_tab.addTab(tab, str(tab_no))
                        self.cycle_tab.setCurrentWidget(tab)
                        tab_no = tab_no + 1
                        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                        output_fig(self.figsaveok, title)
            else:
                for CycNo in CycleNo:
                    fig, ((rate_ax1, rate_ax2, rate_ax3) ,(rate_ax4, rate_ax5, rate_ax6)) = plt.subplots(
                        nrows=2, ncols=3, figsize=(14, 10))
                    tab = QtWidgets.QWidget()
                    tab_layout = QtWidgets.QVBoxLayout(tab)
                    canvas = FigureCanvas(fig)
                    toolbar = NavigationToolbar(canvas, None)
                    chnlcount = chnlcount + 1
                    chnlcountmax = len(subfolder)
                    for FolderBase in subfolder:
                        if "Pattern" not in FolderBase:
                            cyccountmax = len(CycleNo)
                            cyccount = cyccount + 1
                            progressdata = progress(foldercount, foldercountmax, cyccount, cyccountmax, chnlcount, chnlcountmax)
                            self.progressBar.setValue(int(progressdata))
                            Ratenamelist = FolderBase.split("\\")
                            headername = Ratenamelist[-2] + ", " + Ratenamelist[-1] + ", " + str(CycNo) + "cy, "
                            lgnd = Ratenamelist[-1]
                            if not check_cycler(cyclefolder):
                                Ratetemp = toyo_rate_Profile_data( FolderBase, CycNo, mincapacity, mincrate, firstCrate)
                            else:
                                Ratetemp = pne_rate_Profile_data( FolderBase, CycNo, mincapacity, mincrate, firstCrate)
                            if len(all_data_name) == 0:
                                temp_lgnd = ""
                            else:	
                                temp_lgnd = all_data_name[i] + " " + lgnd
                            if hasattr(Ratetemp[1], "rateProfile"):
                                if len(Ratetemp[1].rateProfile) > 2:
                                    self.capacitytext.setText(str(Ratetemp[0]))
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.Vol, rate_ax1, self.vol_y_hlimit,
                                               self.vol_y_llimit, self.vol_y_gap, "Time(min)", "Voltage(V)", temp_lgnd)
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.Vol, rate_ax4, self.vol_y_hlimit,
                                               self.vol_y_llimit, self.vol_y_gap, "Time(min)", "Voltage(V)", temp_lgnd)
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.Crate, rate_ax2, 0, 3.4, 0.2,
                                               "Time(min)", "C-rate", temp_lgnd)
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.Crate, rate_ax5, 0, 3.4, 0.2,
                                               "Time(min)", "C-rate", temp_lgnd)
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.SOC, rate_ax3, 0, 1.2, 0.1,
                                               "Time(min)", "SOC", temp_lgnd)
                                    graph_step(Ratetemp[1].rateProfile.TimeMin, Ratetemp[1].rateProfile.Temp, rate_ax6, -15, 60, 5,
                                               "Time(min)", "Temp.", lgnd)
                                    # Data output option
                                    if self.saveok.isChecked() and save_file_name:
                                        Ratetemp[1].rateProfile.to_excel(
                                            writer,
                                            startcol=writecolno,
                                            index=False,
                                            header=[
                                                headername + "time(min)",
                                                headername + "SOC",
                                                headername + "Voltage",
                                                headername + "Crate",
                                                headername + "Temp."
                                            ])
                                        writecolno = writecolno + 5
                            title = Ratenamelist[-2] + "=" + "%04d" % CycNo
                            plt.suptitle(title, fontsize= 15, fontweight='bold')
                            if len(all_data_name) != 0:
                                rate_ax1.legend(loc="lower right")
                                rate_ax2.legend(loc="upper right")
                                rate_ax3.legend(loc="lower right")
                                rate_ax4.legend(loc="lower right")
                                rate_ax5.legend(loc="upper right")
                                rate_ax6.legend(loc="upper right")
                            else:
                                plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                    tab_layout.addWidget(toolbar)
                    tab_layout.addWidget(canvas)
                    self.cycle_tab.addTab(tab, str(tab_no))
                    self.cycle_tab.setCurrentWidget(tab)
                    tab_no = tab_no + 1
                    plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                    output_fig(self.figsaveok, title)
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()

    def chg_confirm_button(self):
        self.ChgConfirm.setDisabled(True)
        firstCrate, mincapacity, CycleNo, smoothdegree, mincrate, dqscale, dvscale = self.Profile_ini_set()
        # 용량 선정 관련
        global writer
        foldercount, chnlcount, cyccount, writecolno = 0, 0, 0, 0
        root = Tk()
        root.withdraw()
        pne_path = self.pne_path_setting()
        all_data_folder = pne_path[0]
        all_data_name = pne_path[1]
        self.ChgConfirm.setEnabled(True)
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        if self.ect_saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name")
        tab_no = 0
        for i, cyclefolder in enumerate(all_data_folder):
            if os.path.isdir(cyclefolder):
                subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                foldercountmax = len(all_data_folder)
                foldercount = foldercount + 1
                if self.CycProfile.isChecked():
                    for FolderBase in subfolder:
                        chnlcount = chnlcount + 1
                        chnlcountmax = len(subfolder)
                        if "Pattern" not in FolderBase:
                            fig, ((Chg_ax1, Chg_ax2, Chg_ax3) ,(Chg_ax4, Chg_ax5, Chg_ax6)) = plt.subplots(
                                nrows=2, ncols=3, figsize=(14, 10))
                            tab = QtWidgets.QWidget()
                            tab_layout = QtWidgets.QVBoxLayout(tab)
                            canvas = FigureCanvas(fig)
                            toolbar = NavigationToolbar(canvas, None)
                            for CycNo in CycleNo:
                                cyccountmax = len(CycleNo)
                                cyccount = cyccount + 1
                                progressdata = progress(foldercount, foldercountmax, chnlcount, chnlcountmax, cyccount, cyccountmax)
                                self.progressBar.setValue(int(progressdata))
                                Chgnamelist = FolderBase.split("\\")
                                headername = Chgnamelist[-2] + ", " + Chgnamelist[-1] + ", " + str(CycNo) + "cy, "
                                lgnd = "%04d" % CycNo
                                if not check_cycler(cyclefolder):
                                    Chgtemp = toyo_chg_Profile_data( FolderBase, CycNo, mincapacity, mincrate, firstCrate,
                                                                    smoothdegree)
                                else:
                                    Chgtemp = pne_chg_Profile_data( FolderBase, CycNo, mincapacity, mincrate, firstCrate,
                                                                   smoothdegree)
                                if len(all_data_name) == 0:
                                    temp_lgnd = ""
                                else:	
                                    temp_lgnd = all_data_name[i] + " " + lgnd
                                if hasattr(Chgtemp[1], "Profile"):
                                    if len(Chgtemp[1].Profile) > 2:
                                        self.capacitytext.setText(str(Chgtemp[0]))
                                        graph_profile( Chgtemp[1].Profile.SOC, Chgtemp[1].Profile.Vol, Chg_ax1,
                                                      0, 1.3, 0.1, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, "SOC", "Voltage(V)", temp_lgnd)
                                        graph_profile( Chgtemp[1].Profile.SOC, Chgtemp[1].Profile.Vol, Chg_ax3,
                                                      0, 1.3, 0.1, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, "SOC", "Voltage(V)", temp_lgnd)
                                        if self.chk_dqdv.isChecked():
                                            graph_profile( Chgtemp[1].Profile.Vol, Chgtemp[1].Profile.dQdV, Chg_ax2,
                                                        self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, 0, 5.5 * dqscale, 0.5 * dqscale, 
                                                        "Voltage(V)","dQdV", temp_lgnd)
                                        else:
                                            graph_profile( Chgtemp[1].Profile.dQdV, Chgtemp[1].Profile.Vol, Chg_ax2,
                                                        0, 5.5 * dqscale, 0.5 * dqscale, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap,
                                                        "dQdV", "Voltage(V)", temp_lgnd)
                                        graph_profile( Chgtemp[1].Profile.SOC, Chgtemp[1].Profile.Crate, Chg_ax5,
                                                      0, 1.3, 0.1, 0, 3.4, 0.2, "SOC", "C-rate", temp_lgnd) 
                                        graph_profile( Chgtemp[1].Profile.SOC, Chgtemp[1].Profile.dVdQ, Chg_ax4,
                                                      0, 1.3, 0.1, 0, 5.5 * dvscale, 0.5 * dvscale, "SOC", "dVdQ", temp_lgnd)
                                        graph_profile( Chgtemp[1].Profile.SOC, Chgtemp[1].Profile.Temp, Chg_ax6,
                                                      0, 1.3, 0.1, -15, 60, 5, "SOC", "Temp.", lgnd)
                                        # Data output option
                                        if self.saveok.isChecked() and save_file_name:
                                            Chgtemp[1].Profile.to_excel(
                                                writer,
                                                startcol=writecolno,
                                                index=False,
                                                header=[
                                                    headername + "Time(min)",
                                                    headername + "SOC",
                                                    headername + "Energy",
                                                    headername + "Voltage",
                                                    headername + "Crate",
                                                    headername + "dQdV",
                                                    headername + "dVdQ",
                                                    headername + "Temp."
                                                ])
                                            writecolno = writecolno + 8
                                        if self.ect_saveok.isChecked() and save_file_name:
                                            Chgtemp[1].Profile["TimeSec"] = Chgtemp[1].Profile["TimeMin"] * 60
                                            Chgtemp[1].Profile["Curr"] = Chgtemp[1].Profile["Crate"] * Chgtemp[0] / 1000
                                            continue_df = Chgtemp[1].Profile.loc[:,["TimeSec", "Vol", "Curr", "Temp"]]
                                            # 각 열을 소수점 자리수에 맞게 반올림
                                            continue_df['TimeSec'] = continue_df['TimeSec'].round(1)  # 소수점 1자리
                                            continue_df['Vol'] = continue_df['Vol'].round(4)           # 소수점 4자리
                                            continue_df['Curr'] = continue_df['Curr'].round(4)         # 소수점 4자리
                                            continue_df['Temp'] = continue_df['Temp'].round(1)         # 소수점 1자리
                                            continue_df.to_csv(save_file_name + "_"+ "%04d" % CycNo + ".csv", index=False, sep=',',
                                                                header=["time(s)",
                                                                        "Voltage(V)",
                                                                        "Current(A)",
                                                                        "Temp."])
                                title = Chgnamelist[-2] + "=" + Chgnamelist[-1]
                                plt.suptitle(title, fontsize= 15, fontweight='bold')
                                if len(all_data_name) != 0:
                                    Chg_ax1.legend(loc="lower right")
                                    Chg_ax2.legend(loc="lower right")
                                    Chg_ax3.legend(loc="lower right")
                                    Chg_ax4.legend(loc="upper right")
                                    Chg_ax5.legend(loc="upper right")
                                    Chg_ax6.legend(loc="upper right")
                                else:
                                    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                            tab_layout.addWidget(toolbar)
                            tab_layout.addWidget(canvas)
                            self.cycle_tab.addTab(tab, str(tab_no))
                            self.cycle_tab.setCurrentWidget(tab)
                            tab_no = tab_no + 1
                            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                            output_fig(self.figsaveok, title)
                else:
                    for CycNo in CycleNo:
                        chnlcount = chnlcount + 1
                        chnlcountmax = len(subfolder)
                        fig, ((Chg_ax1, Chg_ax2, Chg_ax3) ,(Chg_ax4, Chg_ax5, Chg_ax6)) = plt.subplots(
                            nrows=2, ncols=3, figsize=(14, 10))
                        tab = QtWidgets.QWidget()
                        tab_layout = QtWidgets.QVBoxLayout(tab)
                        canvas = FigureCanvas(fig)
                        toolbar = NavigationToolbar(canvas, None)
                        for FolderBase in subfolder:
                            if "Pattern" not in FolderBase:
                                cyccountmax = len(CycleNo)
                                cyccount = cyccount + 1
                                progressdata = progress(foldercount, foldercountmax, cyccount, cyccountmax, chnlcount, chnlcountmax)
                                self.progressBar.setValue(int(progressdata))
                                Chgnamelist = FolderBase.split("\\")
                                headername = Chgnamelist[-2] + ", " + Chgnamelist[-1] + ", " + str(CycNo) + "cy, "
                                lgnd = Chgnamelist[-1]
                                if not check_cycler(cyclefolder):
                                    Chgtemp = toyo_chg_Profile_data( FolderBase, CycNo, mincapacity, mincrate, firstCrate,
                                                                    smoothdegree)
                                else:
                                    Chgtemp = pne_chg_Profile_data( FolderBase, CycNo, mincapacity, mincrate, firstCrate,
                                                                   smoothdegree)
                                if len(all_data_name) == 0:
                                    temp_lgnd = ""
                                else:	
                                    temp_lgnd = all_data_name[i] + " " + lgnd
                                if hasattr(Chgtemp[1], "Profile"):
                                    if len(Chgtemp[1].Profile) > 2:
                                        self.capacitytext.setText(str(Chgtemp[0]))
                                        graph_profile( Chgtemp[1].Profile.SOC, Chgtemp[1].Profile.Vol, Chg_ax1,
                                                      0, 1.3, 0.1, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, "SOC", "Voltage(V)", temp_lgnd)
                                        graph_profile( Chgtemp[1].Profile.SOC, Chgtemp[1].Profile.Vol, Chg_ax3,
                                                      0, 1.3, 0.1, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, "SOC", "Voltage(V)", temp_lgnd)
                                        if self.chk_dqdv.isChecked():
                                            graph_profile( Chgtemp[1].Profile.Vol, Chgtemp[1].Profile.dQdV, Chg_ax2,
                                                        self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, 0, 5.5 * dqscale, 0.5 * dqscale, 
                                                        "Voltage(V)","dQdV", temp_lgnd)
                                        else:
                                            graph_profile( Chgtemp[1].Profile.dQdV, Chgtemp[1].Profile.Vol, Chg_ax2,
                                                        0, 5.5 * dqscale, 0.5 * dqscale, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap,
                                                        "dQdV", "Voltage(V)", temp_lgnd)
                                        graph_profile( Chgtemp[1].Profile.dQdV, Chgtemp[1].Profile.Vol, Chg_ax2, 0, 5.5 * dqscale, 0.5 * dqscale,
                                                      self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, "dQdV", "Voltage(V)", temp_lgnd)
                                        graph_profile( Chgtemp[1].Profile.SOC, Chgtemp[1].Profile.Crate, Chg_ax5,
                                                      0, 1.3, 0.1, 0, 3.4, 0.2, "SOC", "C-rate", temp_lgnd) 
                                        graph_profile( Chgtemp[1].Profile.SOC, Chgtemp[1].Profile.dVdQ, Chg_ax4,
                                                      0, 1.3, 0.1, 0, 5.5 * dvscale, 0.5 * dvscale, "SOC", "dVdQ", temp_lgnd)
                                        graph_profile( Chgtemp[1].Profile.SOC, Chgtemp[1].Profile.Temp, Chg_ax6,
                                                      0, 1.3, 0.1, -15, 60, 5, "SOC", "Temp.", lgnd) 
                                        # Data output option
                                        if self.saveok.isChecked() and save_file_name:
                                            Chgtemp[1].Profile.to_excel(
                                                writer,
                                                startcol=writecolno,
                                                index=False,
                                                header=[
                                                    headername + "Time(min)",
                                                    headername + "SOC",
                                                    headername + "Energy",
                                                    headername + "Voltage",
                                                    headername + "Crate",
                                                    headername + "dQdV",
                                                    headername + "dVdQ",
                                                    headername + "Temp."
                                                ])
                                            writecolno = writecolno + 8
                                title = Chgnamelist[-2] + "=" + "%04d" % CycNo
                                plt.suptitle(title, fontsize= 15, fontweight='bold')
                                if len(all_data_name) != 0:
                                    Chg_ax1.legend(loc="lower right")
                                    Chg_ax2.legend(loc="lower right")
                                    Chg_ax3.legend(loc="lower right")
                                    Chg_ax4.legend(loc="upper right")
                                    Chg_ax5.legend(loc="upper right")
                                    Chg_ax6.legend(loc="upper right")
                                else:
                                    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                        tab_layout.addWidget(toolbar)
                        tab_layout.addWidget(canvas)
                        self.cycle_tab.addTab(tab, str(tab_no))
                        self.cycle_tab.setCurrentWidget(tab)
                        tab_no = tab_no + 1
                        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                        output_fig(self.figsaveok, title)
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()

    def dchg_confirm_button(self):
        self.DchgConfirm.setDisabled(True)
        firstCrate, mincapacity, CycleNo, smoothdegree, mincrate, dqscale, dvscale = self.Profile_ini_set()
        # 용량 선정 관련
        global writer
        foldercount, chnlcount, cyccount, writecolno = 0, 0, 0, 0
        root = Tk()
        root.withdraw()
        pne_path = self.pne_path_setting()
        all_data_folder = pne_path[0]
        all_data_name = pne_path[1]
        self.DchgConfirm.setEnabled(True)
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        if self.ect_saveok.isChecked():
            # save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".csv")
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name")
        tab_no = 0
        for i, cyclefolder in enumerate(all_data_folder):
            if os.path.isdir(cyclefolder):
                subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                foldercountmax = len(all_data_folder)
                foldercount = foldercount + 1
                if self.CycProfile.isChecked():
                    for FolderBase in subfolder:
                        chnlcount = chnlcount + 1
                        chnlcountmax = len(subfolder)
                        if "Pattern" not in FolderBase:
                            fig, ((Chg_ax1, Chg_ax2, Chg_ax3) ,(Chg_ax4, Chg_ax5, Chg_ax6)) = plt.subplots(
                                nrows=2, ncols=3, figsize=(14, 10))
                            tab = QtWidgets.QWidget()
                            tab_layout = QtWidgets.QVBoxLayout(tab)
                            canvas = FigureCanvas(fig)
                            toolbar = NavigationToolbar(canvas, None)
                            for CycNo in CycleNo:
                                cyccountmax = len(CycleNo)
                                cyccount = cyccount + 1
                                progressdata = progress(foldercount, foldercountmax, chnlcount, chnlcountmax, cyccount, cyccountmax)
                                self.progressBar.setValue(int(progressdata))
                                Dchgnamelist = FolderBase.split("\\")
                                headername = Dchgnamelist[-2] + ", " + Dchgnamelist[-1] + ", " + str(CycNo) + "cy, "
                                lgnd = "%04d" % CycNo
                                if not check_cycler(cyclefolder):
                                    Dchgtemp = toyo_dchg_Profile_data(FolderBase, CycNo, mincapacity, mincrate, firstCrate,
                                                                      smoothdegree)
                                else:
                                    Dchgtemp = pne_dchg_Profile_data(FolderBase, CycNo, mincapacity, mincrate, firstCrate,
                                                                     smoothdegree)
                                if len(all_data_name) == 0:
                                    temp_lgnd = ""
                                else:	
                                    temp_lgnd = all_data_name[i] + " " + lgnd
                                if hasattr(Dchgtemp[1], "Profile"):
                                    if len(Dchgtemp[1].Profile) > 2:
                                        self.capacitytext.setText(str(Dchgtemp[0]))
                                        graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.Vol, Chg_ax1,
                                                      0, 1.3, 0.1, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, "DOD", "Voltage(V)", temp_lgnd)
                                        graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.Vol, Chg_ax3,
                                                      0, 1.3, 0.1, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, "DOD", "Voltage(V)", temp_lgnd)
                                        graph_profile(Dchgtemp[1].Profile.dQdV, Dchgtemp[1].Profile.Vol, Chg_ax2,
                                                      -5 * dqscale, 0.5 * dqscale, 0.5 * dqscale, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap,
                                                      "dQdV", "Voltage(V)", temp_lgnd)
                                        graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.Crate, Chg_ax5,
                                                      0, 1.3, 0.1, 0, 3.4, 0.2, "SOC", "C-rate", temp_lgnd)
                                        graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.dVdQ, Chg_ax4,
                                                      0, 1.3, 0.1, -5 * dvscale, 0.5 * self.dvscale, 0.5 * self.dvscale,
                                                      "DOD", "dVdQ", temp_lgnd)
                                        graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.Temp, Chg_ax6,
                                                      0, 1.3, 0.1, -15, 60, 5, "DOD", "Temp.", lgnd) # Data output option
                                        if self.saveok.isChecked() and save_file_name:
                                            Dchgtemp[1].Profile.to_excel(
                                                writer,
                                                startcol=writecolno,
                                                index=False,
                                                header=[
                                                    headername + "Time(min)",
                                                    headername + "DOD",
                                                    headername + "Energy",
                                                    headername + "Voltage",
                                                    headername + "Crate",
                                                    headername + "dQdV",
                                                    headername + "dVdQ",
                                                    headername + "Temp."
                                                ])
                                            writecolno = writecolno + 8
                                        if self.ect_saveok.isChecked() and save_file_name:
                                            Dchgtemp[1].Profile["TimeSec"] = Dchgtemp[1].Profile.TimeMin * 60
                                            Dchgtemp[1].Profile["Curr"] = Dchgtemp[1].Profile.Crate * Dchgtemp[0] / 1000
                                            continue_df = Dchgtemp[1].Profile.loc[:,["TimeSec", "Vol", "Curr", "Temp"]]
                                            # 각 열을 소수점 자리수에 맞게 반올림
                                            continue_df['TimeSec'] = continue_df['TimeSec'].round(1)  # 소수점 1자리
                                            continue_df['Vol'] = continue_df['Vol'].round(4)           # 소수점 4자리
                                            continue_df['Curr'] = continue_df['Curr'].round(4)         # 소수점 4자리
                                            continue_df['Temp'] = continue_df['Temp'].round(1)         # 소수점 1자리
                                            continue_df.to_csv(save_file_name +"_"+ "%04d" % CycNo + ".csv", index=False, sep=',',
                                                                header=["time(s)",
                                                                        "Voltage(V)",
                                                                        "Current(A)",
                                                                        "Temp."])
                                title = Dchgnamelist[-2] + "=" + Dchgnamelist[-1]
                                plt.suptitle(title, fontsize= 15, fontweight='bold')
                                if len(all_data_name) != 0:
                                    Chg_ax1.legend(loc="lower left")
                                    Chg_ax2.legend(loc="upper left")
                                    Chg_ax3.legend(loc="lower left")
                                    Chg_ax4.legend(loc="lower left")
                                    Chg_ax5.legend(loc="upper right")
                                    Chg_ax6.legend(loc="upper right")
                                else:
                                    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                            tab_layout.addWidget(toolbar)
                            tab_layout.addWidget(canvas)
                            self.cycle_tab.addTab(tab, str(tab_no))
                            self.cycle_tab.setCurrentWidget(tab)
                            tab_no = tab_no + 1
                            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                            output_fig(self.figsaveok, title)
                else:
                    for CycNo in CycleNo:
                        chnlcount = chnlcount + 1
                        chnlcountmax = len(subfolder)
                        fig, ((Chg_ax1, Chg_ax2, Chg_ax3) ,(Chg_ax4, Chg_ax5, Chg_ax6)) = plt.subplots(
                            nrows=2, ncols=3, figsize=(14, 10))
                        tab = QtWidgets.QWidget()
                        tab_layout = QtWidgets.QVBoxLayout(tab)
                        canvas = FigureCanvas(fig)
                        toolbar = NavigationToolbar(canvas, None)
                        for FolderBase in subfolder:
                            if "Pattern" not in FolderBase:
                                cyccountmax = len(CycleNo)
                                cyccount = cyccount + 1
                                progressdata = progress(foldercount, foldercountmax, cyccount, cyccountmax, chnlcount, chnlcountmax)
                                self.progressBar.setValue(int(progressdata))
                                Dchgnamelist = FolderBase.split("\\")
                                headername = Dchgnamelist[-2] + ", " + Dchgnamelist[-1] + ", " + str(CycNo) + "cy, "
                                lgnd = Dchgnamelist[-1]
                                if not check_cycler(cyclefolder):
                                    Dchgtemp = toyo_dchg_Profile_data(FolderBase, CycNo, mincapacity, mincrate, firstCrate, smoothdegree)
                                else:
                                    Dchgtemp = pne_dchg_Profile_data(FolderBase, CycNo, mincapacity, mincrate, firstCrate, smoothdegree)
                                if len(all_data_name) == 0:
                                    temp_lgnd = ""
                                else:	
                                    temp_lgnd = all_data_name[i] + " " + lgnd
                                if hasattr(Dchgtemp[1], "Profile"):
                                    if len(Dchgtemp[1].Profile) > 2:
                                        self.capacitytext.setText(str(Dchgtemp[0]))
                                        graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.Vol, Chg_ax1,
                                                      0, 1.3, 0.1, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, "DOD", "Voltage(V)", temp_lgnd)
                                        graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.Vol, Chg_ax3,
                                                      0, 1.3, 0.1, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap, "DOD", "Voltage(V)", temp_lgnd)
                                        graph_profile(Dchgtemp[1].Profile.dQdV, Dchgtemp[1].Profile.Vol, Chg_ax2,
                                                      -5 * dqscale, 0.5 * dqscale, 0.5 * dqscale, self.vol_y_hlimit, self.vol_y_llimit, self.vol_y_gap,
                                                      "dQdV", "Voltage(V)", temp_lgnd)
                                        graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.Crate, Chg_ax5,
                                                      0, 1.3, 0.1, 0, 3.4, 0.2, "SOC", "C-rate", temp_lgnd)
                                        graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.dVdQ, Chg_ax4,
                                                      0, 1.3, 0.1, -5 * dvscale, 0.5 * self.dvscale, 0.5 * self.dvscale,
                                                      "DOD", "dVdQ", temp_lgnd)
                                        graph_profile(Dchgtemp[1].Profile.SOC, Dchgtemp[1].Profile.Temp, Chg_ax6,
                                                      0, 1.3, 0.1, -15, 60, 5, "DOD", "Temp.", lgnd) 
                                        # Data output option
                                        if self.saveok.isChecked() and save_file_name:
                                            Dchgtemp[1].Profile.to_excel(
                                                writer,
                                                startcol=writecolno,
                                                index=False,
                                                header=[
                                                    headername + "Time(min)",
                                                    headername + "DOD",
                                                    headername + "Energy",
                                                    headername + "Voltage",
                                                    headername + "Crate",
                                                    headername + "dQdV",
                                                    headername + "dVdQ",
                                                    headername + "Temp."
                                                ])
                                            writecolno = writecolno + 8
                                        if self.ect_saveok.isChecked() and save_file_name:
                                            Dchgtemp[1].Profile["TimeSec"] = Dchgtemp[1].Profile.TimeMin * 60
                                            Dchgtemp[1].Profile["Curr"] = Dchgtemp[1].Profile.Crate * Dchgtemp[0] / 1000
                                            continue_df = Dchgtemp[1].Profile.loc[:,["TimeSec", "Vol", "Curr", "Temp"]]
                                            # 각 열을 소수점 자리수에 맞게 반올림
                                            continue_df['TimeSec'] = continue_df['TimeSec'].round(1)  # 소수점 1자리
                                            continue_df['Vol'] = continue_df['Vol'].round(4)           # 소수점 4자리
                                            continue_df['Curr'] = continue_df['Curr'].round(4)         # 소수점 4자리
                                            continue_df['Temp'] = continue_df['Temp'].round(1)         # 소수점 1자리
                                            continue_df.to_csv(save_file_name + "_" + Dchgnamelist[-1] + ".csv", index=False, sep=',',
                                                                header=["time(s)",
                                                                        "Voltage(V)",
                                                                        "Current(A)",
                                                                        "Temp."])
                                title = Dchgnamelist[-2] + "=" + "%04d" % CycNo
                                plt.suptitle(title, fontsize= 15, fontweight='bold')
                                if len(all_data_name) != 0:
                                    Chg_ax1.legend(loc="lower left")
                                    Chg_ax2.legend(loc="upper left")
                                    Chg_ax3.legend(loc="lower left")
                                    Chg_ax4.legend(loc="lower left")
                                    Chg_ax5.legend(loc="upper right")
                                    Chg_ax6.legend(loc="upper right")
                                else:
                                    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                        tab_layout.addWidget(toolbar)
                        tab_layout.addWidget(canvas)
                        self.cycle_tab.addTab(tab, str(tab_no))
                        self.cycle_tab.setCurrentWidget(tab)
                        tab_no = tab_no + 1
                        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                        output_fig(self.figsaveok, title)
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                plt.close()
            else:
                err_msg('파일 or 폴더 없음!!','파일 or 폴더 없음!!')
                return
        self.progressBar.setValue(100)
        if self.saveok.isChecked() and save_file_name:
            writer.close()

    def continue_confirm_button(self):
        if self.chk_ectpath.isChecked():
            self.ect_confirm_button()
        else:
            self.pro_continue_confirm_button()

    def ect_confirm_button(self):
        self.ContinueConfirm.setDisabled(True)
        firstCrate, mincapacity, CycleNo, smoothdegree, mincrate, dqscale, dvscale = self.Profile_ini_set()
        all_data_name = []
        # 용량 선정 관련
        global writer
        write_column_num, write_column_num2, folder_count, chnlcount, cyccount = 0, 0, 0, 0, 0
        root = Tk()
        root.withdraw()
        datafilepath = filedialog.askopenfilename(initialdir="d://", title="Choose Test files")
        if datafilepath:
            cycle_path = pd.read_csv(datafilepath, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
            ect_path = np.array(cycle_path.path.tolist())
            ect_cycle = np.array(cycle_path.cycle.tolist())
            ect_CD = np.array(cycle_path.CD.tolist())
            ect_save = np.array(cycle_path.save.tolist())
            if (self.inicaprate.isChecked()) and ("mAh" in datafilepath):
                self.mincapacity = name_capacity(datafilepath)
                self.capacitytext.setText(str(self.mincapacity))
        self.ContinueConfirm.setEnabled(True)
        tab_no = 0
        for i, cyclefolder in enumerate(ect_path):
            chg_dchg_dcir_no = list((ect_cycle[i].split(" ")))
            if os.path.isdir(cyclefolder):
                subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                foldercountmax = len(ect_path)
                folder_count = folder_count + 1
                for FolderBase in subfolder:
                    for dcir_continue_step in chg_dchg_dcir_no:
                        if "-" in dcir_continue_step:
                            Step_CycNo, Step_CycEnd = map(int, dcir_continue_step.split("-"))
                        else:
                            Step_CycNo, Step_CycEnd = int(dcir_continue_step), int(dcir_continue_step)
                        CycleNo = range(Step_CycNo, Step_CycEnd + 1)
                        if "Pattern" not in FolderBase:
                            fig, ((step_ax1, step_ax2, step_ax3) ,(step_ax4, step_ax5, step_ax6)) = plt.subplots( nrows=2, ncols=3, figsize=(14, 10))
                            tab = QtWidgets.QWidget()
                            tab_layout = QtWidgets.QVBoxLayout(tab)
                            canvas = FigureCanvas(fig)
                            toolbar = NavigationToolbar(canvas, None)
                            progressdata = progress(folder_count, foldercountmax, 1, 1, 1, 1)
                            self.progressBar.setValue(int(progressdata))
                            step_namelist = FolderBase.split("\\")
                            headername = step_namelist[-2] + ", " + step_namelist[-1] + ", " + str( Step_CycNo)
                            headername = headername + "-" + str(Step_CycEnd) + "cy, "
                            if self.CycProfile.isChecked():
                                lgnd = "%04d" % Step_CycNo
                            else:
                                lgnd = step_namelist[-1]
                            temp = pne_Profile_continue_data(FolderBase, Step_CycNo, Step_CycEnd, mincapacity, firstCrate, ect_CD[i])
                            if len(all_data_name) == 0:
                                temp_lgnd = ""
                            else:	
                                temp_lgnd = all_data_name[i]
                            if hasattr(temp[1], "stepchg"):
                                if len(temp[1].stepchg) > 2:
                                    self.capacitytext.setText(str(temp[0]))
                                    graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.Vol, step_ax1, 2.0, 4.8, 0.2, "Time(min)", "Voltage(V)",temp_lgnd)
                                    graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.Vol, step_ax4, 2.0, 4.8, 0.2, "Time(min)", "Voltage(V)",temp_lgnd)
                                    graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.Crate, step_ax2, 0, 3.2, 0.2, "Time(min)", "C-rate",temp_lgnd)
                                    graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.Crate, step_ax5, -3.0, 0.2, 0.2, "Time(min)", "C-rate",temp_lgnd)
                                    graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.SOC, step_ax3, 0, 1.2, 0.1, "Time(min)", "SOC", temp_lgnd)
                                    graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.Temp, step_ax6, -15, 60, 5, "Time(min)", "Temp.", lgnd)
                                    # Data output option
                                    continue_df = temp[1].stepchg.loc[:,["TimeSec", "Vol", "Curr", "Temp"]]
                                    # 각 열을 소수점 자리수에 맞게 반올림
                                    continue_df['TimeSec'] = continue_df['TimeSec'].round(1)  # 소수점 1자리
                                    continue_df['Vol'] = continue_df['Vol'].round(4)           # 소수점 4자리
                                    continue_df['Curr'] = continue_df['Curr'].round(4)         # 소수점 4자리
                                    continue_df['Temp'] = continue_df['Temp'].round(1)         # 소수점 1자리
                                    continue_df.to_csv(("D:\\" + ect_save[i] + ".csv"), index=False, sep=',',
                                                        header=["time(s)",
                                                                "Voltage(V)",
                                                                "Current(A)",
                                                                "Temp."])
                            title = step_namelist[-2] + "=" + "%04d" % Step_CycNo
                            plt.suptitle(title, fontsize= 15, fontweight='bold')
                            if len(all_data_name) != 0:
                                step_ax1.legend(loc="lower left")
                                step_ax2.legend(loc="lower right")
                                step_ax3.legend(loc="upper right")
                                step_ax4.legend(loc="lower right")
                                step_ax5.legend(loc="lower left")
                                step_ax6.legend(loc="upper right")
                            else:
                                plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                            tab_layout.addWidget(toolbar)
                            tab_layout.addWidget(canvas)
                            self.cycle_tab.addTab(tab, str(tab_no))
                            self.cycle_tab.setCurrentWidget(tab)
                            tab_no = tab_no + 1
                            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                            output_fig(self.figsaveok, ect_save[i])
        self.progressBar.setValue(100)
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        plt.close()

    def pro_continue_confirm_button(self):
        self.ContinueConfirm.setDisabled(True)
        firstCrate, mincapacity, CycleNo, smoothdegree, mincrate, dqscale, dvscale = self.Profile_ini_set()
        all_data_name = []
        # 용량 선정 관련
        global writer
        if "-" in self.stepnum.toPlainText():
            write_column_num, write_column_num2, folder_count, chnlcount, cyccount = 0, 0, 0, 0, 0
            root = Tk()
            root.withdraw()
            pne_path = self.pne_path_setting()
            all_data_folder = pne_path[0]
            all_data_name = pne_path[1]
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                if save_file_name:
                    writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
            if self.ect_saveok.isChecked():
                # save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".csv")
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name")
            self.ContinueConfirm.setEnabled(True)
            chg_dchg_dcir_no = list((self.stepnum.toPlainText().split(" ")))
            tab_no = 0
            for i, cyclefolder in enumerate(all_data_folder):
                if os.path.isdir(cyclefolder):
                    subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                    foldercountmax = len(all_data_folder)
                    folder_count = folder_count + 1
                    for FolderBase in subfolder:
                        chnlcount = chnlcount + 1
                        chnlcountmax = len(subfolder)
                        for dcir_continue_step in chg_dchg_dcir_no:
                            if "-" in dcir_continue_step:
                                Step_CycNo, Step_CycEnd = map(int, dcir_continue_step.split("-"))
                                CycleNo = range(Step_CycNo, Step_CycEnd + 1)
                                if "Pattern" not in FolderBase:
                                    fig, ((step_ax1, step_ax2, step_ax3) ,(step_ax4, step_ax5, step_ax6)) = plt.subplots( nrows=2, ncols=3, figsize=(14, 10))
                                    tab = QtWidgets.QWidget()
                                    tab_layout = QtWidgets.QVBoxLayout(tab)
                                    canvas = FigureCanvas(fig)
                                    toolbar = NavigationToolbar(canvas, None)
                                    cyccountmax = len(CycleNo)
                                    cyccount = cyccount + 1
                                    progressdata = progress(folder_count, foldercountmax, cyccount, cyccountmax, chnlcount, chnlcountmax)
                                    self.progressBar.setValue(int(progressdata))
                                    step_namelist = FolderBase.split("\\")
                                    headername = step_namelist[-2] + ", " + step_namelist[-1] + ", " + str( Step_CycNo)
                                    headername = headername + "-" + str(Step_CycEnd) + "cy, "
                                    if self.CycProfile.isChecked():
                                        lgnd = "%04d" % Step_CycNo
                                    else:
                                        lgnd = step_namelist[-1]
                                    if not check_cycler(cyclefolder):
                                        err_msg("Toyo는 준비 중", "토요는 시간나면 추가할께요 ^^;")
                                    else:
                                        temp = pne_Profile_continue_data(FolderBase, Step_CycNo, Step_CycEnd, mincapacity, firstCrate, "")
                                        if len(all_data_name) == 0:
                                            temp_lgnd = ""
                                        else:	
                                            temp_lgnd = all_data_name[i]
                                        if hasattr(temp[1], "stepchg"):
                                            if len(temp[1].stepchg) > 2:
                                                self.capacitytext.setText(str(temp[0]))
                                                graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.Vol, step_ax1,
                                                               2.0, 4.8, 0.2, "Time(min)", "Voltage(V)",temp_lgnd)
                                                graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.Vol, step_ax4,
                                                               2.0, 4.8, 0.2, "Time(min)", "Voltage(V)",temp_lgnd)
                                                graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.OCV, step_ax4,
                                                               2.0, 4.8, 0.2, "Time(min)", "OCV/CCV", "OCV_" + temp_lgnd, "o")
                                                graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.CCV, step_ax4,
                                                               2.0, 4.8, 0.2, "Time(min)", "OCV/CCV", "CCV_" + temp_lgnd, "o")
                                                graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.Crate, step_ax2,
                                                               -1.8, 1.7, 0.2, "Time(min)", "C-rate",temp_lgnd)
                                                graph_continue(temp[2].AccCap, temp[2].OCV, step_ax5, 2.0, 4.8, 0.2,
                                                               "SOC", "OCV/CCV", "OCV_" + temp_lgnd, "o") 
                                                graph_continue(temp[2].AccCap, temp[2].CCV, step_ax5, 2.0, 4.8, 0.2,
                                                               "SOC", "OCV/CCV", "CCV_" + temp_lgnd, "o")
                                                graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.SOC, step_ax3,
                                                               0, 1.2, 0.1, "Time(min)", "SOC", temp_lgnd)
                                                graph_continue(temp[1].stepchg.TimeMin, temp[1].stepchg.Temp, step_ax6,
                                                               -15, 60, 5, "Time(min)", "Temp.", lgnd)
                                                # Data output option
                                                if self.saveok.isChecked() and save_file_name:
                                                    temp[1].stepchg = temp[1].stepchg.loc[:,["TimeSec", "Vol", "Curr","OCV", "CCV",
                                                                                             "Crate", "SOC", "Temp"]]
                                                    temp[1].stepchg.to_excel(writer, sheet_name="Profile", startcol=write_column_num,
                                                                             index=False,
                                                                             header=[headername + "time(s)",
                                                                                     headername + "Voltage(V)",
                                                                                     headername + "Current(A)",
                                                                                     headername + "OCV",
                                                                                     headername + "CCV",
                                                                                     headername + "Crate",
                                                                                     headername + "SOC",
                                                                                     headername + "Temp."])
                                                    write_column_num = write_column_num + 8
                                                    temp[2].to_excel(writer, sheet_name="OCV_CCV", startcol=write_column_num2,
                                                                     index=False,
                                                                     header=[headername + "SOC",
                                                                             headername + "OCV",
                                                                             headername + "CCV"])
                                                    write_column_num2 = write_column_num2 + 3
                                                if self.ect_saveok.isChecked() and save_file_name:
                                                    temp[1].stepchg["TimeSec"] = temp[1].stepchg.TimeMin * 60
                                                    temp[1].stepchg["Curr"] = temp[1].stepchg.Crate * temp[0] / 1000
                                                    continue_df = temp[1].stepchg.loc[:,["TimeSec", "Vol", "Curr", "Temp"]]
                                                    # 각 열을 소수점 자리수에 맞게 반올림
                                                    continue_df['TimeSec'] = continue_df['TimeSec'].round(1)  # 소수점 1자리
                                                    continue_df['Vol'] = continue_df['Vol'].round(4)           # 소수점 4자리
                                                    continue_df['Curr'] = continue_df['Curr'].round(4)         # 소수점 4자리
                                                    continue_df['Temp'] = continue_df['Temp'].round(1)         # 소수점 1자리
                                                    continue_df.to_csv((save_file_name + "_" + "%04d" % tab_no + ".csv"), index=False, sep=',',
                                                                        header=["time(s)",
                                                                                "Voltage(V)",
                                                                                "Current(A)",
                                                                                "Temp."])
                                        if self.CycProfile.isChecked():
                                            title = step_namelist[-2] + "=" + step_namelist[-1]
                                        else:
                                            title = step_namelist[-2] + "=" + "%04d" % Step_CycNo
                                        plt.suptitle(title, fontsize= 15, fontweight='bold')
                                        if len(all_data_name) != 0:
                                            step_ax1.legend(loc="lower left")
                                            step_ax2.legend(loc="lower right")
                                            step_ax3.legend(loc="upper right")
                                            step_ax4.legend(loc="lower right")
                                            step_ax5.legend(loc="lower left")
                                            step_ax6.legend(loc="upper right")
                                        else:
                                            plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                                        if self.CycProfile.isChecked():
                                            tab_layout.addWidget(toolbar)
                                            tab_layout.addWidget(canvas)
                                            self.cycle_tab.addTab(tab, str(tab_no))
                                            self.cycle_tab.setCurrentWidget(tab)
                                            # tab_no = tab_no + 1
                                            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                                            output_fig(self.figsaveok, title)
                                        tab_layout.addWidget(toolbar)
                                        tab_layout.addWidget(canvas)
                                        self.cycle_tab.addTab(tab, str(tab_no))
                                        self.cycle_tab.setCurrentWidget(tab)
                                        tab_no = tab_no + 1
                                        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                                        output_fig(self.figsaveok, title)
            if self.saveok.isChecked() and save_file_name:
                writer.close()
            self.progressBar.setValue(100)
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            plt.close()
        else:
            err_msg('Step 에러','Step에 3-5 같은 연속 형식으로 넣어주세요!')
            self.ContinueConfirm.setEnabled(True)

    def dcir_confirm_button(self):
        firstCrate, mincapacity, CycleNo, smoothdegree, mincrate, dqscale, dvscale = self.Profile_ini_set()
        # 용량 선정 관련
        root = Tk()
        root.withdraw()
        global writer
        # if "-" in self.stepnum.toPlainText():
        write_column_num, folder_count, chnlcount, cyccount = 0, 0, 0, 0
        self.DCIRConfirm.setDisabled(True)
        pne_path = self.pne_path_setting()
        all_data_folder = pne_path[0]
        all_data_name = pne_path[1]
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        self.DCIRConfirm.setEnabled(True)
        # chg_dchg_dcir_no = list((self.stepnum.toPlainText().split(" ")))
        chg_tab_no, dchg_tab_no = 0, 0
        for i, cyclefolder in enumerate(all_data_folder):
            if os.path.isdir(cyclefolder):
                subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                foldercountmax = len(all_data_folder)
                folder_count = folder_count + 1
                for FolderBase in subfolder:
                    chg_dchg_dcir_no = pne_dcir_chk_cycle(FolderBase)
                    chnlcount = chnlcount + 1
                    chnlcountmax = len(subfolder)
                    if chg_dchg_dcir_no is not None:
                        for dcir_continue_step in chg_dchg_dcir_no:
                            if "-" in dcir_continue_step:
                                Step_CycNo, Step_CycEnd = map(int, dcir_continue_step.split("-"))
                                CycleNo = range(Step_CycNo, Step_CycEnd + 1)
                                if "Pattern" not in FolderBase:
                                    fig, ((step_ax1, step_ax3), (step_ax2, step_ax4)) = plt.subplots(
                                        nrows=2, ncols=2, figsize=(14, 8))
                                    tab = QtWidgets.QWidget()
                                    tab_layout = QtWidgets.QVBoxLayout(tab)
                                    canvas = FigureCanvas(fig)
                                    toolbar = NavigationToolbar(canvas, None)
                                    cyccountmax = len(CycleNo)
                                    cyccount = cyccount + 1
                                    progressdata = progress(folder_count, foldercountmax, chnlcount, chnlcountmax, cyccount, cyccountmax)
                                    self.progressBar.setValue(int(progressdata))
                                    step_namelist = FolderBase.split("\\")
                                    headername = step_namelist[-2] + ", " + step_namelist[-1]
                                    if self.CycProfile.isChecked():
                                        lgnd = "%04d" % Step_CycNo
                                    else:
                                        lgnd = step_namelist[-1]
                                    if not check_cycler(cyclefolder):
                                        err_msg("PNE 충방전기 사용 요청", "DCIR은 PNE 충방전기를 사용하여 측정 부탁 드립니다.")
                                    else:
                                        temp = pne_dcir_Profile_data(FolderBase, Step_CycNo, Step_CycEnd, mincapacity, firstCrate)
                                        if (temp is not None) and hasattr(temp[1], "AccCap"):
                                            if len(temp[1]) > 2:
                                                self.capacitytext.setText(str(temp[0]))
                                                graph_soc_continue(temp[1].SOC, temp[1].OCV, step_ax1, 2.0, 4.8, 0.2, "SOC", "OCV/CCV", "OCV", "o")
                                                graph_soc_continue(temp[1].SOC, temp[1].rOCV, step_ax1, 2.0, 4.8, 0.2, "SOC", "OCV/CCV", "rOCV", "o")
                                                graph_soc_continue(temp[1].SOC, temp[1].CCV, step_ax1, 2.0, 4.8, 0.2, "SOC", "OCV/CCV","CCV", "o")
                                                graph_soc_dcir(temp[1].SOC, temp[1].iloc[:, 7], step_ax2, "SOC", "DCIR(mΩ)", " 0.1s DCIR", "o")
                                                graph_soc_dcir(temp[1].SOC, temp[1].iloc[:, 8], step_ax2, "SOC", "DCIR(mΩ)", " 1.0s DCIR", "o")
                                                graph_soc_dcir(temp[1].SOC, temp[1].iloc[:, 9], step_ax2, "SOC", "DCIR(mΩ)", "10.0s DCIR", "o")
                                                graph_soc_dcir(temp[1].SOC, temp[1].iloc[:, 10], step_ax2, "SOC", "DCIR(mΩ)", "20.0s DCIR", "o")
                                                graph_soc_dcir(temp[1].SOC, temp[1].RSS, step_ax2, "SOC", "DCIR(mΩ)", "RSS DCIR", "o")
                                                graph_continue(temp[1].OCV, temp[1].SOC, step_ax3, -20, 120, 10, "Voltage (V)", "SOC","OCV", "o")
                                                graph_continue(temp[1].CCV, temp[1].SOC, step_ax3, -20, 120, 10, "Voltage (V)", "SOC","CCV", "o")
                                                graph_dcir(temp[1].OCV, temp[1].iloc[:, 7], step_ax4, "OCV", "DCIR(mΩ)", " 0.1s DCIR", "o")
                                                graph_dcir(temp[1].OCV, temp[1].iloc[:, 8], step_ax4, "OCV", "DCIR(mΩ)", " 1.0s DCIR", "o")
                                                graph_dcir(temp[1].OCV, temp[1].iloc[:, 9], step_ax4, "OCV", "DCIR(mΩ)", "10.0s DCIR", "o")
                                                graph_dcir(temp[1].OCV, temp[1].iloc[:, 10], step_ax4, "OCV", "DCIR(mΩ)", "20.0s DCIR", "o")
                                                graph_dcir(temp[1].OCV, temp[1].RSS, step_ax4, "OCV", "DCIR(mΩ)", "RSS DCIR", "o")
                                                # Data output option
                                                if self.saveok.isChecked() and save_file_name:
                                                    # temp[1] = temp[1].iloc[:,[1, 2, 4, 6, 7, 8, 9, 10, 5, 3]]
                                                    temp[1] = temp[1].iloc[:,[1, 2, 4, 7, 8, 9, 10, 5, 3]]
                                                    temp[1].to_excel(writer, sheet_name="DCIR", startcol=write_column_num, index=False,
                                                                        header=[headername + " Capacity(mAh)",
                                                                                headername + " SOC",
                                                                                headername + " OCV",
                                                                                # headername + " OCV_est",
                                                                                headername + "  0.1s DCIR",
                                                                                headername + "  1.0s DCIR",
                                                                                headername + " 10.0s DCIR",
                                                                                headername + " 20.0s DCIR",
                                                                                headername + " RSS",
                                                                                headername + " CCV"])
                                                    temp[2] = temp[2].iloc[:,[1, 2, 4, 7, 8, 9, 10, 5, 3]]
                                                    temp[2].to_excel(writer, sheet_name="RSQ", startcol=write_column_num, index=False,
                                                                        header=[headername + " Capacity(mAh)",
                                                                                headername + " SOC",
                                                                                headername + " OCV",
                                                                                # headername + " OCV_est",
                                                                                headername + "  0.1s DCIR RSQ",
                                                                                headername + "  1.0s DCIR RSQ",
                                                                                headername + " 10.0s DCIR RSQ",
                                                                                headername + " 20.0s DCIR RSQ",
                                                                                headername + " RSS",
                                                                                headername + " CCV"])
                                                    write_column_num = write_column_num + 9
                                                if self.CycProfile.isChecked():
                                                    title = step_namelist[-2] + "=" + step_namelist[-1]
                                                else:
                                                    title = step_namelist[-2] + "=" + "%04d" % Step_CycNo
                                                plt.suptitle(title, fontsize= 15, fontweight='bold')
                                                step_ax1.legend(loc="lower right")
                                                step_ax2.legend(loc="upper right")
                                                step_ax3.legend(loc="lower right")
                                                step_ax4.legend(loc="upper right")
                                                tab_layout.addWidget(toolbar)
                                                tab_layout.addWidget(canvas)
                                                if temp[1].iloc[0,2] == 100:
                                                    self.cycle_tab.addTab(tab, "dchg" + str(dchg_tab_no))
                                                    dchg_tab_no = dchg_tab_no + 1
                                                else:
                                                    self.cycle_tab.addTab(tab, "chg" + str(chg_tab_no))
                                                    chg_tab_no = chg_tab_no + 1
                                                self.cycle_tab.setCurrentWidget(tab)
                                                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                                                output_fig(self.figsaveok, title)
                                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                                plt.close()
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        self.progressBar.setValue(100)
        # else:
        #     err_msg('Step 에러','Step에 3-5 같은 연속 형식으로 넣어주세요!')
        #     self.DCIRConfirm.setEnabled(True)

    def conn_disconn(self, conn_drive, drive_name):
        connect_change(conn_drive) if os.path.isdir(drive_name) else disconnect_change(conn_drive)

    def chk_network_drive(self):
        self.conn_disconn(self.mount_toyo, "z:")
        self.conn_disconn(self.mount_pne_1, "y:")
        self.conn_disconn(self.mount_pne_2, "x:")
        self.conn_disconn(self.mount_pne_3, "w:")
        self.conn_disconn(self.mount_pne_4, "v:")
        self.conn_disconn(self.mount_pne_5, "u:")

    def network_drive(self, driver, folder, id, pw):
        if not os.path.isdir(driver):
            if id == "":
                os.system('%SystemRoot%\\system32\\net use ' + driver + ' ' + folder +' ' + ' /persistent:no')
            else:
                os.system('%SystemRoot%\\system32\\net use ' + driver + ' ' + folder +' ' + pw + ' /user:' + id + ' /persistent:no')
        else:
            os.system('%SystemRoot%\\system32\\net use ' + driver + ' /delete /y')
        self.chk_network_drive()

    def mount_toyo_button(self):
        self.network_drive("z:",'"\\\\10.253.44.115\\TOYO-DATA Back Up Folder"', "sec", "qoxjfl1!")

    def mount_pne1_button(self):
        self.network_drive("y:",'"\\\\10.253.44.111\\PNE-Data"', "SAMSUNG", "qoxjfl1!")

    def mount_pne2_button(self):
        self.network_drive("x:",'"\\\\10.253.44.111\\PNE-Data2"', "SAMSUNG", "qoxjfl1!")

    def mount_pne3_button(self):
        self.network_drive("w:",'"\\\\10.252.130.113\\PNE-Data"', "", "")

    def mount_pne4_button(self):
        self.network_drive("v:",'"\\\\10.252.130.145\\PNE-Data"', "", "")

    def mount_pne5_button(self):
        self.network_drive("u:",'"\\\\10.252.130.162\\PNE-Data"', "", "")

    def mount_all_button(self):
        self.progressBar.setValue(0)
        if not os.path.isdir("z:"):
            self.network_drive("z:",'"\\\\10.253.44.115\\TOYO-DATA Back Up Folder"', "sec", "qoxjfl1!")
        self.progressBar.setValue(15)
        if not os.path.isdir("y:"):
            self.network_drive("y:",'"\\\\10.253.44.111\\PNE-Data"', "SAMSUNG", "qoxjfl1!")
        self.progressBar.setValue(30)
        if not os.path.isdir("x:"):
            self.network_drive("x:",'"\\\\10.253.44.111\\PNE-Data2"', "SAMSUNG", "qoxjfl1!")
        self.progressBar.setValue(45)
        if not os.path.isdir("w:"):
            self.network_drive("w:",'"\\\\10.252.130.113\\PNE-Data"', "", "")
        self.progressBar.setValue(60)
        if not os.path.isdir("v:"):
            self.network_drive("v:",'"\\\\10.252.130.145\\PNE-Data"', "", "")
        self.progressBar.setValue(75)
        if not os.path.isdir("u:"):
            self.network_drive("u:",'"\\\\10.252.130.162\\PNE-Data"', "", "")
        self.progressBar.setValue(90)
        self.chk_network_drive()
        self.progressBar.setValue(100)
        self.AllchnlData = pd.DataFrame()
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                self.progressBar.setValue(0)
                for i in range(0, 5):
                    self.toyo_data_make(i, self.toyo_cycler_name[i])
                    self.progressBar.setValue(int(((i + 1) / 5) * 20))
                for j in range(0, 26):
                    self.pne_data_make(j, self.pne_cycler_name[j])
                    self.progressBar.setValue(int(20 + ((j + 1) / 26) * 80))
                self.progressBar.setValue(100)
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                self.AllchnlData.to_excel(writer, index=False)
                writer.close()

    def unmount_all_button(self):
        self.progressBar.setValue(0)
        os.system(r'%SystemRoot%\system32\net use u: /delete /y')
        self.progressBar.setValue(15)
        os.system(r'%SystemRoot%\system32\net use v: /delete /y')
        self.progressBar.setValue(30)
        os.system(r'%SystemRoot%\system32\net use w: /delete /y')
        self.progressBar.setValue(45)
        os.system(r'%SystemRoot%\system32\net use x: /delete /y')
        self.progressBar.setValue(60)
        os.system(r'%SystemRoot%\system32\net use y: /delete /y')
        self.progressBar.setValue(75)
        os.system(r'%SystemRoot%\system32\net use z: /delete /y')
        self.progressBar.setValue(90)
        self.chk_network_drive()
        self.progressBar.setValue(100)

    def split_value0(self, x):
        if '_' in x:
            part = x.split('_')
        else:
            part = x.split(' ')
        return part[0]
    
    def split_value1(self, x):
        if '_' in x:
            part = x.split('_')
            if len(part) > 2:
                if part[2] == '00':
                    return "선행랩"
                else:
                    return part[2] + " 파트"
            else:
                return part[0]
        else:
            part = x.split(' ')
            if len(part) > 1:
                return part[1]
            else:
                return part[0]

    def split_value2(self, x):
        if '_' in x:
            part = x.split('_')
            if len(part) > 3:
                return part[3]
            else:
                return part[0]
        else:
            part = x.split(' ')
            if len(part) > 2:
                return part[2]
            else:
                return part[0]

    def toyo_base_data_make(self, toyo_num, blkname):
        # 경로 확인
        toyoworkpath = "z:\\Working\\"+self.toyo_blk_list[toyo_num]+"\\Chpatrn.cfg"
        if os.path.isfile(toyoworkpath):
            toyo_data = remove_end_comma(toyoworkpath)
            toyo_data = toyo_data[[7, 1, 5, 9]]
            toyo_data.columns = self.toyo_column_list[0:4]
            toyo_data.index = toyo_data.index + 1
            if toyo_num != 3:
                toyoworkpath2 = "z:\\Working\\"+self.toyo_blk_list[toyo_num]+"\\ExperimentStatusReport.dat"
                toyo_data2 = pd.read_csv(toyoworkpath2, sep=",", engine="c", encoding="CP949", on_bad_lines='skip')
                toyo_data2 = toyo_data2.iloc[:, [0, 8, 5, 21, 15, 6, 7, 9, 3]]
                toyo_data2.index = toyo_data2.index + 1
                toyo_data2.columns = ['chno', 'use', 'testname', 'folder', 'temp', 'cyc1', 'cyc2', 'cyc3', 'vol']
            toyo_data["chno"] = toyo_data["chno"].astype(int)
            toyo_data["use"] = toyo_data["use"].astype(int)
            toyo_data["day"] = toyo_data['testname'].apply(self.split_value0)
            toyo_data["part"] = toyo_data['testname'].apply(self.split_value1)
            toyo_data["name"] = toyo_data['testname'].apply(self.split_value2)
            toyo_data["path"] = toyo_data['testname']
            if toyo_num != 3:
                toyo_data["folder"] = toyo_data2["folder"]
                toyo_data["temp"] = toyo_data2['temp']
                toyo_data["cyc"] = toyo_data2['cyc1'].astype(str) + " / " + toyo_data2['cyc2'].astype(str) + " / " + toyo_data2['cyc3'].astype(str)
                toyo_data["vol"] = toyo_data2['vol'].where((toyo_data2["vol"].astype('float') < 5) & (toyo_data2["vol"].astype('float') > 2), "-")
            else:
                toyo_data["folder"] = toyo_data['testname'].str.split(" ").str[2]
                toyo_data["temp"] = toyo_data['testname'].str.split(" ").str[2]
                toyo_data["cyc"] = toyo_data['testname'].str.split(" ").str[2]
                toyo_data["vol"] = toyo_data['testname'].str.split(" ").str[2]
            toyo_data["cyclername"] = blkname
            used_chnl = toyo_data["use"].sum()
            # int64 -> object 타입 변환 (문자열 할당을 위해)
            toyo_data["use"] = toyo_data["use"].astype(object)
            toyo_data.loc[(toyo_data["chno"] == 1) & (toyo_data["use"] == 0), "use"] = "완료"
            toyo_data.loc[(toyo_data["chno"] == 0) & (toyo_data["use"] == 0), "use"] = "작업정지"
            toyo_data.loc[toyo_data["use"] == 1, "use"] = "작업중"
            toyo_data["chno"] = toyo_data.index
        else:
            # 파일이 없을 경우 에러 메시지 표시 및 빈 데이터 반환
            err_msg("Toyo 데이터 없음", f"경로를 확인하세요: {toyoworkpath}")
            toyo_data = pd.DataFrame(columns=self.toyo_column_list)
            used_chnl = 0
        return [toyo_data, used_chnl]

    def toyo_data_make(self, toyo_num, blkname):
        toyo_data = self.toyo_base_data_make(toyo_num, blkname)
        self.df = toyo_data[0]
        self.AllchnlData = pd.concat([self.AllchnlData, self.df])

    def toyo_table_make(self, num_i, num_j, toyo_num, blkname):
        toyo_data = self.toyo_base_data_make(toyo_num, blkname)
        self.df = toyo_data[0]
        self.tb_summary.setItem(0, 0, QtWidgets.QTableWidgetItem(str(num_i * num_j - toyo_data[1])))
        self.tb_summary.setItem(1, 0, QtWidgets.QTableWidgetItem(str(toyo_data[1])))
        for i in range(1, num_i + 1):
            for j in range(1, num_j + 1):
                # 첫번째 선택은 채널 번호
                chnl_name = i + (j - 1) * num_i
                column_name = self.toyo_column_list[self.tb_info.currentIndex() + 1]
                self.tb_channel.setItem(j - 1, i - 1, QtWidgets.QTableWidgetItem(str(chnl_name).zfill(3) + "| " + str(
                    self.df.loc[i + (j - 1) * num_i, str(column_name)])))
                self.tb_channel.item(j - 1, i - 1).setFont(QtGui.QFont("Malgun gothic", 9))
                # text가 있는 부분에 대해서 별도 표시 기능 추가
                if self.df.loc[i + (j - 1) * num_i,"use"] == "작업정지" or self.df.loc[i + (j - 1) * num_i,"use"] == "완료":
                    self.tb_channel.item(j - 1, i - 1).setBackground(QtGui.QColor(255,127,0))
                if toyo_num != 3 and self.df.loc[i + (j - 1) * num_i,"vol"] == "-":
                    self.tb_channel.item(j - 1, i - 1).setBackground(QtGui.QColor(200,255,255))
                # 코인셀 구분
                if (toyo_num == 0 and (i + (j - 1) * num_i) < 17) or ((toyo_num == 0 or toyo_num == 1) and
                                                                      ((i + (j - 1) * num_i) > 64) and ((i + (j - 1) * num_i) < 81)):
                    self.tb_channel.item(j - 1, i - 1).setFont(QtGui.QFont("Malgun gothic", 8))
                # text가 있는 부분에 대해서 별도 표시 기능 추가
                if (str(self.FindText.text()) == "") or (str(self.FindText.text()) in self.df.loc[i + (j - 1) * num_i,"testname"]):
                        # 온도별 구분
                        if (toyo_num == 0 and (i + (j - 1) * num_i) > 64):
                            self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(255,0,0))
                        if (toyo_num == 1 and (i + (j - 1) * num_i) > 64):
                            self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(0,0,255))
                        if (toyo_num == 2 and (i + (j - 1) * num_i) > 64):
                            self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(255,0,0))
                        else:
                            self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(0,0,0))
                else:
                    self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(175, 175, 175))
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                self.progressBar.setValue(0)
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                self.df.to_excel(writer, index=False)
                writer.close()
                self.progressBar.setValue(100)

    def pne_data_make(self, pne_num, blkname):
        # 경로 확인
        if os.path.isdir(self.pne_work_path_list[pne_num]):
            pneworkpath = self.pne_work_path_list[pne_num]+"\\Module_1_channel_info.json"
            pneworkpath2 = self.pne_work_path_list[pne_num]+"\\Module_2_channel_info.json"
        if os.path.isfile(pneworkpath2):
            with open(pneworkpath) as f1:
                js1 = json.loads(f1.read())
            with open(pneworkpath2) as f2:
                js2 = json.loads(f2.read())
            df1 = pd.DataFrame(js1['Channel'])
            df2 = pd.DataFrame(js2['Channel'])
            self.df = pd.concat([df1, df2])
        else:
            with open(pneworkpath) as f1:
                js1 = json.loads(f1.read())
            self.df = pd.DataFrame(js1['Channel'])
        # 데이터 처리
        if os.path.isfile(pneworkpath):
            temp_data = self.df[["Temperature"]]
            temp_data = temp_data.astype('float') * 1000
            temp_data = temp_data.astype('int')
            self.df = self.df[["Ch_No", "State", "Test_Name", "Schedule_Name", "Current_Cycle_Num", "Step_No", "Total_Cycle_Num", "Voltage",
                               "Result_Path"]]
            self.df.columns = self.toyo_column_list[0:4] + ["Current_Cycle_Num", "Step_No", "Total_Cycle_Num", "Voltage", "Result_Path"]
            self.df = self.df.dropna()
            self.df.index = self.df["chno"].astype('int')
            temp_data.index = self.df["chno"].astype('int')
            self.df["day"] = self.df['testname'].apply(self.split_value0)
            self.df["part"] = self.df['testname'].apply(self.split_value1)
            self.df["name"] = self.df['testname'].apply(self.split_value2)
            self.df["temp"] = temp_data
            self.df["Current_Cycle_Num"] = self.df["Current_Cycle_Num"].apply(lambda x: (" " * (4 - len(x))) + x)
            self.df["Step_No"] = self.df["Step_No"].apply(lambda x: (" " * (4 - len(x))) + x)
            self.df["Total_Cycle_Num"] = self.df["Total_Cycle_Num"].apply(lambda x: (" " * (4 - len(x))) + x)
            self.df["cyc"] = self.df["Step_No"] + " / " + self.df["Current_Cycle_Num"] + " / " +  self.df["Total_Cycle_Num"]
            self.df["vol"] = self.df["Voltage"].where(self.df["Voltage"].astype('float') > 0.04, "-")
            self.df["cyclername"] = blkname
            self.df["chno"] = self.df.index
            # 데이터 경로 변경
            self.df = self.change_drive(self.df, self.pne_data_path_list[pne_num])
            self.AllchnlData = pd.concat([self.AllchnlData, self.df])
    
    def pne_table_make(self, num_i, num_j, pne_num, blkname):
        # 경로 확인
        if os.path.isdir(self.pne_work_path_list[pne_num]):
            pneworkpath = self.pne_work_path_list[pne_num]+"\\Module_1_channel_info.json"
            pneworkpath2 = self.pne_work_path_list[pne_num]+"\\Module_2_channel_info.json"
            if os.path.isfile(pneworkpath2):
                with open(pneworkpath) as f1:
                    js1 = json.loads(f1.read())
                with open(pneworkpath2) as f2:
                    js2 = json.loads(f2.read())
                df1 = pd.DataFrame(js1['Channel'])
                df2 = pd.DataFrame(js2['Channel'])
                self.df = pd.concat([df1, df2])
            else:
                with open(pneworkpath) as f1:
                    try:
                        js1 = json.loads(f1.read())
                    except json.JSONDecodeError as e:
                        print(f"JSON 오류: {e} 라인 {e.line} 수정 필요")
                self.df = pd.DataFrame(js1['Channel'])
        # 데이터 처리
            temp_data = self.df[["Temperature"]]
            temp_data = temp_data.astype('float') * 1000
            temp_data = temp_data.astype('int')
            self.df = self.df[["Ch_No", "State", "Test_Name", "Schedule_Name", "Current_Cycle_Num", "Step_No", "Total_Cycle_Num", "Voltage",
                               "Result_Path"]]
            self.df.columns = self.toyo_column_list[0:4] + ["Current_Cycle_Num", "Step_No", "Total_Cycle_Num", "Voltage", "Result_Path"]
            self.df = self.df.dropna()
            self.df.index = self.df["chno"].astype('int')
            temp_data.index = self.df["chno"].astype('int')
            self.df["day"] = self.df['testname'].apply(self.split_value0)
            self.df["part"] = self.df['testname'].apply(self.split_value1)
            self.df["name"] = self.df['testname'].apply(self.split_value2)
            self.df["temp"] = temp_data
            self.df["Current_Cycle_Num"] = self.df["Current_Cycle_Num"].apply(lambda x: (" " * (4 - len(x))) + x)
            self.df["Step_No"] = self.df["Step_No"].apply(lambda x: (" " * (4 - len(x))) + x)
            self.df["Total_Cycle_Num"] = self.df["Total_Cycle_Num"].apply(lambda x: (" " * (4 - len(x))) + x)
            self.df["cyc"] = self.df["Step_No"] + " / " + self.df["Current_Cycle_Num"] + " / " +  self.df["Total_Cycle_Num"]
            self.df["vol"] = self.df["Voltage"].where(self.df["Voltage"].astype('float') > 0.04, "-")
            self.df["cyclername"] = blkname
            self.df["chno"] = self.df.index
            # 데이터 경로 변경
            self.df = self.change_drive(self.df, self.pne_data_path_list[pne_num])
            usedchnlno = len(self.df[(self.df.use =="완료") | (self.df.use == "대기") | (self.df.use == "준비")])
            self.tb_summary.setItem(0, 0, QtWidgets.QTableWidgetItem(str(usedchnlno)))
            self.tb_summary.setItem(1, 0, QtWidgets.QTableWidgetItem(str(num_i * num_j - usedchnlno)))
            for i in range(1, num_i + 1):
                for j in range(1, num_j + 1):
                    chnl_name = i + (j - 1) * num_i
                    column_name = self.toyo_column_list[self.tb_info.currentIndex() + 1]
                    if self.tb_info.currentIndex() == 9:
                        self.tb_channel.setItem(j - 1, i - 1, QtWidgets.QTableWidgetItem(str(self.df.loc[i + (j - 1) * num_i, str(column_name)])))
                        self.tb_channel.item(j - 1, i - 1).setFont(QtGui.QFont("Malgun gothic", 9))
                    else:
                        self.tb_channel.setItem(j - 1, i - 1, QtWidgets.QTableWidgetItem(str(chnl_name).zfill(3) + "| " + str(
                            self.df.loc[i + (j - 1) * num_i, str(column_name)])))
                        self.tb_channel.item(j - 1, i - 1).setFont(QtGui.QFont("Malgun gothic", 9))
                    # 채널 구분 
                    # # 사용 가능 채널 구분 _ 하늘색
                    if (self.df.loc[i + (j - 1) * num_i,"use"] == "대기") or (self.df.loc[i + (j - 1) * num_i,"use"] == "준비"):
                        self.tb_channel.item(j - 1, i - 1).setBackground(QtGui.QColor(200,255,255))
                    elif (self.df.loc[i + (j - 1) * num_i,"use"] == "완료"): # 사용 가능 채널 구분 _ 주황색
                        self.tb_channel.item(j - 1, i - 1).setBackground(QtGui.QColor(255,127,0))
                    elif self.df.loc[i + (j - 1) * num_i,"use"] == "작업멈춤": # 정지 채널 구분 _ 붉은색
                        self.tb_channel.item(j - 1, i - 1).setBackground(QtGui.QColor(255,200,229))
                    # text가 있는 부분에 대해서 별도 표시 기능 추가
                    if (str(self.FindText.text()) == "") or (str(self.FindText.text()) in self.df.loc[i + (j - 1) * num_i,"testname"]):
                            # 온도별 구분
                            if self.df.loc[i + (j - 1) * num_i, "temp"] > 10 and self.df.loc[i + (j - 1) * num_i, "temp"] <= 20:
                                self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(0,0,255)) # 15도 파란색
                            elif self.df.loc[i + (j - 1) * num_i, "temp"] > 30 and self.df.loc[i + (j - 1) * num_i, "temp"] <= 40:
                                self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(0,255,0)) # 35도 녹색
                            elif self.df.loc[i + (j - 1) * num_i, "temp"] > 40 and self.df.loc[i + (j - 1) * num_i, "temp"] <= 50:
                                self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(255,0,0)) # 45도 빨간색
                            else:
                                self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(0,0,0)) # 기본 검은색
                    else:
                        self.tb_channel.item(j - 1, i - 1).setForeground(QtGui.QColor(175, 175, 175))
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                if save_file_name:
                    self.progressBar.setValue(0)
                    writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                    self.df.to_excel(writer, index=False)
                    writer.close()
                    self.progressBar.setValue(100)

    def table_reset(self):
        self.tb_channel.clear()

    def change_drive(self, df, changed):
        # 상세 데이터부터 범용 데이터 순으로 바꾸기 진행
        original_drive = ["D:\\Data\\", "D:\\DATA\\","D:\\", "E:\\Data\\", "E:\\DATA\\", "E:\\"]
        df["path"] = df["Result_Path"].apply(lambda x: x[:x.rfind('\\')+1])
        for cycler_drive in original_drive:
            df["path"] = df["path"].str.replace(cycler_drive, changed)
        return df

    def cycle_error(self):
        err_msg('파일 or 경로없음!!','C드라이브에 cycler_path.txt 파일이 없거나 toyo/PNE 경로 설정 오류')

    def tb_cycler_combobox(self):
        toyo_table_makers = {
        "Toyo1":(8, 16, 0, self.toyo_cycler_name[0]),
        "Toyo2":(8, 16, 1, self.toyo_cycler_name[1]),
        "Toyo3":(8, 16, 2, self.toyo_cycler_name[2]),
        "Toyo4":(5, 2, 3, self.toyo_cycler_name[3]),
        "Toyo5":(5, 4, 4, self.toyo_cycler_name[4])
        }
        pne_table_makers = {
        "PNE1": (8, 16, 0, self.pne_cycler_name[0]),
        "PNE2": (8, 12, 1, self.pne_cycler_name[1]),
        "PNE3": (8, 4, 2, self.pne_cycler_name[2]),
        "PNE4": (8, 4, 3, self.pne_cycler_name[3]),
        "PNE5": (8, 4, 4, self.pne_cycler_name[4]),
        "PNE01": (8, 4, 5, self.pne_cycler_name[5]),
        "PNE02": (8, 4, 6, self.pne_cycler_name[6]),
        "PNE03": (8, 4, 7, self.pne_cycler_name[7]),
        "PNE04": (8, 8, 8, self.pne_cycler_name[8]),
        "PNE05": (8, 8, 9, self.pne_cycler_name[9]),
        "PNE06": (8, 8, 10, self.pne_cycler_name[10]),
        "PNE07": (8, 8, 11, self.pne_cycler_name[11]),
        "PNE08": (8, 8, 12, self.pne_cycler_name[12]),
        "PNE09": (8, 8, 13, self.pne_cycler_name[13]),
        "PNE10": (8, 8, 14, self.pne_cycler_name[14]),
        "PNE11": (8, 8, 15, self.pne_cycler_name[15]),
        "PNE12": (8, 8, 16, self.pne_cycler_name[16]),
        "PNE13": (8, 8, 17, self.pne_cycler_name[17]),
        "PNE14": (8, 8, 18, self.pne_cycler_name[18]),
        "PNE15": (8, 8, 19, self.pne_cycler_name[19]),
        "PNE16": (8, 8, 20, self.pne_cycler_name[20]),
        "PNE17": (8, 8, 21, self.pne_cycler_name[21]),
        "PNE18": (8, 8, 22, self.pne_cycler_name[22]),
        "PNE19": (8, 8, 23, self.pne_cycler_name[23]),
        "PNE20": (8, 8, 24, self.pne_cycler_name[24]),
        "PNE21": (8, 16, 25, self.pne_cycler_name[25]),
        "PNE22": (8, 16, 26, self.pne_cycler_name[26]),
        "PNE23": (8, 4, 27, self.pne_cycler_name[27]),
        "PNE24": (8, 4, 28, self.pne_cycler_name[28]),
        "PNE25": (8, 4, 29, self.pne_cycler_name[29])
        }
        cycler_text = self.tb_cycler.currentText()
        self.table_reset()
        if cycler_text in toyo_table_makers:
            col_count, row_count, index, name = toyo_table_makers[cycler_text]
            self.toyo_table_make(col_count, row_count, index, name)
        if cycler_text in pne_table_makers:
            col_count, row_count, index, name = pne_table_makers[cycler_text]
            self.pne_table_make(col_count, row_count, index, name)

    def tb_room_combobox(self):
        if self.tb_room.currentIndex() == 0:
            self.tb_cycler.clear()
            self.tb_cycler.addItems(["Toyo1", "Toyo2", "Toyo3", "Toyo4", "Toyo5", "PNE1", "PNE2", "PNE3", "PNE4", "PNE5"])
        elif self.tb_room.currentIndex() == 1:
            self.tb_cycler.clear()
            self.tb_cycler.addItems(["PNE01", "PNE02", "PNE03", "PNE04", "PNE05", "PNE06", "PNE07", "PNE08"])
        elif self.tb_room.currentIndex() == 2:
            self.tb_cycler.clear()
            self.tb_cycler.addItems(["PNE09", "PNE10", "PNE11", "PNE12", "PNE13", "PNE14", "PNE15", "PNE16"])
        elif self.tb_room.currentIndex() == 3:
            self.tb_cycler.clear()
            self.tb_cycler.addItems(["PNE17", "PNE18", "PNE19", "PNE20", "PNE21", "PNE22", "PNE23", "PNE24", "PNE25"])
        elif self.tb_room.currentIndex() == 4:
            self.tb_cycler.clear()
            self.tb_cycler.addItems(["Toyo1", "Toyo2", "Toyo3", "Toyo4", "Toyo5", "PNE1", "PNE2", "PNE3", "PNE4", "PNE5",
                                     "PNE01", "PNE02", "PNE03", "PNE04", "PNE05", "PNE06", "PNE07", "PNE08",
                                     "PNE09", "PNE10", "PNE11", "PNE12", "PNE13", "PNE14", "PNE15", "PNE16",
                                     "PNE17", "PNE18", "PNE19", "PNE20", "PNE21", "PNE22", "PNE23", "PNE24", "PNE25"])

    def tb_info_combobox(self):
        self.tb_cycler_combobox()

    def bm_set_profile_button(self):
        self.BMset_battery_status_log_Profile.setDisabled(True)
        global writer
        root = Tk()
        root.withdraw()
        datafilepath = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        self.BMset_battery_status_log_Profile.setEnabled(True)
        if datafilepath:
            filecount = 0
            mincapa = int(self.SetMincapacity.text())
            fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6), (ax7, ax8), (ax9, ax10)) \
                = plt.subplots(nrows=5, ncols=2, figsize=(12, 10))
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                if save_file_name:
                    writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                dfchg = pd.DataFrame()
                dfdchg = pd.DataFrame()
            for filepath in datafilepath:
                filecountmax = len(datafilepath)
                progressdata = filecount/filecountmax * 100
                filecount = filecount + 1
                self.progressBar.setValue(int(progressdata))
                    
                df = pd.read_csv(filepath, usecols=[0, 2, 21, 25, 27, 28], on_bad_lines='skip')
                df.columns = ['Time', 'Curr', 'SOC2', 'SOC', 'Vol', 'Temp']
                if "방전" in filepath:
                    df["Type"] = "Discharge"
                    df["State"] = "Unplugged"
                else:
                    df["Type"] = "Charging"
                    df["State"] = "AC"
                raw_file_split = filepath.split("_")
                CycNo = raw_file_split[1]
                if "csv" in filepath:
                    CycNo = CycNo.replace('.csv','')
                else:
                    CycNo = CycNo.replace('.txt','')
                df["Cyc"] = int(CycNo)
                df=df[df.loc[:,'Curr']!="Batterycurrent"]
                df = df.reset_index()
                df['Time'] = df.index * 2 / 3600
                df['Curr']=df['Curr'].apply(float)/mincapa*(-1)
                df['SOC2']=df['SOC2'].apply(float)/10/mincapa/2
                df['SOC']=df['SOC'].apply(float)
                df['Vol']=df['Vol'].apply(float)/1000
                df['Temp']=df['Temp'].apply(float)/10
                if "방전" in filepath:
                    graph_set_profile(df.Time, df.Vol, ax2, 3.4, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 0, 11, 1)
                    graph_set_profile(df.Time, df.Curr, ax4, -0.6, 0.1, 0.1, "Time(hr)", "Curr", "", 0, 0, 11, 1)
                    graph_set_profile(df.Time, df.Temp, ax6, 20, 50, 4, "Time(hr)", "temp.", "", 0, 0, 11, 1)
                    graph_set_profile(df.Time, df.SOC, ax8, 0, 120, 10, "Time(hr)", "SOC", "", 0, 0, 11, 1)
                    graph_set_profile(df.Time, df.SOC2, ax10, 0, 110, 10, "Time(hr)", "real SOC", "", 0, 0, 11, 1)
                else:
                    df = df[(df["Time"] < 4)]
                    graph_set_profile(df.Time, df.Vol, ax1, 3.4, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 0, 4, 1)
                    graph_set_profile(df.Time, df.Curr, ax3, 0, 12, 1.0, "Time(hr)", "Curr", "", 0, 0, 4, 1)
                    graph_set_profile(df.Time, df.Temp, ax5, 20, 50, 4, "Time(hr)", "temp.", "", 0, 0, 4, 1)
                    graph_set_profile(df.Time, df.SOC, ax7, 0, 120, 10, "Time(hr)", "SOC", "", 0, 0, 4, 1)
                    graph_set_profile(df.Time, df.SOC2, ax9, 0, 120, 10, "Time(hr)", "real SOC", CycNo, 0, 0 , 4, 1)
                if self.saveok.isChecked() and save_file_name:
                    if "방전" in filepath:
                    # 방전 Profile 추출용
                        dfdchg = dfdchg._append(df)
                        # dfdchg.to_excel(writer, sheet_name="dchg")
                    else:
                    # 충전 Profile 추출용
                        dfchg = dfchg._append(df)
                        # dfchg.to_excel(writer, sheet_name="chg")
            if self.saveok.isChecked() and save_file_name:
                dfdchg.to_excel(writer, sheet_name="dchg")
                dfchg.to_excel(writer, sheet_name="chg")
                writer.close()
                
            self.progressBar.setValue(100)
            fig.legend()
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            plt.subplots_adjust(right=0.8)
            plt.show()
    
    def bm_set_cycle_button(self):
        global writer
        root = Tk()
        root.withdraw()
        setxscale = int(self.setcyclexscale.text())
        datafilepath = filedialog.askdirectory(initialdir="d://", title="Choose Test files")
        if datafilepath:
            fig, ((ax1), (ax2)) = plt.subplots(nrows=1, ncols=2, figsize=(8, 4))
            filecount = 0
            mincapa = int(self.SetMincapacity.text())
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                if save_file_name:
                    writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
            dfcyc = pd.DataFrame()
            dfcyc2 = pd.DataFrame()
            subfile = [f for f in os.listdir(datafilepath) if f.startswith('방전_')]
            for filepath in subfile:
                filecountmax = len(subfile)
                progressdata = filecount/filecountmax * 100
                filecount = filecount + 1
                self.progressBar.setValue(int(progressdata))
                df = pd.read_csv(datafilepath+"/"+filepath, usecols=[21], on_bad_lines='skip')
                df.columns = ['SOC']
                raw_file_split = filepath.split("_")
                CycNo = raw_file_split[1]
                if "csv" in filepath:
                    CycNo = CycNo.replace('.csv','')
                else:
                    CycNo = CycNo.replace('.txt','')
                df["Cyc"] = int(CycNo)
                df=df[df.loc[:,'SOC']!="Charge_counter"]
                df['SOC']=df['SOC'].apply(float)/10/mincapa/2/100
                dfcyc = dfcyc._append(df.loc[0])
            subfile2 = [f for f in os.listdir(datafilepath) if f.startswith('충전_')]
            for filepath2 in subfile2:
                filecountmax = len(subfile2)
                progressdata = filecount/filecountmax * 100
                filecount = filecount + 1
                self.progressBar.setValue(int(progressdata))
                df2 = pd.read_csv(datafilepath+"/"+filepath2, usecols=[21], on_bad_lines='skip')
                df2.columns = ['SOC2']
                raw_file_split = filepath2.split("_")
                CycNo = raw_file_split[1]
                if "csv" in filepath:
                    CycNo = CycNo.replace('.csv','')
                else:
                    CycNo = CycNo.replace('.txt','')
                df2["Cyc2"] = int(CycNo)
                df2=df2[df2.loc[:,'SOC2']!="Charge_counter"]
                df2['SOC2']=df2['SOC2'].apply(float)/10/mincapa/2/100
                dfcyc2 = dfcyc2._append(df2.iloc[-1])
            dfcyc = dfcyc.sort_values(by="Cyc")
            dfcyc2 = dfcyc2.sort_values(by="Cyc2")
            graph_cycle(dfcyc.Cyc, dfcyc.SOC, ax1, 0.8, 1.05, 0.05, "Cycle", "Discharge Capacity Ratio", datafilepath, setxscale, 0)
            graph_cycle(dfcyc2.Cyc2, dfcyc2.SOC2, ax2, 0.8, 1.05, 0.05, "Cycle", "Charge Capacity Ratio", datafilepath, setxscale, 0)
            if self.saveok.isChecked() and save_file_name:
                dfcyc=dfcyc[["Cyc", "SOC"]]
                dfcyc2=dfcyc2[["Cyc2", "SOC2"]]
                dfcyc = dfcyc.reset_index()
                dfcyc2 = dfcyc2.reset_index()
                dfcyc.to_excel(writer, sheet_name="dchgcyc")
                dfcyc2.to_excel(writer, sheet_name="chgcyc")
                writer.close()
            self.progressBar.setValue(100)
            fig.legend()
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            plt.show()
    
    def bm_set_profile_button(self):
        global writer
        root = Tk()
        root.withdraw()
        datafilepath = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        filecount = 0
        mincapa = int(self.SetMincapacity.text())
        fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6), (ax7, ax8), (ax9, ax10)) \
            = plt.subplots(nrows=5, ncols=2, figsize=(12, 10))
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
            dfchg = pd.DataFrame()
            dfdchg = pd.DataFrame()
        for filepath in datafilepath:
            filecountmax = len(datafilepath)
            progressdata = filecount/filecountmax * 100
            filecount = filecount + 1
            self.progressBar.setValue(int(progressdata))
            df = pd.read_csv(filepath, usecols=[0, 2, 21, 25, 27, 28], on_bad_lines='skip')
            df.columns = ['Time', 'Curr', 'SOC2', 'SOC', 'Vol', 'Temp']
            if "방전" in filepath:
                df["Type"] = "Discharge"
                df["State"] = "Unplugged"
            else:
                df["Type"] = "Charging"
                df["State"] = "AC"
            raw_file_split = filepath.split("_")
            CycNo = raw_file_split[1]
            if "csv" in filepath:
                CycNo = CycNo.replace('.csv','')
            else:
                CycNo = CycNo.replace('.txt','')
            df["Cyc"] = int(CycNo)
            df=df[df.loc[:,'Curr']!="Batterycurrent"]
            df = df.reset_index()
            df['Time'] = df.index * 2 / 3600
            df['Curr']=df['Curr'].apply(float)/mincapa*(-1)
            df['SOC2']=df['SOC2'].apply(float)/10/mincapa/2
            df['SOC']=df['SOC'].apply(float)
            df['Vol']=df['Vol'].apply(float)/1000
            df['Temp']=df['Temp'].apply(float)/10
            if "방전" in filepath:
                graph_set_profile(df.Time, df.Vol, ax2, 3.4, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 0, 11, 1)
                graph_set_profile(df.Time, df.Curr, ax4, -0.6, 0.1, 0.1, "Time(hr)", "Curr", "", 0, 0, 11, 1)
                graph_set_profile(df.Time, df.Temp, ax6, 20, 50, 4, "Time(hr)", "temp.", "", 0, 0, 11, 1)
                graph_set_profile(df.Time, df.SOC, ax8, 0, 120, 10, "Time(hr)", "SOC", "", 0, 0, 11, 1)
                graph_set_profile(df.Time, df.SOC2, ax10, 0, 110, 10, "Time(hr)", "real SOC", "", 0, 0, 11, 1)
            else:
                df = df[(df["Time"] < 4)]
                graph_set_profile(df.Time, df.Vol, ax1, 3.4, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 0, 4, 1)
                graph_set_profile(df.Time, df.Curr, ax3, 0, 12, 1.0, "Time(hr)", "Curr", "", 0, 0, 4, 1)
                graph_set_profile(df.Time, df.Temp, ax5, 20, 50, 4, "Time(hr)", "temp.", "", 0, 0, 4, 1)
                graph_set_profile(df.Time, df.SOC, ax7, 0, 120, 10, "Time(hr)", "SOC", "", 0, 0, 4, 1)
                graph_set_profile(df.Time, df.SOC2, ax9, 0, 120, 10, "Time(hr)", "real SOC", CycNo, 0, 0, 4, 1)
            if self.saveok.isChecked() and save_file_name:
                if "방전" in filepath:
                    dfdchg = dfdchg._append(df)
                else:
                    dfchg = dfchg._append(df)
        if self.saveok.isChecked() and save_file_name:
            dfdchg.to_excel(writer, sheet_name="dchg")
            dfchg.to_excel(writer, sheet_name="chg")
            writer.close()
        fig.legend()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        plt.subplots_adjust(right=0.8)
        self.progressBar.setValue(100)
        plt.show()
    
    def bm_set_cycle_button(self):
        self.BMSetCycle.setDisabled(True)
        global writer
        root = Tk()
        root.withdraw()
        setxscale = int(self.setcyclexscale.text())
        datafilepath = filedialog.askdirectory(initialdir="d://", title="Choose Test files")
        self.BMSetCycle.setEnabled(True)
        fig, ((ax1), (ax2)) = plt.subplots(nrows=1, ncols=2, figsize=(8, 4))
        filecount = 0
        mincapa = int(self.SetMincapacity.text())
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        dfcyc = pd.DataFrame()
        dfcyc2 = pd.DataFrame()
        subfile = [f for f in os.listdir(datafilepath) if f.startswith('방전_')]
        for filepath in subfile:
            filecountmax = len(subfile)
            progressdata = filecount/filecountmax * 100
            filecount = filecount + 1
            self.progressBar.setValue(int(progressdata))
            df = pd.read_csv(datafilepath+"/"+filepath, usecols=[21], on_bad_lines='skip')
            df.columns = ['SOC']
            raw_file_split = filepath.split("_")
            CycNo = raw_file_split[1]
            if "csv" in filepath:
                CycNo = CycNo.replace('.csv','')
            else:
                CycNo = CycNo.replace('.txt','')
            df["Cyc"] = int(CycNo)
            df=df[df.loc[:,'SOC']!="Charge_counter"]
            df['SOC']=df['SOC'].apply(float)/10/mincapa/2/100
            dfcyc = dfcyc._append(df.loc[0])
        subfile2 = [f for f in os.listdir(datafilepath) if f.startswith('충전_')]
        for filepath2 in subfile2:
            filecountmax = len(subfile2)
            progressdata = filecount/filecountmax * 100
            filecount = filecount + 1
            self.progressBar.setValue(int(progressdata))
            df2 = pd.read_csv(datafilepath+"/"+filepath2, usecols=[21], on_bad_lines='skip')
            df2.columns = ['SOC2']
            raw_file_split = filepath2.split("_")
            CycNo = raw_file_split[1]
            if "csv" in filepath:
                CycNo = CycNo.replace('.csv','')
            else:
                CycNo = CycNo.replace('.txt','')
            df2["Cyc2"] = int(CycNo)
            df2=df2[df2.loc[:,'SOC2']!="Charge_counter"]
            df2['SOC2']=df2['SOC2'].apply(float)/10/mincapa/2/100
            dfcyc2 = dfcyc2._append(df2.iloc[-1])
        dfcyc = dfcyc.sort_values(by="Cyc")
        dfcyc2 = dfcyc2.sort_values(by="Cyc2")
        graph_cycle(dfcyc.Cyc, dfcyc.SOC, ax1, 0.7, 1.05, 0.05, "Cycle", "Discharge Capacity Ratio", datafilepath, setxscale, 0)
        graph_cycle(dfcyc2.Cyc2, dfcyc2.SOC2, ax2, 0.7, 1.05, 0.05, "Cycle", "Charge Capacity Ratio", datafilepath, setxscale, 0)
        if self.saveok.isChecked() and save_file_name:
            dfcyc=dfcyc[["Cyc", "SOC"]]
            dfcyc2=dfcyc2[["Cyc2", "SOC2"]]
            dfcyc = dfcyc.reset_index()
            dfcyc2 = dfcyc2.reset_index()
            dfcyc.to_excel(writer, sheet_name="dchgcyc")
            dfcyc2.to_excel(writer, sheet_name="chgcyc")
            writer.close()
        self.progressBar.setValue(100)
        fig.legend()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        plt.show()

    def battery_dump_data(self, battery_dump_path):
        # 0:Time, 1:VOLTAGE NOW, 2:CURRENT NOW, 3:CURRENT MAX, 4:CHARGING CURRENT, 5:CAPACITY, 6:TBAT, 7:TUSB, 8:TCHG, 9:TWPC, 10:TBLK,
        # 11:TLRP, 12:TDCHG, 13:TSUB, 14:BATTERY STATUS, 15:DIRECT CHARGER STATUS, 16:CHARGING MODE, 17:HEALTH STATUS, 18:CABLE TYPE, 19:MUIC CABLE TYPE,
        # 20:THERMAL ZONE, 21:SLATE MODE, 22:STORE MODE, 23:SAFETY TIMER, 24:CURRENT EVENT, 25:MISC EVENT, 26:TX EVENT, 27:PHM, 28:SRCCAP_TRANSIT,
        # 29:SYS AVG CURRENT, 30:BD_VERSION, 31:VID, 32:PID, 33:XID, 34:VOLTAGE PACK MAIN, 35:VOLTAGE PACK SUB, 36:CURRENT NOW MAIN, 37:CURRENT NOW SUB,
        # 38:CYCLE, 39:OCV, 40:RAW SOC, 41:CAPACITY MAX, 42:WRL_MODE, 43:TX VOUT, 44:TX IOUT, 45:PING FRQ, 46:MIN OP FRQ, 47:MAX OP FRQ, 48:PHM,
        # 49:RX TYPE, 50:OTP FMWR VERSION, 51:WC IC REV
        
        #1:DATE TIME  	2:VOLTAGE NOW 	3:CURRENT NOW 	4:CURRENT MAX 	5:CHARGING CURRENT 	6:CAPACITY 	7:TBAT 	8:TUSB 	9:TCHG 	10:TWPC
        #11:TBLK 	12:TLRP 	13:TDCHG 	14:TSUB 	15:BATTERY STATUS 	16:DIRECT CHARGER STATUS 	17:CHARGING MODE 	
        #18:HEALTH STATUS 	19:CABLE TYPE 	20:MUIC CABLE TYPE 	21:THERMAL ZONE 	22:SLATE MODE 	23:STORE MODE 	24:SAFETY TIMER
        #5:CURRENT EVENT 	26:MISC EVENT 	27:TX EVENT 	28:PHM 	29:SRCCAP TRANSIT 	30:SYS AVG CURRENT 	31:BD_VERSION 	
        #32:DC_RATIO 	33:C_PDO/A_PDO-MAX_V-MIN_V-MAX_CUR 	34:VID 	35:PID 	36:XID 	37:VOLTAGE PACK MAIN 	38:CURRENT NOW MAIN
        #39:CYCLE 	40:OCV 	41:RAW SOC 	42:CAPACITY MAX 	43:WRL_MODE 

        batterydump1 = pd.read_csv(battery_dump_path + "//battery_dump1", sep=",", on_bad_lines='skip')
        batterydump2 = pd.read_csv(battery_dump_path + "//battery_dump2", sep=",", on_bad_lines='skip')
        batterydump1 = batterydump1.iloc[:, [0, 1, 2, 5, 6, 7, 8, 11, 14, 15, 29, 38, 39, 40, 41]]
        batterydump2 = batterydump2.iloc[:, [0, 1, 2, 5, 6, 7, 8, 11, 14, 15, 29, 38, 39, 40, 41]]
        batterydump1.columns = ['Time_temp', 'Vol', 'Curr', 'SOC', 'T_bat', 'T_usb', 'T_chg', 'T_lrp', 'battery_status', 'direct_charger_status',
                               'sys_avg_current', 'cycle', 'ocv', 'SOCraw', 'cap_max']
        batterydump2.columns = ['Time_temp', 'Vol', 'Curr', 'SOC', 'T_bat', 'T_usb', 'T_chg', 'T_lrp', 'battery_status', 'direct_charger_status',
                               'sys_avg_current', 'cycle', 'ocv', 'SOCraw', 'cap_max']
        Profile = pd.concat([batterydump1, batterydump2], axis=0).reset_index(drop=True)
        Profile = Profile.dropna()
        # batterydump1 = batterydump1.iloc[:, [0, 1, 2, 5, 6, 7, 8, 11, 14, 15, 29, 38, 39, 40, 41]]
        # batterydump1.columns = ['Time_temp', 'Vol', 'Curr', 'SOC', 'T_bat', 'T_usb', 'T_chg', 'T_lrp', 'battery_status', 'direct_charger_status',
        #                        'sys_avg_current', 'cycle', 'ocv', 'SOCraw', 'capacity_max']
        # Profile = batterydump.iloc[:, [0, 1, 2, 5, 6, 7, 8, 11, 14, 15, 29, 38, 39, 40, 41]]
        # Profile.columns = ['Time_temp', 'Vol', 'Curr', 'SOC', 'T_bat', 'T_usb', 'T_chg', 'T_lrp', 'battery_status', 'direct_charger_status',
        #                        'sys_avg_current', 'cycle', 'ocv', 'SOCraw', 'capacity_max']
        # 2023-09-10 20:08:25+0530
        Profile["Time"] = Profile["Time_temp"].str[:-5]
        Profile["Time"] = pd.to_datetime(Profile["Time"], format= '%Y-%m-%d %H:%M:%S')
        Profile["Time"] = Profile["Time"] - Profile["Time"][0]
        Profile["Time"] = Profile["Time"].dt.total_seconds().div(3600).astype(float)
        Profile = Profile.loc[Profile["Time"] > -480000]
        Profile["Time"] = Profile["Time"] - Profile["Time"].nsmallest(100).iloc[-1]
        # max_limit = Profile["Time"].nlargest(1).iloc[-1]
        Profile = Profile.loc[(Profile["Time"] > 0)]
        Profile['Curr']=Profile['Curr'].apply(float)/1000
        Profile['SOC']=Profile['SOC'].apply(float)
        Profile['Vol']=Profile['Vol'].apply(float)/1000
        Profile['ocv']=Profile['ocv'].apply(float)/1000
        Profile['T_bat']=Profile['T_bat'].apply(float)/10
        Profile['T_usb']=Profile['T_usb'].apply(float)/10
        Profile['T_chg']=Profile['T_chg'].apply(float)/10
        Profile['T_lrp']=Profile['T_lrp'].apply(float)/10
        Profile['SOCraw']=Profile['SOCraw'].apply(float)/100
        Profile['cap_max']=Profile['cap_max'].apply(float)/10
        # Profile['capacity_max']=Profile['capacity_max'].apply(float)/10
        return Profile

    def set_tab_reset_button(self):
        self.tab_delete(self.set_tab)
        self.tab_no = 0
        
    def set_log_confirm_button(self):
        # battery_dump profile
        # 0:Time, 1:VOLTAGE NOW, 2:CURRENT NOW, 3:CURRENT MAX, 4:CHARGING CURRENT, 5:CAPACITY, 6:TBAT, 7:TUSB, 8:TCHG, 9:TWPC, 10:TBLK,
        # 11:TLRP, 12:TDCHG, 13:TSUB, 14:BATTERY STATUS, 15:DIRECT CHARGER STATUS, 16:CHARGING MODE, 17:HEALTH STATUS, 18:CABLE TYPE, 19:MUIC CABLE TYPE,
        # 20:THERMAL ZONE, 21:SLATE MODE, 22:STORE MODE, 23:SAFETY TIMER, 24:CURRENT EVENT, 25:MISC EVENT, 26:TX EVENT, 27:PHM, 28:SRCCAP_TRANSIT,
        # 29:SYS AVG CURRENT, 30:BD_VERSION, 31:VID, 32:PID, 33:XID, 34:VOLTAGE PACK MAIN, 35:VOLTAGE PACK SUB, 36:CURRENT NOW MAIN, 37:CURRENT NOW SUB,
        # 38:CYCLE, 39:OCV, 40:RAW SOC, 41:CAPACITY MAX, 42:WRL_MODE, 43:TX VOUT, 44:TX IOUT, 45:PING FRQ, 46:MIN OP FRQ, 47:MAX OP FRQ, 48:PHM,
        # 49:RX TYPE, 50:OTP FMWR VERSION, 51:WC IC REV
        global writer
        root = Tk()
        root.withdraw()
        self.SetlogConfirm.setDisabled(True)
        datafilepath = filedialog.askdirectory(initialdir="d://", title="Choose Test Folders")
        self.SetlogConfirm.setEnabled(True)
        # self.tab_delete(self.set_tab)
        if datafilepath:
        # 최근 사이클 산정 및 전체 사이클 적용여부 확인
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                if save_file_name:
                    writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
            fig, ax = plt.subplots(nrows=5, ncols=1, figsize=(6, 10))
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout(tab)
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, None)
            Profile = self.battery_dump_data(datafilepath)
            self.SetMaxCycle.setText(str(Profile.cycle.max()))
        #Short Profile 확인용
            graph_set_profile(Profile.Time, Profile.Vol, ax[0], 3.0, 4.8, 0.2, "Time(hr)", "Volt.(V)", "CCV", 1, 0, 0, 0)
            graph_set_profile(Profile.Time, Profile.ocv, ax[0], 3.0, 4.8, 0.2, "Time(hr)", "Volt.(V)", "OCV", 2, 0, 0, 0)
            graph_set_profile(Profile.Time, Profile.Curr, ax[1], -5, 6, 1, "Time(hr)", "Curr.", "Curr", 1, 0, 0, 0)
            graph_set_profile(Profile.Time, Profile.SOC, ax[2], 0, 120, 10, "Time(hr)", "SOC", "SOC", 1, 0, 0, 0)
            graph_set_profile(Profile.Time, Profile.SOCraw, ax[2], 0, 120, 10, "Time(hr)", "SOC", "rawSOC", 2, 0, 0, 0)
            graph_set_profile(Profile.Time, Profile.T_lrp, ax[3], 20, 50, 4, "Time(hr)", "temp.", "T_lrp", 4, 0, 0, 0)
            graph_set_profile(Profile.Time, Profile.T_usb, ax[3], 20, 50, 4, "Time(hr)", "temp.", "T_usb", 2, 0, 0, 0)
            graph_set_profile(Profile.Time, Profile.T_chg, ax[3], 20, 50, 4, "Time(hr)", "temp.", "T_chg", 3, 0, 0, 0)
            graph_set_profile(Profile.Time, Profile.T_bat, ax[3], 20, 50, 4, "Time(hr)", "Temp.(℃)", "T_bat", 1, 0, 0, 0)
            graph_set_profile(Profile.Time, Profile.cap_max, ax[4], 90, 101, 1, "Time(hr)", "Cap_max", "cap_max", 1, 0, 0, 0)
        # Short 관련
            ax[0].legend(loc="lower left")
            ax[1].legend(loc="lower left")
            ax[2].legend(loc="lower left")
            ax[3].legend(loc="lower left")
            ax[4].legend(loc="lower left")
            for i in range(4):
                # X축 레이블 제거
                ax[i].set_xlabel('')
                # X축 틱 레이블 제거
                ax[i].set_xticklabels([])
            Chgnamelist = datafilepath.split("/")
            tab_layout.addWidget(toolbar)
            tab_layout.addWidget(canvas)
            self.set_tab.addTab(tab, Chgnamelist[-1])
            self.set_tab.setCurrentWidget(tab)
            self.tab_no = self.tab_no + 1
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        if self.saveok.isChecked() and save_file_name:
            Profile.to_excel(writer)
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        plt.close()
        self.progressBar.setValue(100)

    # def SetlogConfirmbutton(self):
    #     '''
    #     Act program Set log
    #     0:[TIME] 1: IMEI 2: Binary version 3: Capacity 4: cisd_fullcaprep_max 5: batt_charging_source
    #     6: charging_type 7: voltage_now 8: voltage_avg 9: current_now 10: current_avg
    #     11: battery_temp 12: ac_temp 13: temperature 14: battery_cycle 15: battery_charger_status
    #     16: batt_slate_mode 17: fg_asoc 18: fg_cycle 19: BIG 20: Little
    #     21: G3D 22: ISP 23: curr_5 24: wc_vrect 25: wc_vout
    #     26: dchg_temp 27: dchg_temp_adc 28: direct_charging_iin 29: AP CUR_CH0 30: AP CUR_CH1
    #     31: AP CUR_CH2 32: AP CUR_CH3 33: AP CUR_CH4 34: AP CUR_CH5 35: AP CUR_CH6
    #     36: AP CUR_CH7 37: AP POW_CH0 38: AP POW_CH1 39: AP POW_CH2 40: AP POW_CH3
    #     41: AP POW_CH4 42: AP POW_CH5 43: AP POW_CH6 44: AP POW_CH7 45: cisd_data
    #     46: LRP 47: USB_TEMP
    #     '''
    #     global writer
    #     root = Tk()
    #     root.withdraw()
    #     self.SetlogConfirm.setDisabled(True)
    #     datafilepath = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
    #     self.SetlogConfirm.setEnabled(True)
    #     if datafilepath:
    #         recentcycno = int(self.recentcycleno.text())
    #         filecount = 0
    #         if self.saveok.isChecked():
    #             save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
    #             if save_file_name:
    #                 writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
    #             cycoutputdf = pd.DataFrame({'name': [''], 'cycle': [''], 'Chg_realSOC': [''], 'Dchg_realSOC': [''], 'Chg time(min)': [''], 'Dchg time(min)': ['']})
    #             chgoutputdf = pd.DataFrame()
    #             dchgoutputdf = pd.DataFrame()
    #         for filepath in datafilepath:
    #             mincapa = int(self.SetMincapacity.text())
    #             fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6), (ax7, ax8), (ax9, ax10)) \
    #                 = plt.subplots(nrows=5, ncols=2, figsize=(12, 10))
    #             chkcyc = set_log_cycle(filepath, self.realcyc.isChecked(), recentcycno, self.allcycle.isChecked(),
    #                                    self.manualcycle.isChecked(), self.manualcycleno) 
    #             filecountmax = len(datafilepath)
    #             filecount = filecount + 1
    #             # 전체 사이클과 최근 사이클 기준 설정
    #             if self.allcycle.isChecked() == True:
    #                 cyclecountmax = range(chkcyc[0], chkcyc[1] + 1)
    #             elif self.manualcycle.isChecked() == True:
    #                 manualcyclenochk = list(map(int, (self.manualcycleno.text().split())))
    #                 if len(manualcyclenochk) > 2:
    #                     manualcyclenochk = [x for x in manualcyclenochk if (x >= chkcyc[0] and x <= chkcyc[1])]
    #                     cyclecountmax = manualcyclenochk
    #                 else:
    #                     cycmin = max(chkcyc[0], manualcyclenochk[0])
    #                     cycmax = min(chkcyc[1], manualcyclenochk[1])
    #                     cyclecountmax = range(cycmin, cycmax + 1)
    #             else:
    #             # 최근 20 cycle 기준으로 설정
    #                 if (chkcyc[1] - chkcyc[0]) > recentcycno:
    #                     cyclecountmax = range(chkcyc[1] - recentcycno , chkcyc[1] + 1)
    #                 else:
    #                     cyclecountmax = range(chkcyc[0], chkcyc[1] + 1)
    #             namelist = filepath.split("/")
    #             for i in cyclecountmax:
    #                 temp = set_act_log_Profile(chkcyc[2].Profile, mincapa, i)
    #                 progressdata = ((filecount - 1) + (i - cyclecountmax[0] + 1)/len(cyclecountmax))/filecountmax * 100
    #                 self.progressBar.setValue(int(progressdata))
    #                 if hasattr(temp, "ChgProfile"):
    #                     chgrealcap = str(round(temp.ChgProfile.SOC2.max(), 2))
    #                     chgmaxtime = str(round(temp.ChgProfile.Time.max() * 60, 1))
    #                     caplegend = "{:3}".format(str(i)) + " C:" + "{:8}".format(chgrealcap)
    #                     temp.ChgProfile = temp.ChgProfile[(temp.ChgProfile["Time"] < 4)]
    #                     graph_set(temp.ChgProfile.Time, temp.ChgProfile.Vol, ax1, 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0)
    #                     graph_set(temp.ChgProfile.Time, temp.ChgProfile.Curr, ax3, 0, 2.4, 0.2, "Time(hr)", "Curr", "", 0)
    #                     graph_set(temp.ChgProfile.Time, temp.ChgProfile.Temp, ax5, 20, 50, 4, "Time(hr)", "temp.", "", 0)
    #                     graph_set(temp.ChgProfile.Time, temp.ChgProfile.SOC, ax7, 0, 120, 10, "Time(hr)", "SOC", "", 0)
    #                     graph_set(temp.ChgProfile.Time, temp.ChgProfile.SOC2, ax9, 0, 120, 10, "Time(hr)", "real SOC", "", 0)
    #                 else:
    #                     chgrealcap = " "
    #                     chgmaxtime = " "
    #                 if hasattr(temp, "DchgProfile"):
    #                     dchgrealcap = str(round(temp.DchgProfile.SOC2.max(), 2))
    #                     dchgmaxtime = str(round(temp.DchgProfile.Time.max() * 60, 1))
    #                     caplegend = caplegend + " D:" + "{:6}".format(dchgrealcap)
    #                     graph_set(temp.DchgProfile.Time, temp.DchgProfile.Vol, ax2, 3.0, 4.6, 0.2, "Time(hr)", "Voltage (V)", "", 1)
    #                     graph_set(temp.DchgProfile.Time, temp.DchgProfile.Curr, ax4, -0.6, 0.1, 0.1, "Time(hr)", "Curr", "", 1)
    #                     graph_set(temp.DchgProfile.Time, temp.DchgProfile.Temp, ax6, 20, 50, 4, "Time(hr)", "temp.", "", 1)
    #                     graph_set(temp.DchgProfile.Time, temp.DchgProfile.SOC, ax8, 0, 120, 10, "Time(hr)", "SOC", "", 1)
    #                     if self.saveok.isChecked():
    #                         graph_set(temp.DchgProfile.Time, 100 - temp.DchgProfile.SOC2, ax10, 0, 120, 10, "Time(hr)", "real SOC", i, 1)
    #                     else:
    #                         graph_set(temp.DchgProfile.Time, 100 - temp.DchgProfile.SOC2, ax10, 0, 120, 10, "Time(hr)", "real SOC", caplegend, 1)
    #                 else:
    #                     dchgrealcap = " "
    #                     dchgmaxtime = " "
    #                 if self.saveok.isChecked():
    #                     cycoutputdata = pd.DataFrame(
    #                         {'name': namelist[-1],
    #                         'cycle': [str(i)],
    #                         'Chg_realSOC': [chgrealcap],
    #                         'Dchg_realSOC': [dchgrealcap],
    #                         'Chg time(min)': [chgmaxtime],
    #                         'Dchg time(min)': [dchgmaxtime]})
    #                     cycoutputdf = cycoutputdf._append(cycoutputdata)
    #                     # 충전 Profile 추출용
    #                     if hasattr(temp, "ChgProfile"):
    #                         chgoutputdf = chgoutputdf._append(temp.ChgProfile)
    #                     # 방전 Profile 추출용
    #                     if hasattr(temp, "DchgProfile"):
    #                         dchgoutputdf = dchgoutputdf._append(temp.DchgProfile)
    #         if self.saveok.isChecked() and save_file_name:
    #             cycoutputdf.to_excel(writer, sheet_name="cycle")
    #             chgoutputdf.to_excel(writer, sheet_name="chg")
    #             dchgoutputdf.to_excel(writer, sheet_name="dchg")
    #             writer.close()
    #         self.progressBar.setValue(100)
    #         fig.legend()
    #         plt.suptitle(namelist[-1], fontsize= 15, fontweight='bold')
    #         plt.tight_layout(pad=1, w_pad=1, h_pad=1)
    #         plt.subplots_adjust(right=0.8)
    #         plt.show()
    #         output_fig(self.figsaveok, namelist[-1])

    # def SetlogcycConfirmbutton(self):
    #     '''
    #     Act program Set log
    #     0:[TIME] 1: IMEI 2: Binary version 3: Capacity 4: cisd_fullcaprep_max 5: batt_charging_source
    #     6: charging_type 7: voltage_now 8: voltage_avg 9: current_now 10: current_avg
    #     11: battery_temp 12: ac_temp 13: temperature 14: battery_cycle 15: battery_charger_status
    #     16: batt_slate_mode 17: fg_asoc 18: fg_cycle 19: BIG 20: Little
    #     21: G3D 22: ISP 23: curr_5 24: wc_vrect 25: wc_vout
    #     26: dchg_temp 27: dchg_temp_adc 28: direct_charging_iin 29: AP CUR_CH0 30: AP CUR_CH1
    #     31: AP CUR_CH2 32: AP CUR_CH3 33: AP CUR_CH4 34: AP CUR_CH5 35: AP CUR_CH6
    #     36: AP CUR_CH7 37: AP POW_CH0 38: AP POW_CH1 39: AP POW_CH2 40: AP POW_CH3
    #     41: AP POW_CH4 42: AP POW_CH5 43: AP POW_CH6 44: AP POW_CH7 45: cisd_data
    #     46: LRP 47: USB_TEMP
    #     '''
    #     global writer
    #     root = Tk()
    #     root.withdraw()
    #     setxscale = int(self.setcyclexscale.text())
    #     self.SetlogcycConfirm.setDisabled(True)
    #     datafilepath = filedialog.askdirectory(initialdir="d://", title="Choose Test files")
    #     self.SetlogcycConfirm.setEnabled(True)
    #     if datafilepath:
    #         fig, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=(4, 3))
    #         filecount = 0
    #         graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    #         if self.saveok.isChecked():
    #             save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
    #             if save_file_name:
    #                 writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
    #         rawdf = pd.DataFrame()
    #         df = pd.DataFrame()
    #         subfile = [f for f in os.listdir(datafilepath)]
    #         #폴더내의 파일 전체 취합
    #         for filename in subfile:
    #             rawdf = pd.read_csv(datafilepath + "/" + filename, on_bad_lines='skip')
    #             rawdf = rawdf.iloc[:-1]
    #             df = pd.concat([df, rawdf], axis=0, ignore_index=True)
    #             # progress bar 관련
    #             filecountmax = len(subfile)
    #             progressdata = filecount/filecountmax * 100
    #             filecount = filecount + 1
    #             self.progressBar.setValue(int(progressdata))
    #         if not df.empty:
    #             # 사이클을 위한 데이터 추출
    #             df.columns = df.columns.str.replace('[^A-Za-z0-9_]+', '', regex=True)
    #             df = df[["battery_cycle", "fg_cycle", "fg_asoc"]]
    #             # 중복 항목 제거 및 index reset
    #             df = df.drop_duplicates(subset='battery_cycle')
    #             df = df.sort_values(by="battery_cycle")
    #             df.reset_index()
    #             #그래프그리기
    #             graph_cycle(df["battery_cycle"], df["fg_asoc"], ax1, 80, 105, 5, "Cycle", "Discharge Capacity Ratio", "ASOC",
    #                         setxscale, graphcolor[0])
    #             if self.saveok.isChecked() and save_file_name:
    #                 df.to_excel(writer, sheet_name="SETcycle")
    #                 writer.close()
    #         self.progressBar.setValue(100)
    #         fig.legend()
    #         plt.tight_layout(pad=1, w_pad=1, h_pad=1)
    #         plt.show()

    def set_confirm_button(self):
        'Battery Status data log'
        '''0:Time 1:Level 2:Charging 3:Temperature(BA) 4:PlugType 5:Speed
        6:Voltage(mV) 7:Temperature(CHG) 8:Temperature(AP) 9:Temperature(Coil) 10:Ctype(Etc)-VOL
        11:Ctype(Etc)-ChargCur 12:Ctype(Etc)-Wire_Vout 13:Ctype(Etc)-Wire_Vrect 14:Temperature(CHG ADC) 15:Temperature(Coil ADC) 
        16:Temperature(BA ADC) 17:SafetyTimer 18:USB_Thermistor 19:SIOP_Level 20:Battery_Cycle
        21:Fg_Cycle 22:Charge_Time_Remaining 23:IIn 24:Temperature(DC) 25:Temperature(DC ADC) 
        26:DC Step 27:DC Status 28:Main Voltage 29:Sub Voltage 30:Main Current Now 
        31:Sub Current Now 32:Temperature(SUB Batt) 33:Temperature(SUB Batt ADC) 34:Current Avg. 35:ASOC1 
        36:Full Cap Nom 37:ASOC2 38:LRP 39:Raw SOC (%) 40:V avg (mV) 41:WC_Freq. 
        42:WC_Tx ID 43:Uno Vout 44:WC_Iin/Iout 45:Power 46:WC_Rx type 47:BSOH 48:Wireless 2.0 auth status 49:Full Voltage 50:Recharging Voltage 
        51:Full Cap Rep 52:CMD DATA 53:Temperature(AP ADC) 54:Battery Cycle Sub 55:charge status 56:Charging Cable 57:Fan Step 58:Fan Rpm
        59:Main Vchg 60:Sub Vchg 61:err_wthm
        '''
        global writer
        root = Tk()
        root.withdraw()
        self.SetConfirm.setDisabled(True)
        datafilepath = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        self.SetConfirm.setEnabled(True)
        if datafilepath:
            recentcycno = int(self.recentcycleno.text())
            filecount = 0
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                if save_file_name:
                    writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                cycoutputdf = pd.DataFrame({'name': [''], 'cycle': [''], 'Chg_realSOC': [''], 'Dchg_realSOC': [''],
                                            'Chg time(min)': [''], 'Dchg time(min)': ['']})
                chgoutputdf = pd.DataFrame()
                dchgoutputdf = pd.DataFrame()
            for filepath in datafilepath:
                mincapa = int(self.SetMincapacity.text())
                fig, ax = plt.subplots(nrows=5, ncols=2, figsize=(18, 10))
                tab = QtWidgets.QWidget()
                tab_layout = QtWidgets.QVBoxLayout(tab)
                canvas = FigureCanvas(fig)
                toolbar = NavigationToolbar(canvas, None)
                chkcyc = set_act_ect_battery_status_cycle(filepath, self.realcyc.isChecked(), recentcycno,
                                                          self.allcycle.isChecked(), self.manualcycle.isChecked(), self.manualcycleno)
                filecountmax = len(datafilepath)
                filecount = filecount + 1
                # 전체 사이클과 최근 사이클 기준 설정
                if self.allcycle.isChecked() == True:
                    cyclecountmax = range(chkcyc[0], chkcyc[1] + 1)
                elif self.manualcycle.isChecked() == True:
                    manualcyclenochk = list(map(int, (self.manualcycleno.text().split())))
                    if len(manualcyclenochk) > 2:
                        manualcyclenochk = [x for x in manualcyclenochk if (x >= chkcyc[0] and x <= chkcyc[1])]
                        cyclecountmax = manualcyclenochk
                    else:
                        cycmin = max(chkcyc[0], manualcyclenochk[0])
                        cycmax = min(chkcyc[1], manualcyclenochk[1])
                        cyclecountmax = range(cycmin, cycmax + 1)
                else:
                # 최근 20 cycle 기준으로 설정
                    if (chkcyc[1] - chkcyc[0]) > recentcycno:
                        cyclecountmax = range(chkcyc[1] - recentcycno , chkcyc[1] + 1)
                    else:
                        cyclecountmax = range(chkcyc[0], chkcyc[1] + 1)
                namelist = filepath.split("/")[-1]
                for i in cyclecountmax:
                    temp = set_battery_status_log_Profile(chkcyc[2].Profile, mincapa, i, chkcyc[2].set)
                    # progressdata = ((filecount - 1) + (i - cyclecountmax[0] + 1)/len(cyclecountmax))/filecountmax * 100
                    progressdata = progress(filecount, filecountmax, (cyclecountmax[0] - i), len(cyclecountmax), 1, 1)
                    self.progressBar.setValue(int(progressdata))
                    if hasattr(temp, "ChgProfile"):
                        chgrealcap = str(round(temp.ChgProfile.SOC2.max(), 2))
                        chgmaxtime = str(round(temp.ChgProfile.Time.max() * 60, 1))
                        caplegend = "{:3}".format(str(i)) + " C:" + "{:8}".format(chgrealcap)
                        temp.ChgProfile = temp.ChgProfile[(temp.ChgProfile["Time"] < 4)]
                        graph_set_profile(temp.ChgProfile.Time * 60, temp.ChgProfile.Vol, ax[0, 0], 3.6, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 0, 120, 10)
                        graph_set_profile(temp.ChgProfile.Time * 60, temp.ChgProfile.Curr/1000, ax[1, 0], 0, 3.2, 0.2, "Time(hr)", "Curr", "", 0, 0, 120, 10)
                        graph_set_profile(temp.ChgProfile.Time * 60, temp.ChgProfile.Temp, ax[2, 0], 20, 50, 4, "Time(hr)", "temp.", "", 0, 0, 120, 10)
                        graph_set_profile(temp.ChgProfile.Time * 60, temp.ChgProfile.SOC, ax[3, 0], 0, 120, 10, "Time(hr)", "SOC", "", 0, 0, 120, 10)
                        graph_set_profile(temp.ChgProfile.Time * 60, temp.ChgProfile.SOC2/1000, ax[4, 0], 0, 120, 10, "Time(hr)", "real SOC", "", 0, 0, 120, 10)
                    else:
                        chgrealcap = " "
                        chgmaxtime = " "
                    if hasattr(temp, "DchgProfile"):
                        dchgrealcap = str(round(temp.DchgProfile.SOC2.max(), 2))
                        dchgmaxtime = str(round(temp.DchgProfile.Time.max() * 60, 1))
                        caplegend = caplegend + " D:" + "{:6}".format(dchgrealcap)
                        graph_set_profile(temp.DchgProfile.Time, temp.DchgProfile.Vol, ax[0, 1], 3.0, 4.6, 0.2, "Time(hr)", "Voltage (V)", "", 0, 0, 11, 1)
                        graph_set_profile(temp.DchgProfile.Time, temp.DchgProfile.Curr/1000, ax[1, 1], -0.6, 0.1, 0.1, "Time(hr)", "Curr", "", 0, 0, 11, 1)
                        graph_set_profile(temp.DchgProfile.Time, temp.DchgProfile.Temp, ax[2, 1], 20, 50, 4, "Time(hr)", "temp.", "", 0, 0, 11, 1)
                        graph_set_profile(temp.DchgProfile.Time, temp.DchgProfile.SOC, ax[3, 1], 0, 120, 10, "Time(hr)", "SOC", "", 0, 0, 11, 1)
                        if self.saveok.isChecked():
                            graph_set_profile(temp.DchgProfile.Time, 100 - temp.DchgProfile.SOC2/1000, ax[4, 1], 0, 120, 10, "Time(hr)", "real SOC",
                                              i, 0, 0, 11, 1)
                        else:
                            graph_set_profile(temp.DchgProfile.Time, 100 - temp.DchgProfile.SOC2/1000, ax[4, 1], 0, 120, 10, "Time(hr)", "real SOC",
                                              caplegend, 0, 0, 11, 1)
                    else:
                        dchgrealcap = " "
                        dchgmaxtime = " "
                    if self.saveok.isChecked():
                        cycoutputdata = pd.DataFrame(
                            {'name': namelist,
                            'cycle': [str(i)],
                            'Chg_realSOC': [chgrealcap],
                            'Dchg_realSOC': [dchgrealcap],
                            'Chg time(min)': [chgmaxtime],
                            'Dchg time(min)': [dchgmaxtime]})
                        cycoutputdf = cycoutputdf._append(cycoutputdata)
                        # 충전 Profile 추출용
                        if hasattr(temp, "ChgProfile"):
                            chgoutputdf = chgoutputdf._append(temp.ChgProfile)
                        # 방전 Profile 추출용
                        if hasattr(temp, "DchgProfile"):
                            dchgoutputdf = dchgoutputdf._append(temp.DchgProfile)
                    # Chgnamelist = datafilepath.split("/")
                    for i in range(2):
                        for j in range(4):
                            # X축 레이블 제거
                            ax[j, i].set_xlabel('')
                            # X축 틱 레이블 제거
                            ax[j, i].set_xticklabels([])
                    tab_layout.addWidget(toolbar)
                    tab_layout.addWidget(canvas)
                    self.set_tab.addTab(tab, namelist)
                    self.set_tab.setCurrentWidget(tab)
                    plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                if self.saveok.isChecked() and save_file_name:
                    cycoutputdf.to_excel(writer, sheet_name="cycle")
                    chgoutputdf.to_excel(writer, sheet_name="chg")
                    dchgoutputdf.to_excel(writer, sheet_name="dchg")
                    writer.close()
                fig.legend()
                plt.subplots_adjust(right=0.8)
                # plt.suptitle(Chgnamelist[-1], fontsize= 15, fontweight='bold')
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                output_fig(self.figsaveok, namelist)
                plt.close()
            self.progressBar.setValue(100)

    def set_cycle_button(self):
        'Battery Status data log'
        '''0:Time 1:Level 2:Charging 3:Temperature(BA) 4:PlugType 5:Speed
        6:Voltage(mV) 7:Temperature(CHG) 8:Temperature(AP) 9:Temperature(Coil) 10:Ctype(Etc)-VOL
        11:Ctype(Etc)-ChargCur 12:Ctype(Etc)-Wire_Vout 13:Ctype(Etc)-Wire_Vrect 14:Temperature(CHG ADC) 15:Temperature(Coil ADC) 
        16:Temperature(BA ADC) 17:SafetyTimer 18:USB_Thermistor 19:SIOP_Level 20:Battery_Cycle
        21:Fg_Cycle 22:Charge_Time_Remaining 23:IIn 24:Temperature(DC) 25:Temperature(DC ADC) 
        26:DC Step 27:DC Status 28:Main Voltage 29:Sub Voltage 30:Main Current Now 
        31:Sub Current Now 32:Temperature(SUB Batt) 33:Temperature(SUB Batt ADC) 34:Current Avg. 35:ASOC1 
        36:Full Cap Nom 37:ASOC2 38:LRP 39:Raw SOC (%) 40:V avg (mV) 41:WC_Freq. 
        42:WC_Tx ID 43:Uno Vout 44:WC_Iin/Iout 45:Power 46:WC_Rx type 47:BSOH 48:Wireless 2.0 auth status 49:Full Voltage 50:Recharging Voltage 
        51:Full Cap Rep 52:CMD DATA 53:Temperature(AP ADC) 54:Battery Cycle Sub 55:charge status 56:Charging Cable 57:Fan Step 58:Fan Rpm
        59:Main Vchg 60:Sub Vchg 61:err_wthm
        '''
        global writer
        root = Tk()
        root.withdraw()
        setxscale = int(self.setcyclexscale.text())
        self.SetCycle.setDisabled(True)
        datafilepath = filedialog.askdirectory(initialdir="d://", title="Choose Test files")
        self.SetCycle.setEnabled(True)
        if datafilepath:
            fig, ((ax1), (ax2)) = plt.subplots(nrows=1, ncols=2, figsize=(8, 3))
            filecount = 0
            mincapa = int(self.SetMincapacity.text())
            graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                if save_file_name:
                    writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
            rawdf = pd.DataFrame()
            df = pd.DataFrame()
            subfile = [f for f in os.listdir(datafilepath)]
            #폴더내의 파일 전체 취합
            for filename in subfile:
                rawdf = pd.read_csv(datafilepath + "/" + filename, on_bad_lines='skip')
                rawdf = rawdf.iloc[:-1]
                df = pd.concat([df, rawdf], axis=0, ignore_index=True)
                # progress bar 관련
                filecountmax = len(subfile)
                progressdata = filecount/filecountmax * 100
                filecount = filecount + 1
                self.progressBar.setValue(int(progressdata))
            if not df.empty:
                # 사이클을 위한 데이터 추출
                df = df[["Battery_Cycle", "Fg_Cycle", "ASOC1", "Full Cap Nom", "ASOC2", "BSOH", "Full Cap Rep", "Battery Cycle Sub"]]
                # 중복 항목 제거 및 index reset
                df = df.drop_duplicates(subset='Battery_Cycle')
                df = df.sort_values(by="Battery_Cycle")
                df["ASOC3"] = df["Full Cap Rep"]/mincapa*100
                df.reset_index()
                #그래프그리기
                graph_cycle(df["Battery_Cycle"], df["ASOC1"], ax1, 80, 105, 5, "Cycle", "Discharge Capacity Ratio", "ASOC1",
                            setxscale, graphcolor[0])
                graph_cycle(df["Battery_Cycle"], df["BSOH"], ax1, 80, 105, 5, "Cycle", "Discharge Capacity Ratio", "BSOH",
                            setxscale, graphcolor[1])
                graph_cycle(df["Battery_Cycle"], df["ASOC3"], ax1, 80, 105, 5, "Cycle", "Discharge Capacity Ratio", "ASOC3",
                            setxscale, graphcolor[4])
                graph_cycle(df["Battery_Cycle"], df["Full Cap Nom"], ax2, 4000, 5000, 50, "Cycle", "Capacity(mAh)", "Full Cap Nom",
                            setxscale, graphcolor[2])
                graph_cycle(df["Battery_Cycle"], df["Full Cap Rep"], ax2, 4000, 5000, 50, "Cycle", "Capacity(mAh)", "Full Cap Rep",
                            setxscale, graphcolor[3])
                if self.saveok.isChecked() and save_file_name:
                    df.to_excel(writer, sheet_name="SETcycle")
                    writer.close()
            self.progressBar.setValue(100)
            fig.legend()
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            plt.show()

    def ect_data(self, datafilepath, state):
        # 260106 App log
        # 0:Time,  1:voltage_now(mV),  2:V avg (mV),  3:Ctype(Etc)-ChargCur,  4:Current Avg.,  5:comp_current_avg,  6:current offset,
        # 7:Level,  8:fg_full_voltage,  9:cc_info,  10:Charging,  11:Battery_Cycle,  12:sleepTime,  13:diffTime,  14:Temperature(BA),
        # 15:temp_ambient,  16:batt_temp,  17:batt_temp_adc,  18:batt_temp_raw,  19:batt_wpc_temp,  20:batt_wpc_temp_adc,  21:chg_temp,
        # 22:chg_temp_adc,  23:dchg_temp,  24:dchg_temp_adc,  25:usb_temp,  26:usb_temp_adc,  27:cutOff(mA),  28:Avg(mA),  29:Queue[0],
        # 30:Queue[1],  31:Queue[2],  32:Queue[3],  33:Queue[4],  34:Queue[5],  35:Queue[6],  36:Queue[7],  37:Queue[8],  38:Queue[9],
        # 39:CNT,  40:ectSOC,  41:RSOC,  42:SOC_RE,  43:SOC_EDV,  44:RSOH,  45:SOH,  46:AnodePotential,  47:SOH_dR,  48:SOH_CA,  49:SOH_X,
        # 50:SC_VALUE,  51:SC_SCORE,  52:SC_Grade,  53:SC_V_Acc,  54:SC_V_Avg,  55:avg_I_ISC,  56:avg_R_ISC,  57:avg_R_ISC_min,  58:LUT_VOLT0,
        # 59:LUT_VOLT1,  60:LUT_VOLT2,  61:LUT_VOLT3,  62:T_move,  63:OCV, 
        Profile = pd.read_csv(datafilepath, sep=",", on_bad_lines='skip', skiprows = 1,  encoding="UTF-8")
        if Profile.iloc[0,0] == "Time":
            Profile = pd.read_csv(datafilepath, sep=",", skiprows = 1, on_bad_lines='skip')
        Profile.columns = Profile.columns.str.replace('[^A-Za-z0-9_]+', '', regex=True)
        Profile = Profile[['Time', 'voltage_nowmV', 'CtypeEtcChargCur', 'CurrentAvg', 'TemperatureBA', 'Level', 'ectSOC',
                           'RSOC', 'SOC_RE', 'Charging', 'Battery_Cycle', 'AnodePotential', 'SC_SCORE', 'VavgmV', 'LUT_VOLT0',
                           'LUT_VOLT1', 'LUT_VOLT2', 'LUT_VOLT3']]
        Profile.columns = ['Time', 'Vol', 'Curr', 'CurrAvg', 'Temp', 'SOC', 'SOCectraw',
                        'RSOCect', 'SOCect', 'Type', 'Cyc', 'anodeE', 'short', 'Vavg', '1stepV', '2stepV',
                        '3stepV', '4stepV']
        Profile.Time = '20'+ Profile['Time'].astype(str)
        Profile = Profile[:-1]
        cycmin = int(Profile.Cyc.min())
        cycmax = int(Profile.Cyc.max())
        if self.realcyc.isChecked() == 0 and state == "profile":
            if cycmin != cycmax:
                # 'Unplugged' 또는 ' NONE'에서 'AC' 또는 ' PDIC_APDO'로 전환되는 지점을 찾습니다.
                plug_change = (
                    (Profile['Type'].shift(1).isin([" Discharging"])) &
                    (Profile['Type'].isin([" Charging", " Full"]))
                )
                # 'Battery_Cycle'의 초기값을 설정합니다.
                Profile['Cyc'] = cycmin
                # 전환 지점에서 1씩 증가하는 값을 누적합으로 계산하여 적용합니다.
                # cumsum() 함수는 True(1)인 값의 누적합을 효율적으로 계산합니다.
                Profile['Cyc'] += plug_change.cumsum()
        cycmax = int(Profile.Cyc.max())
        if not Profile.empty:
            # 시간 확인
            Profile["Time"] = pd.to_datetime(Profile["Time"], format="%Y%m%d %H:%M:%S.%f")
            Profile["Time"] = Profile["Time"] - Profile["Time"].loc[0]
            Profile["Time"] = Profile["Time"].dt.total_seconds().div(3600).astype(float)
            Profile['Curr']=Profile['Curr'].apply(float)/1000
            Profile['CurrAvg']=Profile['CurrAvg'].apply(float)/1000
            Profile['SOC']=Profile['SOC'].apply(float)
            Profile['Vol']=Profile['Vol'].apply(float)/1000
            Profile['Temp']=Profile['Temp'].apply(float)
            Profile['Cyc']=Profile['Cyc'].apply(int)
            Profile['anodeE']=Profile['anodeE'].apply(float)/1000
            Profile['SOCectraw']=Profile['SOCectraw'].apply(float)/10
            Profile['RSOCect']=Profile['RSOCect'].apply(float)/10
            Profile['SOCect']=Profile['SOCect'].apply(float)/10
            Profile["delTime"] = 0
            Profile["delCap"] = 0
            Profile["SOCref"] = 0
            Profile["delCapAvg"] = 0
            Profile["SOCrefAvg"] = 0
        return Profile
    
    def ect_short_button(self):
        global writer
        root = Tk()
        root.withdraw()
        self.ECTShort.setDisabled(True)
        datafilepaths = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        self.ECTShort.setEnabled(True)
        if datafilepaths:
            for datafilepath in datafilepaths:
            # 최근 사이클 산정 및 전체 사이클 적용여부 확인
                mincapa = int(self.SetMincapacity.text())
                if self.saveok.isChecked():
                    save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                    if save_file_name:
                        writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                fig, ax = plt.subplots(nrows=5, ncols=1, figsize=(6, 10))
                tab = QtWidgets.QWidget()
                tab_layout = QtWidgets.QVBoxLayout(tab)
                canvas = FigureCanvas(fig)
                toolbar = NavigationToolbar(canvas, None)
                Profile = self.ect_data(datafilepath, "short")
            #Short Profile 확인용
                graph_set_profile(Profile.Time, Profile.Vol, ax[0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 0, 0, 0)
                # graph_set(Profile.Time, Profile.anodeE, ax2, -0.1, 0.8, 0.1, "Time(hr)", "anodeE", "", 99)
                graph_set_profile(Profile.Time, Profile.CurrAvg, ax[1], -10, 11, 2, "Time(hr)", "Curr(A)", "", 0, 0, 0, 0)
                graph_set_profile(Profile.Time, Profile.Temp, ax[2], 20, 50, 4, "Time(hr)", "temp.(℃)", "", 0, 0, 0, 0)
                graph_set_profile(Profile.Time, Profile.SOC, ax[3], 0, 120, 10, "Time(hr)", "SOC/SOCect", "", 0, 0, 0, 0)
                graph_set_profile(Profile.Time, Profile.SOCect, ax[3], 0, 120, 10, "Time(hr)", "SOC/SOCect", "", 1, 0, 0, 0)
                # graph_set_profile(Profile.Time, Profile.SOCectraw, ax[3], 0, 120, 10, "Time(hr)", "SOC/SOCect/SOCectraw", "", 2, 0, 0, 0)
            # Short 관련
                graph_set_profile(Profile.Time, Profile.short, ax[4], 0, 6, 1, "Time(hr)", "Short Score", "", 0, 0, 0, 0)
                # 마지막 행을 제외한 각 서브플롯 설정
                for i in range(4):
                    # X축 레이블 제거
                    ax[i].set_xlabel('')
                    # X축 틱 레이블 제거
                    ax[i].set_xticklabels([])
                Chgnamelist = datafilepath.split("/")
                tab_layout.addWidget(toolbar)
                tab_layout.addWidget(canvas)
                self.set_tab.addTab(tab, Chgnamelist[-1])
                self.set_tab.setCurrentWidget(tab)
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            if self.saveok.isChecked() and save_file_name:
                Profile.to_excel(writer)
                writer.close()
            fig.legend()
            plt.subplots_adjust(right=0.8)
            # plt.suptitle(Chgnamelist[-1], fontsize= 15, fontweight='bold')
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            output_fig(self.figsaveok,Chgnamelist)
            plt.close()
        self.progressBar.setValue(100)

    def ect_soc_button(self):
        global writer
        root = Tk()
        root.withdraw()
        self.ECTSOC.setDisabled(True)
        datafilepaths = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        self.ECTSOC.setEnabled(True)
        filecount = 0
        filecountmax = len(datafilepaths)
        if datafilepaths:
            for datafilepath in datafilepaths:
            # 최근 사이클 산정 및 전체 사이클 적용여부 확인
                recentcycno = int(self.recentcycleno.text())
                # mincapa = int(self.SetMincapacity.text())
                setoffvol = self.setoffvoltage.text()
                if self.saveok.isChecked():
                    save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                    if save_file_name:
                        writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                    dfdchg = pd.DataFrame()
                fig, ax = plt.subplots(nrows=4, ncols=2, figsize=(18, 10))
                tab = QtWidgets.QWidget()
                tab_layout = QtWidgets.QVBoxLayout(tab)
                canvas = FigureCanvas(fig)
                toolbar = NavigationToolbar(canvas, None)
                Profile = self.ect_data(datafilepath, "profile")
                Profile["Vavg_est"] = Profile["Vol"].rolling(window=45, min_periods=1).mean()
            # 전체 사이클과 최근 사이클 기준 설정
                if not Profile.empty:
                    # 시간 확인
                    if setoffvol != "" and (Profile["Vavg_est"].min() < float(setoffvol)) :
                        cutoff_index = Profile.index[Profile["Vavg_est"] <= float(setoffvol)].tolist()
                        Profile = Profile.loc[:cutoff_index[0]]
                    tempDchgProfile = Profile[Profile.Type == " Discharging"]
            # 전체 사이클과 최근 사이클 기준 설정
                if self.allcycle.isChecked() == True:
                    cyclecountmax = range(Profile.Cyc.min(), Profile.Cyc.max()+1)
                elif self.manualcycle.isChecked() == True:
                    manualcyclenochk = list(map(int, (self.manualcycleno.text().split())))
                    if len(manualcyclenochk) > 2:
                        manualcyclenochk = [x for x in manualcyclenochk if (x >= Profile.Cyc.min() and x <= Profile.Cyc.max())]
                        cyclecountmax = manualcyclenochk
                    else:
                        cycmin = max(Profile.Cyc.min(), manualcyclenochk[0])
                        cycmax = min(Profile.Cyc.max(), manualcyclenochk[1])
                        cyclecountmax = range(cycmin, cycmax + 1)
                else: # 최근 20 cycle 기준으로 설정
                    if (Profile.Cyc.max() - Profile.Cyc.min()) > recentcycno:
                        cyclecountmax = range(Profile.Cyc.max() - recentcycno , Profile.Cyc.max() + 1)
                    elif Profile.Cyc.max() == Profile.Cyc.min():
                        cyclecountmax = [Profile.Cyc.min()]
                    else:
                        cyclecountmax = range(Profile.Cyc.min(), Profile.Cyc.max() + 1)
                for i in cyclecountmax:
                    DchgProfile = tempDchgProfile[(tempDchgProfile.Cyc == i)]
                    DchgProfile = DchgProfile.reset_index()
                    DchgProfile.delTime = DchgProfile.Time.diff()
                    DchgProfile.delCap = DchgProfile.delTime * DchgProfile.Curr
                    DchgProfile.delCapAvg = DchgProfile.delTime * DchgProfile.CurrAvg
                    DchgRealCap = abs(DchgProfile.delCap.cumsum())
                    DchgRealAvgCap = abs(DchgProfile.delCapAvg.cumsum())
                    DchgSOCrefmax = DchgRealCap / DchgRealCap.max()
                    DchgSOCrefAvgmax = DchgRealAvgCap / DchgRealAvgCap.max()
                    DchgProfile.SOCref = 100 - DchgSOCrefmax * 100
                    DchgProfile.SOCrefAvg = 100 - DchgSOCrefAvgmax * 100
                    if DchgRealAvgCap.max() > 1:
                        self.socmaxcapacity.setText(str(int(DchgRealAvgCap.max() * 1000)))
                    if not DchgProfile.empty:
                        DchgProfile.Time = DchgProfile.Time - DchgProfile.Time.loc[0]
                    DchgProfile.SOCError = DchgProfile.SOCrefAvg - DchgProfile.SOC
                    DchgProfile.SOCectError = DchgProfile.SOCrefAvg - DchgProfile.SOCect
                    progressdata = progress(filecount, filecountmax, (cyclecountmax[0] - i), len(cyclecountmax), 1, 1)
                    self.progressBar.setValue(int(progressdata))
                    self.socerrormax.setText(str(round(DchgProfile.SOCError.abs().max(),3)))
                    self.socerroravg.setText(str(round(DchgProfile.SOCError.abs().mean(),3)))
                    self.ectsocerrormax.setText(str(round(DchgProfile.SOCectError.abs().max(),3)))
                    self.ectsocerroravg.setText(str(round(DchgProfile.SOCectError.abs().mean(),3)))
                # 방전 관련
                    graph_soc_set(DchgProfile.Time, DchgProfile.Vol, ax[0, 0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 1)
                    graph_soc_set(DchgProfile.Time, DchgProfile.Vavg_est, ax[0, 0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 3)
                    graph_soc_set(DchgProfile.Time, DchgProfile.anodeE, ax[1, 0], 0, 0.8, 0.1, "Time(hr)", "Anode Voltage (V)", "", 1)
                    graph_soc_set(DchgProfile.Time, DchgProfile.CurrAvg, ax[2, 0], 0, 0, 0, "Time(hr)", "Current(A)", "", 1)
                    graph_soc_set(DchgProfile.Time, DchgProfile.Temp, ax[3, 0], -20, 60, 10, "Time(hr)", "Temperature (℃)", "", 1)
                # SOC 비교
                    graph_soc_set(DchgProfile.Time, DchgProfile.SOCectraw, ax[0, 1], 0, 110, 10, "Time(hr)", "ASOC_ect", "ASOC_ect", 6)
                    graph_soc_set(DchgProfile.Time, DchgProfile.RSOCect, ax[0, 1], 0, 110, 10, "Time(hr)", "SOCraw_ect", "SOCraw_ect", 7)
                    graph_soc_set(DchgProfile.Time, DchgProfile.SOCect, ax[0, 1], 0, 110, 10, "Time(hr)", "SOC_ect", "SOC_ect", 4)
                    graph_soc_set(DchgProfile.Time, DchgProfile.SOC, ax[1, 1], 0, 110, 10, "Time(hr)", "SOC/ SOC_ect/ SOC_ref", "SOC", 3)
                    graph_soc_set(DchgProfile.Time, DchgProfile.SOCect, ax[1, 1], 0, 110, 10, "Time(hr)", "SOC/ SOC_ect/ SOC_ref", "SOC_ect", 4)
                    graph_soc_set(DchgProfile.Time, DchgProfile.SOCrefAvg, ax[1, 1], 0, 110, 10, "Time(hr)", "SOC/SOCect/SOCref", "SOC_ref", 5)
                    graph_soc_set(DchgProfile.Time, DchgProfile.SOCError, ax[2, 1], -10, 11, 2, "Time(hr)", "Error(%)", "SOC", 3)
                    graph_soc_set(DchgProfile.Time, DchgProfile.SOCectError, ax[2, 1], -10, 11, 2, "Time(hr)", "Error(%)", "SOC_ect", 4)
                    graph_soc_err(DchgProfile.SOCrefAvg, DchgProfile.SOCError, ax[3, 1], -10, 11, 2, "SOCref", "Error(%)", "SOC", 3)
                    graph_soc_err(DchgProfile.SOCrefAvg, DchgProfile.SOCectError, ax[3, 1], -10, 11, 2, "SOCref", "Error(%)", "SOC_ect", 4)
                if self.saveok.isChecked() and save_file_name:
                    dfdchg = dfdchg._append(DchgProfile)
                if self.saveok.isChecked() and save_file_name:
                    dfdchg.to_excel(writer, sheet_name="dchg")
                    writer.close()
                tab_name_list = datafilepath.split("/")[-1].split(".")[-2]
                ax[0, 0].legend(loc="lower left")
                ax[1, 0].legend(loc="upper left")
                ax[2, 0].legend(loc="lower right")
                ax[3, 0].legend(loc="upper right")
                ax[0, 1].legend(loc="upper right")
                ax[1, 1].legend(loc="upper right")
                ax[2, 1].legend(loc="upper left")
                ax[3, 1].legend(loc="upper left")
                tab_layout.addWidget(toolbar)
                tab_layout.addWidget(canvas)
                self.set_tab.addTab(tab, tab_name_list) 
                self.set_tab.setCurrentWidget(tab)
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                output_fig(self.figsaveok, tab_name_list)
                plt.close()
                filecount = filecount + 1
            self.progressBar.setValue(100)

    def ect_set_profile_button(self):
        global writer
        root = Tk()
        root.withdraw()
        self.ECTSetProfile.setDisabled(True)
        datafilepaths = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        self.ECTSetProfile.setEnabled(True)
        if datafilepaths:
            for datafilepath in datafilepaths:
            # 최근 사이클 산정 및 전체 사이클 적용여부 확인
                recentcycno = int(self.recentcycleno.text())
                if self.saveok.isChecked():
                    save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                    if save_file_name:
                        writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                    dfchg = pd.DataFrame()
                    dfdchg = pd.DataFrame()
                fig, ax = plt.subplots(nrows=5, ncols=2, figsize=(18, 10))
                # fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6), (ax7, ax8), (ax9, ax10)) = plt.subplots(nrows=5, ncols=2, figsize=(18, 10))
                tab = QtWidgets.QWidget()
                tab_layout = QtWidgets.QVBoxLayout(tab)
                canvas = FigureCanvas(fig)
                toolbar = NavigationToolbar(canvas, None)
                Profile = self.ect_data(datafilepath, "profile")
            # 전체 사이클과 최근 사이클 기준 설정
                if not Profile.empty:
                    tempDchgProfile = Profile[Profile.Type == " Discharging"]
                    tempChgProfile = Profile[Profile.Type != " Discharging"]
            # 전체 사이클과 최근 사이클 기준 설정
                if self.allcycle.isChecked() == True:
                    cyclecountmax = range(Profile.Cyc.min(), Profile.Cyc.max()+1)
                elif self.manualcycle.isChecked() == True:
                    manualcyclenochk = list(map(int, (self.manualcycleno.text().split())))
                    if len(manualcyclenochk) > 2:
                        manualcyclenochk = [x for x in manualcyclenochk if (x >= Profile.Cyc.min() and x <= Profile.Cyc.max())]
                        cyclecountmax = manualcyclenochk
                    else:
                        cycmin = max(Profile.Cyc.min(), manualcyclenochk[0])
                        cycmax = min(Profile.Cyc.max(), manualcyclenochk[1])
                        cyclecountmax = range(cycmin, cycmax + 1)
                else:
            # 최근 20 cycle 기준으로 설정
                    if (Profile.Cyc.max() - Profile.Cyc.min()) > recentcycno:
                        cyclecountmax = range(Profile.Cyc.max() - recentcycno , Profile.Cyc.max() + 1)
                    elif Profile.Cyc.max() == Profile.Cyc.min():
                        cyclecountmax = [Profile.Cyc.min()]
                    else:
                        cyclecountmax = range(Profile.Cyc.min(), Profile.Cyc.max() + 1)
                for cycno in cyclecountmax:
                    DchgProfile = tempDchgProfile[(tempDchgProfile.Cyc == cycno)]
                    ChgProfile = tempChgProfile[(tempChgProfile.Cyc == cycno)]
                    DchgProfile = DchgProfile.reset_index()
                    ChgProfile = ChgProfile.reset_index()
                    DchgProfile.delTime = DchgProfile.Time.diff()
                    DchgProfile.delCap = DchgProfile.delTime * DchgProfile.Curr
                    SOCrefmax = abs(DchgProfile.delCap.cumsum() * 100)
                    DchgProfile.SOCref = 100 - SOCrefmax
                    DchgProfile.delCapAvg = DchgProfile.delTime * DchgProfile.CurrAvg
                    SOCrefAvgmax = abs(DchgProfile.delCapAvg.cumsum() * 100)
                    DchgProfile.SOCrefAvg = 100 - SOCrefAvgmax
                    ChgProfile.delTime = ChgProfile.Time.diff()
                    ChgProfile.delCap = ChgProfile.delTime * ChgProfile.Curr
                    ChgProfile.SOCref = 100-abs(ChgProfile.delCap.cumsum() * 100)
                    ChgProfile.delCapAvg = ChgProfile.delTime * ChgProfile.CurrAvg
                    ChgProfile.SOCrefAvg = 100-abs(ChgProfile.delCapAvg.cumsum() * 100)
                    if not DchgProfile.empty:
                        DchgProfile.Time = DchgProfile.Time - DchgProfile.Time.loc[0]
                    if not ChgProfile.empty:
                        ChgProfile.Time = ChgProfile.Time - ChgProfile.Time.loc[0]
                    progressdata = (cycno - cyclecountmax[0] + 1)/len(cyclecountmax) * 100
                    self.progressBar.setValue(int(progressdata))
                    ChgProfile = ChgProfile[(ChgProfile["Time"] < 4)]
                    DchgProfile.SOCError = DchgProfile.SOCrefAvg - DchgProfile.SOC
                    DchgProfile.SOCectError = DchgProfile.SOCrefAvg - DchgProfile.SOCect
                # 충전 관련
                    graph_set_profile(ChgProfile.Time, ChgProfile.Vol, ax[0, 0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 0, 4, 1)
                    graph_set_profile(ChgProfile.Time, ChgProfile.anodeE, ax[1, 0], -0.1, 0.3, 0.05, "Time(hr)", "anodeE (V)", "", 0, 0, 4, 1)
                    graph_set_profile(ChgProfile.Time, ChgProfile.CurrAvg/1000, ax[2, 0], 0, 0, 0, "Time(hr)", "CurrAvg (A)", "", 0, 0, 4, 1)
                    graph_set_profile(ChgProfile.Time, ChgProfile.Temp, ax[3, 0], 20, 50, 4, "Time(hr)", "temp.(℃ )", "", 0, 0, 4, 1)
                    graph_set_profile(ChgProfile.Time, ChgProfile.SOC, ax[4, 0], 0, 120, 10, "Time(hr)", "SOC", "", 1, 0, 4, 1)
                    graph_set_profile(ChgProfile.Time, ChgProfile.SOCect, ax[4, 0], 0, 120, 10, "Time(hr)", "SOC", "", 2, 0, 4, 1)
                # 방전 관련
                    graph_set_profile(DchgProfile.Time, DchgProfile.Vol, ax[0, 1], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 0, 11, 1)
                    graph_set_profile(DchgProfile.Time, DchgProfile.anodeE, ax[1, 1], 0, 0.8, 0.1, "Time(hr)", "anodeE (V)", "", 0, 0, 11, 1)
                    graph_set_profile(DchgProfile.Time, DchgProfile.CurrAvg/1000, ax[2, 1], 0, 0, 0, "Time(hr)", "CurrAvg (A)", "", 0, 0, 11, 1)
                    graph_set_profile(DchgProfile.Time, DchgProfile.Temp, ax[3, 1], 20, 50, 4, "Time(hr)", "temp.(℃)", "", 0, 0, 11, 1)
                    graph_set_profile(DchgProfile.Time, DchgProfile.SOC, ax[4, 1], 0, 120, 10, "Time(hr)", "SOC", "", 1, 0, 11, 1)
                    graph_set_profile(DchgProfile.Time, DchgProfile.SOCect, ax[4, 1], 0, 120, 10, "Time(hr)", "SOC", "", 2, 0, 11, 1)
                # SOC 비교
                    if "1stepV" in ChgProfile.columns:
                        graph_set_guide(ChgProfile.Time, ChgProfile["1stepV"], ax[0 ,0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 4, 1)
                        graph_set_guide(ChgProfile.Time, ChgProfile["2stepV"], ax[0, 0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 4, 1)
                        graph_set_guide(ChgProfile.Time, ChgProfile["3stepV"], ax[0, 0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 4, 1)
                        graph_set_guide(ChgProfile.Time, ChgProfile["4stepV"], ax[0, 0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 0, 4, 1)
                    plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                for i in range(4):
                    for j in range(2):
                        # X축 레이블 제거
                        ax[i, j].set_xlabel('')
                        # X축 틱 레이블 제거
                        ax[i, j].set_xticklabels([])
                if self.saveok.isChecked() and save_file_name:
                    dfdchg = dfdchg._append(DchgProfile)
                    dfchg = dfchg._append(ChgProfile)
                if self.saveok.isChecked() and save_file_name:
                    if not self.chk_setcyc_sep.isChecked():
                        dfdchg.to_excel(writer, sheet_name="dchg")
                        dfchg.to_excel(writer, sheet_name="chg")
                    else:
                        Profile.to_excel(writer)
                    writer.close()
                fig.legend()
                plt.subplots_adjust(right=0.8)
                tab_name_list = datafilepath.split("/")[-1].split(".")[-2]
                # plt.suptitle(Chgnamelist[-1], fontsize=15)
                tab_layout.addWidget(toolbar)
                tab_layout.addWidget(canvas)
                self.set_tab.addTab(tab, tab_name_list) 
                self.set_tab.setCurrentWidget(tab)
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                output_fig(self.figsaveok, tab_name_list)
                plt.close()
            self.progressBar.setValue(100)

    def ect_set_cycle_button(self):
        self.ECTSetCycle.setDisabled(True)
        global writer
        setxscale = int(self.setcyclexscale.text())
        subfile = []
        root = Tk()
        root.withdraw()
        datafilepath = filedialog.askdirectory(initialdir="d://", title="Choose Test files")
        self.ECTSetCycle.setEnabled(True)
        if datafilepath:
            fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3, figsize=(12, 6))
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout(tab)
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, None)
            filecount = 0
            graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                if save_file_name:
                    writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
            df = pd.DataFrame()
            predf = pd.DataFrame()
            # 하위 폴더 내의 파일까지 검색
            for (root, directories, files) in os.walk(datafilepath):
                for file in files:
                    if '.txt' in file:
                        file_path = os.path.join(root,file)
                        file_path = file_path.replace('\\','/')
                        subfile.append(file_path)
            # 폴더내의 파일 전체 취합
            for filename in subfile:
                predf = pd.read_csv(filename, on_bad_lines='skip', skiprows = 1)
                if predf.iloc[0,0] == "Time":
                    predf = pd.read_csv(filename, skiprows = 1, on_bad_lines='skip')
                predf = predf.iloc[:-1]
                df = pd.concat([df, predf], axis=0, ignore_index=True)
                filecountmax = len(subfile)
                progressdata = filecount/filecountmax * 100
                filecount = filecount + 1
                self.progressBar.setValue(int(progressdata))
            # 사이클을 위한 데이터 추출
            if not df.empty:
                df.columns = df.columns.str.replace('[^A-Za-z0-9_]+', '', regex=True)
                if "SC_VALUE" in df.columns:
                    if "LUT_VOLT0" in df.columns:
                        df = df[["Battery_Cycle", "SOH", "SOH_dR", "SOH_CA", "SOH_X", "LUT_VOLT0", "LUT_VOLT1", "LUT_VOLT2", "LUT_VOLT3",
                                 "SC_VALUE", "SC_SCORE", "SC_V_Acc", "SC_V_Avg"]]
                    else:
                        df = df[["Battery_Cycle", "SOH", "SOH_dR", "SOH_CA", "SOH_X", "SC_VALUE", "SC_SCORE", "SC_V_Acc", "SC_V_Avg"]]
                else:
                    df = df[["Battery_Cycle", "SOH", "SOH_dR", "SOH_CA", "SOH_X"]]
                # 중복 항목 제거 및 index reset
                df = df.drop_duplicates(subset="Battery_Cycle", keep='first', inplace=False, ignore_index=False)
                df = df.sort_values(by="Battery_Cycle")
                df.reset_index()
                # SOH 관련 단위 변경
                df["SOH"] = df["SOH"] / 10
                df["SOH_CA"] = df["SOH_CA"] / 10
                df["SOH_X"] = df["SOH_X"] / (-10)
                #그래프그리기
                graph_cycle(df["Battery_Cycle"], df["SOH"], ax1, 80, 105, 5, "Cycle", "Capacity ratio", "SOH", setxscale, graphcolor[0])
                graph_cycle(df["Battery_Cycle"], df["SOH_CA"], ax1, 80, 105, 5, "Cycle", "Capacity ratio", "SOH_CA", setxscale, graphcolor[1])
                graph_cycle(df["Battery_Cycle"], df["SOH_X"], ax4, -5, 15, 5, "Cycle", "Mass balance", "SOH_X", setxscale, graphcolor[3])
                graph_cycle(df["Battery_Cycle"], df["SOH_dR"], ax2, 0, 0, 0, "Cycle", "Anode Resistance", "SOH_dR", setxscale, graphcolor[2])
                if "SC_VALUE" in df.columns:
                    graph_cycle(df["Battery_Cycle"], df["SC_VALUE"], ax6, 0, 14, 2, "Cycle", "SC_VALUE", "SC_VALUE", setxscale, graphcolor[4])
                    graph_cycle(df["Battery_Cycle"], df["SC_SCORE"], ax3, 0, 6, 1, "Cycle", "SC_SCORE", "SC_SCORE", setxscale, graphcolor[5])
                    if "LUT_VOLT0" in df.columns:
                        graph_cycle(df["Battery_Cycle"], df["LUT_VOLT0"], ax5, 4, 4.6, 0.1, "Cycle", "Chg-Cut off", "1step limit",
                                    setxscale, graphcolor[0])
                        graph_cycle(df["Battery_Cycle"], df["LUT_VOLT1"], ax5, 4, 4.6, 0.1, "Cycle", "Chg-Cut off", "2step limit",
                                    setxscale, graphcolor[1])
                        graph_cycle(df["Battery_Cycle"], df["LUT_VOLT2"], ax5, 4, 4.6, 0.1, "Cycle", "Chg-Cut off", "3step limit",
                                    setxscale, graphcolor[2])
                        graph_cycle(df["Battery_Cycle"], df["LUT_VOLT3"], ax5, 4, 4.6, 0.1, "Cycle", "Chg-Cut off", "4step limit",
                                    setxscale, graphcolor[3])
                if self.saveok.isChecked() and save_file_name:
                    df.to_excel(writer, sheet_name="SETcycle")
                    writer.close()
            self.progressBar.setValue(100)
            tab_name_list = datafilepath.split("/")[-1].split(".")[-2]
            ax1.legend(loc="lower left")
            ax2.legend(loc="upper left")
            ax3.legend(loc="upper left")
            ax4.legend(loc="upper left")
            ax5.legend(loc="upper right")
            ax6.legend(loc="upper left")
            # fig.legend()
            tab_layout.addWidget(toolbar)
            tab_layout.addWidget(canvas)
            self.set_tab.addTab(tab, tab_name_list) 
            self.set_tab.setCurrentWidget(tab)
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            output_fig(self.figsaveok, tab_name_list)
            plt.close()

    def ect_set_log_button(self):
        '''
        ECT result
        0 Time 1 voltage_now(mV) 2 Vavg(mV) 3 Ctype(Etc)-ChargCur 4 CurrentAvg. 5 Level
        6 Charging 7 Battery_Cycle 8 diffTime 9 Temperature(BA) 10 temp_ambient
        11 batt_temp 12 batt_temp_adc 13 batt_temp_raw 14 batt_wpc_temp 15 batt_wpc_temp_adc
        16 chg_temp 17 chg_temp_adc 18 dchg_temp 19 dchg_temp_adc 20 usb_temp 
        21 usb_temp_adc 22 compVoltage 23 ectSOC 24 RSOC 25 SOC_RE 
        26 SOC_EDV 27 SOH 28 AnodePotential 29 SOH_dR 30 SOH_CA 
        31 SOH_X 32 SC_VALUE 33 SC_SCORE 34 SC_V_Acc 35 SC_V_Avg 
        36 LUT_VOLT0 37 LUT_VOLT1 38 LUT_VOLT2 39 LUT_VOLT3 40 T_move
        '''
        global writer
        root = Tk()
        root.withdraw()
        self.ECTSetlog.setDisabled(True)
        datafilepaths = multi_askopendirnames()
        self.ECTSetlog.setEnabled(True)
        set_count = 1
        if datafilepaths:
            for set in datafilepaths:
                progressdata = progress(1, 1, 1, 1, set_count, len(datafilepaths))
                set_count = set_count + 1
                if self.saveok.isChecked():
                    save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                    if save_file_name:
                        writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                    df = pd.DataFrame()
                fig, ax = plt.subplots(nrows=5, ncols=2, figsize=(18, 10))
                tab = QtWidgets.QWidget()
                tab_layout = QtWidgets.QVBoxLayout(tab)
                canvas = FigureCanvas(fig)
                toolbar = NavigationToolbar(canvas, None)
                appheader = ['Time', 'Vol', 'V avg (mV)', 'Ctype(Etc)-ChargCur', 'CurrAvg',
                            'SOC', 'fg_full_voltage', 'Charging', 'Battery_Cycle', 'sleepTime', 'diffTime',
                            'Temp', 'temp_ambient', 'batt_temp', 'batt_temp_adc', 'batt_temp_raw',
                            'batt_wpc_temp', 'batt_wpc_temp_adc', 'chg_temp', 'chg_temp_adc', 'dchg_temp',
                            'dchg_temp_adc', 'usb_temp', 'usb_temp_adc', 'SOCect', 'RSOC', 'SOC_RE', 'SOC_EDV',
                            'SOH', 'anodeE', 'SOH_dR', 'SOH_CA', 'SOH_X', 'SC_VALUE', 'SC_SCORE', 'SC_V_Acc',
                            'SC_V_Avg', 'LUT_VOLT0', 'LUT_VOLT1', 'LUT_VOLT2', 'LUT_VOLT3', 'T_move', 'OCV']
                inputheader = ['Time', 'log_SOC', 'log_Temp', 'log_Vol', 'log_CurrAvg', 'log_sleeptime', 'log_ect_full_voltage']
                outputheader = ['Time', 'log_ECT_CNT', 'log_SOCect', 'log_ECT_RSOC', 'log_ECT_SOC_RE', 'log_ECT_SOC_EDV', 'log_ECT_SOH', 'log_anodeE',
                                'log_ECT_SOH_dR', 'log_ECT_SOH_CA', 'log_ECT_SOH_X', 'log_ECT_ISD_Value', 'log_ECT_ISD_Score', 'log_ECT_ISD_Vacc',
                                'log_ECT_LDP_Step0', 'log_ECT_LDP_Step1', 'log_ECT_LDP_Step2', 'log_ECT_LDP_Step3', 'log_ECT_T_MOVE', 'log_ECT_OCV']
                # 파일 경로 패턴
                app_pattern = str(set) + '\\*ChemBatt_LOG*.txt'
                input_pattern = str(set) + '\\ect_inputlog.txt.*'
                output_pattern = str(set) + '\\ect_outputlog.txt.*'
                app_files = sorted(glob.glob(app_pattern))
                input_files = sorted(glob.glob(input_pattern))
                output_files = sorted(glob.glob(output_pattern))
                # 데이터프레임 로드 및 병합
                appdata = pd.concat(
                    (pd.read_csv(file, header=None, skiprows = 2, names=appheader) for file in app_files),
                    axis=0
                )
                inputlog = pd.concat(
                    (pd.read_csv(file, header=None, names=inputheader) for file in input_files),
                    axis=0
                )
                outputlog = pd.concat(
                    (pd.read_csv(file, header=None, names=outputheader) for file in output_files),
                    axis=0
                )
                # app결과의 시간을 timestamp로 수정
                appdata['Time'] = appdata['Time'].apply(to_timestamp)
                appdata['Time'] = appdata['Time'] + 10
                xlim = [inputlog["Time"].min() // 10000 * 10000, inputlog["Time"].max() // 10000 * 10000, 10000]
                inputlog.set_index('Time', inplace=True)
                outputlog.set_index('Time', inplace=True)
                appdata.set_index('Time', inplace=True)
                inputlog = inputlog[~inputlog.index.duplicated()]
                outputlog = outputlog[~outputlog.index.duplicated()]
                overall = pd.concat([inputlog, outputlog], axis=1, join='outer')
                # overall = overall[~overall.index.duplicated()]
                appdata = appdata[~appdata.index.duplicated()]
                overall = pd.concat([overall, appdata], axis=1, join='outer')
                overall['log_SOC'] = np.where(overall['log_SOC'] >= 10000, np.nan, overall['log_SOC'])
                # 충전 관련
                graph_set_profile(overall.index, overall.Vol/1000, ax[0, 0], 3.0, 4.8, 0.2, "Time(sec)", "Voltage (V)", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.CurrAvg/1000, ax[1 ,0], 0, 0, 0, "Time(sec)", "CurrAvg (A)", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.Temp, ax[2, 0], 20, 50, 4, "Time(sec)", "temp.(℃ )", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.SOC, ax[3, 0], 0, 120, 10, "Time(sec)", "SOC", "", 1, xlim[0], xlim[1], xlim[2])
                # graph_set_profile(overall.index, overall.SOCect/ 10, ax[3, 0], 0, 120, 10, "Time(sec)", "SOC_ect", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.anodeE/ 1000, ax[4, 0], -0.1, 1.6, 0.1, "Time(sec)", "anodeE (V)", "App", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.log_Vol/1000, ax[0, 0], 3.0, 4.8, 0.2, "Time(sec)", "Voltage (V)", "", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.log_CurrAvg/1000, ax[1, 0], 0, 0, 0, "Time(sec)", "CurrAvg (A)", "", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.log_Temp/ 10, ax[2, 0], 20, 50, 4, "Time(sec)", "temp.(℃ )", "", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.log_SOC/ 10, ax[3, 0], 0, 120, 10, "Time(sec)", "SOC", "", 2, xlim[0], xlim[1], xlim[2])
                # graph_set_profile(overall.index, overall.log_SOCect/ 10, ax[3, 0], 0, 120, 10, "Time(sec)", "SOC_ect", "", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.log_anodeE/ 1000, ax[4, 0], -0.1, 1.6, 0.1, "Time(sec)", "anodeE (V)", "log", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.Vol/1000 - overall.log_Vol/1000, ax[0, 1], -0.05, 0.06, 0.01, "Time(sec)", "Voltage (V)", "", 3, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.CurrAvg/1000 - overall.log_CurrAvg/1000, ax[1 ,1], -0.05, 0.06, 0.01, "Time(sec)", "CurrAvg (A)", "", 3, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.Temp - overall.log_Temp/10, ax[2, 1], -2, 3, 0.5, "Time(sec)", "temp.(℃ )", "", 3, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.SOC - overall.log_SOC/10, ax[3, 1], -5, 6, 1, "Time(sec)", "SOC", "", 3, xlim[0], xlim[1], xlim[2])
                # graph_set_profile(overall.index, overall.SOCect/ 10 - overall.log_SOCect/ 10, ax[4, 1], -5, 6, 1, "Time(sec)", "SOC_ect", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile(overall.index, overall.anodeE/ 1000 - overall.log_anodeE/ 1000, ax[4, 1], -0.1, 0.1, 0.02, "Time(sec)", "anodeE (V)", "delta", 3, xlim[0], xlim[1], xlim[2])
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                for i in range(4):
                    for j in range(2):
                        # X축 레이블 제거
                        ax[i, j].set_xlabel('')
                        # X축 틱 레이블 제거
                        ax[i, j].set_xticklabels([])
                if self.saveok.isChecked() and save_file_name:
                    df = df._append(overall)
                if self.saveok.isChecked() and save_file_name:
                    if not self.chk_setcyc_sep.isChecked():
                        df.to_excel(writer, sheet_name="log")
                    else:
                        overall.to_excel(writer)
                    writer.close()
                fig.legend()
                plt.subplots_adjust(right=0.8)
                tab_name_list =set.split("/")[-1].split("\\")[-1]
                # plt.suptitle(Chgnamelist[-1], fontsize=15)
                tab_layout.addWidget(toolbar)
                tab_layout.addWidget(canvas)
                self.set_tab.addTab(tab, tab_name_list) 
                self.set_tab.setCurrentWidget(tab)
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                output_fig(self.figsaveok, tab_name_list)
                plt.close()
            self.progressBar.setValue(100)

    def ect_set_log2_button(self):
        '''
        ECT result
        0 Time 1 voltage_now(mV) 2 Vavg(mV) 3 Ctype(Etc)-ChargCur 4 CurrentAvg. 5 Level
        6 Charging 7 Battery_Cycle 8 diffTime 9 Temperature(BA) 10 temp_ambient
        11 batt_temp 12 batt_temp_adc 13 batt_temp_raw 14 batt_wpc_temp 15 batt_wpc_temp_adc
        16 chg_temp 17 chg_temp_adc 18 dchg_temp 19 dchg_temp_adc 20 usb_temp 
        21 usb_temp_adc 22 compVoltage 23 ectSOC 24 RSOC 25 SOC_RE 
        26 SOC_EDV 27 SOH 28 AnodePotential 29 SOH_dR 30 SOH_CA 
        31 SOH_X 32 SC_VALUE 33 SC_SCORE 34 SC_V_Acc 35 SC_V_Avg 
        36 LUT_VOLT0 37 LUT_VOLT1 38 LUT_VOLT2 39 LUT_VOLT3 40 T_move
        '''
        global writer
        root = Tk()
        root.withdraw()
        self.ECTSetlog2.setDisabled(True)
        datafilepaths = multi_askopendirnames()
        self.ECTSetlog2.setEnabled(True)
        set_count = 1
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name")
        if datafilepaths:
            for set in datafilepaths:
                progressdata = progress(1, 1, 1, 1, set_count, len(datafilepaths))
                set_count = set_count + 1
                fig, ax = plt.subplots(nrows=5, ncols=2, figsize=(18, 10))
                tab = QtWidgets.QWidget()
                tab_layout = QtWidgets.QVBoxLayout(tab)
                canvas = FigureCanvas(fig)
                toolbar = NavigationToolbar(canvas, None)
                inputheader = ['Time', 'log_SOC', 'log_Temp', 'log_Vol', 'log_CurrAvg', 'log_sleeptime', 'log_ect_full_voltage', 'FG_cap']
                # curr_timestamp,
                # output.ECT_CNT, output.ECT_T_MOVE, output.ECT_OCV, output.ECT_ASOC, output.ECT_RSOC, 
                # output.ECT_SOC_RE, output.ECT_SOC_EDV, output.ECT_SOH, output.ECT_SOH_dR, output.ECT_SOH_CA, 
                # output.ECT_SOH_X, output.ECT_SOH_RSOH, output.ECT_ISD_Value, output.ECT_ISD_Score, output.ECT_ISD_Grade, output.ECT_ISD_Vacc, 
                # output.ECT_ISD_Vavg, output.ECT_ISD_I, output.ECT_ISD_R, output.ECT_LDP_0Step, output.ECT_LDP_1Step, output.ECT_LDP_2Step, 
                # output.ECT_LDP_3Step, output.ECT_Anode_Potential);
                outputheader0 = ['Time', 'log_ECT_CNT', 'log_ECT_T_MOVE', 'log_ECT_OCV', 'log_SOCect', 'log_ECT_RSOC',
                                'log_ECT_SOC_RE', 'log_ECT_SOC_EDV', 'log_ECT_SOH', 'log_ECT_SOH_dR', 'log_ECT_SOH_CA',
                                'log_ECT_SOH_X', 'log_ECT_SOH_MX', 'log_ECT_ISD_Value', 'log_ECT_ISD_Score', 'log_ECT_ISD_Vacc',
                                'log_ECT_ISD_Vavg','log_ECT_ISD_I', 'log_ECT_ISD_R', 'log_ECT_LDP_Step0', 'log_ECT_LDP_Step1', 'log_ECT_LDP_Step2',
                                'log_ECT_LDP_Step3', 'log_anodeE']
                outputheader = ['Time', 'log_ECT_CNT', 'log_ECT_T_MOVE', 'log_ECT_OCV', 'log_SOCect', 'log_ECT_RSOC',
                                'log_ECT_SOC_RE', 'log_ECT_SOC_EDV', 'log_ECT_SOH', 'log_ECT_SOH_dR', 'log_ECT_SOH_CA',
                                'log_ECT_SOH_X', 'log_ECT_SOH_MX', 'log_ECT_ISD_Value', 'log_ECT_ISD_Score', 'log_ECT_ISD_Grade', 'log_ECT_ISD_Vacc',
                                'log_ECT_ISD_Vavg','log_ECT_ISD_I', 'log_ECT_ISD_R', 'log_ECT_LDP_Step0', 'log_ECT_LDP_Step1', 'log_ECT_LDP_Step2',
                                'log_ECT_LDP_Step3', 'log_anodeE']
                # 파일 경로 패턴
                input_pattern = str(set) + '\\ect_inputlog.txt*'
                output_pattern = str(set) + '\\ect_outputlog.txt*'
                input_files = sorted(glob.glob(input_pattern))
                output_files = sorted(glob.glob(output_pattern))
                # 데이터프레임 로드 및 병합
                inputlog = pd.concat(
                    (pd.read_csv(file, header=None) for file in input_files),
                    axis=0
                )
                outputlog = pd.concat(
                    (pd.read_csv(file, header=None) for file in output_files),
                    axis=0
                )
                inputlog.columns = inputheader
                if len(outputlog.columns) == 24:
                    outputlog.columns = outputheader0
                else:
                    outputlog.columns = outputheader
                # app결과의 시간을 timestamp로 수정
                inputlog.set_index('Time', inplace=True)
                outputlog.set_index('Time', inplace=True)
                inputlog = inputlog[~inputlog.index.duplicated()]
                outputlog = outputlog[~outputlog.index.duplicated()]
                # x_min = 0
                # x_max = ((inputlog.index.max() - x_min) // 3600 * 3600) / 3600
                x_min = inputlog.index.min() // 3600 * 3600
                x_max = inputlog.index.max() // 3600 * 3600
                x_gap = 0
                # x_gap = (x_max - x_min) // 100
                # xlim = [x_min, x_max, x_gap]
                xlim = [0, (x_max - x_min) / 3600, x_gap]
                overall = pd.concat([inputlog, outputlog], axis=1, join='outer')
                overall['log_SOC'] = np.where(overall['log_SOC'] >= 10000, np.nan, overall['log_SOC'])
                # 충전 관련
                # graph_set_profile(overall.index, overall.log_Vol / 1000, ax[0, 0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_Vol / 1000, ax[0, 0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_LDP_Step0, ax[0, 0], 4.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_LDP_Step1, ax[0, 0], 4.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 3, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_LDP_Step2, ax[0, 0], 4.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 4, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_LDP_Step3, ax[0, 0], 4.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 5, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_OCV / 1000, ax[0, 0], 3.0, 4.8, 0.2, "Time(hr)", "Voltage (V)", "", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_CurrAvg / 1000, ax[1, 0], 0, 0, 0, "Time(hr)", "CurrAvg/ISD (A)", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_ISD_I / 1000, ax[1, 0], 0, 0, 0, "Time(hr)", "CurrAvg/ISD (A)", "", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_Temp / 10, ax[2, 0], 20, 50, 4, "Time(hr)", "temp.(℃ )", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_SOC / 10, ax[3, 0], 0, 120, 10, "Time(hr)", "SOC", "SOC", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_SOCect / 10, ax[3, 0], 0, 120, 10, "Time(hr)", "SOC", "ECT_ASOC", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_RSOC / 10, ax[3, 0], 0, 120, 10, "Time(hr)", "SOC", "ECT_RSOC", 3, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_SOC_RE / 10, ax[3, 0], 0, 120, 10, "Time(hr)", "SOC", "ECT_UISOC", 4, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_anodeE / 1000, ax[4, 0], -0.2, 1.6, 0.2, "Time(hr)", "anodeE (V)", "log", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_SOH_dR, ax[0, 1], 0, 0, 0, "Time(hr)", "SEI resistance", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_SOH / 10, ax[1, 1], 80, 110, 5, "Time(hr)", "SOH", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_SOH_CA / 10, ax[1, 1], 80, 110, 5, "Time(hr)", "SOH", "", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_SOH_X / 10, ax[2, 1], 0, 25, 5, "Time(hr)", "SOH_X", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_ISD_Value, ax[3, 1], 0, 11, 1, "Time(hr)", "ISD value", "", 1, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_ISD_Score, ax[3, 1], 0, 6, 1, "Time(hr)", "ISD score", "", 2, xlim[0], xlim[1], xlim[2])
                graph_set_profile((overall.index - x_min)/3600, overall.log_ECT_ISD_R, ax[4, 1], 0, 1100, 100, "Time(hr)", "ISD resistance", "", 1, xlim[0], xlim[1], xlim[2])
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                tab_name_list =set.split("/")[-1].split("\\")[-1]
                for i in range(4):
                    for j in range(2):
                        # X축 레이블 제거
                        ax[i, j].set_xlabel('')
                        # X축 틱 레이블 제거
                        ax[i, j].set_xticklabels([])
                if self.saveok.isChecked() and save_file_name:
                    overall_sorted = overall.sort_index()
                    overall_sorted.to_csv(save_file_name + '_' + tab_name_list + '.csv')
                fig.legend()
                plt.subplots_adjust(right=0.8)
                # plt.suptitle(Chgnamelist[-1], fontsize=15)
                tab_layout.addWidget(toolbar)
                tab_layout.addWidget(canvas)
                self.set_tab.addTab(tab, tab_name_list) 
                self.set_tab.setCurrentWidget(tab)
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                output_fig(self.figsaveok, tab_name_list)
                plt.close()
            self.progressBar.setValue(100)

    # 소재 정보 데이터 파일 경로 설정
    def dvdq_material_button(self):
        ca_mat_filepath = filedialog.askopenfilename(initialdir="d://dvdqraw//", title="양극 개별 Profile 데이터 선택")
        self.ca_mat_dvdq_path.setText(str(ca_mat_filepath))
        an_mat_filepath = filedialog.askopenfilename(initialdir="d://dvdqraw//", title="음극 개별 Profile 데이터 선택")
        self.an_mat_dvdq_path.setText(str(an_mat_filepath))

    def dvdq_profile_button(self):
        real_filepath = filedialog.askopenfilename(initialdir="d://dvdqraw//", title="실측 결과 Profile 데이터 선택")
        self.pro_dvdq_path.setText(str(real_filepath))

    def dvdq_ini_reset_button(self):
        self.ca_mass_ini.setText(str(""))
        self.ca_slip_ini.setText(str(""))
        self.an_mass_ini.setText(str(""))
        self.an_slip_ini.setText(str(""))
        self.fittingdegree = 1
        self.min_rms = np.inf

    def dvdq_graph(self, simul_full, min_params, rms):
        self.tab_delete(self.dvdq_simul_tab)
        # while self.dvdq_simul_tab.count() > 0:
        #     self.dvdq_simul_tab.removeTab(0)
        # tab 그래프 추가
        fig = plt.figure(figsize=(8, 8))
        tab = QtWidgets.QWidget()
        tab_layout = QtWidgets.QVBoxLayout(tab)
        canvas = FigureCanvas(fig)
        ax1 = plt.subplot(2, 1, 1)
        ax2 = plt.subplot(2, 1, 2)
        toolbar = NavigationToolbar(canvas, None)
        # Voltage Profile 그리기
        ax1.plot(simul_full.full_cap, simul_full.an_volt, "-", color = "b")
        ax1.plot(simul_full.full_cap, simul_full.ca_volt, "-", color = "r")
        ax1.plot(simul_full.full_cap, simul_full.full_volt, "--", color = "g")
        ax1.plot(simul_full.full_cap, simul_full.real_volt, "-", color = "k")
        ax1.set_ylim(0, 4.7)
        ax1.set_xticks(np.linspace(-5, 105, 23))
        ax1.legend(["음극", "양극", "예측", "실측"])
        ax1.set_xlabel("SOC")
        ax1.set_ylabel("Voltage")
        ax1.grid(which="major", axis="both", alpha=0.5)
        # dVdQ 그래프 그리기
        ax2.plot(simul_full.full_cap, simul_full.an_dvdq, "-", color = "b")
        ax2.plot(simul_full.full_cap, simul_full.ca_dvdq, "-", color = "r")
        ax2.plot(simul_full.full_cap, simul_full.full_dvdq, "--", color = "g")
        ax2.plot(simul_full.full_cap, simul_full.real_dvdq, "-", color = "k")
        ax2.set_ylim(-0.02, 0.02)
        ax2.set_xticks(np.linspace(-5, 105, 23))
        ax2.legend(["음극 dVdQ", "양극 dVdQ", "예측 dVdQ", "실측 dVdQ"])
        ax2.set_xlabel("SOC")
        ax2.set_ylabel("dVdQ")
        ax2.grid(which="major", axis="both", alpha=0.5)
        fig.subplots_adjust(top=0.92, bottom=0.08, left=0.10, right=0.95, hspace=0.25, wspace=0.35)
        # chtname = real_filepath.split("/")
        fig.legend()
        # SaveFileName set-up
        fig.suptitle(
            # 'title:' + str(chtname[-1])
            'ca_mass:' + str(f"{min_params[0]:.2f}")
            + ',     ca_slip:' + str(f"{min_params[1]:.2f}")
            + ',     an_mass:' + str(f"{min_params[2]:.2f}")
            + ',     an_slip:' + str(f"{min_params[3]:.2f}")
            + ',     rms(%):' + str(f"{(rms * 100):.3f}")
            , fontsize= 12)
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(canvas)
        self.dvdq_simul_tab.addTab(tab, str(self.pro_dvdq_path.text()))
        self.dvdq_simul_tab.setCurrentWidget(tab)
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        plt.close()

    def dvdq_fitting_button(self):
        global writer
        ca_mat_filepath = str(self.ca_mat_dvdq_path.text())
        an_mat_filepath = str(self.an_mat_dvdq_path.text())
        real_filepath = str(self.pro_dvdq_path.text())
        if "mAh" in real_filepath: # 파일 이름에 용량 관련 문자 있을 때
                dvdq_min_cap = name_capacity(real_filepath)
        else:
            dvdq_min_cap = 100
        if os.path.isfile(ca_mat_filepath):
            ca_ccv_raw = pd.read_csv(ca_mat_filepath, sep="\t")
            an_ccv_raw = pd.read_csv(an_mat_filepath, sep="\t")
        else:
            self.dvdq_material_button()
            ca_mat_filepath = str(self.ca_mat_dvdq_path.text())
            an_mat_filepath = str(self.an_mat_dvdq_path.text())
            ca_ccv_raw = pd.read_csv(ca_mat_filepath, sep="\t")
            an_ccv_raw = pd.read_csv(an_mat_filepath, sep="\t")
        ca_ccv_raw.columns = ["ca_cap", "ca_volt"]
        an_ccv_raw.columns = ["an_cap", "an_volt"]
        if os.path.isfile(real_filepath):
            real_raw = pd.read_csv(real_filepath, sep="\t")
        else:
            self.dvdq_profile_button()
            real_filepath = str(self.pro_dvdq_path.text())
            real_raw = pd.read_csv(real_filepath, sep="\t")
        real_raw.columns = ["real_cap", "real_volt"]
        # 셀 용량 기준
        full_cell_max_cap = max(real_raw.real_cap)
        # 미분을 위한 smoothing 기준
        full_period = int(self.dvdq_full_smoothing_no.text())
        # 각 parameter의 초기값 세팅
        if self.ca_mass_ini.text() == "":
            ca_mass_ini = full_cell_max_cap/max(ca_ccv_raw.ca_cap)
            self.ca_mass_ini.setText(str(ca_mass_ini))
        else:
            ca_mass_ini = float(self.ca_mass_ini.text())
        if self.ca_slip_ini.text() == "":
            ca_slip_ini = 1
            self.ca_slip_ini.setText(str(ca_slip_ini))
        else:
            ca_slip_ini = float(self.ca_slip_ini.text())
        if self.an_mass_ini.text() == "":
            an_mass_ini = full_cell_max_cap/max(an_ccv_raw.an_cap)
            self.an_mass_ini.setText(str(an_mass_ini))
        else:
            an_mass_ini = float(self.an_mass_ini.text())
        if self.an_slip_ini.text() == "":
            an_slip_ini = 1
            self.an_slip_ini.setText(str(an_slip_ini))
        else:
            an_slip_ini = float(self.an_slip_ini.text())
        # 열화 상태 고려 및 LL 산포에 따른 보정치 추가
        self.fittingdegree = self.fittingdegree * 1.2
        if self.ca_mass_ini_fix.isChecked():
            ca_mass_min = ca_mass_ini
            ca_mass_max = ca_mass_ini
        else:
            ca_mass_min = ca_mass_ini * (1 - 0.1 / self.fittingdegree)
            ca_mass_max = ca_mass_ini * (1 + 0.1 / self.fittingdegree)
        if self.ca_slip_ini_fix.isChecked():
            ca_slip_min = ca_slip_ini
            ca_slip_max = ca_slip_ini
        else:
            ca_slip_min = ca_slip_ini - (full_cell_max_cap * (0.05 / self.fittingdegree))
            ca_slip_max = ca_slip_ini + (full_cell_max_cap * (0.05 / self.fittingdegree))
        if self.an_mass_ini_fix.isChecked():
            an_mass_min = an_mass_ini
            an_mass_max = an_mass_ini
        else:
            an_mass_min = an_mass_ini * (1 - 0.1 / self.fittingdegree)
            an_mass_max = an_mass_ini * (1 + 0.1 / self.fittingdegree)
        if self.an_slip_ini_fix.isChecked():
            an_slip_min = an_slip_ini
            an_slip_max = an_slip_ini
        else:
            an_slip_min = an_slip_ini - (full_cell_max_cap * (0.05 / self.fittingdegree))
            an_slip_max = an_slip_ini + (full_cell_max_cap * (0.05 / self.fittingdegree))
        # 목적함수 초기화 실행
        min_params = None
        for i in range(int(self.dvdq_test_no.text())):
            ca_mass, ca_slip, an_mass, an_slip = generate_params(ca_mass_min, ca_mass_max, ca_slip_min, ca_slip_max, an_mass_min, an_mass_max,
                                                                 an_slip_min, an_slip_max)
            simul_full = generate_simulation_full(ca_ccv_raw, an_ccv_raw, real_raw, ca_mass, ca_slip, an_mass, an_slip, full_cell_max_cap,
                                                  dvdq_min_cap, full_period)
            # 지정 영역에서만 rms 산정
            simul_full = simul_full.loc[(simul_full["full_cap"] > int(
                self.dvdq_start_soc.text())) & (simul_full["full_cap"] < int(self.dvdq_end_soc.text()))]
            simul_diff = np.subtract(simul_full.full_dvdq, simul_full.real_dvdq)
            simul_diff[np.isnan(simul_diff)] = 0
            simul_rms = np.sqrt(np.mean(simul_diff ** 2))
            if simul_rms < self.min_rms:
                self.min_rms = simul_rms
                min_params = (ca_mass, ca_slip, an_mass, an_slip)
                self.dvdq_rms.setText(str(self.min_rms * 100))
                self.ca_mass_ini.setText(str(min_params[0]))
                self.ca_slip_ini.setText(str(min_params[1]))
                self.an_mass_ini.setText(str(min_params[2]))
                self.an_slip_ini.setText(str(min_params[3]))
            self.progressBar.setValue(int(int(i)/int(self.dvdq_test_no.text())*100))
        if min_params is not None:
            simul_full = generate_simulation_full(ca_ccv_raw, an_ccv_raw, real_raw, min_params[0], min_params[1],
                                                    min_params[2], min_params[3], full_cell_max_cap, dvdq_min_cap, full_period)
            simul_full = simul_full.loc[(simul_full["full_cap"] > int(
                self.dvdq_start_soc.text())) & (simul_full["full_cap"] < int(self.dvdq_end_soc.text()))]
            self.dvdq_graph(simul_full, min_params, self.min_rms)
            ca_max_cap = max(ca_ccv_raw.ca_cap) * min_params[0]
            an_max_cap = max(an_ccv_raw.an_cap) * min_params[2]
            self.full_cell_max_cap_txt.setText(str(full_cell_max_cap))
            self.ca_max_cap_txt.setText(str(ca_max_cap))
            self.an_max_cap_txt.setText(str(an_max_cap))
            result_para = pd.DataFrame({"para": min_params})
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                if save_file_name != '':
                    # parameter를 별도 시트에 저장
                    writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                    result_para.to_excel(writer, sheet_name="parameter", index=False)
                    simul_full.to_excel(writer, sheet_name="dvdq", index=False)
                    writer.close()
        else:
            self.dvdq_fitting2_button()
        self.progressBar.setValue(100)

    def dvdq_fitting2_button(self):
        self.fittingdegree = 1
        self.min_rms = np.inf
        if self.ca_mass_ini.text():
            global writer
            ca_mat_filepath = str(self.ca_mat_dvdq_path.text())
            an_mat_filepath = str(self.an_mat_dvdq_path.text())
            real_filepath = str(self.pro_dvdq_path.text())
            if "mAh" in real_filepath: # 파일 이름에 용량 관련 문자 있을 때
                dvdq_min_cap = name_capacity(real_filepath)
            else:
                dvdq_min_cap = 100
            ca_ccv_raw = pd.read_csv(ca_mat_filepath, sep="\t")
            ca_ccv_raw.columns = ["ca_cap", "ca_volt"]
            an_ccv_raw = pd.read_csv(an_mat_filepath, sep="\t")
            an_ccv_raw.columns = ["an_cap", "an_volt"]
            real_raw = pd.read_csv(real_filepath, sep="\t")
            real_raw.columns = ["real_cap", "real_volt"]
            
            # 셀 용량 기준
            full_cell_max_cap = max(real_raw.real_cap)
            # 미분을 위한 smoothing 기준
            full_period = int(self.dvdq_full_smoothing_no.text())
            # 각 parameter의 초기값 세팅
            ca_mass_ini = float(self.ca_mass_ini.text())
            ca_slip_ini = float(self.ca_slip_ini.text())
            an_mass_ini = float(self.an_mass_ini.text())
            an_slip_ini = float(self.an_slip_ini.text())
            simul_full = generate_simulation_full(ca_ccv_raw, an_ccv_raw, real_raw, ca_mass_ini, ca_slip_ini,
                                                  an_mass_ini, an_slip_ini, full_cell_max_cap, dvdq_min_cap, full_period)
            simul_full = simul_full.loc[(simul_full["full_cap"] > int(self.dvdq_start_soc.text())) &
                                        (simul_full["full_cap"] < int(self.dvdq_end_soc.text()))]
            simul_diff = np.subtract(simul_full.full_dvdq, simul_full.real_dvdq)
            simul_diff[np.isnan(simul_diff)] = 0
            simul_rms = np.sqrt(np.mean(simul_diff ** 2))
            self.min_rms = simul_rms
            self.dvdq_rms.setText(str(self.min_rms * 100))
            ini_params = [ca_mass_ini, ca_slip_ini, an_mass_ini, an_slip_ini]
            self.dvdq_graph(simul_full, ini_params, simul_rms)
            self.progressBar.setValue(100)
            ca_max_cap = max(ca_ccv_raw.ca_cap) * ca_mass_ini
            an_max_cap = max(an_ccv_raw.an_cap) * an_mass_ini
            self.full_cell_max_cap_txt.setText(str(full_cell_max_cap))
            self.ca_max_cap_txt.setText(str(ca_max_cap))
            self.an_max_cap_txt.setText(str(an_max_cap))
            result_para = pd.DataFrame({"para": [ca_mass_ini, ca_slip_ini, an_mass_ini, an_slip_ini]})
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
                if save_file_name:
                    # parameter를 별도 시트에 저장
                    result_para.to_excel(writer, sheet_name="parameter", index=False)
                    simul_full.to_excel(writer, sheet_name="dvdq", index=False)
                    writer.close()
    
    def load_cycparameter_button(self):
        cyc_filepaths = filedialog.askopenfilenames(initialdir="d://cycparameter//",
                                                    title="불러올 02C, 05C 사이클 parameter 데이터를 순차적으로 선택")
        self.cycparameter.setText(str(cyc_filepaths[0]))
        parameterfilepath = self.cycparameter.text()
        self.cycparameter2.setText(str(cyc_filepaths[1]))
        parameterfilepath2 = self.cycparameter2.text()
        self.folderappcycestimation.setEnabled(True)
        self.pathappcycestimation.setEnabled(True)
        if parameterfilepath:
            parameter_df = pd.read_csv(parameterfilepath, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
            parameter_df = parameter_df.dropna(axis=0)
            self.aTextEdit_02c.setText(str(round(parameter_df.iloc[0, 0], 50)))
            self.bTextEdit_02c.setText(str(round(parameter_df.iloc[1, 0], 50)))
            self.b1TextEdit_02c.setText(str(round(parameter_df.iloc[2, 0], 50)))
            self.cTextEdit_02c.setText(str(round(parameter_df.iloc[3, 0], 50)))
            self.dTextEdit_02c.setText(str(round(parameter_df.iloc[4, 0], 50)))
            self.eTextEdit_02c.setText(str(round(parameter_df.iloc[5, 0], 50)))
            self.fTextEdit_02c.setText(str(round(parameter_df.iloc[6, 0], 50)))
            self.fdTextEdit_02c.setText(str(round(parameter_df.iloc[7, 0], 50)))
            
        if parameterfilepath2:
            parameter_df2 = pd.read_csv(parameterfilepath2, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
            parameter_df2 = parameter_df2.dropna(axis=0)
            self.aTextEdit_05c.setText(str(round(parameter_df2.iloc[0, 0], 50)))
            self.bTextEdit_05c.setText(str(round(parameter_df2.iloc[1, 0], 50)))
            self.b1TextEdit_05c.setText(str(round(parameter_df2.iloc[2, 0], 50)))
            self.cTextEdit_05c.setText(str(round(parameter_df2.iloc[3, 0], 50)))
            self.dTextEdit_05c.setText(str(round(parameter_df2.iloc[4, 0], 50)))
            self.eTextEdit_05c.setText(str(round(parameter_df2.iloc[5, 0], 50)))
            self.fTextEdit_05c.setText(str(round(parameter_df2.iloc[6, 0], 50)))
            self.fdTextEdit_05c.setText(str(round(parameter_df2.iloc[7, 0], 50)))
    
    def app_cycle_tab_reset_button(self):
        self.tab_delete(self.cycle_simul_tab)
        self.tab_no = 0

    def path_approval_cycle_estimation_button(self):
        def cyccapparameter(x, f_d):
            return 1 - np.exp(a_par1 * x[1] + b_par1) * (x[0] * f_d) ** b1_par1 - np.exp(c_par1 * x[1] + d_par1) * (
                x[0] * f_d) ** (e_par1 * x[1] + f_par1)
        def cyccapparameter02(x, f_d):
            return 1 - np.exp(a_par2 * x[1] + b_par2) * (x[0] * f_d) ** b1_par2 - np.exp(c_par2 * x[1] + d_par2) * (
                x[0] * f_d) ** (e_par2 * x[1] + f_par2)
        a_par1 = float(self.aTextEdit_02c.text())
        b_par1 = float(self.bTextEdit_02c.text())
        b1_par1 = float(self.b1TextEdit_02c.text())
        c_par1 = float(self.cTextEdit_02c.text())
        d_par1 = float(self.dTextEdit_02c.text())
        e_par1 = float(self.eTextEdit_02c.text())
        f_par1 = float(self.fTextEdit_02c.text())
        fd_par1 = float(self.fdTextEdit_02c.text())
        
        a_par2 = float(self.aTextEdit_05c.text())
        b_par2 = float(self.bTextEdit_05c.text())
        b1_par2 = float(self.b1TextEdit_05c.text())
        c_par2 = float(self.cTextEdit_05c.text())
        d_par2 = float(self.dTextEdit_05c.text())
        e_par2 = float(self.eTextEdit_05c.text())
        f_par2 = float(self.fTextEdit_05c.text())
        fd_par2 = float(self.fdTextEdit_05c.text())
        
        firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale = self.cyc_ini_set()
        # 용량 선정 관련
        global writer
        foldercount, chnlcount, colorno, writecolno = 0, 0, 0, 0
        root = Tk()
        root.withdraw()
        self.pathappcycestimation.setDisabled(True)
        self.chk_cyclepath.setChecked(True)
        pne_path = self.pne_path_setting()
        self.chk_cyclepath.setChecked(False)
        all_data_folder = pne_path[0]
        all_data_name = pne_path[1]
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        self.pathappcycestimation.setEnabled(True)
        graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        for i, cyclefolder in enumerate(all_data_folder):
            # tab 그래프 추가
            fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(8, 6))
            if os.path.exists(cyclefolder):
                if os.path.isdir(cyclefolder):
                    subfolder = [f.path for f in os.scandir(cyclefolder) if f.is_dir()]
                    foldercountmax = len(all_data_folder)
                    foldercount = foldercount + 1
                    for FolderBase in subfolder:
                        # tab 그래프 추가
                        tab = QtWidgets.QWidget()
                        tab_layout = QtWidgets.QVBoxLayout(tab)
                        canvas = FigureCanvas(fig)
                        toolbar = NavigationToolbar(canvas, None)
                        chnlcountmax = len(subfolder)
                        chnlcount = chnlcount + 1
                        # progressdata = (foldercount + chnlcount/chnlcountmax - 1)/foldercountmax * 100
                        progressdata = progress(foldercount, foldercountmax, chnlcount, chnlcountmax, 1, 1)
                        self.progressBar.setValue(int(progressdata))
                        cycnamelist = FolderBase.split("\\")
                        headername = [cycnamelist[-2] + ", " + cycnamelist[-1]]
                        if len(all_data_name) != 0:
                            title = all_data_name[i]
                        else:
                            title = cycnamelist[-2]
                        if not check_cycler(cyclefolder):
                            pass
                        else:
                            cyctemp = pne_simul_cycle_data(FolderBase, mincapacity, firstCrate)
                        # print(FolderBase)
                        if isinstance(cyctemp[1], pd.DataFrame) and hasattr(cyctemp[1], "Dchg"):
                            self.capacitytext.setText(str(cyctemp[0]))
                            if self.cyc_long_life.isChecked() and hasattr(cyctemp[1], "long_acc"):
                                cyctemp[1]["Dchg"] = cyctemp[1]["Dchg"] - cyctemp[1]["long_acc"]
                            y1 = cyctemp[1]["Dchg"]
                            t1 =cyctemp[1]["Temp"]
                            y2 = cyctemp[3]["Dchg"]
                            t2 =cyctemp[3]["Temp"]
                            if t1.max() < 273:
                                t1 = 23 + 273
                                t2 = 23 + 273
                            x1 = cyctemp[1].index
                            x2 = cyctemp[3].index
                            dataadd1 = pd.DataFrame({'x1': x1, 't1': t1, 'y1': y1})
                            dataadd2 = pd.DataFrame({'x2': x2, 't2': t2, 'y2': y2})
                            dfall1 = dataadd1.dropna()
                            dfall2 = dataadd2.dropna()
                            maxfevset = 5000
                            p1 = [fd_par1]
                            p2 = [fd_par2]
                            if self.simul_x_max.text() == 0:
                                df1 = pd.DataFrame({'x1': range(1, 2000, 1)})
                                df2 = pd.DataFrame({'x2': range(1, 2000, 1)})
                            else:
                                df1 = pd.DataFrame({'x1': range(1, int(self.simul_x_max.text()), 1)})
                                df2 = pd.DataFrame({'x2': range(1, int(self.simul_x_max.text()), 1)})
                            df1.t1 = 23 + 273
                            df2.t2 = 23 + 273
                            popt1, pcov1 = curve_fit(cyccapparameter, (dfall1.x1, dfall1.t1), dfall1.y1, p1, maxfev=maxfevset)
                            popt2, pcov2 = curve_fit(cyccapparameter02, (dfall2.x2, dfall2.t2), dfall2.y2, p2, maxfev=maxfevset)
                            residuals1 = dfall1.y1 - cyccapparameter((dfall1.x1, dfall1.t1), *popt1)
                            residuals2 = dfall2.y2 - cyccapparameter02((dfall2.x2, dfall2.t2), *popt2)
                            ss_res1 = np.sum(residuals1 ** 2)
                            ss_res2 = np.sum(residuals2 ** 2)
                            ss_tot1 = np.sum((dfall1.y1 - np.mean(dfall1.y1)) ** 2)
                            ss_tot2 = np.sum((dfall2.y2 - np.mean(dfall2.y2)) ** 2)
                            r_squared1 = 1 - (ss_res1/ss_tot1)
                            r_squared2 = 1 - (ss_res2/ss_tot2)
                            if self.simul_long_life.isChecked():
                                real_y1 = dfall1.y1 * cyctemp[2] - cyctemp[1]["long_acc"]
                                simul_y1 = cyccapparameter((df1.x1, df1.t1), *popt1) * cyctemp[2] - cyctemp[1]["long_acc"]
                            else:
                                real_y1 = dfall1.y1 * cyctemp[2]
                                simul_y1 = cyccapparameter((df1.x1, df1.t1), *popt1) * cyctemp[2]
                            ax1.plot(dfall1.x1, real_y1, 'o', color=graphcolor[colorno], markersize=3,
                                     label='가속 = %5.3f' % tuple(popt1[0] / p1))
                            ax1.plot(df1.x1, simul_y1, color=graphcolor[colorno], label='오차 = %5.3f' % r_squared1)
                            ax1.plot(dfall2.x2, dfall2.y2 * cyctemp[4], 'o', color=graphcolor[colorno], markersize=5,
                                     label='가속 = %5.3f' % tuple(popt2[0] / p2))
                            ax1.plot(df2.x2, cyccapparameter02((df2.x2, df2.t2), *popt2) * cyctemp[4], '--', color=graphcolor[colorno],
                                     label='오차 = %5.3f' % r_squared2)
                            colorno = colorno % 9 + 1
                            # Data output option
                            output_df_all = cyctemp[7][["Dchg", "Temp", "Curr", "max_vol", "min_vol"]]
                            output_df_05c = cyctemp[1][["Dchg", "Temp", "Curr", "max_vol", "min_vol"]]
                            output_df_02c = cyctemp[3][["Dchg", "Temp", "Curr", "max_vol", "min_vol"]]
                            if self.saveok.isChecked() and save_file_name:
                                output_df_all.to_excel(writer, sheet_name="app_cycle", startcol=writecolno)
                                output_df_05c.to_excel(writer, sheet_name="highrate_cycle", startcol=writecolno)
                                output_df_02c.to_excel(writer, sheet_name="rate02c_cycle", startcol=writecolno)
                                writecolno = writecolno + 6
                            if len(all_data_name) != 0:
                                plt.suptitle(title, fontsize= 15, fontweight='bold')
                            else:
                                plt.suptitle(title, fontsize= 15, fontweight='bold')
                            ax1.tick_params(axis='both', which='major', labelsize=12) 
                            ax1.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                            ax1.set_ylim(float(self.simul_y_min.text()), float(self.simul_y_max.text()))
                            # ax1.set_xlim(0.5, 1.1)
                            ax1.set_ylabel('capacity ratio', fontsize = 14)
                            ax1.set_xlabel('cycle or day', fontsize = 14)
                            ax1.grid(which="major", axis="both", alpha=.5)
                            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                            output_fig(self.figsaveok, cycnamelist[-2])
                    tab_layout.addWidget(toolbar)
                    tab_layout.addWidget(canvas)
                    self.cycle_simul_tab.addTab(tab, f"예측{i+1}")
                    self.cycle_simul_tab.setCurrentWidget(tab)
                    plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        # plt.show()
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        plt.close()
        self.progressBar.setValue(100)
    
    def folder_approval_cycle_estimation_button(self):
        def cyccapparameter(x, f_d):
            return 1 - np.exp(a_par1 * x[1] + b_par1) * (x[0] * f_d) ** b1_par1 - np.exp(c_par1 * x[1] + d_par1) \
                * (x[0] * f_d) ** (e_par1 * x[1] + f_par1)
        def cyccapparameter02(x, f_d):
            return 1 - np.exp(a_par2 * x[1] + b_par2) * (x[0] * f_d) ** b1_par2 - np.exp(c_par2 * x[1] + d_par2) \
                * (x[0] * f_d) ** (e_par2 * x[1] + f_par2)
        
        a_par1 = float(self.aTextEdit_02c.text())
        b_par1 = float(self.bTextEdit_02c.text())
        b1_par1 = float(self.b1TextEdit_02c.text())
        c_par1 = float(self.cTextEdit_02c.text())
        d_par1 = float(self.dTextEdit_02c.text())
        e_par1 = float(self.eTextEdit_02c.text())
        f_par1 = float(self.fTextEdit_02c.text())
        fd_par1 = float(self.fdTextEdit_02c.text())
        
        a_par2 = float(self.aTextEdit_05c.text())
        b_par2 = float(self.bTextEdit_05c.text())
        b1_par2 = float(self.b1TextEdit_05c.text())
        c_par2 = float(self.cTextEdit_05c.text())
        d_par2 = float(self.dTextEdit_05c.text())
        e_par2 = float(self.eTextEdit_05c.text())
        f_par2 = float(self.fTextEdit_05c.text())
        fd_par2 = float(self.fdTextEdit_05c.text())
        
        firstCrate, mincapacity, xscale, ylimithigh, ylimitlow, irscale = self.cyc_ini_set()
        # 용량 선정 관련
        global writer
        foldercount, chnlcount, colorno, num = 0, 0, 0, 0
        root = Tk()
        root.withdraw()
        self.folderappcycestimation.setDisabled(True)
        pne_path = filedialog.askopenfilenames(initialdir="D://", title="Data File Name", defaultextension=".txt")
        self.folderappcycestimation.setEnabled(True)
        graphcolor = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        for i, cyclefolder in enumerate(pne_path):
            # tab 그래프 추가
            if os.path.exists(cyclefolder):
                foldercountmax = len(pne_path)
                foldercount = foldercount + 1
                # tab 그래프 추가
                chnlcountmax = len(cyclefolder)
                chnlcount = chnlcount + 1
                # progressdata = (foldercount + chnlcount/chnlcountmax - 1)/foldercountmax * 100
                progressdata = progress(foldercount, foldercountmax, chnlcount, chnlcountmax, 1, 1)
                self.progressBar.setValue(int(progressdata))
                title = cyclefolder
                df = pd.read_csv(cyclefolder, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
                for i in range(0, len(df.columns)):
                    if i % 6 == 5:
                        df_trim = df.iloc[:, (i - 5): (i + 1)]
                        df_trim.columns = ['TotlCycle', 'Dchg', 'Temp', 'Curr', 'max_vol', 'min_vol']
                        cyctemp = pne_simul_cycle_data_file(df_trim, cyclefolder, mincapacity, firstCrate)
                        if isinstance(cyctemp[1], pd.DataFrame) and hasattr(cyctemp[1], "Dchg"):
                            num = num + 1
                            fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(12, 12))
                            tab = QtWidgets.QWidget()
                            tab_layout = QtWidgets.QVBoxLayout(tab)
                            canvas = FigureCanvas(fig)
                            toolbar = NavigationToolbar(canvas, None)
                            self.capacitytext.setText(str(cyctemp[0]))
                            if self.cyc_long_life.isChecked() and hasattr(cyctemp[1], "long_acc"):
                                cyctemp[1]["Dchg"] = cyctemp[1]["Dchg"] - cyctemp[1]["long_acc"]
                            y1 = cyctemp[1]["Dchg"]
                            t1 = cyctemp[1]["Temp"]
                            y2 = cyctemp[3]["Dchg"]
                            t2 = cyctemp[3]["Temp"]
                            if t1.max() < 273:
                                t1 = 23 + 273
                                t2 = 23 + 273
                            x1 = cyctemp[1].index
                            x2 = cyctemp[3].index
                            dataadd1 = pd.DataFrame({'x1': x1, 't1': t1, 'y1': y1})
                            dataadd2 = pd.DataFrame({'x2': x2, 't2': t2, 'y2': y2})
                            dfall1 = dataadd1.dropna()
                            dfall2 = dataadd2.dropna()
                            maxfevset = 5000
                            p1 = [fd_par1]
                            p2 = [fd_par2]
                            if self.simul_x_max.text() == 0:
                                df1 = pd.DataFrame({'x1': range(1, 2000, 1)})
                                df2 = pd.DataFrame({'x2': range(1, 2000, 1)})
                            else:
                                df1 = pd.DataFrame({'x1': range(1, int(self.simul_x_max.text()), 1)})
                                df2 = pd.DataFrame({'x2': range(1, int(self.simul_x_max.text()), 1)})
                            df1.t1 = 23 + 273
                            df2.t2 = 23 + 273
                            popt1, pcov1 = curve_fit(cyccapparameter, (dfall1.x1, dfall1.t1), dfall1.y1, p1, maxfev=maxfevset)
                            popt2, pcov2 = curve_fit(cyccapparameter02, (dfall2.x2, dfall2.t2), dfall2.y2, p2, maxfev=maxfevset)
                            residuals1 = dfall1.y1 - cyccapparameter((dfall1.x1, dfall1.t1), *popt1)
                            residuals2 = dfall2.y2 - cyccapparameter02((dfall2.x2, dfall2.t2), *popt2)
                            ss_res1 = np.sum(residuals1 ** 2)
                            ss_res2 = np.sum(residuals2 ** 2)
                            ss_tot1 = np.sum((dfall1.y1 - np.mean(dfall1.y1)) ** 2)
                            ss_tot2 = np.sum((dfall2.y2 - np.mean(dfall2.y2)) ** 2)
                            r_squared1 = 1 - (ss_res1/ss_tot1)
                            r_squared2 = 1 - (ss_res2/ss_tot2)
                            if self.simul_long_life.isChecked():
                                real_y1 = dfall1.y1 * cyctemp[2] - cyctemp[1]["long_acc"]
                                simul_y1 = cyccapparameter((df1.x1, df1.t1), *popt1) * cyctemp[2] - cyctemp[1]["long_acc"]
                            else:
                                real_y1 = dfall1.y1 * cyctemp[2]
                                simul_y1 = cyccapparameter((df1.x1, df1.t1), *popt1) * cyctemp[2]
                            ax1.plot(dfall1.x1, real_y1, 'o', color=graphcolor[colorno], markersize=3,
                                     label='사이클 가속 = %5.3f' % tuple(popt1[0] / p1))
                            ax1.plot(df1.x1, simul_y1, color=graphcolor[colorno], label='사이클 오차 = %5.3f' % r_squared1)
                            ax1.plot(dfall2.x2, dfall2.y2 * cyctemp[4], 'o', color=graphcolor[colorno], markersize=3,
                                     label='0.2C 가속 = %5.3f' % tuple(popt2[0] / p2))
                            ax1.plot(df2.x2, cyccapparameter02((df2.x2, df2.t2), *popt2) * cyctemp[4], '--', color=graphcolor[colorno],
                                     label='0.2C 오차 = %5.3f' % r_squared2)
                            colorno = colorno % 9 + 1
                            ax1.tick_params(axis='both', which='major', labelsize=12) 
                            ax1.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                            ax1.set_ylim(float(self.simul_y_min.text()), float(self.simul_y_max.text()))
                            ax1.set_ylabel('capacity ratio', fontsize = 14)
                            ax1.set_xlabel('cycle or day', fontsize = 14)
                            ax1.grid(which="major", axis="both", alpha=.5)
                            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                            plt.suptitle(title, fontsize= 15, fontweight='bold')
                            tab_layout.addWidget(toolbar)
                            tab_layout.addWidget(canvas)
                            self.cycle_simul_tab.addTab(tab, f"예측{num}")
                            self.cycle_simul_tab.setCurrentWidget(tab)
                            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        plt.close()
        self.progressBar.setValue(100)

    def eu_tab_reset_button(self):
        self.tab_delete(self.cycle_simul_tab_eu)
        self.tab_no = 0
        
    def eu_parameter_reset_button(self):
        # 초기 매개변수 리스트 (이름과 순서를 명시적으로 정의)
        initial_params = {
            "a": 0.03,
            "b": -18,
            "b1": 0.7,
            "c": 2.3,
            "d": -782,
            "e": -0.28,
            "f": 96,
            "fd": 1
        }
        # 각 매개변수를 텍스트 필드에 설정
        for param_name, value in initial_params.items():
            # QTextEdit 객체 이름 패턴: self.{param_name}TextEdit_eu
            widget_name = f"{param_name}TextEdit_eu"
            # 객체가 존재할 경우 값 설정
            if hasattr(self, widget_name):
                getattr(self, widget_name).setText(f"{value:.5f}")  # 소수점 5자리까지 표시

    def eu_load_cycparameter_button(self):
        # 파일 선택 대화상자 열기
        cyc_filepath = filedialog.askopenfilename(initialdir=r"d://", title="사이클 파라미터 데이터 선택")
        self.cycparameter_eu.setText(cyc_filepath)
        parameterfilepath = self.cycparameter_eu.text()

        if parameterfilepath:
            # CSV 파일 읽기 (오류 발생 시 NaN으로 처리)
            parameter_df = pd.read_csv(parameterfilepath, sep="\t", engine="c", encoding="UTF-8",
                                       skiprows=1, on_bad_lines='skip')
            # 결측치 제거
            parameter_df = parameter_df.dropna(axis=0)
            # "02C" 컬럼 존재 여부 확인
            if "02C" in parameter_df.columns:
                # "02C" 컬럼 데이터 추출
                col_data = parameter_df["02C"]
                
                # 각 매개변수를 텍스트박스에 설정 (과학적 표기법 방지)
                self.aTextEdit_eu.setText(f"{col_data.iloc[0]:.15f}")
                self.bTextEdit_eu.setText(f"{col_data.iloc[1]:.15f}")
                self.b1TextEdit_eu.setText(f"{col_data.iloc[2]:.15f}")
                self.cTextEdit_eu.setText(f"{col_data.iloc[3]:.15f}")
                self.dTextEdit_eu.setText(f"{col_data.iloc[4]:.15f}")
                self.eTextEdit_eu.setText(f"{col_data.iloc[5]:.15f}")
                self.fTextEdit_eu.setText(f"{col_data.iloc[6]:.15f}")
                self.fdTextEdit_eu.setText(f"{col_data.iloc[7]:.15f}")
            else:
                # "02C" 컬럼이 없는 경우 경고 메시지 출력
                err_msg("에러","parameter 컬럼 없음") 
                # self.aTextEdit_eu.setText("02C 컬럼 없음")
    
    def eu_save_cycparameter_button(self):
        par1 = float(self.aTextEdit_eu.text())
        par2 = float(self.bTextEdit_eu.text())
        par3 = float(self.b1TextEdit_eu.text())
        par4 = float(self.cTextEdit_eu.text())
        par5 = float(self.dTextEdit_eu.text())
        par6 = float(self.eTextEdit_eu.text())
        par7 = float(self.fTextEdit_eu.text())
        par8 = float(self.fdTextEdit_eu.text())
        filepath = self.cycparameter_eu.text()
        namelist = filepath.split("/")
        namelist = namelist[-1].split(".")
        
        df = pd.DataFrame()
        df["02C"] = [par1, par2, par3, par4, par5, par6, par7, par8]
        save_file_name = "d:/para_" + namelist[0] + ".txt"
        # parameter를 별도 시트에 저장
        with open(save_file_name, 'w') as f:
            f.write('\n')
            df.to_csv(f, sep='\t', index=False, header=True)
        err_msg("저장", "저장되었습니다.") 
        output_para_fig(self.figsaveok, "fig_" + namelist[0])

    def eu_fitting_confirm_button(self):
        global writer
        # exp complex degradation (cycle 기준, day 기준)
        def swellingfit(x, a_par, b_par, b1_par, c_par, d_par, e_par, f_par, f_d):
            return np.exp(a_par * x[1] + b_par) * (x[0] * f_d) ** b1_par + np.exp(c_par * x[1] + d_par) * (x[0] * f_d) ** (e_par * x[1] + f_par)
        def capacityfit(x, a_par, b_par, b1_par, c_par, d_par, e_par, f_par, f_d):
            return 1 - np.exp(a_par * x[1] + b_par) * (x[0] * f_d) ** b1_par - np.exp(c_par * x[1] + d_par) * (x[0] * f_d) ** (e_par * x[1] + f_par)
        if self.aTextEdit_eu.text() == "":
            parini1 = [0.03, -18, 0.7, 2.3, -782, -0.28, 96, 1]
            self.aTextEdit_eu.setText(str(parini1[0]))
            self.bTextEdit_eu.setText(str(parini1[1]))
            self.b1TextEdit_eu.setText(str(parini1[2]))
            self.cTextEdit_eu.setText(str(parini1[3]))
            self.dTextEdit_eu.setText(str(parini1[4]))
            self.eTextEdit_eu.setText(str(parini1[5]))
            self.fTextEdit_eu.setText(str(parini1[6]))
            self.fdTextEdit_eu.setText(str(parini1[7]))
        # UI 변수를 초기치로 산정
        a_par1 = float(self.aTextEdit_eu.text())
        b_par1 = float(self.bTextEdit_eu.text())
        b1_par1 = float(self.b1TextEdit_eu.text())
        c_par1 = float(self.cTextEdit_eu.text())
        d_par1 = float(self.dTextEdit_eu.text())
        e_par1 = float(self.eTextEdit_eu.text())
        f_par1 = float(self.fTextEdit_eu.text())
        fd_par1 = float(self.fdTextEdit_eu.text())
        p0 = [a_par1, b_par1, b1_par1, c_par1, d_par1, e_par1, f_par1, fd_par1]
        root = Tk()
        root.withdraw()
        self.xscale = int(self.simul_x_max_eu.text())
        y_max = float(self.simul_y_max_eu.text())
        y_min = float(self.simul_y_min_eu.text())
        datafilepath = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        if datafilepath:
            self.cycparameter_eu.setText(str(datafilepath[0]))
        file = 0
        num = 0
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        for filepath in datafilepath:
            # tab 그래프 추가
            fig, ax = plt.subplots(figsize=(6, 6))
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout(tab)
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, None)
            dfall = pd.DataFrame({'x': [], 't': [], 'y': []})
            df = pd.read_csv(filepath, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
            if not "02C" in df.columns:
                namelist = filepath.split("/")
                namelist = namelist[-1].split(".")
                filemax = len(datafilepath)
                file = file + 1
                first_column_name = df.columns[1]
                if isinstance(first_column_name, str) and first_column_name.isdigit():
                    for i in range(1, len(df.columns)):
                        y1 = df.iloc[:,i]
                        x1 = df.iloc[:len(y1),0]
                        # # 초기값으로 100분율 환산
                        dataadd = pd.DataFrame({'x': x1, 'y': y1})
                        dataadd = dataadd.dropna()
                        if df.iloc[0, i] != 0 and not dataadd.empty and len(dataadd) >= 2 and dataadd.shape[1] >= 2:
                            x_0 = dataadd.iloc[0,0]
                            x_1 = dataadd.iloc[1,0]
                            y_0 = dataadd.iloc[0,1]
                            y_1 = dataadd.iloc[1,1]
                            coefficients = np.polyfit([x_0, x_1], [y_0, y_1], 1)
                            polynomial = np.poly1d(coefficients)
                            y_max_cap = polynomial(0)
                            if not self.fix_swelling_eu.isChecked():
                                dataadd.y = dataadd.y/y_max_cap
                        dataadd['t'] = float(df.columns[i][:2])
                        if dataadd.t.max() < 273:
                            dataadd.t = dataadd.t + 273
                        # 전체 dataframe을 누적
                        dfall = dfall._append(dataadd)
                        progressdata = (file + 1 + num/len(list(df)))/filemax * 100
                        self.progressBar.setValue(int(progressdata))
                else:
                    for i in range(0, len(df.columns)):
                        num = num + 1
                        if i % 3 == 2:
                            y1 = df.iloc[:, i]
                            x1 = df.iloc[:, i - 2][:len(y1)]
                            # # 초기값으로 100분율 환산
                            if df.iloc[0, i] != 0:
                                x_0 = x1[0]
                                x_1 = x1[1]
                                y_0 = y1[0]
                                y_1 = y1[1]
                                coefficients = np.polyfit([x_0, x_1], [y_0, y_1], 1)
                                polynomial = np.poly1d(coefficients)
                                y_max_cap = polynomial(0)
                                if not self.fix_swelling_eu.isChecked():
                                    y1 = y1/y_max_cap
                            # 용량이 있는 값을 기준으로 온도를 절대값으로 환산
                            t1 = df.iloc[:, i - 1][:len(y1)]
                            if t1.max() < 273:
                                t1 = t1 + 273
                            # 용량이 있는 값을 기준으로 cycle 산정
                            dataadd = pd.DataFrame({'x': x1, 't': t1, 'y': y1})
                            # 전체 dataframe을 누적
                            dfall = dfall._append(dataadd)
                            progressdata = (file + 1 + num/len(list(df)))/filemax * 100
                            self.progressBar.setValue(int(progressdata))
                dfall = dfall.dropna()
                # 초기값을 100%로 맞추는 데이터 추가
                df2 = pd.DataFrame({'x': range(1, self.xscale, 1)})
                if self.fix_swelling_eu.isChecked():
                    df2.t0 = 23 + 273
                    df2.t1 = 35 + 273
                    df2.t2 = 40 + 273
                    df2.t3 = 45 + 273
                else:
                    df2.t1 = 23 + 273
                    df2.t2 = 35 + 273
                    df2.t3 = 45 + 273
                # Fitting 계산
                maxfevset = 100000
                try:
                    if self.fix_swelling_eu.isChecked():
                        popt, pcov = curve_fit(swellingfit, (dfall.x, dfall.t), dfall.y, p0, maxfev=maxfevset)
                    else:
                        popt, pcov = curve_fit(capacityfit, (dfall.x, dfall.t), dfall.y, p0, maxfev=maxfevset)
                except (RuntimeError, TypeError) as e:
                    continue
                if self.fix_swelling_eu.isChecked():
                    residuals = dfall.y - swellingfit((dfall.x, dfall.t), *popt)
                else:
                    residuals = dfall.y - capacityfit((dfall.x, dfall.t), *popt)
                ss_res = np.sum(residuals ** 2)
                ss_tot = np.sum((dfall.y - np.mean(dfall.y)) ** 2)
                r_squared = 1 - (ss_res/ss_tot)
                if self.fix_swelling_eu.isChecked():
                    result0 = swellingfit((df2.x, df2.t0), *popt)
                    result1 = swellingfit((df2.x, df2.t1), *popt)
                    result2 = swellingfit((df2.x, df2.t2), *popt)
                    result3 = swellingfit((df2.x, df2.t3), *popt)
                    eol_cycle = result1.abs().idxmin()
                else:
                    result1 = capacityfit((df2.x, df2.t1), *popt)
                    result2 = capacityfit((df2.x, df2.t2), *popt)
                    result3 = capacityfit((df2.x, df2.t3), *popt)
                    eol_cycle = (result1 - 0.8).abs().idxmin()
                self.aTextEdit_eu.setText(str(round(popt[0], 50)))
                self.bTextEdit_eu.setText(str(round(popt[1], 50)))
                self.b1TextEdit_eu.setText(str(round(popt[2], 50)))
                self.cTextEdit_eu.setText(str(round(popt[3], 50)))
                self.dTextEdit_eu.setText(str(round(popt[4], 50)))
                self.eTextEdit_eu.setText(str(round(popt[5], 50)))
                self.fTextEdit_eu.setText(str(round(popt[6], 50)))
                self.fdTextEdit_eu.setText(str(round(popt[7], 50)))
                if self.fix_swelling_eu.isChecked():
                    dfall_23 = dfall[dfall["t"] == 296]
                    dfall_35 = dfall[dfall["t"] == 308]
                    dfall_40 = dfall[dfall["t"] == 313]
                    dfall_45 = dfall[dfall["t"] == 318]
                    ax.plot(df2.x, result0, 'blue', label='23도')
                    ax.plot(df2.x, result1, 'orange', label='35도')
                    ax.plot(df2.x, result2, 'pink', label='40도/ R^2 = %5.4f' % r_squared)
                    ax.plot(df2.x, result3, 'red', label='45도/' + namelist[-2])
                    ax.plot(dfall_23.x, dfall_23.y, 'o', color='blue', markersize=2)
                    ax.plot(dfall_35.x, dfall_35.y, 'o', color='orange', markersize=2)
                    ax.plot(dfall_40.x, dfall_40.y, 'o', color='pink', markersize=2)
                    ax.plot(dfall_45.x, dfall_45.y, 'o', color='red', markersize=2)
                else:
                    dfall_23 = dfall[dfall["t"] == 296]
                    dfall_35 = dfall[dfall["t"] == 308]
                    dfall_45 = dfall[dfall["t"] == 318]
                    ax.plot(df2.x, result1, 'blue', label='23도/R^2 = %5.4f' % r_squared)
                    ax.plot(df2.x, result2, 'orange', label='35도/' + namelist[-2])
                    ax.plot(df2.x, result3, 'red', label='45도/' + str(eol_cycle))
                    ax.plot(dfall_23.x, dfall_23.y, 'o', color='blue', markersize=2)
                    ax.plot(dfall_35.x, dfall_35.y, 'o', color='orange', markersize=2)
                    ax.plot(dfall_45.x, dfall_45.y, 'o', color='red', markersize=2)
                graph_eu_set(ax, y_min, y_max)
                plt.suptitle('fit: a=%5.4f, b=%5.4f, b1=%5.4f, c=%5.4f, d=%5.4f, e=%5.4f, f=%5.4f, f_d=%5.4f' % tuple(popt), fontsize= 14)
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                # 데이터 저장
                result0 = df2.x
                if self.fix_swelling_eu.isChecked():
                    result = pd.DataFrame({"x": result0, str(df2.t1 - 273): result1, "40": result2, "45": result3})
                else:
                    result = pd.DataFrame({"x": result0, str(df2.t1 - 273): result1, "35": result2, "45": result3})
                result_para = pd.DataFrame({"para": popt})
                if self.saveok.isChecked() and save_file_name:
                    result_para.to_excel(writer, sheet_name="parameter", index=False)
                    result.to_excel(writer, sheet_name=str(namelist[-2][:30]), index=False)
                tab_layout.addWidget(toolbar)
                tab_layout.addWidget(canvas)
                filename =filepath.split(".t")[-2].split("/")[-1].split("\\")[-1]
                self.cycle_simul_tab_eu.addTab(tab, filename)
                self.cycle_simul_tab_eu.setCurrentWidget(tab)
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()
    
    def eu_constant_fitting_confirm_button(self):
        global writer
        # exp 열화 모드 - parameter 고정 후 가속 계수 확인
        def cyccapparameter(x, f_d):
            return 1 - np.exp(a_par1 * x[1] + b_par1) * (x[0] * f_d) ** b1_par1 - np.exp(c_par1 * x[1] + d_par1) * (
                x[0] * f_d) ** (e_par1 * x[1] + f_par1)
        def cycswellingparameter(x, f_d):
            return np.exp(a_par1 * x[1] + b_par1) * (x[0] * f_d) ** b1_par1 + np.exp(c_par1 * x[1] + d_par1) * (
                x[0] * f_d) ** (e_par1 * x[1] + f_par1)
        
        if self.aTextEdit_eu.text() == "":
            parini1 = [0.03, -18, 0.7, 2.3, -782, -0.28, 96, 1]
            self.aTextEdit_eu.setText(str(parini1[0]))
            self.bTextEdit_eu.setText(str(parini1[1]))
            self.b1TextEdit_eu.setText(str(parini1[2]))
            self.cTextEdit_eu.setText(str(parini1[3]))
            self.dTextEdit_eu.setText(str(parini1[4]))
            self.eTextEdit_eu.setText(str(parini1[5]))
            self.fTextEdit_eu.setText(str(parini1[6]))
            self.fdTextEdit_eu.setText(str(parini1[7]))
        
        # UI 변수를 초기치로 산정
        a_par1 = float(self.aTextEdit_eu.text())
        b_par1 = float(self.bTextEdit_eu.text())
        b1_par1 = float(self.b1TextEdit_eu.text())
        c_par1 = float(self.cTextEdit_eu.text())
        d_par1 = float(self.dTextEdit_eu.text())
        e_par1 = float(self.eTextEdit_eu.text())
        f_par1 = float(self.fTextEdit_eu.text())
        fd_par1 = float(self.fdTextEdit_eu.text())
        self.xscale = int(self.simul_x_max_eu.text())
        y_max = float(self.simul_y_max_eu.text())
        y_min = float(self.simul_y_min_eu.text())
        # 결과 온도 관련
        temp = [23, 28, 35, 40, 45]
        # parameter 계산 및 fd 산정
        root = Tk()
        root.withdraw()
        datafilepath = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        if datafilepath:
            self.cycparameter_eu.setText(str(datafilepath[0]))
        file = 0
        num = 0
        writerowno = 0
        result = pd.DataFrame()
        raw_all = pd.DataFrame()
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        # 3열 데이터 연결, 절대온도 변환, max 1로 변경
        for filepath in datafilepath:
            # tab 그래프 추가
            fig, ax = plt.subplots(figsize=(6, 6))
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout(tab)
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, None)
            dfall = pd.DataFrame({'x': [], 't': [], 'y': []})
            df = pd.read_csv(filepath, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
            if not "02C" in df.columns:
                const_namelist = filepath.split("/")
                filemax = len(datafilepath)
                file = file + 1
                first_column_name = df.columns[1]
                if isinstance(first_column_name, str) and first_column_name.isdigit():
                    for i in range(1, len(df.columns)):
                        y1 = df.iloc[:,i]
                        x1 = df.iloc[:len(y1),0]
                        # 초기값으로 100분율 환산
                        dataadd = pd.DataFrame({'x': x1, 'y': y1})
                        dataadd = dataadd.dropna()
                        if df.iloc[0, i] != 0:
                            x_0 = dataadd.iloc[0,0]
                            x_1 = dataadd.iloc[1,0]
                            y_0 = dataadd.iloc[0,1]
                            y_1 = dataadd.iloc[1,1]
                            coefficients = np.polyfit([x_0, x_1], [y_0, y_1], 1)
                            polynomial = np.poly1d(coefficients)
                            y_max_cap = polynomial(1)
                            if not self.fix_swelling_eu.isChecked():
                                dataadd.y = dataadd.y/y_max_cap
                        raw_all = pd.concat([dataadd, raw_all], axis=1)
                        dataadd['t'] = float(df.columns[i][:2])
                        if dataadd.t.max() < 273:
                            dataadd.t = dataadd.t + 273
                        # 전체 dataframe을 누적
                        dfall = dfall._append(dataadd)
                        progressdata = (file + 1 + num/len(list(df)))/filemax * 100
                        self.progressBar.setValue(int(progressdata))
                else:
                    for i in range(0, len(df.columns)):
                        num = num + 1
                        if i % 3 == 2:
                            y1 = df.iloc[:, i]
                            x1 = df.iloc[:, i - 2][:len(y1)]
                            # if df.iloc[0, i] != 0:
                            #     y1 = y1/df.iloc[0, i]
                            # 초기값으로 100분율 환산
                            if df.iloc[0, i] != 0:
                                x_0 = x1[0]
                                x_1 = x1[1]
                                y_0 = y1[0]
                                y_1 = y1[1]
                                coefficients = np.polyfit([x_0, x_1], [y_0, y_1], 1)
                                polynomial = np.poly1d(coefficients)
                                y_max_cap = polynomial(1)
                                if not self.fix_swelling_eu.isChecked():
                                    y1 = y1/y_max_cap
                            t1 = df.iloc[:, i - 1][:len(y1)]
                            if t1.max() < 273:
                                t1 = t1 + 273
                            dataadd = pd.DataFrame({'x': x1, 't': t1, 'y': y1})
                            raw_all = pd.concat([dfall, raw_all], axis=1)
                            dfall = dfall._append(dataadd)
                            progressdata = (file + 1 + num/len(list(df)))/filemax * 100
                            self.progressBar.setValue(int(progressdata))
                dfall = dfall.dropna()
                maxfevset = 5000
                p0 = [fd_par1]
                df2 = pd.DataFrame({'x': range(1, self.xscale, 1)})
                # if self.fix_swelling_eu.isChecked():
                df2.t1 = temp[0] + 273
                df2.t2 = temp[1] + 273
                df2.t3 = temp[2] + 273
                df2.t4 = temp[3] + 273
                df2.t5 = temp[4] + 273
                try:
                    if self.fix_swelling_eu.isChecked():
                        popt, pcov = curve_fit(cycswellingparameter, (dfall.x, dfall.t), dfall.y, p0, maxfev=maxfevset)
                    else:
                        popt, pcov = curve_fit(cyccapparameter, (dfall.x, dfall.t), dfall.y, p0, maxfev=maxfevset)
                except (RuntimeError, TypeError) as e:
                    continue
                if self.fix_swelling_eu.isChecked():
                    residuals = dfall.y -cycswellingparameter((dfall.x, dfall.t), *popt)
                else:
                    residuals = dfall.y -cyccapparameter((dfall.x, dfall.t), *popt)
                ss_res = np.sum(residuals ** 2)
                ss_tot = np.sum((dfall.y - np.mean(dfall.y)) ** 2)
                r_squared = 1 - (ss_res/ss_tot)
                if self.fix_swelling_eu.isChecked():
                    result1 = cycswellingparameter((df2.x, df2.t1), *popt)
                    result2 = cycswellingparameter((df2.x, df2.t2), *popt)
                    result3 = cycswellingparameter((df2.x, df2.t3), *popt)
                    result4 = cycswellingparameter((df2.x, df2.t4), *popt)
                    result5 = cycswellingparameter((df2.x, df2.t5), *popt)
                    eol_cycle1 = (0.08 - result1).abs().idxmin()
                    eol_cycle2 = (0.08 - result2).abs().idxmin()
                    eol_cycle3 = (0.08 - result3).abs().idxmin()
                    eol_cycle4 = (0.08 - result4).abs().idxmin()
                    eol_cycle5 = (0.08 - result5).abs().idxmin()
                else:
                    result1 = cyccapparameter((df2.x, df2.t1), *popt)
                    result2 = cyccapparameter((df2.x, df2.t2), *popt)
                    result3 = cyccapparameter((df2.x, df2.t3), *popt)
                    result4 = cyccapparameter((df2.x, df2.t4), *popt)
                    result5 = cyccapparameter((df2.x, df2.t5), *popt)
                    eol_cycle1 = (result1 - 0.8).abs().idxmin()
                    eol_cycle2 = (result2 - 0.8).abs().idxmin()
                    eol_cycle3 = (result3 - 0.8).abs().idxmin()
                    eol_cycle4 = (result4 - 0.8).abs().idxmin()
                    eol_cycle5 = (result5 - 0.8).abs().idxmin()
                r_square_label = 'R^2 = %5.4f' % r_squared
                self.fdTextEdit_eu_2.setText(str(round(popt[0], 50)))
                filename = filepath.split(".t")[-2].split("/")[-1].split("\\")[-1]
                dfall_1 = dfall[dfall["t"] == temp[0] + 273]
                dfall_2 = dfall[dfall["t"] == temp[1] + 273]
                dfall_3 = dfall[dfall["t"] == temp[2] + 273]
                dfall_4 = dfall[dfall["t"] == temp[3] + 273]
                dfall_5 = dfall[dfall["t"] == temp[4] + 273]
                ax.plot(df2.x, result1, 'b-', label= str(temp[0]) + ' / ' + str(eol_cycle1))
                ax.plot(df2.x, result2, 'g-', label= str(temp[1]) + ' / ' + str(eol_cycle2))
                ax.plot(df2.x, result3, 'orange', label= str(temp[2]) + ' / ' + str(eol_cycle3))
                ax.plot(df2.x, result4, 'pink', label= str(temp[3]) + ' / ' + str(eol_cycle4) + '/R^2 = %5.4f' % r_squared)
                ax.plot(df2.x, result5, 'r-', label= str(temp[4]) + ' / ' + str(eol_cycle5) + '/가속 = %5.3f' % tuple(popt[0] / p0))
                if not dfall_1.empty:
                    ax.plot(dfall_1.x, dfall_1.y, 'o', color='blue', markersize=1)
                if not dfall_2.empty:
                    ax.plot(dfall_2.x, dfall_2.y, 'o', color='green', markersize=1)
                if not dfall_3.empty:
                    ax.plot(dfall_3.x, dfall_3.y, 'o', color='orange', markersize=1)
                if not dfall_4.empty:
                    ax.plot(dfall_4.x, dfall_4.y, 'o', color='pink', markersize=1)
                if not dfall_5.empty:
                    ax.plot(dfall_5.x, dfall_5.y, 'o', color='red', markersize=1)
                graph_eu_set(ax, y_min, y_max)
                plt.suptitle(filename, fontsize= 14, fontweight='bold')
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                # 데이터 저장
                result0 = df2.x
                # if self.fix_swelling_eu.isChecked():
                result = pd.DataFrame({"x": result0, str(df2.t1 - 273): result1, str(df2.t2 - 273): result2, str(df2.t3 - 273): result3,
                                        str(df2.t4 - 273): result4, str(df2.t5 - 273): result5})
                result_para = pd.DataFrame({"para": popt})
                if self.saveok.isChecked() and save_file_name:
                    output_data(result_para, "parameter", writerowno + 1, 1, "para", [const_namelist[-1]])
                    writerowno = writerowno + 1
                    result.to_excel(writer, sheet_name="estimation", index=False)
                    raw_all.to_excel(writer, sheet_name="raw", index=False)
                tab_layout.addWidget(toolbar)
                tab_layout.addWidget(canvas)
                self.cycle_simul_tab_eu.addTab(tab, filename)
                self.cycle_simul_tab_eu.setCurrentWidget(tab)
                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        if self.saveok.isChecked() and save_file_name:
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()

    def eu_indiv_constant_fitting_confirm_button(self):
        global writer
        # exp 열화 모드 - parameter 고정 후 가속 계수 확인
        def cyccapparameter(x, f_d):
            return 1 - np.exp(a_par1 * x[1] + b_par1) * (x[0] * f_d) ** b1_par1 - np.exp(c_par1 * x[1] + d_par1) * (
                x[0] * f_d) ** (e_par1 * x[1] + f_par1)
        
        if self.aTextEdit_eu.text() == "":
            parini1 = [0.03, -18, 0.7, 2.3, -782, -0.28, 96, 1]
            self.aTextEdit_eu.setText(str(parini1[0]))
            self.bTextEdit_eu.setText(str(parini1[1]))
            self.b1TextEdit_eu.setText(str(parini1[2]))
            self.cTextEdit_eu.setText(str(parini1[3]))
            self.dTextEdit_eu.setText(str(parini1[4]))
            self.eTextEdit_eu.setText(str(parini1[5]))
            self.fTextEdit_eu.setText(str(parini1[6]))
            self.fdTextEdit_eu.setText(str(parini1[7]))
        
        # UI 변수를 초기치로 산정
        a_par1 = float(self.aTextEdit_eu.text())
        b_par1 = float(self.bTextEdit_eu.text())
        b1_par1 = float(self.b1TextEdit_eu.text())
        c_par1 = float(self.cTextEdit_eu.text())
        d_par1 = float(self.dTextEdit_eu.text())
        e_par1 = float(self.eTextEdit_eu.text())
        f_par1 = float(self.fTextEdit_eu.text())
        fd_par1 = float(self.fdTextEdit_eu.text())
        self.xscale = int(self.simul_x_max_eu.text())
        y_max = float(self.simul_y_max_eu.text())
        y_min = float(self.simul_y_min_eu.text())
        # parameter 계산 및 fd 산정
        root = Tk()
        root.withdraw()
        datafilepath = filedialog.askopenfilenames(initialdir="d://", title="Choose Test files")
        if datafilepath:
            self.cycparameter_eu.setText(str(datafilepath[0]))
        file = 0
        num = 0
        writerowno = 0
        eol_cycle = 0
        result_all = pd.DataFrame()
        raw_all = pd.DataFrame()
        if self.saveok.isChecked():
            save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            if save_file_name:
                writer = pd.ExcelWriter(save_file_name, engine="xlsxwriter")
        # 3열 데이터 연결, 절대온도 변환, max 1로 변경
        for filepath in datafilepath:
            # tab 그래프 추가
            fig, ax = plt.subplots(figsize=(6, 6))
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout(tab)
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, None)
            dfall = pd.DataFrame({'x': [], 't': [], 'y': []})
            df = pd.read_csv(filepath, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
            if not "02C" in df.columns:
                const_namelist = filepath.split("/")
                filemax = len(datafilepath)
                file = file + 1
                first_column_name = df.columns[1]
                if isinstance(first_column_name, str) and first_column_name.isdigit():
                    for i in range(1, len(df.columns)):
                        y1 = df.iloc[:,i]
                        x1 = df.iloc[:len(y1),0]
                        # 초기값으로 100분율 환산
                        dataadd = pd.DataFrame({'x': x1, 'y': y1})
                        dataadd = dataadd.dropna()
                        if df.iloc[0, i] != 0 and len(y1)!= 0:
                            x_0 = dataadd.iloc[0,0]
                            x_1 = dataadd.iloc[1,0]
                            y_0 = dataadd.iloc[0,1]
                            y_1 = dataadd.iloc[1,1]
                            coefficients = np.polyfit([x_0, x_1], [y_0, y_1], 1)
                            polynomial = np.poly1d(coefficients)
                            y_max_cap = polynomial(1)
                            dataadd.y = dataadd.y/y_max_cap
                        raw_all = pd.concat([dataadd, raw_all], axis=1)
                        dataadd['t'] = float(df.columns[i][:2])
                        if dataadd.t.max() < 273:
                            dataadd.t = dataadd.t + 273
                        progressdata = (file + 1 + num/len(list(df)))/filemax * 100
                        dfall = dfall._append(dataadd)
                        self.progressBar.setValue(int(progressdata))
                        if dataadd.t.max() == 296:
                            dfall = dfall[dfall.t == 296]
                            dfall = dfall.dropna()
                            maxfevset = 5000
                            p0 = [fd_par1]
                            df2 = pd.DataFrame({'x': range(1, self.xscale, 1)})
                            df2.t1 = 23 + 273
                            popt, pcov = curve_fit(cyccapparameter, (dfall.x, dfall.t), dfall.y, p0, maxfev=maxfevset)
                            residuals = dfall.y - cyccapparameter((dfall.x, dfall.t), *popt)
                            ss_res = np.sum(residuals ** 2)
                            ss_tot = np.sum((dfall.y - np.mean(dfall.y)) ** 2)
                            r_squared = 1 - (ss_res/ss_tot)
                            result1 = cyccapparameter((df2.x, df2.t1), *popt)
                            eol_cycle = (result1 - 0.8).abs().idxmin()
                            r_square_label = 'R^2 = %5.4f' % r_squared
                            acc_const = round(popt[0]/p0[0], 3)
                            self.fdTextEdit_eu.setText(str(round(popt[0], 50)))
                            filename = filepath.split(".t")[-2].split("/")[-1].split("\\")[-1]
                            ax.plot(df2.x, result1, label=r_square_label + ' / ' + str(eol_cycle) + ' / ' + str(acc_const))
                            ax.plot(dfall.x, dfall.y, 'o', color='blue', markersize=3)
                            plt.suptitle(filename, fontsize= 14, fontweight='bold')
                            graph_eu_set(ax, y_min, y_max)
                            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                            # 데이터 저장
                            result0 = df2.x
                            result = pd.DataFrame({"x": result0, str(df2.t1 - 273): result1})
                            result_all = pd.concat([result_all, result], axis=1)
                            result_para = pd.DataFrame({"para": popt})
                            if self.saveok.isChecked() and save_file_name:
                                output_data(result_para, "parameter", writerowno + 1, 1, "para", [const_namelist[-1]])
                                writerowno = writerowno + 1
                            tab_layout.addWidget(toolbar)
                            tab_layout.addWidget(canvas)
                            self.cycle_simul_tab_eu.addTab(tab, filename)
                            self.cycle_simul_tab_eu.setCurrentWidget(tab)
                            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                else:
                    for i in range(0, len(df.columns)):
                        num = num + 1
                        if i % 3 == 2:
                            y1 = df.iloc[:, i]
                            x1 = df.iloc[:, i - 2][:len(y1)]
                            # 초기값으로 100분율 환산
                            if df.iloc[0, i] != 0:
                                x_0 = x1[0]
                                x_1 = x1[1]
                                y_0 = y1[0]
                                y_1 = y1[1]
                                coefficients = np.polyfit([x_0, x_1], [y_0, y_1], 1)
                                polynomial = np.poly1d(coefficients)
                                y_max_cap = polynomial(1)
                                y1 = y1/y_max_cap
                            t1 = df.iloc[:, i - 1][:len(y1)]
                            if t1.max() < 273:
                                t1 = t1 + 273
                            dfall = pd.DataFrame({'x': x1, 't': t1, 'y': y1})
                            progressdata = (file + 1 + num/len(list(df)))/filemax * 100
                            raw_all = pd.concat([dfall, raw_all], axis=1)
                            self.progressBar.setValue(int(progressdata))
                            if t1.max() == 296:
                                dfall = dfall[dfall.t == 296]
                                dfall = dfall.dropna()
                                maxfevset = 5000
                                p0 = [fd_par1]
                                df2 = pd.DataFrame({'x': range(1, self.xscale, 1)})
                                df2.t1 = 23 + 273
                                popt, pcov = curve_fit(cyccapparameter, (dfall.x, dfall.t), dfall.y, p0, maxfev=maxfevset)
                                residuals = dfall.y - cyccapparameter((dfall.x, dfall.t), *popt)
                                ss_res = np.sum(residuals ** 2)
                                ss_tot = np.sum((dfall.y - np.mean(dfall.y)) ** 2)
                                r_squared = 1 - (ss_res/ss_tot)
                                result1 = cyccapparameter((df2.x, df2.t1), *popt)
                                eol_cycle = min(eol_cycle, (result1 - 0.8).abs().idxmin())
                                r_square_label = 'R^2 = %5.4f' % r_squared
                                acc_const = round(popt[0]/p0[0], 3)
                                self.fdTextEdit_eu_2.setText(str(round(popt[0], 50)))
                                filename = filepath.split(".t")[-2].split("/")[-1].split("\\")[-1]
                                ax.plot(df2.x, result1, label=r_square_label + ' / ' + str(eol_cycle) + ' / ' + str(acc_const))
                                ax.plot(dfall.x, dfall.y, 'o', color='blue', markersize=3)
                                graph_eu_set(ax, y_min, y_max)
                                plt.suptitle(filename, fontsize= 14, fontweight='bold')
                                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
                                # 데이터 저장
                                result0 = df2.x
                                result = pd.DataFrame({"x": result0, str(df2.t1 - 273): result1})
                                result_all = pd.concat([result_all, result], axis=1)
                                result_para = pd.DataFrame({"para": popt})
                                if self.saveok.isChecked() and save_file_name:
                                    output_data(result_para, "parameter", writerowno + 1, 1, "para", [const_namelist[-1]])
                                    writerowno = writerowno + 1
                                tab_layout.addWidget(toolbar)
                                tab_layout.addWidget(canvas)
                                self.cycle_simul_tab_eu.addTab(tab, filename)
                                self.cycle_simul_tab_eu.setCurrentWidget(tab)
                                plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        if self.saveok.isChecked() and save_file_name:
            result_all.to_excel(writer, sheet_name="estimation", index=False)
            raw_all.to_excel(writer, sheet_name="raw", index=False)
            writer.close()
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
        plt.close()

    def simulation_tab_reset_confirm_button(self):
        self.tab_delete(self.real_cycle_simul_tab)
        self.tab_no = 0
    
    def simulation_confirm_button(self):
        def BaseEquation(a_par, b_par, fd, b1_par, c_par, d_par, e_par, f_par, temp_par, so_par, x):
            return np.exp(a_par * temp_par + b_par) * (x * fd) ** b1_par + np.exp( c_par * temp_par + d_par) * (x * fd) ** (
                e_par * temp_par + f_par) - so_par
        # exp-열화모드, parameter 고정 후 열화 parameter 계산 (각각에 soh와 soir을 빼서 수식을 0에 맞춤)
        def cyccapparameter(x):
            return (1 - BaseEquation(a_par1, b_par1, cycle_cap_simul_fd, b1_par1, c_par1, d_par1, e_par1, f_par1, cycle_temp, (-1) * soh, x))
        def cycirparameter(x):
            return BaseEquation(a_par3, b_par3, cycle_dcir_simul_fd, b1_par3, c_par3, d_par3, e_par3, f_par3, cycle_temp, soir, x)
        # parameter 고정 후 열화 parameter 계산
        def stgcapparameter(x):
            return (1 - BaseEquation(a_par2, b_par2, storage2_cap_simul_fd, b1_par2, c_par2, d_par2, e_par2, f_par2, storage_temp2, (-1) * soh, x))
        def stgirparameter(x):
            return BaseEquation(a_par4, b_par4, storage2_dcir_simul_fd, b1_par4, c_par4, d_par4, e_par4, f_par4, storage_temp2, soir, x)
        def stgcapparameter2(x):
            return (1 - BaseEquation(a_par2, b_par2, storage1_cap_simul_fd, b1_par2, c_par2, d_par2, e_par2, f_par2, storage_temp1, (-1) * soh, x))
        def stgirparameter2(x):
            return BaseEquation(a_par4, b_par4, storage1_dcir_simul_fd, b1_par4, c_par4, d_par4, e_par4, f_par4, storage_temp1, soir, x)
        # parameter 계산 및 fd 산정
        root = Tk()
        root.withdraw()
        # parameter folder 지정
        dirname = filedialog.askdirectory(initialdir="d://parameter", title="Choose Test Folders") 
        self.capparameterload_path.setText(dirname)
        # 용량 parameter 설정
        if os.path.isfile(dirname + "//para_cyccapparameter.txt"):
            df_cyc = pd.read_csv(dirname + "//para_cyccapparameter.txt", sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
        if os.path.isfile(dirname + "/para_stgcapparameter.txt"):
            df_stg = pd.read_csv(dirname + "//para_stgcapparameter.txt", sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
        if os.path.isfile(dirname + "//para_capparameter.txt"):
            df_par = pd.read_csv(dirname + "//para_capparameter.txt", sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
        # 저항 parameter 설정
        if os.path.isfile(dirname + "//para_cycirparameter.txt"):
            df_cyc2 = pd.read_csv(dirname + "//para_cycirparameter.txt", sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
        if os.path.isfile(dirname + "//para_stgirparameter.txt"):
            df_stg2 = pd.read_csv(dirname + "//para_stgirparameter.txt", sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
        if os.path.isfile(dirname + "//para_irparameter.txt"):
            df_par2 = pd.read_csv(dirname + "//para_irparameter.txt", sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
        self.aTextEdit.setText(str(round(df_par.iloc[0, 0], 50)))
        self.bTextEdit.setText(str(round(df_par.iloc[1, 0], 50)))
        self.b1TextEdit.setText(str(round(df_par.iloc[2, 0], 50)))
        self.cTextEdit.setText(str(round(df_par.iloc[3, 0], 50)))
        self.dTextEdit.setText(str(round(df_par.iloc[4, 0], 50)))
        self.eTextEdit.setText(str(round(df_par.iloc[5, 0], 50)))
        self.fTextEdit.setText(str(round(df_par.iloc[6, 0], 50)))
        self.fdTextEdit.setText(str(round(df_par.iloc[7, 0], 50)))
        self.aTextEdit_2.setText(str(round(df_par.iloc[0, 1], 50)))
        self.bTextEdit_2.setText(str(round(df_par.iloc[1, 1], 50)))
        self.b1TextEdit_2.setText(str(round(df_par.iloc[2, 1], 50)))
        self.cTextEdit_2.setText(str(round(df_par.iloc[3, 1], 50)))
        self.dTextEdit_2.setText(str(round(df_par.iloc[4, 1], 50)))
        self.eTextEdit_2.setText(str(round(df_par.iloc[5, 1], 50)))
        self.fTextEdit_2.setText(str(round(df_par.iloc[6, 1], 50)))
        self.fdTextEdit_2.setText(str(round(df_par.iloc[7, 1], 50)))
        self.aTextEdit_3.setText(str(round(df_par2.iloc[0, 0], 50)))
        self.bTextEdit_3.setText(str(round(df_par2.iloc[1, 0], 50)))
        self.b1TextEdit_3.setText(str(round(df_par2.iloc[2, 0], 50)))
        self.cTextEdit_3.setText(str(round(df_par2.iloc[3, 0], 50)))
        self.dTextEdit_3.setText(str(round(df_par2.iloc[4, 0], 50)))
        self.eTextEdit_3.setText(str(round(df_par2.iloc[5, 0], 50)))
        self.fTextEdit_3.setText(str(round(df_par2.iloc[6, 0], 50)))
        self.fdTextEdit_3.setText(str(round(df_par2.iloc[7, 0], 50)))
        self.aTextEdit_4.setText(str(round(df_par2.iloc[0, 1], 50)))
        self.bTextEdit_4.setText(str(round(df_par2.iloc[1, 1], 50)))
        self.b1TextEdit_4.setText(str(round(df_par2.iloc[2, 1], 50)))
        self.cTextEdit_4.setText(str(round(df_par2.iloc[3, 1], 50)))
        self.dTextEdit_4.setText(str(round(df_par2.iloc[4, 1], 50)))
        self.eTextEdit_4.setText(str(round(df_par2.iloc[5, 1], 50)))
        self.fTextEdit_4.setText(str(round(df_par2.iloc[6, 1], 50)))
        self.fdTextEdit_4.setText(str(round(df_par2.iloc[7, 1], 50)))
        a_par1 = float(self.aTextEdit.text())
        b_par1 = float(self.bTextEdit.text())
        b1_par1 = float(self.b1TextEdit.text())
        c_par1 = float(self.cTextEdit.text())
        d_par1 = float(self.dTextEdit.text())
        e_par1 = float(self.eTextEdit.text())
        f_par1 = float(self.fTextEdit.text())
        a_par2 = float(self.aTextEdit_2.text())
        b_par2 = float(self.bTextEdit_2.text())
        b1_par2 = float(self.b1TextEdit_2.text())
        c_par2 = float(self.cTextEdit_2.text())
        d_par2 = float(self.dTextEdit_2.text())
        e_par2 = float(self.eTextEdit_2.text())
        f_par2 = float(self.fTextEdit_2.text())
        a_par3 = float(self.aTextEdit_3.text())
        b_par3 = float(self.bTextEdit_3.text())
        b1_par3 = float(self.b1TextEdit_3.text())
        c_par3 = float(self.cTextEdit_3.text())
        d_par3 = float(self.dTextEdit_3.text())
        e_par3 = float(self.eTextEdit_3.text())
        f_par3 = float(self.fTextEdit_3.text())
        a_par4 = float(self.aTextEdit_4.text())
        b_par4 = float(self.bTextEdit_4.text())
        b1_par4 = float(self.b1TextEdit_4.text())
        c_par4 = float(self.cTextEdit_4.text())
        d_par4 = float(self.dTextEdit_4.text())
        e_par4 = float(self.eTextEdit_4.text())
        f_par4 = float(self.fTextEdit_4.text())
        # 입력 condition
        all_input_data_path = filedialog.askopenfilenames(initialdir = dirname, title="Choose Test files")
        # while self.real_cycle_simul_tab.count() > 0:
        #     self.real_cycle_simul_tab.removeTab(0)
        for input_data_path in all_input_data_path:
            fig, ((axe1, axe4), (axe2, axe5)) = plt.subplots(nrows=2, ncols=2, figsize=(12, 9))
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout(tab)
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, None)
            if input_data_path != "":
                input_data = pd.read_csv(input_data_path, sep="\t", engine="c", encoding="UTF-8", skiprows=1, on_bad_lines='skip')
                # 장수명
                self.txt_longcycleno.setText(str(input_data.iloc[0, 1]))
                self.txt_longcyclevol.setText(str(input_data.iloc[1, 1]))
                self.txt_relcap.setText(str(input_data.iloc[2, 1]))
                # 사이클
                self.xaxixTextEdit.setText(str(int(input_data.iloc[3, 1])))
                self.UsedCapTextEdit.setText(str(input_data.iloc[4, 1]))
                self.DODTextEdit.setText(str(input_data.iloc[5, 1]))
                # 충전 조건
                self.CrateTextEdit.setText(str(input_data.iloc[6, 1]))
                self.SOCTextEdit.setText(str(input_data.iloc[7, 1]))
                self.DcrateTextEdit.setText(str(input_data.iloc[8, 1]))
                self.TempTextEdit.setText(str(input_data.iloc[9, 1]))
                # 저장
                self.SOCTextEdit_3.setText(str(input_data.iloc[10, 1]))
                self.TempTextEdit_3.setText(str(input_data.iloc[11, 1]))
                self.RestTextEdit_2.setText(str(input_data.iloc[12, 1]))
                # 저장2
                self.SOCTextEdit_2.setText(str(input_data.iloc[13, 1]))
                self.TempTextEdit_2.setText(str(input_data.iloc[14, 1]))
                self.RestTextEdit.setText(str(input_data.iloc[15, 1]))
            # SaveFileName set-up
            if self.saveok.isChecked():
                save_file_name = filedialog.asksaveasfilename(initialdir="D://", title="Save File Name", defaultextension=".xlsx")
            # cycle 인자
            self.xscale = int(self.xaxixTextEdit.text())
            cycle_crate = float(self.CrateTextEdit.text())
            cycle_dcrate = float(self.DcrateTextEdit.text())
            cycle_soc = float(self.SOCTextEdit.text())
            cycle_dod = float(self.DODTextEdit.text())
            cycle_temp = float(self.TempTextEdit.text()) + 273
            # 저장1 인자
            storage_temp1 = float(self.TempTextEdit_3.text()) + 273
            storage_rest1 = float(self.RestTextEdit_2.text())
            storage_soc1 = float(self.SOCTextEdit_3.text())
            # 저장2 인자
            storage_temp2 = float(self.TempTextEdit_2.text()) + 273
            storage_rest2 = float(self.RestTextEdit.text())
            storage_soc2 = float(self.SOCTextEdit_2.text())
            usedcap = float(self.UsedCapTextEdit.text())
            cycle, time, soh, soir = 0, 0, 1, 0
            degree_storage1_cap = 0
            degree_storage1_dcir = 0
            degree_storage2_cap = 0
            degree_storage2_dcir = 0
            storagecycle = 0
            stgcountratio = float(self.txt_storageratio.text())
            stgcountratio2 = float(self.txt_storageratio2.text())
            result = pd.DataFrame(
                {"cycle": 0,
                "time": 0,
                "storagecycle": 0,
                "degree_cycle_cap": 0,
                "degree_storage1_cap": 0,
                "degree_storage2_cap": 0,
                "degree_cycle_dcir": 0,
                "degree_storage1_dcir": 0,
                "degree_storage2_dcir": 0,
                "SOH": 1,
                "rSOH": 1,
                "SOIR": 0},
                index=[0])
            for i in range(0, 100000):
                if self.nolonglife.isChecked():
                    # 장수명 미적용
                    cycle_soc_cal = cycle_soc
                    storage_soc1_cal = storage_soc1
                    storage_soc2_cal = storage_soc2
                    long_cycle = list(map(int, (self.txt_longcycleno.text().split())))
                    long_cycle_vol = list(map(float, (self.txt_longcyclevol.text().split())))
                    real_cap = list(map(float, (self.txt_relcap.text().split())))
                    cycle_soc_cal = cycle_soc - long_cycle_vol[0]
                    storage_soc1_cal = storage_soc1 - long_cycle_vol[0]
                    storage_soc2_cal = storage_soc2 - long_cycle_vol[0]
                    para_rsoh = real_cap[0]/100
                elif self.hhp_longlife.isChecked():
                    # 장수명 적용 parameter
                    long_cycle = list(map(int, (self.txt_longcycleno.text().split())))
                    long_cycle_vol = list(map(float, (self.txt_longcyclevol.text().split())))
                    real_cap = list(map(float, (self.txt_relcap.text().split())))
                    # 장수명 적용 시 전압 변화, 실용량 변화 산정
                    # compare to long cycle and storge cycle
                    if storagecycle > cycle:
                        complexcycle = storagecycle 
                    else:
                        complexcycle = cycle
                    # 장수명 마지막 스텝
                    cycle_soc_cal = cycle_soc - long_cycle_vol[len(long_cycle) - 1]
                    storage_soc1_cal = storage_soc1 - long_cycle_vol[len(long_cycle) - 1]
                    storage_soc2_cal = storage_soc2 - long_cycle_vol[len(long_cycle) - 1]
                    para_rsoh = real_cap[len(long_cycle) - 1] / 100
                    # 사이클에 따른 장수명 계산
                    for cyc_i in range(0, len(long_cycle) - 1):
                        if (complexcycle >= long_cycle[cyc_i]) and (complexcycle <= long_cycle[cyc_i + 1]):
                            cycle_soc_cal = cycle_soc - long_cycle_vol[cyc_i]
                            storage_soc1_cal = storage_soc1 - long_cycle_vol[cyc_i]
                            storage_soc2_cal = storage_soc2 - long_cycle_vol[cyc_i]
                            para_rsoh = real_cap[cyc_i]/100
                # 사이클 Fd 구하기 (타펠식, 아레니우스식의 복합식 사용) - 용량/저항, 기준 fd를 base로 가속비를 곱해서 계산
                if "df_cyc" in locals():
                    cycle_cap_simul_fd = (df_cyc.Crate[0] * cycle_crate + df_cyc.Crate[1]) * (df_cyc.SOC[0] * cycle_soc_cal + df_cyc.SOC[1]) * (
                        df_cyc.DOD[0] * cycle_dod + df_cyc.DOD[1]) * (df_cyc.fd[0])
                    cycle_dcir_simul_fd = (df_cyc2.Crate[0] * cycle_crate + df_cyc2.Crate[1]) * (df_cyc2.SOC[0] * cycle_soc_cal + df_cyc2.SOC[1]) * (
                        df_cyc2.DOD[0] * cycle_dod + df_cyc2.DOD[1]) * (df_cyc2.fd[0])
                else:
                    err_msg('파일 or 경로없음!!','Check condition file !!')
                    return
                if "df_stg" in locals():
                    # 저장1 Fd 구하기 (Tafel식 사용 delta E = a ln i) - 용량/저항, 직접 fd를 산출
                    storage1_cap_simul_fd = np.exp(df_stg.iloc[0, 0] * storage_soc1_cal + df_stg.iloc[1, 0])
                    storage1_dcir_simul_fd = np.exp(df_stg2.iloc[0, 0] * storage_soc1_cal + df_stg2.iloc[1, 0])
                    # 저장2 Fd 구하기 (Tafel식 사용 delta E = a ln i) - 용량/저항, 직접 fd를 산출
                    storage2_cap_simul_fd = np.exp(df_stg.iloc[0, 0] * storage_soc2_cal + df_stg.iloc[1, 0])
                    storage2_dcir_simul_fd = np.exp(df_stg2.iloc[0, 0] * storage_soc2_cal + df_stg2.iloc[1, 0])
                else:
                    err_msg('파일 or 경로없음!!','Check condition file !!')
                    return
                # soh 기준으로 cycle 환산 - SET 기준
                cycle = cycle + usedcap/para_rsoh
                # 충전, 방전 기준으로 시간 산정
                time = usedcap/cycle_crate/24 + usedcap/cycle_dcrate/24 + time
                # 수명-역으로 값을 찾는 수식
                inverse_cycle_cap_soh = root_scalar(cyccapparameter, bracket=[0, 500000], method='brentq')
                inverse_cycle_dcir_soh = root_scalar(cycirparameter, bracket=[0, 500000], method='brentq')
                solve_inverse_cycle_cap_soh = inverse_cycle_cap_soh.root
                solve_inverse_cycle_dcir_soh = inverse_cycle_dcir_soh.root
                if np.isnan(solve_inverse_cycle_cap_soh):
                    solve_inverse_cycle_cap_soh = 0
                    solve_inverse_cycle_dcir_soh = 0
                # 수명 열화 - 사용 용량으로 열화 계산
                degree_cycle_cap = (cyccapparameter(solve_inverse_cycle_cap_soh) - cyccapparameter(solve_inverse_cycle_cap_soh + usedcap))
                degree_cycle_dcir = (cycirparameter(solve_inverse_cycle_dcir_soh + usedcap) - cycirparameter(solve_inverse_cycle_dcir_soh))
                soh = soh - degree_cycle_cap
                rsoh = soh * para_rsoh
                soir = soir + degree_cycle_dcir
                cycle_result = pd.DataFrame(
                    {"cycle": cycle,
                    "time": time,
                    "storagecycle": storagecycle,
                    "degree_cycle_cap": degree_cycle_cap,
                    "degree_storage1_cap": degree_storage1_cap,
                    "degree_storage2_cap": degree_storage2_cap,
                    "degree_cycle_dcir": degree_cycle_dcir,
                    "degree_storage1_dcir": degree_storage1_dcir,
                    "degree_storage2_dcir": degree_storage2_dcir,
                    "SOH": soh,
                    "rSOH": rsoh,
                    "SOIR": soir},
                    index=[3 * i + 1])
                result = pd.concat([result, cycle_result])
                # 저장 1차-역으로 값을 찾는 수식
                inverse_storage1_cap_soh = root_scalar(stgcapparameter2, bracket=[0, 500000], method='brentq')
                inverse_storage1_dcir_soh = root_scalar(stgirparameter2, bracket=[0, 500000], method='brentq')
                solve_inverse_storage1_cap_soh = inverse_storage1_cap_soh.root
                solve_inverse_storage1_dcir_soh = inverse_storage1_dcir_soh.root
                if np.isnan(solve_inverse_storage1_cap_soh):
                    solve_inverse_storage1_cap_soh = 0
                    solve_inverse_storage1_dcir_soh = 0
                # 저장 1차 열화
                time = time + storage_rest1
                if stgcountratio == 0:
                    storagecycle = storagecycle
                else:
                    storagecycle = storagecycle + storage_rest1/(stgcountratio/24)
                degree_storage1_cap = (stgcapparameter2(solve_inverse_storage1_cap_soh) - stgcapparameter2(
                    solve_inverse_storage1_cap_soh + storage_rest1))
                degree_storage1_dcir = (stgirparameter2(solve_inverse_storage1_dcir_soh + storage_rest1) - stgirparameter2(
                    solve_inverse_storage1_dcir_soh))
                soh = soh - degree_storage1_cap
                rsoh = soh * para_rsoh
                soir = soir + degree_storage1_dcir
                storage1_result = pd.DataFrame(
                    {"cycle": cycle,
                    "time": time,
                    "storagecycle": storagecycle,
                    "degree_cycle_cap": degree_cycle_cap,
                    "degree_storage1_cap": degree_storage1_cap,
                    "degree_storage2_cap": degree_storage2_cap,
                    "degree_cycle_dcir": degree_cycle_dcir,
                    "degree_storage1_dcir": degree_storage1_dcir,
                    "degree_storage2_dcir": degree_storage2_dcir,
                    "SOH": soh,
                    "rSOH": rsoh,
                    "SOIR": soir},
                    index=[3 * i + 2])
                result = pd.concat([result, storage1_result])
                # 저장 2차-역으로 값을 찾는 수식
                inverse_storage2_cap_soh = root_scalar(stgcapparameter, bracket=[0, 500000], method='brentq')
                inverse_storage2_dcir_soh = root_scalar(stgirparameter, bracket=[0, 500000], method='brentq')
                solve_inverse_storage2_cap_soh = inverse_storage2_cap_soh.root
                solve_inverse_storage2_dcir_soh = inverse_storage2_dcir_soh.root
                if np.isnan(solve_inverse_storage2_cap_soh):
                    solve_inverse_storage2_cap_soh = 0
                    solve_inverse_storage2_dcir_soh = 0
                # 저장 2차 열화
                time = time + storage_rest2
                if stgcountratio2 == 0:
                    storagecycle = storagecycle
                else:
                    storagecycle = storagecycle + storage_rest2/(stgcountratio2/24)
                degree_storage2_cap = (stgcapparameter(solve_inverse_storage2_cap_soh) - stgcapparameter(
                    solve_inverse_storage2_cap_soh + storage_rest2))
                degree_storage2_dcir = (stgirparameter(solve_inverse_storage2_dcir_soh + storage_rest2) - stgirparameter(
                    solve_inverse_storage2_dcir_soh))
                soh = soh - degree_storage2_cap
                rsoh = soh * para_rsoh
                soir = soir + degree_storage2_dcir
                storage2_result = pd.DataFrame(
                    {"cycle": cycle,
                    "time": time,
                    "storagecycle": storagecycle,
                    "degree_cycle_cap": degree_cycle_cap,
                    "degree_storage1_cap": degree_storage1_cap,
                    "degree_storage2_cap": degree_storage2_cap,
                    "degree_cycle_dcir": degree_cycle_dcir,
                    "degree_storage1_dcir": degree_storage1_dcir,
                    "degree_storage2_dcir": degree_storage2_dcir,
                    "SOH": soh,
                    "rSOH": rsoh,
                    "SOIR": soir},
                    index=[3 * i + 3])
                result = pd.concat([result, storage2_result])
                if soh < 0.75 or np.isnan(soh) or cycle > self.xscale:
                    break
                self.progressBar.setValue(int((1 - soh)/0.5 * 100))
            
            # tab 그래프 추가
            result.cycdeg_sum = 1 - result.degree_cycle_cap.cumsum()/3
            result.cycir_sum = result.degree_cycle_dcir.cumsum()/3
            result.stgdeg_sum1 = 1 - result.degree_storage1_cap.cumsum()/3
            result.stgir_sum1 = result.degree_storage1_dcir.cumsum()/3
            result.stgdeg_sum2 = 1 - result.degree_storage2_cap.cumsum()/3
            result.stgir_sum2 = result.degree_storage2_dcir.cumsum()/3
            # 전압에 의한 가속 계수 선정
            self.FdTextEdit.setText(str(round(cycle_cap_simul_fd, 50)))
            self.FdTextEdit_3.setText(str(round(cycle_dcir_simul_fd, 50)))
            self.FdTextEdit_2.setText(str(round(storage2_cap_simul_fd, 50)))
            self.FdTextEdit_4.setText(str(round(storage2_dcir_simul_fd, 50)))
            self.FdTextEdit_5.setText(str(round(storage1_cap_simul_fd, 50)))
            self.FdTextEdit_6.setText(str(round(storage1_dcir_simul_fd, 50)))
            if self.chk_cell_cycle.isChecked():
                graph_simulation(axe1, result.cycle, result.SOH, 'b-', 'Cell Capacity', self.xscale, 0.75, 1, 'cycle', 'Capacity')
            if self.chk_set_cycle.isChecked():
                graph_simulation(axe1, result.cycle, result.rSOH, 'k-', 'SET Capacity', self.xscale, 0.75, 1, 'cycle', 'Capacity')
            if self.chk_detail_cycle.isChecked():
                graph_simulation(axe1, result.cycle, result.cycdeg_sum, 'r-', 'soh_cyc', self.xscale, 0.75, 1, 'cycle', 'Capacity')
                graph_simulation(axe1, result.cycle, result.stgdeg_sum1, 'g-', 'soh_stg1', self.xscale, 0.75, 1, 'cycle', 'Capacity')
                graph_simulation(axe1, result.cycle, result.stgdeg_sum2, 'm-', 'soh_stg2', self.xscale, 0.75, 1, 'cycle', 'Capacity')
            if self.chk_cell_cycle.isChecked():
                graph_simulation(axe4, result.time, result.SOH, 'b-', 'Cell Capacity', self.xscale, 0.75, 1, 'day', 'Capacity')
            if self.chk_set_cycle.isChecked():
                graph_simulation(axe4, result.time, result.rSOH, 'k-', 'SET Capacity', self.xscale, 0.75, 1, 'day', 'Capacity')
            if self.chk_detail_cycle.isChecked():
                graph_simulation(axe4, result.time, result.cycdeg_sum, 'r-', 'soh_cyc', self.xscale, 0.75, 1, 'day', 'Capacity')
                graph_simulation(axe4, result.time, result.stgdeg_sum1, 'g-', 'soh_stg1', self.xscale, 0.75, 1, 'day', 'Capacity')
                graph_simulation(axe4, result.time, result.stgdeg_sum2, 'm-', 'soh_stg2', self.xscale, 0.75, 1, 'day', 'Capacity')
            graph_simulation(axe2, result.cycle, result.SOIR, 'b-', 'Swelling', self.xscale, 0, 0.08, 'cycle', 'Swelling')
            if self.chk_detail_cycle.isChecked():
                graph_simulation(axe2, result.cycle, result.cycir_sum, 'r-', 'DCIR_cyc', self.xscale, 0, 0.08, 'cycle', 'Swelling')
                graph_simulation(axe2, result.cycle, result.stgir_sum1, 'g-', 'DCIR_stg1', self.xscale, 0, 0.08, 'cycle', 'Swelling')
                graph_simulation(axe2, result.cycle, result.stgir_sum2, 'm-', 'DCIR_stg2', self.xscale, 0, 0.08, 'cycle', 'Swelling')
            graph_simulation(axe5, result.time, result.SOIR, 'b-', 'Swelling', self.xscale, 0, 0.08, 'day', 'Swelling')
            if self.chk_detail_cycle.isChecked():
                graph_simulation(axe5, result.time, result.cycir_sum, 'r-', 'DCIR_cyc', self.xscale, 0, 0.08, 'day', 'Swelling')
                graph_simulation(axe5, result.time, result.stgir_sum1, 'g-', 'DCIR_stg1', self.xscale, 0, 0.08, 'day', 'Swelling')
                graph_simulation(axe5, result.time, result.stgir_sum2, 'm-', 'DCIR_stg2', self.xscale, 0, 0.08, 'day', 'Swelling')
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            if input_data_path != "":
                filename = input_data_path.split(".t")[-2].split("/")[-1].split("\\")[-1]
            else:
                filename = "simulation"
            tab_layout.addWidget(toolbar)
            tab_layout.addWidget(canvas)
            self.real_cycle_simul_tab.addTab(tab, filename)
            self.real_cycle_simul_tab.setCurrentWidget(tab)
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            if self.saveok.isChecked():
                result.to_excel("simul" + filename, index=False)
                output_fig(self.figsaveok, "fig" + filename)
        plt.tight_layout(pad=1, w_pad=1, h_pad=1)
        self.progressBar.setValue(100)
            # plt.show()
        plt.close()

    def ptn_change_pattern_button(self):
        # ui에서 데이터 확인
        self.progressBar.setValue(0)
        ptn_ori_path = str(self.ptn_ori_path.text())
        ptn_crate = float(self.ptn_crate.text())
        ptn_capacity = float(self.ptn_capacity.text())
        # 파일 있는지 확인
        if not os.path.isfile(ptn_ori_path):
            ptn_ori_path = filedialog.askopenfilename(initialdir="c:\\Program Files\\PNE CTSPro\\Database\\Cycler_Schedule_2000.mdbd",
                                                      title="Choose Test files")
            self.ptn_ori_path.setText(str(ptn_ori_path))
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=' + ptn_ori_path + ';')
        conn =pyodbc.connect(conn_str)
        # 쿼리 실행
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT TestID FROM Step;")
        if (not hasattr(self, "ptn_df_select")) or (len(self.ptn_df_select) == 0) or (self.ptn_df_select[0] == ""):
            pass
        else:
            for testidcount in self.ptn_df_select:
                cursor.execute("SELECT MAX(Iref) From Step WHERE TestID = ? AND StepType = 2", str(testidcount))
                max_value = cursor.fetchone()[0]
                if max_value is not None:
                    base_capacity = max_value / ptn_crate
                    real_capacity = ptn_capacity
                    if self.chk_coincell.isChecked():
                        cursor.execute("UPDATE Step SET Iref = -round(-Iref /? *?, 3) WHERE TestID =?",
                                    str(base_capacity), str(real_capacity), str(testidcount))
                        cursor.execute("UPDATE Step SET EndI = -round(-EndI /? *?, 3) WHERE TestID =?", 
                                    str(base_capacity), str(real_capacity), str(testidcount))
                    else:
                        cursor.execute("UPDATE Step SET Iref = -int(-Iref /? *?) WHERE TestID =?",
                                    str(base_capacity), str(real_capacity), str(testidcount))
                        cursor.execute("UPDATE Step SET EndI = -int(-EndI /? *?) WHERE TestID =?", 
                                    str(base_capacity), str(real_capacity), str(testidcount))
        # 변경 사항 저장
        conn.commit()
        # 커서 및 연결 닫기
        cursor.close()
        conn.close()
        self.progressBar.setValue(100)

    def ptn_change_refi_button(self):
        self.progressBar.setValue(0)
        # ui에서 데이터 확인
        ptn_ori_path = str(self.ptn_ori_path.text())
        ptn_refi_pre = float(self.ptn_refi_pre.text())
        ptn_refi_after = float(self.ptn_refi_after.text())
        # 파일 있는지 확인
        if not os.path.isfile(ptn_ori_path):
            ptn_ori_path = filedialog.askopenfilename(initialdir="c:\\Program Files\\PNE CTSPro\\Database\\Cycler_Schedule_2000.mdbd",
                                                      title="Choose Test files")
            self.ptn_ori_path.setText(str(ptn_ori_path))
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=' + ptn_ori_path + ';')
        conn =pyodbc.connect(conn_str)
        # 쿼리 실행
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT TestID FROM Step;")
        if (not hasattr(self, "ptn_df_select")) or (self.ptn_df_select[0] == ""):
            pass
        else:
            for testidcount in self.ptn_df_select:
                # 문자 인식 문제를 위한 강제 변환
                if self.chk_coincell.isChecked():
                    cursor.execute("UPDATE Step SET Iref = round(Iref /? *?, 3) WHERE TestID =?",
                                str(1), str(1), str(testidcount))
                    cursor.execute("UPDATE Step SET Iref = ? WHERE Iref = ? AND TestID = ?",
                                str(ptn_refi_after), str(ptn_refi_pre), str(testidcount))
                else:
                    cursor.execute("UPDATE Step SET Iref = int(Iref /? *?) WHERE TestID =?",
                                str(1), str(1), str(testidcount))
                    cursor.execute("UPDATE Step SET Iref = ? WHERE Iref = ? AND TestID = ?",
                                str(ptn_refi_after), str(ptn_refi_pre), str(testidcount))
        # 변경 사항 저장
        conn.commit()
        # 커서 및 연결 닫기
        cursor.close()
        conn.close()
        self.progressBar.setValue(100)

    def ptn_change_chgv_button(self):
        self.progressBar.setValue(0)
        # ui에서 데이터 확인
        ptn_ori_path = str(self.ptn_ori_path.text())
        ptn_chgv_pre = float(self.ptn_chgv_pre.text())
        ptn_chgv_after = float(self.ptn_chgv_after.text())
        # 파일 있는지 확인
        if not os.path.isfile(ptn_ori_path):
            ptn_ori_path = filedialog.askopenfilename(initialdir="c:\\Program Files\\PNE CTSPro\\Database\\Cycler_Schedule_2000.mdbd",
                                                      title="Choose Test files")
            self.ptn_ori_path.setText(str(ptn_ori_path))
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=' + ptn_ori_path + ';')
        conn =pyodbc.connect(conn_str)
        # 쿼리 실행
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT TestID FROM Step;")
        if (not hasattr(self, "ptn_df_select")) or (self.ptn_df_select[0] == ""):
            pass
        else:
            for testidcount in self.ptn_df_select:
                cursor.execute("UPDATE Step SET Vref_Charge = int(Vref_Charge /? *?) WHERE TestID =?",
                            str(1), str(1), str(testidcount))
                cursor.execute("UPDATE Step SET Vref_Charge = ? WHERE Vref_Charge = ? AND TestID =?",
                            str(ptn_chgv_after), str(ptn_chgv_pre), str(testidcount))
        # 변경 사항 저장
        conn.commit()
        # 커서 및 연결 닫기
        cursor.close()
        conn.close()
        self.progressBar.setValue(100)

    def ptn_change_dchgv_button(self):
        self.progressBar.setValue(0)
        # ui에서 데이터 확인
        ptn_ori_path = str(self.ptn_ori_path.text())
        ptn_dchgv_pre = float(self.ptn_dchgv_pre.text())
        ptn_dchgv_after = float(self.ptn_dchgv_after.text())
        # 파일 있는지 확인
        if not os.path.isfile(ptn_ori_path):
            ptn_ori_path = filedialog.askopenfilename(initialdir="c:\\Program Files\\PNE CTSPro\\Database\\Cycler_Schedule_2000.mdbd",
                                                      title="Choose Test files")
            self.ptn_ori_path.setText(str(ptn_ori_path))
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=' + ptn_ori_path + ';')
        conn =pyodbc.connect(conn_str)
        # 쿼리 실행
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT TestID FROM Step;")
        if (not hasattr(self, "ptn_df_select")) or (self.ptn_df_select[0] == ""):
            pass
        else:
            for testidcount in self.ptn_df_select:
                cursor.execute("UPDATE Step SET Vref_DisCharge = int(Vref_DisCharge /? *?) WHERE TestID = ?",
                            str(1), str(1), str(testidcount))
                cursor.execute("UPDATE Step SET Vref_DisCharge = ? WHERE Vref_DisCharge = ? AND TestID = ?",
                            str(ptn_dchgv_after), str(ptn_dchgv_pre), str(testidcount))
        # 변경 사항 저장
        conn.commit()
        # 커서 및 연결 닫기
        cursor.close()
        conn.close()
        self.progressBar.setValue(100)

    def ptn_change_endv_button(self):
        self.progressBar.setValue(0)
        # ui에서 데이터 확인
        ptn_ori_path = str(self.ptn_ori_path.text())
        ptn_endv_pre = float(self.ptn_endv_pre.text())
        ptn_endv_after = float(self.ptn_endv_after.text())
        # 파일 있는지 확인
        if not os.path.isfile(ptn_ori_path):
            ptn_ori_path = filedialog.askopenfilename(initialdir="c:\\Program Files\\PNE CTSPro\\Database\\Cycler_Schedule_2000.mdbd",
                                                      title="Choose Test files")
            self.ptn_ori_path.setText(str(ptn_ori_path))
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=' + ptn_ori_path + ';')
        conn =pyodbc.connect(conn_str)
        # 쿼리 실행
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT TestID FROM Step;")
        if (not hasattr(self, "ptn_df_select")) or (self.ptn_df_select[0] == ""):
            pass
        else:
            for testidcount in self.ptn_df_select:
                cursor.execute("UPDATE Step SET EndV = int(EndV /? *?) WHERE TestID = ?",
                            str(1), str(1), str(testidcount))
                cursor.execute("UPDATE Step SET EndV = ? WHERE EndV = ? AND TestID = ?",
                            str(ptn_endv_after), str(ptn_endv_pre), str(testidcount))
        # 변경 사항 저장
        conn.commit()
        # 커서 및 연결 닫기
        cursor.close()
        conn.close()
        self.progressBar.setValue(100)

    def ptn_change_endi_button(self):
        self.progressBar.setValue(0)
        # ui에서 데이터 확인
        ptn_ori_path = str(self.ptn_ori_path.text())
        ptn_endi_pre = float(self.ptn_endi_pre.text())
        ptn_endi_after = float(self.ptn_endi_after.text())
        # 파일 있는지 확인
        if not os.path.isfile(ptn_ori_path):
            ptn_ori_path = filedialog.askopenfilename(initialdir="c:\\Program Files\\PNE CTSPro\\Database\\Cycler_Schedule_2000.mdbd",
                                                      title="Choose Test files")
            self.ptn_ori_path.setText(str(ptn_ori_path))
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=' + ptn_ori_path + ';')
        conn =pyodbc.connect(conn_str)
        # 쿼리 실행
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT TestID FROM Step;")
        if (not hasattr(self, "ptn_df_select")) or (self.ptn_df_select[0] == ""):
            pass
        else:
            for testidcount in self.ptn_df_select:
                # 문자 인식 문제를 위한 강제 변환
                if self.chk_coincell.isChecked():
                    cursor.execute("UPDATE Step SET EndI = round(EndI /? *?, 3) WHERE TestID =?",
                                str(1), str(1), str(testidcount))
                    cursor.execute("UPDATE Step SET EndI = ? WHERE EndI = ? AND TestID = ?",
                                str(ptn_endi_after), str(ptn_endi_pre), str(testidcount))
                else:
                    cursor.execute("UPDATE Step SET EndI = int(EndI /? *?) WHERE TestID =?",
                                str(1), str(1), str(testidcount))
                    cursor.execute("UPDATE Step SET EndI = ? WHERE EndI = ? AND TestID = ?",
                                str(ptn_endi_after), str(ptn_endi_pre), str(testidcount))
        # 변경 사항 저장
        conn.commit()
        # 커서 및 연결 닫기
        cursor.close()
        conn.close()
        self.progressBar.setValue(100)

    def ptn_change_step_button(self):
        self.progressBar.setValue(0)
        # ui에서 데이터 확인
        ptn_ori_path = str(self.ptn_ori_path.text())
        ptn_step_pre = int(self.ptn_step_pre.text())
        ptn_step_after = int(self.ptn_step_after.text())
        # 파일 있는지 확인
        if not os.path.isfile(ptn_ori_path):
            ptn_ori_path = filedialog.askopenfilename(initialdir="c:\\Program Files\\PNE CTSPro\\Database\\Cycler_Schedule_2000.mdbd",
                                                      title="Choose Test files")
            self.ptn_ori_path.setText(str(ptn_ori_path))
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=' + ptn_ori_path + ';')
        conn =pyodbc.connect(conn_str)
        # 쿼리 실행 (dataframe으로 변화, 수정 후 다시 StepID에 맞춰서 변경)
        df = pd.read_sql("SELECT * FROM Step", conn)
        # 선택한 Test ID만 기준으로 dataframe에서 변경
        df["Value2"] = df["Value2"].str.replace(str(" " + str(ptn_step_pre) + " "), str(" " + str(ptn_step_pre + ptn_step_after) + " "))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT TestID FROM Step;")
        if (not hasattr(self, "ptn_df_select")) or (self.ptn_df_select[0] == ""):
            pass
        else:
            for testidcount in self.ptn_df_select:
                for StepIDcount in df["StepID"]:
                    cursor.execute("UPDATE Step SET Value2 = ? WHERE StepID = ? AND TestID = ?",
                                str(df[df["StepID"] == StepIDcount]["Value2"].values[0]) , str(StepIDcount), str(testidcount))
        # 변경 사항 저장
        conn.commit()
        # 커서 및 연결 닫기
        cursor.close()
        conn.close()
        self.progressBar.setValue(100)

    def ptn_load_button(self):
        self.progressBar.setValue(0)
        # ui에서 데이터 확인
        ptn_ori_path = str(self.ptn_ori_path.text())
        # 파일 있는지 확인
        if not os.path.isfile(ptn_ori_path):
            ptn_ori_path = filedialog.askopenfilename(initialdir="c:\\Program Files\\PNE CTSPro\\Database\\Cycler_Schedule_2000.mdbd",
                                                      title="Choose Test files")
            self.ptn_ori_path.setText(str(ptn_ori_path))
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=' + ptn_ori_path + ';')
        conn =pyodbc.connect(conn_str)
        # 쿼리 실행 (Pattern 이름 테이블을 dataframe으로 변화, 수정 후 다시 StepID에 맞춰서 변경)
        pne_ptn_df = pd.read_sql("SELECT * FROM TestName", conn)
        pne_ptn_folder_name = pd.read_sql("SELECT * FROM BatteryModel", conn)
        self.pne_ptn_merged_df = pd.merge(pne_ptn_df, pne_ptn_folder_name, on='ModelID')
        self.pne_ptn_merged_df = self.pne_ptn_merged_df[["ModelName", "TestName", "Description_x", "TestID", "No", "TestNo"]]
        self.pne_ptn_merged_df = self.pne_ptn_merged_df.sort_values(by=['No','TestNo'], ascending=[True, True]).reset_index(drop=True)
        # 패턴 list 및 선택 초기화
        self.ptn_list.clear()
        self.ptn_df_select = []
        # dataframe을 기준으로 table widget 생성
        self.ptn_list.setRowCount(len(self.pne_ptn_merged_df.index))
        self.ptn_list.setColumnCount(len(self.pne_ptn_merged_df.columns) - 3)
        self.ptn_list.setHorizontalHeaderLabels(["패턴폴더", "패턴이름", "비고"])
        self.ptn_list.horizontalHeader().setVisible(True)
        for row_index, row in enumerate(self.pne_ptn_merged_df.index):
            for col_index, column in enumerate(self.pne_ptn_merged_df.columns):
                value = self.pne_ptn_merged_df.loc[row][column]
                # QTableWidget의 row_index 열, col_index 행에 들어갈 아이템을 생성
                item = QtWidgets.QTableWidgetItem(str(value))
                # 생성된 아이템을 위젯의 row_index, col_index (행, 열)에 배치
                self.ptn_list.setItem(row_index, col_index, item)
        self.ptn_list.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.ptn_list.cellClicked.connect(self.ptn_get_selected_items)
        # 커서 및 연결 닫기
        conn.close()
        self.progressBar.setValue(100)

    def ptn_get_selected_items(self, row, column):
        self.ptn_df_select = []
        for index in self.ptn_list.selectionModel().selectedRows():
            self.ptn_df_select.append(self.pne_ptn_merged_df.iloc[index.row(), 3])
        if len(self.ptn_df_select) == 0:
            self.ptn_df_select = [""]
