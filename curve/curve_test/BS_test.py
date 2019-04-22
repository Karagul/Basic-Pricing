# -*- coding: utf-8 -*-
"""
Created on Thu Nov 29 08:49:51 2018
This is the function to do bootstrapping
on the live data from bloomberg
Inputs should be a set of market rates
and the corresponding instruments conventions
@author: Shaolun Du
@contacts: shaolun.du@gmail.com
"""
""" General Settings Swap conventions
"""
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
                'float':{ 'freq':2, },
                'LIBOR_day_count':'30/360',
                'OIS_day_count':'ACT/360',},
    }
""" Function: 
    def boot_strapping_LIBOR( sdate, 
                              convention,
                              instruments, 
                              Day_Counter )
    Instruments = {
                    "cash":[[rates set], NUM]
                    "future":[[rates set], NUM]
                    "swap":[[rates set], NUM]
                    }
    convention = { instruemtns convention }
    Day_Counter = function of year fraction
"""
from IO import Reader as reader
from curve import Day_Counter_func as Day_Counter
from curve import Boot_Strapping as B_S
from curve import Boot_Strap_Tools_Func as BS_TF
import pandas as pd
""" Get raw data
"""
f_name = "Raw_Inputs.xlsx"
s_name = "Data"
c_num, f_num, s_num = 5,7,100
reader = reader.excel_reader(f_name)
ccy, date, Cash, Future, Swap = reader.read_instruments(s_name)
instrument = {}
instrument["cash"]   = [ Cash, c_num ]
instrument["future"] = [ Future, f_num ]
instrument["swap"]   = [ Swap, s_num ]
""" Set up valuation date and currency
    then generate the cure by bootstrapping
"""
value_date  = date
currency    = ccy
convention  = convention_book[currency]
Day_Counter = Day_Counter.Day_Counter(convention["LIBOR_day_count"])
curve = B_S.boot_strapping_LIBOR( value_date, 
                                  convention,
                                  instrument, 
                                  Day_Counter)
#curve = BS_TF.augument_by_frequency( curve, 1 )
""" Output curve into excel
"""
col_num, row_num = 0, 0
output_name = "Live_"+currency+"_"+str(value_date) +".xlsx"
writer = pd.ExcelWriter(output_name)
df = pd.DataFrame( curve )
df.to_excel( writer,
             startrow   = row_num,
             startcol   = col_num,
             sheet_name = "Answer" )
writer.save()









