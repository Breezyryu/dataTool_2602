#########################################################################################
### 데이터에 단위 적용 Library astropy (python -m pip install "astropy[all]")
#########################################################################################
import astropy.units as u
def UNIT_check():
    new_units=dict()

    u.Ah = u.def_unit('Ah',u.A*u.h, prefixes=True, namespace=new_units)
    u.add_enabled_units(u.Ah)

    u.mAh = u.def_unit('mAh',u.Ah/1000, prefixes=True, namespace=new_units)
    u.add_enabled_units(u.mAh)

    u.sec = u.def_unit('sec',u.s, prefixes=True, namespace=new_units)
    u.add_enabled_units(u.sec)

    u.deg_C2 = u.def_unit("'C",u.deg_C, prefixes=True, namespace=new_units)
    u.add_enabled_units(u.deg_C2)

    u.deg_C3 = u.def_unit("℃", u.deg_C, prefixes=True, namespace=new_units)
    u.add_enabled_units(u.deg_C3)

    u.add_enabled_units(new_units)

    return {'t': u.sec, 'V': u.V, 'Q': u.mAh, 'I': u.A, 'T': u.deg_C3}


### 사용 가능한 기능 예시
# print(UNIT_check())
# print((u.Ah).compose())
# print((u.s).find_equivalent_units())
# print(1000*u.mAh.to(u.mAh))
# print(u.Unit('kAh').to(u.Unit('Ah')))