import astropy.units as u

def initialize_units():
    """
    Initialize and return custom units for Battery Data Analysis.
    """
    new_units = {}

    if not hasattr(u, 'Ah'):
        u.Ah = u.def_unit('Ah', u.A * u.h, prefixes=True, namespace=new_units)
        u.add_enabled_units(u.Ah)

    if not hasattr(u, 'mAh'):
        u.mAh = u.def_unit('mAh', u.Ah / 1000, prefixes=True, namespace=new_units)
        u.add_enabled_units(u.mAh)

    if not hasattr(u, 'sec'):
        u.sec = u.def_unit('sec', u.s, prefixes=True, namespace=new_units)
        u.add_enabled_units(u.sec)

    if not hasattr(u, 'deg_C2'):
        u.deg_C2 = u.def_unit("'C", u.deg_C, prefixes=True, namespace=new_units)
        u.add_enabled_units(u.deg_C2)

    if not hasattr(u, 'deg_C3'):
        u.deg_C3 = u.def_unit("℃", u.deg_C, prefixes=True, namespace=new_units)
        u.add_enabled_units(u.deg_C3)

    return {'t': u.sec, 'V': u.V, 'Q': u.mAh, 'I': u.A, 'T': u.deg_C3}

UNITS = initialize_units()
