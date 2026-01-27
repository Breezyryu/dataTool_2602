"""
Battery Data Tool - Toyo Processor Module

Toyo 충방전기 데이터 처리 함수
원본: origin_datatool/BatteryDataTool.py (Lines 443-620+)

📌 활용 스킬: scientific-critical-thinking

충방전기 데이터 구조:
    Toyo 충방전기는 capacity.log 파일과 개별 cycle 파일로 데이터를 저장합니다.
    - capacity.log: 전체 cycle 요약 데이터
    - 000001, 000002, ...: 각 cycle의 상세 profile 데이터
"""

import os
import sys
import re
import pandas as pd
import numpy as np
from typing import Optional, Any

# 순환 import 방지를 위해 함수 내부에서 import
# from ..utils.helpers import name_capacity


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


def toyo_read_csv(*args) -> Optional[pd.DataFrame]:
    """Toyo 데이터 CSV 파일 읽기.
    
    Args:
        *args: 가변 인자
            - args[0]: 폴더 경로
            - args[1]: (선택) cycle 번호
    
    Returns:
        DataFrame 또는 None (파일 없을 경우)
    
    Example:
        >>> df = toyo_read_csv("path/to/data")  # capacity.log 읽기
        >>> df = toyo_read_csv("path/to/data", 1)  # cycle 1 읽기
    """
    if len(args) == 1:
        filepath = args[0] + "\\capacity.log"
        skiprows = 0
    else:
        filepath = args[0] + "\\%06d" % args[1]
        skiprows = 3
    
    if os.path.isfile(filepath):
        dataraw = pd.read_csv(
            filepath, sep=",", skiprows=skiprows,
            engine="c", encoding="cp949", on_bad_lines='skip'
        )
        return dataraw
    return None


def toyo_Profile_import(raw_file_path: str, cycle: int) -> Any:
    """Toyo Profile 데이터 불러오기.
    
    전기화학적 맥락:
        Profile 데이터는 시간에 따른 전압/전류/온도 변화를 기록합니다.
        CC-CV 충전, CC 방전의 상세 곡선을 분석할 수 있습니다.
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        cycle: 불러올 cycle 번호
    
    Returns:
        df 객체 (df.dataraw에 데이터 저장)
    """
    df = pd.DataFrame()
    dataraw = toyo_read_csv(raw_file_path, cycle)
    
    if dataraw is not None and not dataraw.empty:
        if "PassTime[Sec]" in dataraw.columns:
            if "Temp1[Deg]" in dataraw.columns:
                # Toyo BLK 3600_3000
                dataraw = dataraw[["PassTime[Sec]", "Voltage[V]", "Current[mA]", 
                                   "Condition", "Temp1[Deg]"]]
            else:
                # 신뢰성 충방전기 (Temp 없음)
                dataraw = dataraw[["PassTime[Sec]", "Voltage[V]", "Current[mA]", 
                                   "Condition", "TotlCycle"]]
                dataraw.columns = ["PassTime[Sec]", "Voltage[V]", "Current[mA]", 
                                   "Condition", "Temp1[Deg]"]
        else:
            # Toyo BLK5200
            dataraw = dataraw[["Passed Time[Sec]", "Voltage[V]", "Current[mA]", 
                               "Condition", "Temp1[deg]"]]
            dataraw.columns = ["PassTime[Sec]", "Voltage[V]", "Current[mA]", 
                               "Condition", "Temp1[Deg]"]
        df.dataraw = dataraw
    return df


def toyo_cycle_import(raw_file_path: str) -> Any:
    """Toyo Cycle 요약 데이터 불러오기.
    
    전기화학적 맥락:
        capacity.log 파일에서 각 cycle의 요약 통계를 읽습니다:
        - TotlCycle: 누적 cycle 번호
        - Condition: 1=충전, 2=방전
        - Cap[mAh]: 용량
        - Ocv: 휴지 후 개방회로전압
        - PeakTemp[Deg]: 최고 온도
        - AveVolt[V]: 평균 전압
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
    
    Returns:
        df 객체 (df.dataraw에 데이터 저장)
    """
    df = pd.DataFrame()
    dataraw = toyo_read_csv(raw_file_path)
    
    if dataraw is not None and not dataraw.empty:
        if "Cap[mAh]" in dataraw.columns:
            dataraw = dataraw[["TotlCycle", "Condition", "Cap[mAh]", "Ocv", "Finish", 
                               "Mode", "PeakVolt[V]", "Pow[mWh]", "PeakTemp[Deg]", "AveVolt[V]"]]
        else:
            dataraw = dataraw[["Total Cycle", "Condition", "Capacity[mAh]", "OCV[V]", 
                               "End Factor", "Mode", "Peak Volt.[V]", "Power[mWh]",
                               "Peak Temp.[deg]", "Ave. Volt.[V]"]]
            dataraw.columns = ["TotlCycle", "Condition", "Cap[mAh]", "Ocv", "Finish", 
                               "Mode", "PeakVolt[V]", "Pow[mWh]", "PeakTemp[Deg]", "AveVolt[V]"]
        df.dataraw = dataraw
    return df


def toyo_min_cap(raw_file_path: str, mincapacity: float, inirate: float) -> float:
    """Toyo 데이터에서 최소 용량(정격 용량) 산정.
    
    전기화학적 맥락:
        정격 용량은 C-rate 계산의 기준입니다.
        C-rate = 전류(mA) / 용량(mAh)
        
        산정 방법:
        1. 사용자가 직접 입력한 경우: 해당 값 사용
        2. 파일명에 mAh가 포함된 경우: 파일명에서 추출
        3. 그 외: 첫 cycle 전류를 기준 C-rate로 나누어 계산
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        mincapacity: 사용자 입력 용량 (0이면 자동 산정)
        inirate: 첫 cycle 기준 C-rate (기본 0.2C)
    
    Returns:
        산정된 정격 용량 (mAh)
    """
    if mincapacity == 0:
        if "mAh" in raw_file_path:
            mincap = name_capacity(raw_file_path)
        else:
            inicapraw = toyo_read_csv(raw_file_path, 1)
            if inicapraw is not None:
                mincap = int(round(inicapraw["Current[mA]"].max() / inirate))
            else:
                mincap = 0
    else:
        mincap = mincapacity
    return mincap


def toyo_cycle_data(raw_file_path: str, mincapacity: float, inirate: float, chkir: bool) -> list:
    """Toyo Cycle 데이터 처리.
    
    전기화학적 맥락:
        capacity.log에서 추출한 원시 데이터를 정리하여
        수명 분석에 필요한 지표들을 계산합니다:
        
        주요 출력 지표:
        - Dchg: 방전 용량 비율 (정격 대비)
        - Chg: 충전 용량 비율
        - Eff: 쿨롱 효율 (Dchg/Chg)
        - Eff2: 역방향 효율 (Chg2/Dchg)
        - RndV: 휴지 종료 전압 (OCV)
        - AvgV: 평균 방전 전압
        - Temp: 최고 온도
        - dcir: DC 내부저항 (mΩ)
        - DchgEng: 방전 에너지 (mWh)
        
        데이터 전처리:
        - 연속 충전/방전 step 병합
        - 최소 용량 이상만 유효 cycle로 인정
        - DCIR 계산 (전압 강하 / 전류)
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
        mincapacity: 정격 용량 (0이면 자동 산정)
        inirate: 첫 cycle 기준 C-rate
        chkir: DCIR 계산 여부 체크박스
    
    Returns:
        [mincapacity, df] 리스트
        - mincapacity: 산정된 정격 용량
        - df: 처리된 데이터 (df.NewData에 저장)
    """
    df = pd.DataFrame()
    
    # 용량 산정
    tempmincap = toyo_min_cap(raw_file_path, mincapacity, inirate)
    mincapacity = tempmincap
    
    # CSV 데이터 로딩
    tempdata = toyo_cycle_import(raw_file_path)
    
    if hasattr(tempdata, "dataraw") and not tempdata.dataraw.empty:
        Cycleraw = tempdata.dataraw.copy()
        
        # 기존 cycle 저장
        Cycleraw.loc[:, "OriCycle"] = Cycleraw.loc[:, "TotlCycle"]
        
        # 방전 시작 시 data 변경
        if Cycleraw.loc[0, "Condition"] == 2 and len(Cycleraw.index) > 2:
            if Cycleraw.loc[1, "TotlCycle"] == 1:
                Cycleraw.loc[Cycleraw["Condition"] == 2, "TotlCycle"] -= 1
                Cycleraw = Cycleraw.drop(0, axis=0)
                Cycleraw = Cycleraw.reset_index()
        
        # 연속 충전/방전 데이터 병합
        i = 0
        while i < len(Cycleraw) - 1:
            current_cond = Cycleraw.loc[i, "Condition"]
            next_cond = Cycleraw.loc[i + 1, "Condition"]
            if current_cond in (1, 2) and current_cond == next_cond:
                if current_cond == 1:
                    # 충전 데이터 처리 (용량 합산, OCV는 첫 step 유지)
                    Cycleraw.loc[i + 1, "Cap[mAh]"] += Cycleraw.loc[i, "Cap[mAh]"]
                    Cycleraw.loc[i + 1, "Ocv"] = Cycleraw.loc[i, "Ocv"]
                else:
                    # 방전 데이터 처리 (용량, 에너지 합산, 평균 전압 재계산)
                    Cycleraw.loc[i + 1, "Cap[mAh]"] += Cycleraw.loc[i, "Cap[mAh]"]
                    Cycleraw.loc[i + 1, "Pow[mWh]"] += Cycleraw.loc[i, "Pow[mWh]"]
                    Cycleraw.loc[i + 1, "AveVolt[V]"] = (
                        Cycleraw.loc[i + 1, "Pow[mWh]"] / Cycleraw.loc[i + 1, "Cap[mAh]"]
                    )
                Cycleraw = Cycleraw.drop(i, axis=0).reset_index(drop=True)
            else:
                i += 1
        
        # 충전 데이터 추출 (CV 종료 제외, 최소 용량 이상)
        chgdata = Cycleraw[
            (Cycleraw["Condition"] == 1) & 
            (Cycleraw["Finish"] != "                 Vol") & 
            (Cycleraw["Finish"] != "Volt") & 
            (Cycleraw["Cap[mAh]"] > (mincapacity / 60))
        ].copy()
        chgdata.index = chgdata["TotlCycle"]
        Chg = chgdata["Cap[mAh]"]
        Ocv = chgdata["Ocv"]
        
        Cycleraw.index = Cycleraw["TotlCycle"]
        
        # DCIR 데이터 추출
        dcir = Cycleraw[
            ((Cycleraw["Finish"] == "                 Tim") | 
             (Cycleraw["Finish"] == "Tim") | 
             (Cycleraw["Finish"] == "Time")) & 
            (Cycleraw["Condition"] == 2) & 
            (Cycleraw["Cap[mAh]"] < (mincapacity / 60))
        ].copy()
        cycnum = dcir["TotlCycle"]
        
        # 방전 데이터 추출
        Dchgdata = Cycleraw[
            (Cycleraw["Condition"] == 2) & 
            (Cycleraw["Cap[mAh]"] > (mincapacity / 60))
        ].copy()
        Dchg = Dchgdata["Cap[mAh]"]
        Temp = Dchgdata["PeakTemp[Deg]"]
        DchgEng = Dchgdata["Pow[mWh]"]
        Chg2 = Chg.shift(periods=-1)
        AvgV = Dchgdata["AveVolt[V]"]
        OriCycle = Dchgdata.loc[:, "OriCycle"]
        
        # DCIR 계산 (profile 데이터에서 전압 강하 추출)
        for cycle in cycnum:
            cycle_file = raw_file_path + "\\%06d" % cycle
            if os.path.isfile(cycle_file):
                dcirpro = pd.read_csv(
                    cycle_file, sep=",", skiprows=3,
                    engine="c", encoding="cp949", on_bad_lines='skip'
                )
                if "PassTime[Sec]" in dcirpro.columns:
                    dcirpro = dcirpro[["PassTime[Sec]", "Voltage[V]", "Current[mA]", 
                                       "Condition", "Temp1[Deg]"]]
                else:
                    dcirpro = dcirpro[["Passed Time[Sec]", "Voltage[V]", "Current[mA]", 
                                       "Condition", "Temp1[deg]"]]
                    dcirpro.columns = ["PassTime[Sec]", "Voltage[V]", "Current[mA]", 
                                       "Condition", "Temp1[Deg]"]
                
                dcircal = dcirpro[(dcirpro["Condition"] == 2)]
                if len(dcircal) > 0:
                    # DCIR = ΔV / I * 1000000 (mΩ 변환)
                    dcir.loc[int(cycle), "dcir"] = (
                        (dcircal["Voltage[V]"].max() - dcircal["Voltage[V]"].min()) / 
                        round(dcircal["Current[mA]"].max()) * 1000000
                    )
        
        # DCIR cycle 번호 할당
        n = 1
        cyccal = []
        if len(dcir) != 0:
            if (len(Dchg) / (len(dcir) / 2)) >= 10:
                dcirstep = (int(len(Dchg) / (len(dcir) / 2) / 10) + 1) * 10
            else:
                dcirstep = int(len(Dchg) / (len(dcir) / 2)) + 1
            
            for i in range(len(dcir)):
                if chkir:
                    cyccal.append(n)
                    n = n + 1
                else:
                    cyccal.append(n)
                    if i % 2 == 0:
                        n = n + 1
                    else:
                        n = n + dcirstep - 1
        
        dcir["Cyc"] = cyccal
        dcir = dcir.set_index(dcir["Cyc"])
        
        # 효율 계산
        Eff = Dchg / Chg  # 쿨롱 효율
        Eff2 = Chg2 / Dchg  # 역방향 효율
        
        # 용량 비율로 변환
        Dchg = Dchg / mincapacity
        Chg = Chg / mincapacity
        
        # 결과 DataFrame 생성
        df.NewData = pd.DataFrame({
            "Dchg": Dchg,
            "RndV": Ocv,
            "Eff": Eff,
            "Chg": Chg,
            "DchgEng": DchgEng,
            "Eff2": Eff2,
            "Temp": Temp,
            "AvgV": AvgV,
            "OriCyc": OriCycle
        })
        df.NewData = df.NewData.dropna(axis=0, how='all', subset=['Dchg'])
        df.NewData = df.NewData.reset_index()
        
        if hasattr(dcir, "dcir"):
            df.NewData = pd.concat([df.NewData, dcir["dcir"]], axis=1, join="outer")
        else:
            df.NewData.loc[0, "dcir"] = 0
        
        df.NewData = df.NewData.drop("TotlCycle", axis=1)
    else:
        sys.exit()
    
    return [mincapacity, df]
