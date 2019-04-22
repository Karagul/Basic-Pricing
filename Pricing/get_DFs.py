# -*- coding: utf-8 -*-
"""
Created on Tue Dec 18 08:47:33 2018
This is the function linked to excel 
which can generate discount factors into 
live pricing excel front end

@Author:   Alan
@Contacts: Shaolun.du@gmail.com

"""
import os 
import xlwings as xw
from IO import Reader as reader
import Pricing.SWAP_Pricer as Pricer
import Pricing.LP_Tools as Tools

""" Set up enviroments
"""
dir_path = os.path.dirname(
            os.path.dirname(
             os.path.realpath(__file__)))
f_name   = dir_path+"\\Basic Pricing.xlsm"
ccy_list     = [ "USD","EUR","COP","BRL",
                 "JPY","GBP","CHF","CAD" ]

""" Set up objects
"""
reader  = reader.excel_reader( f_name )

data  = reader.read_basic_swap_input( "Pricer" )
source = data["source"]
freq,isEOM,Margin = reader.read_DFs( "Pricer" )

if "Y" in isEOM.upper():
    isEOM = True
else:
    isEOM = False
""" Choose Pricing Source
"""
if "H" in source.upper():
    s_name    = "Rate_History"
    s_fx_name = "FX_Curve_History"
elif "L" in source.upper():
    s_name    = "Rate_Live"
    s_fx_name = "FX_Curve_Live"

cv_instrument    = reader.read_instruments(s_name, 8)
cv_fx_instrument = reader.read_instruments(s_fx_name, 8)
cv_instrument    = Tools.Add_margin( cv_instrument, Margin )
cv_fx_instrument = Tools.Add_margin( cv_fx_instrument, Margin )
""" Start Generating Curves
"""
sheet_name = "DFs"
sht = xw.Book.caller().sheets[sheet_name]
val_date = reader.read_value_date("Pricer")
Pricer = Pricer.SWAPer( cv_instrument,
                        cv_fx_instrument,
                        "",
                        "" )
""" Get DFs and output into live pricing.xlsm
"""
i_row, i_col = 5, 1 
for ccy in ccy_list:
    cv,fx_cv = Pricer.get_raw_dfs( val_date,
                                   ccy,
                                   freq,
                                   isEOM,
                                   Margin )
    for e1,e2 in zip(cv,fx_cv):
        sht.range(i_row,i_col).value   = str(e1[0])
        sht.range(i_row,i_col+1).value = e1[1]
        sht.range(i_row,i_col+2).value = str(e2[0])
        sht.range(i_row,i_col+3).value = e2[1]
        i_row += 1
    i_row = 5
    i_col += 4




