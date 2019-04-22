# -*- coding: utf-8 -*-
""" Day Count Convention file remember all possible 
    Day Convention issue to handle
    @author: Alan
    @contacts: Shaolun.du@gmail.com
"""
# NOTER: This is the old function which
#        which is no longer used

def get_convention_by_currency( currency ):
    convention_book = {  
    'USD':{ 'fix':{ 'freq':2,},
            'float':{'freq':4,},
            'LIBOR_day_count':'30/360',
            'OIS_day_count':'ACT/360', },
    'EUR':{ 'fix':{ 'freq':1, },
            'float':{ 'freq':2,},
            'LIBOR_day_count':'30/360',
            'OIS_day_count':'ACT/360',},
    'GBP':{ 'fix':{ 'freq':2,},
            'float':{ 'freq':2,},
            'LIBOR_day_count':'ACT/365',
            'OIS_day_count':'ACT/365',},
    'JPY':{ 'fix':{ 'freq':2,},
            'float':{ 'freq':2,},
            'LIBOR_day_count':'ACT/365',
            'OIS_day_count':'ACT/365', },
    'CAD':{ 'fix':{ 'freq':2,},
            'float':{ 'freq':2,},
            'LIBOR_day_count':'ACT/365',
            'OIS_day_count':'ACT/365', },
    'CHF':{ 'fix':{ 'freq':1,},
            'float':{ 'freq':2,},
            'LIBOR_day_count':'30/360',
            'OIS_day_count':'ACT/360', },
    'BRL':{ 'fix':{ 'freq':2,},
            'float':{ 'freq':2,},
            'LIBOR_day_count':'30/360',
            'OIS_day_count':'ACT/360',},
    'COP':{ 'fix':{ 'freq':2,},
            'float':{ 'freq':4,},
            'LIBOR_day_count':'ACT/360',
            'OIS_day_count':'ACT/360',},
        }
    if not currency in convention_book:
        print("Current currency:{0}".format( currency ) )
        print("Current in get_convention_by_currency...")
        print("Cannot find currency code in Convention...")
        print("Return 0...")
        return 0
    return convention_book[currency]

