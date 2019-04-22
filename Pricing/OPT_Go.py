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
from Pricing import Vol_Live as Vol
from Pricing import OPT_Pricer as OPT

""" Set up enviroments
"""
dir_path = os.path.dirname(
            os.path.dirname(os.path.realpath(__file__)))
f_name   = dir_path+"\\Basic Pricing.xlsm"
reader   = reader.excel_reader(f_name)

inputs   = reader.read_basic_opt_input("Pricer")

cv_date  = inputs["curve date"]
val_date = inputs["value date"]
source   = inputs["source"]
""" Choose Pricing Source
"""
fx_name    = "FX_Rate"
s_name     = "Rate_History"
s_fx_name  = "FX_Curve_History"
s_opt_name = "Vol_Surface"
    
sheet_name = "Pricer"
opt_source = "LIVE"
db_name    = "Yield_Curve"

# Spot FX market
fx_spot = reader.read_FX_rates(fx_name)
# Libor rate market
cv_instrument    = reader.read_instruments( s_name, 8)
# FX rate market
cv_fx_instrument = reader.read_instruments( s_fx_name, 8)
# Volatility normal market
vol_instrument   = reader.read_vol( s_opt_name, 4)

""" Start Pricing and Setting up pricing objects
"""
disc_cv_details = { "type" : "LIBOR",
                    "spread" : 0 }

reader.close() # Reslease workbook

vol_s = Vol.Val_Surface( val_date,
                         vol_instrument )

OPT = OPT.OPTer( cv_instrument,
                 vol_s ) 

inst   = OPT.gen_opt_instruments(inputs)
ans_bk = OPT.price_opt( inst, val_date)

""" Start pricing and output to Pricer sheet
"""
# Writting to excel
i_row,i_col = 43, 6
sht = xw.Book.caller().sheets[sheet_name]
sht.range((i_row,i_col),(i_row,i_col)).value = ans_bk["NPV"]
sht.range((i_row-1,i_col+2),(i_row-1,i_col+2)).value = ans_bk["delta"]
sht.range((i_row,i_col+2),(i_row,i_col+2)).value = ans_bk["gamma"]
sht.range((i_row+1,i_col+2),(i_row+1,i_col+2)).value = ans_bk["vega"]
sht.range((i_row+2,i_col+2),(i_row+2,i_col+2)).value = ans_bk["theta"]
sht.range((i_row+3,i_col+2),(i_row+3,i_col+2)).value = ans_bk["rho"]
