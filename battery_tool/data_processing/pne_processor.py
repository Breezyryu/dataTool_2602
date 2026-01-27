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
