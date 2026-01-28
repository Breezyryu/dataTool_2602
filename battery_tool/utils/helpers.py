"""
Battery Data Tool - Utility Helpers Module

유틸리티 함수 모음: 날짜 변환, 용량 파싱, 충방전기 타입 감지 등
원본: BatteryDataTool.py (Lines 32-180)
"""

import os
import re
import bisect
from datetime import datetime, timezone
from typing import Union, Optional, List

import pandas as pd
from tkinter import filedialog


# ============================================================================
# 날짜/시간 유틸리티
# ============================================================================

def to_timestamp(date_str: str) -> int:
    """날짜 문자열을 Unix timestamp로 변환.
    
    Toyo 충방전기 데이터 파일의 타임스탬프 파싱에 사용됩니다.
    
    Args:
        date_str: "YYMMDD HH:MM:SS.msec" 형식의 날짜 문자열
                  예: "170102 12:30:45.123"
    
    Returns:
        Unix timestamp (초 단위, KST→UTC 보정됨)
    
    Example:
        >>> to_timestamp("170102 12:30:45.123")
        1483331445
    """
    # 형식 파싱 (YYMMDD HH:MM:SS.msec)
    year = int(date_str[:2])
    month = int(date_str[2:4])
    day = int(date_str[4:6])
    hour = int(date_str[7:9])
    minute = int(date_str[10:12])
    second = int(date_str[13:15])
    millisecond = int(date_str[16:19])

    # 연도는 2000년대를 가정 (예: 17 -> 2017)
    year += 2000

    # datetime 객체로 변환
    dt = datetime(year, month, day, hour, minute, second, 
                  millisecond * 1000, tzinfo=timezone.utc)
    # Unix Timestamp로 변환 (초 단위) - KST(+9) → UTC 보정
    return int(dt.timestamp() - 9 * 3600)


# ============================================================================
# 진행률 계산
# ============================================================================

def progress(count1: int, max1: int, 
             count2: int, max2: int, 
             count3: int, max3: int) -> float:
    """3단계 중첩 루프의 진행률 계산 (0-100%).
    
    GUI에서 데이터 처리 진행 상황을 표시할 때 사용됩니다.
    
    Args:
        count1, max1: 1단계 루프 (가장 바깥)
        count2, max2: 2단계 루프 (중간)
        count3, max3: 3단계 루프 (가장 안쪽)
    
    Returns:
        진행률 (0.0 ~ 100.0)
    """
    progressdata = ((count1 + ((count2 + (count3 / max3) - 1) / max2) - 1) / max1 * 100)
    return progressdata


# ============================================================================
# 디렉토리/파일 유틸리티
# ============================================================================

def multi_askopendirnames() -> List[str]:
    """여러 디렉토리를 연속으로 선택.
    
    tkinter의 파일 다이얼로그를 사용하여 여러 배터리 셀 데이터 폴더를 
    일괄 선택할 수 있습니다.
    
    Returns:
        선택된 디렉토리 경로 리스트
    """
    directories = []
    while True:
        if len(directories) == 0:
            ini_dir = "d://"
        else:
            # 이전 선택의 상위 디렉토리에서 시작
            normalized_path = os.path.normpath(directories[-1])
            parent_dir = os.path.dirname(normalized_path)
            ini_dir = os.path.join(parent_dir, "")
        
        directory = filedialog.askdirectory(
            initialdir=ini_dir, 
            title="원하는 폴더를 계속해서 선택하세요"
        )
        if not directory:
            break
        directories.append(directory)
    return directories


# ============================================================================
# 문자열 파싱 유틸리티
# ============================================================================

def extract_text_in_brackets(input_string: str) -> str:
    """대괄호 [] 안의 텍스트 추출.
    
    폴더명에서 배터리 스펙을 파싱할 때 사용됩니다.
    
    Args:
        input_string: 대괄호를 포함한 문자열
    
    Returns:
        대괄호 안의 내용. 없으면 원본 문자열을 3자리로 패딩
    
    Example:
        >>> extract_text_in_brackets("[45V 4470mAh]")
        "45V 4470mAh"
        >>> extract_text_in_brackets("001")
        "001"
    """
    match = re.search(r'\[(.*?)\]', input_string)
    return match.group(1) if match else str(input_string).zfill(3)


def name_capacity(data_file_path: Union[str, list]) -> float:
    """파일 경로에서 배터리 용량(mAh)을 추출.
    
    전기화학적 맥락:
        정격 용량은 C-rate 계산의 기준이 됩니다.
        C-rate = 전류(mA) / 용량(mAh)
        예: 4500mAh 배터리에서 4500mA = 1C
    
    Args:
        data_file_path: 파일 경로 문자열
    
    Returns:
        용량(mAh). 추출 실패 시 0.0
    
    Example:
        >>> name_capacity("Cell_3500mAh_001")
        3500.0
        >>> name_capacity("4-187mAh_half")
        4.187
    """
    if not isinstance(data_file_path, list):
        # 특수 문자를 공백으로 대체
        raw_file_path = re.sub(r'[._@\$$$$$$\(\)]', ' ', data_file_path)
        # "숫자mAh" 패턴 찾기 (소수점은 '-' 또는 '.'로 표현)
        match = re.search(r'(\d+([\-\.]\d+)?)mAh', raw_file_path)
        if match:
            min_cap = match.group(1).replace('-', '.')
            return float(min_cap)
        return 0
    else:
        return 0


def convert_steplist(input_str: str) -> List[int]:
    """문자열을 스텝 번호 리스트로 변환.
    
    사용자가 입력한 스텝 범위를 파싱하여 Profile 데이터 필터링에 사용됩니다.
    
    Args:
        input_str: 스텝 범위 문자열 (예: "1 3-5 7")
    
    Returns:
        스텝 번호 리스트
    
    Example:
        >>> convert_steplist("1 3-5 7")
        [1, 3, 4, 5, 7]
    """
    output_list = []
    for part in input_str.split():
        if "-" in part:
            start, end = map(int, part.split("-"))
            output_list.extend(range(start, end + 1))
        else:
            output_list.append(int(part))
    return output_list


# ============================================================================
# 충방전기 관련 유틸리티
# ============================================================================

def check_cycler(raw_file_path: str) -> bool:
    """충방전기 타입 구분 (PNE vs Toyo).
    
    전기화학적 맥락:
        - PNE 충방전기: Pattern 폴더 기반 테스트 스케줄
        - Toyo 충방전기: capacity.log 파일 기반 cycle 데이터
    
    Args:
        raw_file_path: 원시 데이터 폴더 경로
    
    Returns:
        True = PNE, False = Toyo
    """
    # Pattern 폴더 유무로 PNE와 Toyo 구분
    cycler = os.path.isdir(raw_file_path + "\\Pattern")
    return cycler


# ============================================================================
# DataFrame 유틸리티
# ============================================================================

def separate_series(df_series: pd.Series, num: int) -> pd.DataFrame:
    """시리즈를 정해진 개수의 column으로 분리.
    
    Args:
        df_series: 입력 시리즈
        num: 분리할 열의 개수
    
    Returns:
        분리된 DataFrame
    """
    result_df = pd.DataFrame()
    for i, value in enumerate(df_series, 1):
        col_name = f'col{(i - 1) % num}'
        row_idx = (i - 1) // num
        result_df.at[row_idx, col_name] = value
    return result_df


def same_add(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """동일 값에 대해 순차적으로 증가하는 새 컬럼 생성.
    
    Cycle 데이터에서 중복된 인덱스를 처리할 때 사용됩니다.
    
    Args:
        df: 입력 DataFrame
        column_name: 기준 컬럼명
    
    Returns:
        새 컬럼이 추가된 DataFrame
    """
    new_column_name = f"{column_name}_add"
    df[new_column_name] = df[column_name].apply(lambda x: x)
    df[new_column_name] = df.groupby(column_name)[new_column_name].cumcount().add(df[column_name])
    df[new_column_name] = df[new_column_name] - df[new_column_name].min() + 1
    return df


def remove_end_comma(file_path: str) -> pd.DataFrame:
    """CSV 파일의 각 줄 끝에 있는 쉼표를 제거.
    
    일부 충방전기 데이터 파일의 형식 오류를 수정합니다.
    
    Args:
        file_path: CSV 파일 경로
    
    Returns:
        정리된 DataFrame
    """
    with open(file_path, 'r', newline='', encoding='ANSI') as input_file:
        rows = input_file.read().splitlines()
    
    for i, row in enumerate(rows):
        if row.endswith(','):
            rows[i] = row[:-1]
    
    df = pd.DataFrame(row.split(',') for row in rows)
    return df


def binary_search(numbers: list, target) -> int:
    """주어진 숫자가 정렬된 리스트의 몇 번째에 해당하는지 반환.
    
    Args:
        numbers: 정렬된 숫자 리스트
        target: 찾을 값
    
    Returns:
        삽입 위치 인덱스
    """
    index = bisect.bisect_left(numbers, target)
    return index
