# -*- coding: utf-8 -*-
"""
Created on Thu Dec 4 08:49:51 2018
This is the main function to do 
swap pricing find out the corresponding
fixed rate of a given swap/XCS
Inputs:
    Live Pricing.xlsm contains tab:
        [ "Rate_Upload":    for LIBOR curve instruments,
          "FX_Curve_Upload":for Basis adjusted curve 
                            instruments,
          "FX_Upload":      for fx live spot rate,
          "Schedule":       a list of inputs swap positions 
                            for pricing
        ]
Outputs:
    fixed swap rate on leg2 (in default)
    Can be adjusted and out put all detailed cash flows
    
@author: Shaolun Du
@contacts: shaolun.du@gmail.com
"""
import os
import xlwings as xw
from IO import Reader as reader
from Pricing import SWAP_Pricer as Pricer

""" Set up enviroments
"""
dir_path = os.path.dirname(
            os.path.dirname(os.path.realpath(__file__)))
f_name   = dir_path+"\\Basic Pricing.xlsm"
reader   = reader.excel_reader(f_name)

inputs   = reader.read_basic_swap_input("Pricer")

cv_date  = inputs["curve date"]
val_date = inputs["value date"]
source   = inputs["source"]
Cur_NPV  = inputs["Cur_NPV"]
""" Choose Pricing Source
"""
fx_name    = "FX_Rate"
s_name     = "Rate_History"
s_fx_name  = "FX_Curve_History"
s_opt_name = "Vol_Surface"
    
sheet_name = "Pricer"
db_name    = "Yield_Curve"

# Spot FX market
fx_spot = reader.read_FX_rates(fx_name)
# Libor rate market
cv_instrument    = reader.read_instruments(s_name, 8)
# FX rate market
cv_fx_instrument = reader.read_instruments(s_fx_name, 8)
# Volatility normal market
vol_instrument   = reader.read_vol( s_opt_name, 4 )

""" Start Pricing and Setting up pricing objects
"""
disc_cv_details = { "type" : "LIBOR",
                    "spread" : 0 }

reader.close() # Reslease workbook

Pricer = Pricer.SWAPer( cv_instrument,
                        cv_fx_instrument,
                        fx_spot,
                        "" )
inst = Pricer.gen_swap_instruments(inputs)
NPV,pv01,Rate,KRDs = Pricer.get_ans( inst, Cur_NPV, cv_date, val_date )
""" Start pricing and output to Pricer sheet
"""
# Writting to excel
i_row,i_col = 12, 6
sht = xw.Book.caller().sheets[sheet_name]
sht.range((i_row+1,i_col),(i_row+1,i_col)).value = NPV
sht.range((i_row+2,i_col),(i_row+2,i_col)).value = Rate
sht.range((i_row+3,i_col),(i_row+3,i_col)).value = pv01
sht.range((i_row,i_col+2),(i_row,i_col+2)).value = KRDs[1]
sht.range((i_row+1,i_col+2),(i_row+1,i_col+2)).value = KRDs[2]
sht.range((i_row+2,i_col+2),(i_row+2,i_col+2)).value = KRDs[3]
sht.range((i_row+3,i_col+2),(i_row+3,i_col+2)).value = KRDs[5]
sht.range((i_row+4,i_col+2),(i_row+4,i_col+2)).value = KRDs[7]
sht.range((i_row+5,i_col+2),(i_row+5,i_col+2)).value = KRDs[10]
sht.range((i_row+6,i_col+2),(i_row+6,i_col+2)).value = KRDs[15]
sht.range((i_row+7,i_col+2),(i_row+7,i_col+2)).value = KRDs[20]+KRDs[25]
sht.range((i_row+8,i_col+2),(i_row+8,i_col+2)).value = KRDs[30]+KRDs[40]

