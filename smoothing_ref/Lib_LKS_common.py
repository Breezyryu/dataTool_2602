import os
import numpy as np
import pandas as pd
import xlwings as xw

#########################################################################################
### 현재 선택된 엑셀 셀 위치 정보 획득
#########################################################################################
def ActCell():
    cell = xw.books.active.selection
    return cell.row, cell.column
# print(f'{get_char(ActCell()[1])}{ActCell()[0]}')

#########################################################################################
### 엑셀 데이터 발췌 (ver.1, 경로 지정)
#########################################################################################
def from_excel1(file_path,sheet_num=0,loc='A1',exp_opt='table',q=0):
    meth = pd.DataFrame if exp_opt == 'table' else np.ndarray
    app = xw.App(visible=True)

    app.screen_updating = False
    app.calculate = 'manual'
    app.enable_events = False

    bk = app.books.open(file_path)
    sh = bk.sheets[sheet_num]
    df = sh.range(loc).options(meth,index=False,expand=exp_opt).value
    if q == 1:
        bk.close() 

    app.screen_updating = True
    app.calculate = 'automatic'
    app.enable_events = True
    if q == 2:
        app.quit()  
    return df

#########################################################################################
### 엑셀 데이터 발췌 (ver.2, 현재 선택된 엑셀 셀 위치 기준)
#########################################################################################
def from_excel2(exp_opt='table'):
    meth = pd.DataFrame if exp_opt == 'table' else np.ndarray
    sh = xw.books.active.selection
    df = sh.options(meth,index=False,expand=exp_opt).value
    return df

#########################################################################################
### 엑셀 데이터 발췌 (ver.3, 경로 지정 & 병렬 실행 고려)
#########################################################################################
def from_excel3(file_path,sheet_num=0,loc='A1',exp_opt='table'):
    meth = pd.DataFrame if exp_opt == 'table' else np.ndarray
    app_key = f'{file_path.split("/")[-1].split(".")[0]}'
    globals()[app_key] = xw.App(visible=True)
    app = globals()[app_key]

    app.screen_updating = False
    app.calculate = 'manual'
    app.enable_events = False

    bk = app.books.open(file_path)
    sh = bk.sheets[sheet_num]
    df = sh.range(loc).options(meth,index=False,expand=exp_opt).value
    bk.close()

    app.screen_updating = True
    app.calculate = 'automatic'
    app.enable_events = True
    app.quit()
    return df

#########################################################################################
### 엑셀 초기화 (열린 엑셀 일괄 강제 종료)
#########################################################################################
def init_excel():
    try:
        os.system("taskkill /f /im EXCEL.exe")
    except:
        pass

#########################################################################################
### 경우의 수 조합 생성 (ver.1)
#########################################################################################
def Cartesian_product_v1(df,col=3):
    ids = df.dropna(subset=[df.columns[col]]).iloc[:,0].astype(int).to_list()
    lists = []
    for id in ids:
        options = df.iloc[id,col:].dropna().astype(float).to_list()
        if len(lists) == 0:
            for option in options:
                lists.append([option])
        else:
            lists2 = []
            lists_old = lists
            for ls in lists_old:
                for option in options:
                    new_ls = ls.copy()
                    new_ls.append(option)
                    lists2.append(new_ls)
            lists = lists2
    return ids, lists

#########################################################################################
### 경우의 수 조합 생성 (ver.2)
#########################################################################################
def Cartesian_product_v2(df,col=3):
    ids = df.dropna(subset=[df.columns[col]]).iloc[:,0].astype(int).to_list()
    lists = [[]]
    for id in ids:
        options = df.iloc[id,col:].dropna().astype(float).to_list()
        lists = [list+[option] for list in lists for option in options]
    return ids, lists

# df = from_excel2()
# df.iloc[:,0]=df.iloc[:,0].astype(int)
# df.iloc[:,2:]=df.iloc[:,2:].astype(float)
# ids, lists = Cartesian_product_v2(df)
# print(df)
# print(ids)
# print(lists)