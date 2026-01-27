# %% [markdown]
# # Battery Tool 사용 가이드
# 
# 리팩토링된 `battery_tool` 패키지 디버깅 및 활용 예제

# %%
# 모듈 import
from battery_tool.utils import check_cycler, name_capacity
from battery_tool.data_processing import (
    toyo_cycle_data, 
    pne_cycle_data,
    toyo_chg_Profile_data,
)
from battery_tool.gui import (
    process_cycle_data,
    create_cycle_plot,
    process_charge_profile,
)

print("✅ battery_tool 모듈 import 성공!")

# %% [markdown]
# ## 1. 데이터 경로 설정
# 
# 실제 데이터 경로로 변경하세요.

# %%
# 예시 경로 (실제 경로로 변경 필요)
# Toyo 충방전기 예시
toyo_path = r"C:\Users\Ryu\battery\Rawdata\TOYO\Sample"  # 변경 필요

# PNE 충방전기 예시  
pne_path = r"C:\Users\Ryu\battery\Rawdata\PNE01\CH001"   # 변경 필요

# %% [markdown]
# ## 2. 충방전기 종류 확인

# %%
import os

# 경로가 존재하는지 확인
test_path = pne_path  # 테스트할 경로

if os.path.exists(test_path):
    is_pne = check_cycler(test_path)
    cycler_type = "PNE" if is_pne else "Toyo"
    print(f"📍 경로: {test_path}")
    print(f"🔋 충방전기 종류: {cycler_type}")
else:
    print(f"❌ 경로가 존재하지 않습니다: {test_path}")
    print("   실제 데이터 경로로 변경해주세요.")

# %% [markdown]
# ## 3. 파일명에서 용량 추출

# %%
sample_path = r"D:\Data\LG_3500mAh_Test"
capacity = name_capacity(sample_path)
print(f"📊 추출된 용량: {capacity} mAh")

# %% [markdown]
# ## 4. Cycle 데이터 처리 (통합 함수)

# %%
# process_cycle_data는 Toyo/PNE를 자동 감지합니다
if os.path.exists(test_path):
    try:
        mincap, df = process_cycle_data(
            raw_file_path=test_path,
            mincapacity=0,       # 0이면 자동 산정
            ini_crate=0.2,       # 초기 C-rate
            chkir=False,         # DCIR 체크
        )
        
        print(f"✅ 처리 완료!")
        print(f"   정격 용량: {mincap} mAh")
        
        if hasattr(df, 'NewData'):
            print(f"   Cycle 수: {len(df.NewData)}")
            print(f"\n📋 데이터 미리보기:")
            print(df.NewData.head())
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
else:
    print("⚠️ 테스트 경로를 실제 데이터 경로로 변경해주세요.")

# %% [markdown]
# ## 5. Cycle 그래프 생성

# %%
import matplotlib.pyplot as plt

# df가 정의되어 있고 데이터가 있는 경우
if 'df' in dir() and hasattr(df, 'NewData') and not df.NewData.empty:
    fig = create_cycle_plot(
        df=df,
        mincapacity=mincap,
        xscale=1.0,
        ylimit_low=0.7,
        ylimit_high=1.05,
        title="Sample Cell Cycle Data"
    )
    plt.show()
else:
    print("⚠️ 먼저 Cycle 데이터를 처리해주세요.")

# %% [markdown]
# ## 6. 개별 Toyo/PNE 함수 직접 사용

# %%
# Toyo 데이터 직접 처리 예시
# mincap, df = toyo_cycle_data(toyo_path, mincapacity=0, inirate=0.2, chkir=False)

# PNE 데이터 직접 처리 예시
# mincap, df = pne_cycle_data(pne_path, mincapacity=0, ini_crate=0.2, 
#                             chkir=False, chkir2=False, mkdcir=False)

# %% [markdown]
# ## 7. Profile 데이터 처리

# %%
# 특정 Cycle의 충전 Profile 분석
if os.path.exists(test_path):
    try:
        cap, profile_df = process_charge_profile(
            raw_file_path=test_path,
            cycle=1,             # 분석할 cycle 번호
            mincapacity=0,
            cutoff=2.5,          # 전압 하한
            ini_rate=0.2,
            smooth_degree=0      # 0이면 자동
        )
        
        if hasattr(profile_df, 'Profile') or hasattr(profile_df, 'stepchg'):
            print("✅ Profile 처리 완료!")
            attr = 'Profile' if hasattr(profile_df, 'Profile') else 'stepchg'
            print(getattr(profile_df, attr).head())
    except Exception as e:
        print(f"❌ 오류: {e}")

# %% [markdown]
# ## 8. dV/dQ 분석

# %%
from battery_tool.gui import analyze_dvdq, calculate_degradation_metrics
import numpy as np

# 샘플 데이터로 dV/dQ 분석 테스트
sample_profile = {
    'SOC': np.linspace(0, 1, 100),
    'dVdQ': np.random.randn(100) * 0.1 + np.sin(np.linspace(0, 2*np.pi, 100))
}
sample_df = type('obj', (object,), {'columns': ['SOC', 'dVdQ']})()

# 열화 지표 계산 예시
initial_params = {'positive_mass': 1.0, 'negative_mass': 1.0, 'slip': 0.0}
current_params = {'positive_mass': 0.95, 'negative_mass': 0.92, 'slip': 0.02}

metrics = calculate_degradation_metrics(initial_params, current_params)
print("📉 열화 지표:")
for key, value in metrics.items():
    print(f"   {key}: {value:.2f}")

# %% [markdown]
# ## 📚 모듈 구조 확인

# %%
import battery_tool

print("📦 battery_tool 패키지 구조:")
print("├── utils          - 유틸리티 함수")
print("├── visualization  - 그래프 함수")
print("├── data_processing - Toyo/PNE 데이터 처리")
print("├── analysis       - dV/dQ 분석")
print("└── gui            - 비즈니스 로직 (핸들러)")
