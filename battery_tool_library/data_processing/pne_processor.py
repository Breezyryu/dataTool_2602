"""
Battery Data Tool - PNE Processor Module

PNE 충방전기 데이터 처리 함수
원본: origin_datatool/BatteryDataTool.py (Lines 866-950+)

📌 활용 스킬: scientific-critical-thinking

충방전기 데이터 구조:
    PNE 충방전기는 Pattern 폴더와 Restore 폴더로 데이터를 저장합니다.
    - Pattern/: 테스트 패턴 정의 파일
    - Restore/: 실측 데이터 (SaveData*.csv, SaveEndData*.csv)
    - savingFileIndex_start.csv: 파일 인덱스 매핑
"""

import os
import bisect
import re
import pandas as pd
import numpy as np
from typing import Optional, List, Any, Tuple


def binary_search(numbers: list, target) -> int:
    """이진 탐색으로 삽입 위치 찾기."""
    return bisect.bisect_left(numbers, target)


def name_capacity(data_file_path) -> float:
    """파일 경로에서 배터리 용량(mAh) 추출. (로컬 복사본)"""
    if not isinstance(data_file_path, list):
        raw_file_path = re.sub(r'[._@\$$$$$$\(\)]', ' ', data_file_path)
        match = re.search(r'(\d+([\-\.]\d+)?)mAh', raw_file_path)
        if match:
            min_cap = match.group(1).replace('-', '.')
            return float(min_cap)
        return 0
    return 0


def pne_search_cycle(rawdir: str, start: int, end: int) -> List[int]:
    """PNE 데이터에서 원하는 cycle이 포함된 파일 범위 찾기.
    
    전기화학적 맥락:
        PNE 충방전기는 데이터를 여러 파일에 분할 저장합니다.
        특정 cycle의 데이터를 찾으려면 인덱스 파일을 참조해야 합니다.
    
    Args:
        rawdir: Restore 폴더 경로
        start: 시작 cycle 번호
        end: 종료 cycle 번호
    
    Returns:
        [file_start, file_end] 파일 인덱스 리스트
        파일을 찾지 못한 경우 [-1, -1]
    """
    file_start = -1
    file_end = -1
    
    if os.path.isdir(rawdir):
        subfile = [f for f in os.listdir(rawdir) if f.endswith(".csv")]
        
        for files in subfile:
            # SaveEndData 파일에서 cycle 인덱스 찾기
            if "SaveEndData" in files:
                df = pd.read_csv(
                    rawdir + files, sep=",", skiprows=0,
                    engine="c", header=None, encoding="cp949", on_bad_lines='skip'
                )
                
                if start != 1:
                    index_min = df.loc[(df.loc[:, 27] == (start - 1)), 0].tolist()
                else:
                    index_min = [0]
                
                index_max = df.loc[(df.loc[:, 27] == end), 0].tolist()
                if not index_max:
                    index_max = df.loc[(df.loc[:, 27] == df.loc[:, 27].max()), 0].tolist()
                
                # 파일 인덱스 매핑 파일 읽기
                index_file = rawdir + "savingFileIndex_start.csv"
                if os.path.isfile(index_file):
                    df2 = pd.read_csv(
                        index_file, delim_whitespace=True, skiprows=0,
                        engine="c", header=None, encoding="cp949", on_bad_lines='skip'
                    )
                    df2 = df2.loc[:, 3].tolist()
                    index2 = []
                    for element in df2:
                        new_element = int(str(element).replace(',', ''))
                        index2.append(new_element)
                    
                    if len(index_min) != 0:
                        file_start = binary_search(index2, index_min[-1] + 1) - 1
                        file_end = binary_search(index2, index_max[-1]) - 1
    
    return [file_start, file_end]


def pne_data(raw_file_path: str, inicycle: int) -> Any:
    """PNE Profile 데이터 기본 로딩.
    
    전기화학적 맥락:
        PNE 충방전기의 Restore 폴더에서 특정 cycle의 
        상세 profile 데이터를 읽어옵니다.
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        inicycle: 불러올 cycle 번호
    
    Returns:
        df 객체 (df.Profileraw에 데이터 저장)
    """
    df = pd.DataFrame()
    
    restore_dir = raw_file_path + "\\Restore\\"
    if os.path.isdir(restore_dir):
        rawdir = restore_dir
        filepos = pne_search_cycle(rawdir, inicycle, inicycle + 1)
        
        if os.path.isdir(rawdir) and (filepos[0] != -1):
            subfile = [f for f in os.listdir(rawdir) if f.endswith(".csv")]
            for files in subfile[(filepos[0]):(filepos[1] + 1)]:
                if "SaveData" in files:
                    Profilerawtemp = pd.read_csv(
                        rawdir + files, sep=",", skiprows=0,
                        engine="c", header=None, encoding="cp949", on_bad_lines='skip'
                    )
                    if hasattr(df, "Profileraw"):
                        df.Profileraw = pd.concat([df.Profileraw, Profilerawtemp], ignore_index=True)
                    else:
                        df.Profileraw = Profilerawtemp
    
    return df


def pne_continue_data(raw_file_path: str, inicycle: int, endcycle: int) -> Any:
    """PNE 연속 데이터 Profile 로딩.
    
    여러 cycle에 걸친 연속 데이터를 하나의 DataFrame으로 합칩니다.
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        inicycle: 시작 cycle 번호
        endcycle: 종료 cycle 번호
    
    Returns:
        df 객체 (df.Profileraw에 데이터 저장)
    """
    df = pd.DataFrame()
    
    restore_dir = raw_file_path + "\\Restore\\"
    if os.path.isdir(restore_dir):
        rawdir = restore_dir
        if os.path.isdir(rawdir):
            subfile = [f for f in os.listdir(rawdir) if f.endswith(".csv")]
            filepos = pne_search_cycle(rawdir, inicycle, endcycle)
            
            if filepos[0] != -1:
                for files in subfile[(filepos[0]):(filepos[1] + 1)]:
                    if "SaveData" in files:
                        Profilerawtemp = pd.read_csv(
                            rawdir + files, sep=",", skiprows=0,
                            engine="c", header=None, encoding="cp949", on_bad_lines='skip'
                        )
                        if hasattr(df, "Profileraw"):
                            df.Profileraw = pd.concat([df.Profileraw, Profilerawtemp], ignore_index=True)
                        else:
                            df.Profileraw = Profilerawtemp
            elif filepos[0] == -1 and inicycle == 1:
                for files in subfile[0:(filepos[1] + 1)]:
                    if "SaveData" in files:
                        Profilerawtemp = pd.read_csv(
                            rawdir + files, sep=",", skiprows=0,
                            engine="c", header=None, encoding="cp949", on_bad_lines='skip'
                        )
                        if hasattr(df, "Profileraw"):
                            df.Profileraw = pd.concat([df.Profileraw, Profilerawtemp], ignore_index=True)
                        else:
                            df.Profileraw = Profilerawtemp
    
    return df


def pne_min_cap(raw_file_path: str, mincapacity: float, inirate: float) -> float:
    """PNE 데이터에서 최소 용량(정격 용량) 산정.
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        mincapacity: 사용자 입력 용량 (0이면 자동 산정)
        inirate: 첫 cycle 기준 C-rate
    
    Returns:
        산정된 정격 용량 (mAh)
    """
    if mincapacity == 0:
        if "mAh" in raw_file_path:
            mincap = name_capacity(raw_file_path)
        else:
            # 첫 cycle에서 전류 기반으로 용량 추정
            df = pne_data(raw_file_path, 1)
            if hasattr(df, "Profileraw") and not df.Profileraw.empty:
                # 컬럼 10이 전류 (PNE 포맷)
                max_current = df.Profileraw.iloc[:, 10].max()
                mincap = int(round(max_current / inirate))
            else:
                mincap = 0
    else:
        mincap = mincapacity
    return mincap


def same_add(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """동일 값에 순번 추가.
    
    같은 cycle 번호가 여러 번 나올 때 구분을 위해 순번을 추가합니다.
    """
    df = df.copy()
    df[column + "_add"] = df.groupby(column).cumcount() + 1
    # cycle * 0.1 + 순번 형태로 변형
    df[column + "_add"] = df[column] + df[column + "_add"] * 0.1
    return df


def pne_cyc_continue_data(raw_file_path: str) -> Any:
    """PNE 전체 Cycle 데이터 로딩.
    
    SaveEndData.csv 파일에서 전체 cycle 요약 데이터를 읽습니다.
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
    
    Returns:
        df 객체 (df.Cycrawtemp에 데이터 저장)
    """
    df = pd.DataFrame()
    restore_dir = raw_file_path + "\\Restore\\"
    
    if os.path.isdir(restore_dir):
        subfile = [f for f in os.listdir(restore_dir) if f.endswith(".csv")]
        for files in subfile:
            if "SaveEndData" in files:
                df.Cycrawtemp = pd.read_csv(
                    restore_dir + files, sep=",", skiprows=0,
                    engine="c", header=None, encoding="cp949", on_bad_lines='skip'
                )
    return df


# ============================================================================
# PNE Cycle 처리 함수
# ============================================================================

def pne_cycle_data(
    raw_file_path: str,
    mincapacity: float,
    ini_crate: float,
    chkir: bool,
    chkir2: bool,
    mkdcir: bool
) -> list:
    """PNE Cycle 데이터 처리.
    
    전기화학적 맥락:
        SaveEndData.csv에서 추출한 원시 데이터를 정리하여
        수명 분석에 필요한 지표들을 계산합니다.
        
        PNE 데이터 컬럼 매핑:
        - 27: Total Cycle
        - 2: StepType (1=충전, 2=방전, 3=휴지)
        - 6: EndState (64=휴지, 65=전압, 66=전류, 78=용량)
        - 8: Voltage (mV)
        - 9: Current (μA 또는 mA)
        - 10: Chg Capacity (mAh)
        - 11: Dchg Capacity (mAh)
        - 15: Dchg WattHour (Wh)
        - 20: Impedance
        - 24: Temperature (°C)
        
        DCIR 계산 모드:
        - chkir: 기본 DCIR (10s pulse)
        - chkir2: 연속 DCIR
        - mkdcir: 1s pulse + RSS DCIR 복합
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        mincapacity: 정격 용량 (0이면 자동)
        ini_crate: 첫 cycle C-rate
        chkir: 기본 DCIR 사용 여부
        chkir2: 연속 DCIR 사용 여부
        mkdcir: 복합 DCIR 사용 여부
    
    Returns:
        [mincapacity, df] 리스트
    """
    df = pd.DataFrame()
    
    if raw_file_path[-4:-1] != "ter":
        mincapacity = pne_min_cap(raw_file_path, mincapacity, ini_crate)
        
        restore_dir = raw_file_path + "\\Restore\\"
        if os.path.isdir(restore_dir):
            subfile = [f for f in os.listdir(restore_dir) if f.endswith('.csv')]
            
            for files in subfile:
                if "SaveEndData.csv" in files:
                    file_path = restore_dir + files
                    if os.stat(file_path).st_size > 0 and mincapacity is not None:
                        Cycleraw = pd.read_csv(
                            file_path, sep=",", skiprows=0,
                            engine="c", header=None, encoding="cp949", on_bad_lines='skip'
                        )
                        Cycleraw = Cycleraw[[27, 2, 10, 11, 8, 20, 45, 15, 17, 9, 24, 29, 6]]
                        Cycleraw.columns = ["TotlCycle", "Condition", "chgCap", "DchgCap", 
                                            "Ocv", "imp", "volmax", "DchgEngD", "steptime", 
                                            "Curr", "Temp", "AvgV", "EndState"]
                        
                        # PNE21/22는 단위가 다름
                        if ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path):
                            Cycleraw.DchgCap = Cycleraw.DchgCap / 1000
                            Cycleraw.chgCap = Cycleraw.chgCap / 1000
                            Cycleraw.Curr = Cycleraw.Curr / 1000
                        
                        # DCIR 처리
                        dcir = None
                        if chkir:
                            dcirtemp = Cycleraw[(Cycleraw["Condition"] == 2) & 
                                               (Cycleraw["volmax"] > 4100000)]
                            dcirtemp.index = dcirtemp["TotlCycle"]
                            dcir = dcirtemp.imp / 1000
                            dcir = dcir[~dcir.index.duplicated()]
                        elif not mkdcir:
                            dcirtemp = Cycleraw[(Cycleraw["Condition"] == 2) & 
                                               (Cycleraw["steptime"] <= 6000)]
                            dcirtemp = dcirtemp.copy()
                            dcirtemp["dcir"] = dcirtemp.imp / 1000
                        
                        # Pivot table로 주요 지표 계산
                        pivot_data = Cycleraw.pivot_table(
                            index="TotlCycle",
                            columns="Condition",
                            values=["DchgCap", "DchgEngD", "chgCap", "Ocv", "Temp"],
                            aggfunc={
                                "DchgCap": "sum",
                                "DchgEngD": "sum",
                                "chgCap": "sum",
                                "Ocv": "min",
                                "Temp": "max"
                            }
                        )
                        
                        # 각 지표 추출 및 정규화
                        Dchg = pivot_data["DchgCap"][2] / mincapacity / 1000
                        DchgEng = pivot_data["DchgEngD"][2] / 1000
                        Chg = pivot_data["chgCap"][1] / mincapacity / 1000
                        Ocv = pivot_data["Ocv"][3] / 1000000
                        Temp = pivot_data["Temp"][2] / 1000
                        
                        ChgCap2 = Chg.shift(periods=-1)
                        Eff = Dchg / Chg  # 쿨롱 효율
                        Eff2 = ChgCap2 / Dchg  # 역방향 효율
                        AvgV = DchgEng / Dchg / mincapacity * 1000
                        OriCycle = pd.Series(Dchg.index)
                        
                        # 결과 DataFrame 생성
                        df.NewData = pd.concat(
                            [Dchg, Ocv, Eff, Chg, DchgEng, Eff2, Temp, AvgV, OriCycle],
                            axis=1
                        ).reset_index(drop=True)
                        df.NewData.columns = ["Dchg", "RndV", "Eff", "Chg", "DchgEng", 
                                              "Eff2", "Temp", "AvgV", "OriCyc"]
                        
                        # DCIR 컬럼 추가
                        if chkir and dcir is not None and len(OriCycle) == len(dcir):
                            df.NewData["dcir"] = dcir.values
                        elif not chkir and not mkdcir and 'dcirtemp' in locals():
                            if hasattr(dcirtemp, "dcir") and not dcirtemp.dcir.empty:
                                n = 1
                                cyccal = []
                                if len(dcirtemp) != 0:
                                    dcirstep = max(1, int(len(Dchg) / len(dcirtemp) * 2 / 10) * 10)
                                    for i in range(len(dcirtemp)):
                                        cyccal.append(n)
                                        n += 1 if i % 2 == 0 else dcirstep - 1
                                dcir_df = pd.DataFrame({"Cyc": cyccal, "dcir_raw": dcirtemp.dcir})
                                dcir_df = dcir_df.set_index(dcir_df["Cyc"])
                                df.NewData["dcir"] = dcir_df["dcir_raw"]
                            else:
                                df.NewData.loc[0, "dcir"] = 0
                        else:
                            df.NewData.loc[0, "dcir"] = 0
    
    return [mincapacity, df]


# ============================================================================
# PNE Profile 처리 함수
# ============================================================================

def pne_step_Profile_data(
    raw_file_path: str,
    inicycle: int,
    mincapacity: float,
    cutoff: float,
    inirate: float
) -> list:
    """PNE Step 충전 Profile 처리.
    
    전기화학적 맥락:
        Step 충전 패턴의 전류-전압 변화를 분석합니다.
        여러 step이 있는 경우 시간과 용량을 연속으로 병합합니다.
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        inicycle: 분석할 cycle 번호
        mincapacity: 정격 용량 (0이면 자동)
        cutoff: 전류 하한 (C-rate)
        inirate: 첫 cycle C-rate
    
    Returns:
        [mincapacity, df] 리스트
    """
    df = pd.DataFrame()
    
    if raw_file_path[-4:-1] != "ter":
        tempcap = pne_min_cap(raw_file_path, mincapacity, inirate)
        mincapacity = tempcap
        
        profile_raw = pne_data(raw_file_path, inicycle)
        
        if hasattr(profile_raw, "Profileraw"):
            # 충전 부분만 추출 (Condition 1, 9)
            profile_raw.Profileraw = profile_raw.Profileraw[
                (profile_raw.Profileraw[27] == inicycle) & 
                (profile_raw.Profileraw[2].isin([9, 1]))
            ]
            profile_raw.Profileraw = profile_raw.Profileraw[[17, 8, 9, 21, 10, 7]]
            profile_raw.Profileraw.columns = ["PassTime[Sec]", "Voltage[V]", "Current[mA]", 
                                               "Temp1[Deg]", "Chgcap", "step"]
            
            # 단위 변환
            profile_raw.Profileraw["PassTime[Sec]"] = profile_raw.Profileraw["PassTime[Sec]"] / 100 / 60
            profile_raw.Profileraw["Voltage[V]"] = profile_raw.Profileraw["Voltage[V]"] / 1000000
            
            if ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path):
                profile_raw.Profileraw["Current[mA]"] = profile_raw.Profileraw["Current[mA]"] / mincapacity / 1000000
                profile_raw.Profileraw["Chgcap"] = profile_raw.Profileraw["Chgcap"] / mincapacity / 1000000
            else:
                profile_raw.Profileraw["Current[mA]"] = profile_raw.Profileraw["Current[mA]"] / mincapacity / 1000
                profile_raw.Profileraw["Chgcap"] = profile_raw.Profileraw["Chgcap"] / mincapacity / 1000
            
            profile_raw.Profileraw["Temp1[Deg]"] = profile_raw.Profileraw["Temp1[Deg]"] / 1000
            
            stepmin = profile_raw.Profileraw.step.min()
            stepmax = profile_raw.Profileraw.step.max()
            stepdiv = stepmax - stepmin
            
            if not np.isnan(stepdiv):
                if stepdiv == 0:
                    df.stepchg = profile_raw.Profileraw
                else:
                    Profiles = [profile_raw.Profileraw.loc[profile_raw.Profileraw.step == stepmin]]
                    for i in range(1, int(stepdiv) + 1):
                        next_profile = profile_raw.Profileraw.loc[
                            profile_raw.Profileraw.step == stepmin + i
                        ].copy()
                        next_profile["PassTime[Sec]"] += Profiles[-1]["PassTime[Sec]"].max()
                        next_profile["Chgcap"] += Profiles[-1]["Chgcap"].max()
                        Profiles.append(next_profile)
                    df.stepchg = pd.concat(Profiles)
        
        if hasattr(df, "stepchg"):
            df.stepchg = df.stepchg[(df.stepchg["Current[mA]"] >= cutoff)]
            df.stepchg = df.stepchg[["PassTime[Sec]", "Chgcap", "Voltage[V]", 
                                      "Current[mA]", "Temp1[Deg]"]]
            df.stepchg.columns = ["TimeMin", "SOC", "Vol", "Crate", "Temp"]
    
    return [mincapacity, df]


def pne_rate_Profile_data(
    raw_file_path: str,
    inicycle: int,
    mincapacity: float,
    cutoff: float,
    inirate: float
) -> list:
    """PNE 율별 충전 Profile 처리.
    
    다양한 C-rate에서의 충전 특성을 분석합니다.
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        inicycle: 분석할 cycle 번호
        mincapacity: 정격 용량 (0이면 자동)
        cutoff: 전류 하한 (C-rate)
        inirate: 첫 cycle C-rate
    
    Returns:
        [mincapacity, df] 리스트
    """
    df = pd.DataFrame()
    
    if raw_file_path[-4:-1] != "ter":
        tempcap = pne_min_cap(raw_file_path, mincapacity, inirate)
        mincapacity = tempcap
        
        pnetempdata = pne_data(raw_file_path, inicycle)
        
        if hasattr(pnetempdata, 'Profileraw'):
            Profileraw = pnetempdata.Profileraw
            Profileraw = Profileraw.loc[
                (Profileraw[27] == inicycle) & (Profileraw[2].isin([9, 1]))
            ]
            Profileraw = Profileraw[[17, 8, 9, 21, 10, 7]]
            Profileraw.columns = ["PassTime[Sec]", "Voltage[V]", "Current[mA]", 
                                  "Temp1[Deg]", "Chgcap", "step"]
            
            # 단위 변환
            Profileraw["PassTime[Sec]"] = Profileraw["PassTime[Sec]"] / 100 / 60
            Profileraw["Voltage[V]"] = Profileraw["Voltage[V]"] / 1000000
            
            if ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path):
                Profileraw["Current[mA]"] = Profileraw["Current[mA]"] / mincapacity / 1000000
                Profileraw["Chgcap"] = Profileraw["Chgcap"] / mincapacity / 1000000
            else:
                Profileraw["Current[mA]"] = Profileraw["Current[mA]"] / mincapacity / 1000
                Profileraw["Chgcap"] = Profileraw["Chgcap"] / mincapacity / 1000
            
            Profileraw["Temp1[Deg]"] = Profileraw["Temp1[Deg]"] / 1000
            
            if hasattr(df, "rateProfile") or len(Profileraw) > 0:
                df.rateProfile = Profileraw
                df.rateProfile = df.rateProfile[(df.rateProfile["Current[mA]"] >= cutoff)]
                df.rateProfile = df.rateProfile[["PassTime[Sec]", "Chgcap", "Voltage[V]", 
                                                  "Current[mA]", "Temp1[Deg]"]]
                df.rateProfile.columns = ["TimeMin", "SOC", "Vol", "Crate", "Temp"]
    
    return [mincapacity, df]

