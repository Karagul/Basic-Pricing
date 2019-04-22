# -*- coding: utf-8 -*-
"""
Created on Mon Nov  5 04:49:38 2018
This is the function to generate all curves we have in the data base

@author: shaolun du
@contacts: Shaolun.du@gmail.com
"""
from curve import Curve_Keeper as BS_CK
from Day_Counter import Day_Counter_func as Day_Count
from curve import Boot_Strap_Tools_Func as Tools
import pandas as pd
import numpy as np
import xlwings as xw
import datetime as dt
import matplotlib.pyplot as plt


###################################
####--- Below is for testing ---###
sdate = "2019-02-14"
output_name = "Curve_" + sdate + ".xlsx"
col_num, row_num = 0, 0
currency = ["EUR"]
spread = 0    # In % units

writer = pd.ExcelWriter(output_name)

CK = BS_CK.Curve_Keeper(sdate,"Yield_Curve")
Day_Counter = Day_Count.Day_Counter("30/360")
for ccy in currency:
    cvs = CK.gen_curve( ccy,
                        -1,
                        0,
                        spread,
                        Day_Counter )
    cv = cvs["LIBOR"]
    cv = Tools.augument_by_frequency( cv , 1)
    df = pd.DataFrame(cv)
    df.columns = ["Date", "LIBOR:"+ccy+" Spread:"+str(spread)]
    df.to_excel( writer,
                 startrow = row_num,
                 startcol = col_num,
                 sheet_name = "Curves" )
    col_num += 3
    
    cv = cvs["FX"]
    cv = Tools.augument_by_frequency( cv , 1)
    df = pd.DataFrame(cv)
    df.columns = ["Date", "FX:"+ccy+" Spread:"+str(spread)]
    df.to_excel( writer,
                 startrow = row_num,
                 startcol = col_num,
                 sheet_name = "Curves" )
    col_num += 3
writer.save()

    
    
    
    
    
    
    