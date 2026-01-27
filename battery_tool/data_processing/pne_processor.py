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


# ============================================================================
# PNE 충방전 Profile 처리 함수 (dQ/dV, dV/dQ 분석 포함)
# 📌 활용 스킬: scientific-critical-thinking
# ============================================================================

def pne_chg_Profile_data(
    raw_file_path: str,
    inicycle: int,
    mincapacity: float,
    cutoff: float,
    inirate: float,
    smoothdegree: int
) -> list:
    """PNE 충전 Profile 처리 (dQ/dV, dV/dQ 분석 포함).
    
    전기화학적 맥락:
        충전 프로파일에서 미분 분석(dQ/dV, dV/dQ)을 수행합니다.
        - dQ/dV 피크: 상전이(phase transition) 위치 반영
        - dV/dQ 피크: 리튬 삽입/탈리 전이점 반영
        smoothdegree가 0이면 데이터 길이/30으로 자동 설정
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        inicycle: 분석할 cycle 번호
        mincapacity: 정격 용량 (0이면 자동)
        cutoff: 전류 하한 (C-rate)
        inirate: 첫 cycle C-rate
        smoothdegree: 미분 스무딩 윈도우 크기
    
    Returns:
        [mincapacity, df] 리스트 (df.Profile에 분석 결과)
    """
    df = pd.DataFrame()
    
    if raw_file_path[-4:-1] != "ter":
        # PNE 채널, 용량 산정
        tempcap = pne_min_cap(raw_file_path, mincapacity, inirate)
        mincapacity = tempcap
        
        # data 기본 처리
        df = pne_data(raw_file_path, inicycle)
        
        if hasattr(df, 'Profileraw'):
            df.Profileraw = df.Profileraw.loc[
                (df.Profileraw[27] == inicycle) & (df.Profileraw[2].isin([9, 1]))
            ]
            df.Profileraw = df.Profileraw[[17, 8, 9, 10, 14, 21, 7]]
            df.Profileraw.columns = ["PassTime[Sec]", "Voltage[V]", "Current[mA]", 
                                     "Chgcap", "Chgwh", "Temp1[Deg]", "step"]
            
            # 충전 단위 변환
            df.Profileraw["PassTime[Sec]"] = df.Profileraw["PassTime[Sec]"] / 100 / 60
            df.Profileraw["Voltage[V]"] = df.Profileraw["Voltage[V]"] / 1000000
            
            if ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path):
                df.Profileraw["Current[mA]"] = df.Profileraw["Current[mA]"] / mincapacity / 1000000
                df.Profileraw["Chgcap"] = df.Profileraw["Chgcap"] / mincapacity / 1000000
            else:
                df.Profileraw["Current[mA]"] = df.Profileraw["Current[mA]"] / mincapacity / 1000
                df.Profileraw["Chgcap"] = df.Profileraw["Chgcap"] / mincapacity / 1000
            
            df.Profileraw["Temp1[Deg]"] = df.Profileraw["Temp1[Deg]"] / 1000
            
            stepmin = df.Profileraw.step.min()
            stepmax = df.Profileraw.step.max()
            stepdiv = stepmax - stepmin
            
            if not np.isnan(stepdiv):
                if stepdiv == 0:
                    df.Profile = df.Profileraw
                else:
                    Profiles = [df.Profileraw.loc[df.Profileraw.step == stepmin]]
                    for i in range(1, int(stepdiv) + 1):
                        next_prof = df.Profileraw.loc[df.Profileraw.step == stepmin + i].copy()
                        next_prof["PassTime[Sec]"] += Profiles[-1]["PassTime[Sec]"].max()
                        next_prof["Chgcap"] += Profiles[-1]["Chgcap"].max()
                        Profiles.append(next_prof)
                    df.Profile = pd.concat(Profiles)
        
        if hasattr(df, "Profile"):
            df.Profile = df.Profile.reset_index()
            # cut-off
            df.Profile = df.Profile[(df.Profile["Current[mA]"] >= cutoff)]
            
            # 충전 용량 산정, dQdV 산정
            df.Profile["dVdQ"] = 0
            df.Profile["delcap"] = 0
            df.Profile["delvol"] = 0
            
            if smoothdegree == 0:
                smoothdegree = int(len(df.Profile) / 30)
            
            df.Profile["delvol"] = df.Profile["Voltage[V]"].diff(periods=smoothdegree)
            df.Profile["delcap"] = df.Profile["Chgcap"].diff(periods=smoothdegree)
            df.Profile["dQdV"] = df.Profile["delcap"] / df.Profile["delvol"]
            df.Profile["dVdQ"] = df.Profile["delvol"] / df.Profile["delcap"]
            
            df.Profile = df.Profile[["PassTime[Sec]", "Chgcap", "Chgwh", "Voltage[V]", 
                                     "Current[mA]", "dQdV", "dVdQ", "Temp1[Deg]"]]
            df.Profile.columns = ["TimeMin", "SOC", "Energy", "Vol", "Crate", "dQdV", "dVdQ", "Temp"]
    
    return [mincapacity, df]


def pne_dchg_Profile_data(
    raw_file_path: str,
    inicycle: int,
    mincapacity: float,
    cutoff: float,
    inirate: float,
    smoothdegree: int
) -> list:
    """PNE 방전 Profile 처리 (dQ/dV, dV/dQ 분석 포함).
    
    전기화학적 맥락:
        방전 프로파일에서 미분 분석을 수행합니다.
        cutoff 전압 이상의 데이터만 분석합니다.
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        inicycle: 분석할 cycle 번호
        mincapacity: 정격 용량 (0이면 자동)
        cutoff: 전압 하한 (V)
        inirate: 첫 cycle C-rate
        smoothdegree: 미분 스무딩 윈도우 크기
    
    Returns:
        [mincapacity, df] 리스트 (df.Profile에 분석 결과)
    """
    df = pd.DataFrame()
    
    if raw_file_path[-4:-1] != "ter":
        # PNE 채널, 용량 산정
        tempcap = pne_min_cap(raw_file_path, mincapacity, inirate)
        mincapacity = tempcap
        
        # data 기본 처리
        pnetempdata = pne_data(raw_file_path, inicycle)
        
        if hasattr(pnetempdata, 'Profileraw'):
            Profileraw = pnetempdata.Profileraw
            Profileraw = Profileraw.loc[
                (Profileraw[27] == inicycle) & (Profileraw[2].isin([9, 2]))
            ]
            Profileraw = Profileraw[[17, 8, 9, 11, 15, 21, 7]]
            Profileraw.columns = ["PassTime[Sec]", "Voltage[V]", "Current[mA]", 
                                  "Dchgcap", "Dchgwh", "Temp1[Deg]", "step"]
            
            # 단위 변환
            Profileraw["PassTime[Sec]"] = Profileraw["PassTime[Sec]"] / 100 / 60
            Profileraw["Voltage[V]"] = Profileraw["Voltage[V]"] / 1000000
            
            if ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path):
                Profileraw["Current[mA]"] = Profileraw["Current[mA]"] / mincapacity / 1000000 * (-1)
                Profileraw["Dchgcap"] = Profileraw["Dchgcap"] / mincapacity / 1000000
            else:
                Profileraw["Current[mA]"] = Profileraw["Current[mA]"] / mincapacity / 1000 * (-1)
                Profileraw["Dchgcap"] = Profileraw["Dchgcap"] / mincapacity / 1000
            
            Profileraw["Temp1[Deg]"] = Profileraw["Temp1[Deg]"] / 1000
            
            stepmin = Profileraw.step.min()
            stepmax = Profileraw.step.max()
            stepdiv = stepmax - stepmin
            
            if not np.isnan(stepdiv):
                if stepdiv == 0:
                    df.Profile = Profileraw
                else:
                    Profiles = [Profileraw.loc[Profileraw.step == stepmin]]
                    for i in range(1, int(stepdiv) + 1):
                        next_prof = Profileraw.loc[Profileraw.step == stepmin + i].copy()
                        next_prof["PassTime[Sec]"] += Profiles[-1]["PassTime[Sec]"].max()
                        next_prof["Dchgcap"] += Profiles[-1]["Dchgcap"].max()
                        Profiles.append(next_prof)
                    df.Profile = pd.concat(Profiles)
        
        if hasattr(df, 'Profile'):
            df.Profile = df.Profile.reset_index()
            # cut-off
            df.Profile = df.Profile[(df.Profile["Voltage[V]"] >= cutoff)]
            
            # 방전 용량 산정, dQdV 산정
            df.Profile["dQdV"] = 0
            df.Profile["dVdQ"] = 0
            df.Profile["delcap"] = 0
            df.Profile["delvol"] = 0
            
            if smoothdegree == 0:
                smoothdegree = int(len(df.Profile) / 30)
            
            df.Profile["delvol"] = df.Profile["Voltage[V]"].diff(periods=smoothdegree)
            df.Profile["delcap"] = df.Profile["Dchgcap"].diff(periods=smoothdegree)
            df.Profile["dQdV"] = df.Profile["delcap"] / df.Profile["delvol"]
            df.Profile["dVdQ"] = df.Profile["delvol"] / df.Profile["delcap"]
            
            df.Profile = df.Profile[["PassTime[Sec]", "Dchgcap", "Dchgwh", "Voltage[V]", 
                                     "Current[mA]", "dQdV", "dVdQ", "Temp1[Deg]"]]
            df.Profile.columns = ["TimeMin", "SOC", "Energy", "Vol", "Crate", "dQdV", "dVdQ", "Temp"]
    
    return [mincapacity, df]


def pne_continue_profile_scale_change(
    raw_file_path: str,
    df: pd.DataFrame,
    mincapacity: float
) -> pd.DataFrame:
    """PNE 연속 데이터 스케일 변환.
    
    전기화학적 맥락:
        PNE 원시 데이터의 단위를 표준 단위로 변환합니다.
        - 시간: /100s → 초
        - 전압: μV → V
        - 전류: μA → mA, C-rate 계산
        - 용량: μAh → mAh, 정규화
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로 (PNE21/22 판별용)
        df: 변환할 DataFrame
        mincapacity: 정격 용량 (mAh)
    
    Returns:
        변환된 DataFrame
    """
    df = df.reset_index()
    df["TotTime[Day]"] = df["TotTime[Day]"] * 8640000
    df["TotTime[Sec]"] = (df["TotTime[Sec]"] + df["TotTime[Day]"]) / 100
    
    # 시작값 0으로 변경
    df["TotTime[Sec]"] = df["TotTime[Sec]"] - df.loc[0, "TotTime[Sec]"]
    df["TotTime[Min]"] = df["TotTime[Sec]"] / 60
    df["Voltage[V]"] = df["Voltage[V]"] / 1000000
    
    if ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path):
        df["Crate"] = (df["Current[mA]"] / mincapacity / 1000000).round(2)
        df["Current[mA]"] = df["Current[mA]"] / 1000000000
        df["ChgCap"] = df["ChgCap"] / mincapacity / 1000000
        df["DchgCap"] = df["DchgCap"] / mincapacity / 1000000
    else:
        df["Crate"] = (df["Current[mA]"] / mincapacity / 1000).round(2)
        df["Current[mA]"] = df["Current[mA]"] / 1000000
        df["ChgCap"] = df["ChgCap"] / mincapacity / 1000
        df["DchgCap"] = df["DchgCap"] / mincapacity / 1000
    
    df["SOC"] = df["DchgCap"] + df["ChgCap"]
    df["Temp1[Deg]"] = df["Temp1[Deg]"] / 1000
    df["StepTime"] = df["StepTime"] / 100
    
    return df


def pne_Profile_continue_data(
    raw_file_path: str,
    inicycle: int,
    endcycle: int,
    mincapacity: float,
    inirate: float,
    CDstate: str
) -> list:
    """PNE 연속 Profile 데이터 처리.
    
    전기화학적 맥락:
        여러 cycle에 걸친 연속 데이터를 처리합니다.
        CDstate에 따라 충전/방전/전체 데이터를 선택합니다.
        - CHG: 충전만
        - DCHG/DCH: 방전만
        - Cycle/7cyc/GITT: 전체 cycle
        - "": OCV/CCV 테이블 포함 처리
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        inicycle: 시작 cycle 번호
        endcycle: 종료 cycle 번호
        mincapacity: 정격 용량 (0이면 자동)
        inirate: 첫 cycle C-rate
        CDstate: 충방전 상태 ("CHG", "DCHG", "DCH", "Cycle", "7cyc", "GITT", "")
    
    Returns:
        [mincapacity, df, CycfileSOC] 리스트
    """
    df = pd.DataFrame()
    CycfileSOC = pd.DataFrame()
    
    if raw_file_path[-4:-1] != "ter":
        if CDstate != "":
            # PNE 채널, 용량 산정
            tempcap = pne_min_cap(raw_file_path, mincapacity, inirate)
            mincapacity = tempcap
            
            # data 기본 처리
            pneProfile = pne_continue_data(raw_file_path, inicycle, endcycle)
            
            if hasattr(pneProfile, 'Profileraw'):
                Profileraw = pneProfile.Profileraw
                
                if CDstate == "CHG":
                    Profileraw = Profileraw.loc[
                        (Profileraw[27] >= inicycle) & (Profileraw[27] <= endcycle) & 
                        Profileraw[2].isin([9, 1])
                    ]
                elif (CDstate == "DCHG") or (CDstate == "DCH"):
                    Profileraw = Profileraw.loc[
                        (Profileraw[27] >= inicycle) & (Profileraw[27] <= endcycle) & 
                        Profileraw[2].isin([9, 2])
                    ]
                elif (CDstate == "Cycle") or (CDstate == "7cyc") or (CDstate == "GITT"):
                    Profileraw = Profileraw.loc[
                        (Profileraw[27] >= inicycle) & (Profileraw[27] <= endcycle)
                    ]
                
                Profileraw = Profileraw[[0, 18, 19, 8, 9, 21, 10, 11, 7, 17]]
                Profileraw.columns = ["index", "TotTime[Day]", "TotTime[Sec]", "Voltage[V]", 
                                      "Current[mA]", "Temp1[Deg]", "ChgCap", "DchgCap", 
                                      "step", "StepTime"]
                Profileraw = pne_continue_profile_scale_change(raw_file_path, Profileraw, mincapacity)
                df.stepchg = Profileraw
                
                if hasattr(df, "stepchg"):
                    df.stepchg = df.stepchg[["TotTime[Sec]", "TotTime[Min]", "SOC", 
                                             "Voltage[V]", "Current[mA]", "Crate", "Temp1[Deg]"]]
                    df.stepchg.columns = ["TimeSec", "TimeMin", "SOC", "Vol", "Curr", "Crate", "Temp"]
        else:
            # PNE 채널, 용량 산정
            tempcap = pne_min_cap(raw_file_path, mincapacity, inirate)
            mincapacity = tempcap
            
            # data 기본 처리
            pneProfile = pne_continue_data(raw_file_path, inicycle, endcycle)
            pnecyc = pne_cyc_continue_data(raw_file_path)
            
            if hasattr(pnecyc, "Cycrawtemp") and hasattr(pneProfile, 'Profileraw'):
                # cycle 데이터를 기준으로 OCV, CCV 데이터 확인
                pnecyc.Cycrawtemp = pnecyc.Cycrawtemp.loc[
                    (pnecyc.Cycrawtemp[27] >= inicycle) & (pnecyc.Cycrawtemp[27] <= endcycle)
                ]
                CycfileCap = pnecyc.Cycrawtemp.loc[
                    ((pnecyc.Cycrawtemp[2] == 1) | (pnecyc.Cycrawtemp[2] == 2)), [0, 8, 10, 11]
                ]
                CycfileCap = CycfileCap.copy()
                CycfileCap.loc[:, "AccCap"] = (CycfileCap.loc[:, 10].cumsum() - CycfileCap[11].cumsum())
                CycfileCap = CycfileCap.reset_index()
                CycfileCap.loc[:, "AccCap"] = (CycfileCap.loc[:, "AccCap"] - CycfileCap.loc[0, "AccCap"]) / 1000
                
                CycfileOCV = pnecyc.Cycrawtemp.loc[(pnecyc.Cycrawtemp[2] == 3), [0, 8]]
                CycfileCCV = pnecyc.Cycrawtemp.loc[
                    ((pnecyc.Cycrawtemp[2] == 1) | (pnecyc.Cycrawtemp[2] == 2)), [0, 8]
                ]
                Cycfileraw = pd.merge(CycfileOCV, CycfileCCV, on=0, how='outer')
                
                # Cap, OCV, CCV table 별도 산정
                tempCap = CycfileCap.loc[:, "AccCap"].dropna(axis=0).tolist()
                Cap = [abs(i / mincapacity) for i in tempCap]
                tempOCV = CycfileOCV[8].dropna(axis=0).tolist()
                OCV = [i / 1000000 for i in tempOCV]
                tempCCV = CycfileCCV[8].dropna(axis=0).tolist()
                CCV = [i / 1000000 for i in tempCCV]
                
                min_length = min(len(Cap), len(OCV), len(CCV))
                CycfileSOC = pd.DataFrame({
                    "AccCap": Cap[:min_length], 
                    "OCV": OCV[:min_length], 
                    "CCV": CCV[:min_length]
                })
                
                # Profile 데이터를 기준으로 산정
                Profileraw = pneProfile.Profileraw
                Profileraw = Profileraw.loc[
                    (Profileraw[27] >= inicycle) & (Profileraw[27] <= endcycle)
                ]
                Profileraw = Profileraw[[0, 18, 19, 8, 9, 21, 10, 11, 7, 17]]
                Profileraw = pd.merge(Profileraw, Cycfileraw, on=0, how='outer')
                Profileraw.columns = ["index", "TotTime[Day]", "TotTime[Sec]", "Voltage[V]", 
                                      "Current[mA]", "Temp1[Deg]", "ChgCap", "DchgCap", 
                                      "step", "StepTime", "OCV", "CCV"]
                Profileraw["OCV"] = Profileraw["OCV"] / 1000000
                Profileraw["CCV"] = Profileraw["CCV"] / 1000000
                Profileraw = pne_continue_profile_scale_change(raw_file_path, Profileraw, mincapacity)
                df.stepchg = Profileraw
                
                if hasattr(df, "stepchg"):
                    df.stepchg = df.stepchg[["TotTime[Sec]", "TotTime[Min]", "SOC", 
                                             "Voltage[V]", "Current[mA]", "Crate", 
                                             "Temp1[Deg]", "OCV", "CCV"]]
                    df.stepchg.columns = ["TimeSec", "TimeMin", "SOC", "Vol", "Curr", 
                                          "Crate", "Temp", "OCV", "CCV"]
    
    return [mincapacity, df, CycfileSOC]


# ============================================================================
# PNE DCIR 처리 함수
# 📌 활용 스킬: scientific-critical-thinking
# ============================================================================

def pne_dcir_chk_cycle(raw_file_path: str) -> List[str]:
    """PNE DCIR 가능한 cycle 범위 확인.
    
    전기화학적 맥락:
        DCIR 측정이 수행된 cycle 범위를 확인합니다.
        20s pulse 조건 (steptime == 2000)을 기준으로 판별합니다.
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
    
    Returns:
        ["min-max", ...] 형태의 cycle 범위 리스트
    """
    result = []
    
    if raw_file_path[-4:-1] != "ter":
        pne_dcir_chk = pne_cyc_continue_data(raw_file_path)
        
        if hasattr(pne_dcir_chk, "Cycrawtemp"):
            df = pne_dcir_chk.Cycrawtemp
            df = df[[27, 2, 10, 11, 8, 20, 45, 15, 17, 9, 24, 29, 6]]
            df.columns = ["TotlCycle", "Condition", "chgCap", "DchgCap", "Ocv", "imp", "volmax",
                          "DchgEngD", "steptime", "Curr", "Temp", "AvgV", "EndState"]
            
            # 조건에 맞는 데이터 필터링 (방전 20s pulse)
            filtered_df = df[(df['Condition'] == 2) & (df['EndState'] == 64) & (df['steptime'] == 2000)]
            filtered_df2 = df[(df['Condition'] == 1) & (df['EndState'] == 64) & (df['steptime'] == 2000)]
            
            if not filtered_df.empty:
                min_value = filtered_df['TotlCycle'].min()
                max_value = filtered_df['TotlCycle'].max()
                result = [f"{min_value}-{max_value}"]
                
                if not filtered_df2.empty:
                    min_value2 = filtered_df2['TotlCycle'].min()
                    max_value2 = filtered_df2['TotlCycle'].max()
                    result.append(f"{min_value2}-{max_value2}")
    
    return result


def pne_dcir_Profile_data(
    raw_file_path: str,
    inicycle: int,
    endcycle: int,
    mincapacity: float,
    inirate: float
) -> list:
    """PNE DCIR Profile 데이터 처리.
    
    전기화학적 맥락:
        DCIR (DC Internal Resistance) 측정 데이터를 처리합니다.
        다양한 시간 간격(0, 0.3, 1, 10, 20초)에서의 전압 변화를 분석합니다.
        Slope-based DCIR: 전류-전압 기울기로 저항 계산
        RSS (Rest State Resistance): 휴지 후 전압 기반 저항 계산
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        inicycle: 시작 cycle 번호
        endcycle: 종료 cycle 번호
        mincapacity: 정격 용량 (0이면 자동)
        inirate: 첫 cycle C-rate
    
    Returns:
        [mincapacity, Profileraw, CycfileCap] 리스트
    """
    Profileraw = pd.DataFrame()
    CycfileCap = pd.DataFrame()
    
    if raw_file_path[-4:-1] != "ter":
        # PNE 채널, 용량 산정
        tempcap = pne_min_cap(raw_file_path, mincapacity, inirate)
        mincapacity = tempcap
        
        # data 기본 처리
        pneProfile = pne_continue_data(raw_file_path, inicycle, endcycle)
        pnecycraw = pne_cyc_continue_data(raw_file_path)
        
        if hasattr(pneProfile, 'Profileraw'):
            Profileraw = pneProfile.Profileraw
            Profileraw = Profileraw.loc[
                (Profileraw[27] >= inicycle) & (Profileraw[27] <= endcycle)
            ]
            Profileraw = Profileraw[[0, 18, 19, 8, 9, 21, 10, 11, 7, 27, 17]]
            Profileraw.columns = ["index", "TotTime[Day]", "TotTime[Sec]", "Voltage[V]", 
                                  "Current[mA]", "Temp1[Deg]", "ChgCap", "DchgCap", 
                                  "step", "TotCyc", "StepTime"]
            
            # 20s 종료되는 step을 기준으로 DCIR step, 전류 산정
            dcir_base = Profileraw.loc[Profileraw["StepTime"] == 20]
            dcir_base = dcir_base.reset_index(drop=True)
            dcir_step = list(set(dcir_base["step"].tolist()))
            
            # 율별 pulse C-rate 확인
            if len(dcir_base) >= 4:
                if ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path):
                    dcir_crate = [round((dcir_base.loc[i, "Current[mA]"] / 1000000) / mincapacity, 2) 
                                  for i in range(0, 4)]
                else:
                    dcir_crate = [round((dcir_base.loc[i, "Current[mA]"] / 1000) / mincapacity, 2) 
                                  for i in range(0, 4)]
                dcir_crate.sort()
            else:
                dcir_crate = []
            
            # DCIR 시간을 0.2초로 변경
            dcir_time = [0.0, 0.3, 1.0, 10.0, 20.0]
            
            # Profile 데이터를 기준으로 산정
            Profileraw = pne_continue_profile_scale_change(raw_file_path, Profileraw, mincapacity)
            Profileraw = Profileraw[Profileraw["step"].isin(dcir_step)]
            Profileraw = Profileraw[Profileraw["StepTime"].isin(dcir_time)]
            if dcir_crate:
                Profileraw = Profileraw[Profileraw["Crate"].isin(dcir_crate)]
            Profileraw = Profileraw[["TotTime[Sec]", "TotTime[Min]", "Voltage[V]", 
                                     "Current[mA]", "Crate", "Temp1[Deg]", "step", 
                                     "TotCyc", "StepTime"]]
            Profileraw.columns = ["TimeSec", "TimeMin", "Vol", "Curr", "Crate", 
                                  "Temp", "step", "Cyc", "StepTime"]
        
        if hasattr(pnecycraw, "Cycrawtemp"):
            # cycle 데이터를 기준으로 OCV, CCV 데이터 확인
            pnecyc = pnecycraw.Cycrawtemp
            pnecyc2 = pnecycraw.Cycrawtemp.copy()
            
            pnecyc = pnecyc.loc[(pnecyc[27] >= (inicycle - 1)) & (pnecyc[27] <= (endcycle - 1))]
            pnecyc2 = pnecyc2.loc[(pnecyc2[27] >= inicycle) & (pnecyc2[27] <= endcycle)]
            
            if len(pnecyc) != 0 and len(pnecyc2) != 0:
                CycfileCap = pnecyc.loc[(pnecyc[2] == 8), [0, 27, 10, 11, 8, 9]]
                real_ocv = pnecyc2.loc[
                    (pnecyc2[2] == 3) & 
                    (pnecyc2[17].isin([360000, 720000, 1080000, 2160000])), 
                    [8]
                ]
                real_ocv = real_ocv.reset_index()
                
                CycfileCap = CycfileCap.copy()
                CycfileCap["AccCap"] = (CycfileCap.loc[:, 10].cumsum() - CycfileCap[11].cumsum())
                CycfileCap = CycfileCap.reset_index()
                CycfileCap["AccCap"] = abs((CycfileCap.loc[:, "AccCap"] - CycfileCap.loc[0, "AccCap"]) / 1000)
                
                if ('PNE21' in raw_file_path) or ('PNE22' in raw_file_path):
                    CycfileCap["AccCap"] = CycfileCap["AccCap"] / 1000
                
                if dcir_crate and dcir_crate[-2] < 0:
                    CycfileCap["SOC"] = (1 - CycfileCap["AccCap"] / mincapacity) * 100
                else:
                    CycfileCap["SOC"] = (CycfileCap["AccCap"] / mincapacity) * 100
                
                CycfileCap["SOC"] = CycfileCap["SOC"] - (CycfileCap["SOC"].max() - 100)
                CycfileCap["Cyc"] = CycfileCap[27]
                
                if len(real_ocv) > 0:
                    CycfileCap["rOCV"] = real_ocv[8].values[:len(CycfileCap)] / 1000000
                CycfileCap["CCV"] = CycfileCap[8] / 1000000
                CycfileCap["curr"] = CycfileCap[9] / 1000000
                CycfileCap.loc[0, "CCV"] = np.nan
                CycfileCap["RSS"] = abs((CycfileCap["CCV"] - CycfileCap["rOCV"]) / CycfileCap["curr"]) * 1000
                CycfileCap = CycfileCap[["Cyc", "AccCap", "SOC", "CCV", "rOCV", "RSS"]]
                CycfileCap["Cyc"] = CycfileCap["Cyc"] + 1
    
    return [mincapacity, Profileraw, CycfileCap]


# ============================================================================
# PNE 시뮬레이션 함수 (수명 예측용)
# 📌 활용 스킬: scientific-critical-thinking
# ============================================================================

def pne_simul_cycle_data(
    raw_file_path: str,
    min_capacity: float,
    ini_crate: float
) -> list:
    """PNE 시뮬레이션용 Cycle 데이터 처리.
    
    전기화학적 맥락:
        수명 예측 시뮬레이션을 위한 데이터 전처리입니다.
        0.5C와 0.2C 방전 데이터를 분리하여 분석합니다.
        - 0.5C: 가속 노화 패턴 (고율 방전)
        - 0.2C: RPT (Reference Performance Test) 패턴
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        min_capacity: 정격 용량 (0이면 자동)
        ini_crate: 첫 cycle C-rate
    
    Returns:
        [mincapacity, df05, df05_cap_max, df02, df02_cap_max, 
         df05_long_cycle, df05_long_value, df_all] 리스트
    """
    df_all = pd.DataFrame()
    df02 = pd.DataFrame()
    df02_cap_max = 0
    df05 = pd.DataFrame()
    df05_cap_max = 0
    df05_long_cycle = []
    df05_long_value = []
    mincapacity = 0
    
    if raw_file_path[-4:-1] != "ter":
        # PNE 채널, 용량 산정
        mincapacity = pne_min_cap(raw_file_path, min_capacity, ini_crate)
        
        # data 기본 처리 (csv data loading)
        restore_dir = raw_file_path + "\\Restore\\"
        if os.path.isdir(restore_dir):
            subfile = [f for f in os.listdir(restore_dir) if f.endswith('.csv')]
            
            for files in subfile:
                if "SaveEndData.csv" in files:
                    file_path = restore_dir + files
                    if os.stat(file_path).st_size != 0:
                        Cycleraw = pd.read_csv(
                            file_path, sep=",", skiprows=0, engine="c",
                            header=None, encoding="cp949", on_bad_lines='skip'
                        )
                        Cycleraw = Cycleraw[[27, 2, 11, 9, 24, 6, 8]]
                        Cycleraw.columns = ["TotlCycle", "Condition", "DchgCap", "Curr", 
                                            "Temp", "EndState", "Vol"]
            
            if 'Cycleraw' in locals() and not Cycleraw.empty:
                # condition을 기준으로 용량 산정
                max_cap = Cycleraw.query("Condition == 2").pivot_table(
                    index="TotlCycle", columns="Condition", values="DchgCap", aggfunc="sum"
                )
                max_vol = Cycleraw.query("Condition == 1").pivot_table(
                    index="TotlCycle", columns="Condition", values="Vol", aggfunc="max"
                )
                min_vol = Cycleraw.query("Condition == 2").pivot_table(
                    index="TotlCycle", columns="Condition", values="Vol", aggfunc="min"
                )
                min_crate = Cycleraw.query("Condition == 2").pivot_table(
                    index="TotlCycle", columns="Condition", values="Curr", aggfunc="max"
                )
                avg_temp = Cycleraw.query("Condition == 2").pivot_table(
                    index="TotlCycle", columns="Condition", values="Temp", aggfunc="mean"
                )
                
                df_all = pd.DataFrame({
                    "Temp": avg_temp.iloc[:, 0] if len(avg_temp.columns) > 0 else [],
                    "Curr": min_crate.iloc[:, 0] if len(min_crate.columns) > 0 else [],
                    "Dchg": max_cap.iloc[:, 0] if len(max_cap.columns) > 0 else [],
                    "max_vol": max_vol.iloc[:, 0] if len(max_vol.columns) > 0 else [],
                    "min_vol": min_vol.iloc[:, 0] if len(min_vol.columns) > 0 else []
                })
                
                df_all["Temp"] = df_all["Temp"] / 1000
                df_all["Curr"] = -1 * df_all["Curr"] / mincapacity / 1000
                df_all["max_vol"] = df_all["max_vol"] / 1000
                df_all["Dchg"] = df_all["Dchg"] / mincapacity / 1000
                df_all["min_vol"] = df_all["min_vol"] / 1000
                
                # 0.5C 데이터 처리
                df05 = df_all.query('0.490 < Curr < 0.510').copy()
                
                if len(df05) > 40:
                    df05["Dchg_Diff"] = df05["Dchg"].diff()
                    df05["max_vol_diff"] = df05["max_vol"].diff()
                    df05["min_vol_diff"] = df05["min_vol"].diff()
                    df05 = df05.loc[df05["Dchg"].idxmax():]
                    df05_cap_max = df05["Dchg"].iloc[0] - df05["Dchg_Diff"].iloc[0:30].mean() * float(df05.index[0])
                    df05["Dchg"] = df05["Dchg"] / df05_cap_max
                    df05["long"] = 0
                    
                    # 장수명 부분 제거 관련 코드
                    for i in range(len(df05) - 1):
                        if ((df05["max_vol_diff"].iloc[i] < -15) | 
                            (df05["min_vol_diff"].iloc[i] > 50)) & (i > 0):
                            df05.iloc[i, df05.columns.get_loc("long")] = df05["Dchg_Diff"].iloc[i]
                            df05_long_cycle.append(df05.index[i])
                            df05_long_value.append(df05["Dchg_Diff"].iloc[i])
                    
                    df05["long_acc"] = df05["long"].cumsum()
                
                # 0.2C 데이터 처리
                df02 = df_all.query('0.190 < Curr < 0.210').copy()
                df02_max_vol = df_all["max_vol"].max()
                df02 = df02[df02["max_vol"] > (df02_max_vol - 10)]
                
                if len(df02) > 3:
                    df02 = df02.iloc[1:]
                    if len(df02) > 1 and (df02.index[1] - df02.index[0]) < 40:
                        df02 = df02.iloc[1::2]
                    df02.index = df02.index - df02.index[0]
                    df02["Dchg_Diff"] = df02["Dchg"].diff()
                    df02 = df02.loc[df02["Dchg"].idxmax():]
                    if len(df02) > 1:
                        df02_cap_max = df02["Dchg"].max() - df02["Dchg_Diff"].iloc[1] * df02.index[0] / (df02.index[1] - df02.index[0])
                    else:
                        df02_cap_max = df02["Dchg"].max()
                    df02["Dchg"] = df02["Dchg"] / df02_cap_max
    
    return [mincapacity, df05, df05_cap_max, df02, df02_cap_max, df05_long_cycle, df05_long_value, df_all]


def pne_simul_cycle_data_file(
    df_all: pd.DataFrame,
    raw_file_path: str,
    min_capacity: float,
    ini_crate: float
) -> list:
    """PNE 파일 기반 시뮬레이션 Cycle 데이터 처리.
    
    이미 로드된 df_all 데이터에서 시뮬레이션용 데이터를 추출합니다.
    
    Args:
        df_all: 전체 cycle 데이터 DataFrame
        raw_file_path: 원시 데이터 폴더 경로 (용량 산정용)
        min_capacity: 정격 용량 (0이면 자동)
        ini_crate: 첫 cycle C-rate
    
    Returns:
        [mincapacity, df05, df05_cap_max, df02, df02_cap_max, 
         df05_long_cycle, df05_long_value, df_all] 리스트
    """
    df02 = pd.DataFrame()
    df02_cap_max = 0
    df05 = pd.DataFrame()
    df05_cap_max = 0
    df05_long_cycle = []
    df05_long_value = []
    
    # PNE 채널, 용량 산정
    mincapacity = pne_min_cap(raw_file_path, min_capacity, ini_crate)
    
    # 0.5C 데이터 처리
    df05 = df_all.query('0.490 < Curr < 0.510').copy()
    
    if len(df05) > 40:
        df05["Dchg_Diff"] = df05["Dchg"].diff()
        df05["max_vol_diff"] = df05["max_vol"].diff()
        df05["min_vol_diff"] = df05["min_vol"].diff()
        df05 = df05.loc[df05["Dchg"].idxmax():]
        df05_cap_max = df05["Dchg"].iloc[0] - df05["Dchg_Diff"].iloc[0:30].mean() * float(df05.index[0])
        df05["Dchg"] = df05["Dchg"] / df05_cap_max
        df05["long"] = 0
        
        # 장수명 부분 제거 관련 코드
        for i in range(len(df05) - 1):
            if ((df05["max_vol_diff"].iloc[i] < -15) | 
                (df05["min_vol_diff"].iloc[i] > 50)) & (i > 0):
                df05.iloc[i, df05.columns.get_loc("long")] = df05["Dchg_Diff"].iloc[i]
                df05_long_cycle.append(df05.index[i])
                df05_long_value.append(df05["Dchg_Diff"].iloc[i])
        
        df05["long_acc"] = df05["long"].cumsum()
    
    # 0.2C 데이터 처리
    df02 = df_all.query('0.190 < Curr < 0.210').copy()
    df02_max_vol = df_all["max_vol"].max()
    df02 = df02[df02["max_vol"] > (df02_max_vol - 10)]
    
    if len(df02) > 3:
        df02 = df02.iloc[1:]
        if len(df02) > 1 and (df02.index[1] - df02.index[0]) < 40:
            df02 = df02.iloc[1::2]
        df02.index = df02.index - df02.index[0]
        df02["Dchg_Diff"] = df02["Dchg"].diff()
        df02 = df02.loc[df02["Dchg"].idxmax():]
        if len(df02) > 1:
            df02_cap_max = df02["Dchg"].max() - df02["Dchg_Diff"].iloc[1] * df02.index[0] / (df02.index[1] - df02.index[0])
        else:
            df02_cap_max = df02["Dchg"].max()
        df02["Dchg"] = df02["Dchg"] / df02_cap_max
    
    return [mincapacity, df05, df05_cap_max, df02, df02_cap_max, df05_long_cycle, df05_long_value, df_all]

