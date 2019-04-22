# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 14:29:40 2019
Get Market data into ecel

@author: Shaolun Du
@contacts: Shaolun.du@gmail.com
"""
import os
import xlwings as xw

from IO import Reader as reader
from DB import dbExecute as db
""" Set up enviroments
"""
dir_path = os.path.dirname(
            os.path.dirname(
             os.path.realpath(__file__)))
f_name   = dir_path + "\\Basic Pricing.xlsm"
reader   = reader.excel_reader(f_name)

inputs   = reader.read_basic_mkt_input("Pricer")

cv_date  = inputs["curve date"]
val_date = inputs["value date"]
source   = inputs["source"]

schema_name = "Yield_Curve"
# Load libor rates curve
tb_name = "yield_curve"
sqlstring = "Select * from "+tb_name+" where sdate = '"+str(cv_date)+"'"
ans_libor = db.dbExecute( schema_name, sqlstring )

# Load fx rates curve
tb_name = "fx_curve"
sqlstring = "Select * from "+tb_name+" where sdate = '"+str(cv_date)+"'"
ans_fx = db.dbExecute( schema_name, sqlstring )

# Load fx spot
tb_name = "fx_spot"
sqlstring = "Select * from "+tb_name+" where sdate = '"+str(cv_date)+"'"
fx_spot = db.dbExecute( schema_name, sqlstring )

# Load vol cube/surface
tb_name = "vcub"
sqlstring = "Select * from "+tb_name+" where sdate = '"+str(cv_date)+"'"
vcub = db.dbExecute( schema_name, sqlstring )
###################################
## Write into rate historical curve
bk = xw.Book.caller()
sheet_name = "Rate_History"
sht = bk.sheets[sheet_name]
ccy_li = ["USD","EUR","JPY","GBP","CHF","CAD","BRL","COP"]
cah_col = 1
fut_col = 3
swp_col = 5
for loc in range(len(ccy_li)):
    data = [ele for ele in ans_libor if ele["currency"]==ccy_li[loc]]
    cah_data = sorted([[ele["maturity"],ele["rates"]] for ele in data if ele["type"] == "cash"],key=lambda x:x[0])
    fut_data = sorted([[ele["maturity"],ele["rates"]] for ele in data if ele["type"] == "future"],key=lambda x:x[0])
    swp_data = sorted([[ele["maturity"],ele["rates"]] for ele in data if ele["type"] == "swap"],key=lambda x:x[0])
    base_row = 6+loc*25
    for cah_row in range(6):
        try:
            sht.range((base_row+cah_row,cah_col),(base_row+cah_row,cah_col)).value = cah_data[cah_row][0]
            sht.range((base_row+cah_row,cah_col+1),(base_row+cah_row,cah_col+1)).value = cah_data[cah_row][1]
        except:
            pass    
    for fut_row in range(8):
        try:
            sht.range((base_row+fut_row,fut_col),(base_row+fut_row,fut_col)).value = fut_data[fut_row][0]
            sht.range((base_row+fut_row,fut_col+1),(base_row+fut_row,fut_col+1)).value = fut_data[fut_row][1]
        except:
            pass    
    for swp_row in range(21):
        try:
            sht.range((base_row+swp_row,swp_col),(base_row+swp_row,swp_col)).value = swp_data[swp_row][0]
            sht.range((base_row+swp_row,swp_col+1),(base_row+swp_row,swp_col+1)).value = swp_data[swp_row][1]
        except:
            pass
#######################################      
## Write into fx curve historical curve
sheet_name = "FX_Curve_History"   
sht = bk.sheets[sheet_name]
ccy_li = [ "USD","EUR","JPY",
           "GBP","CHF","CAD",
           "BRL","COP" ]
cah_col = 1
fut_col = 3
swp_col = 5
for loc in range(len(ccy_li)):
    data = [ele for ele in ans_fx if ele["currency"]==ccy_li[loc]]
    cah_data = sorted([[ele["maturity"],ele["rates"]] for ele in data if ele["type"] == "cash"],key=lambda x:x[0])
    fut_data = sorted([[ele["maturity"],ele["rates"]] for ele in data if ele["type"] == "future"],key=lambda x:x[0])
    swp_data = sorted([[ele["maturity"],ele["rates"]] for ele in data if ele["type"] == "swap"],key=lambda x:x[0])
    base_row = 6+loc*25
    for cah_row in range(6):
        try:
            sht.range((base_row+cah_row,cah_col),(base_row+cah_row,cah_col)).value = cah_data[cah_row][0]
            sht.range((base_row+cah_row,cah_col+1),(base_row+cah_row,cah_col+1)).value = cah_data[cah_row][1]
        except:
            pass    
    for fut_row in range(8):
        try:
            sht.range((base_row+fut_row,fut_col),(base_row+fut_row,fut_col)).value = fut_data[fut_row][0]
            sht.range((base_row+fut_row,fut_col+1),(base_row+fut_row,fut_col+1)).value = fut_data[fut_row][1]
        except:
            pass    
    for swp_row in range(21):
        try:
            sht.range((base_row+swp_row,swp_col),(base_row+swp_row,swp_col)).value = swp_data[swp_row][0]
            sht.range((base_row+swp_row,swp_col+1),(base_row+swp_row,swp_col+1)).value = swp_data[swp_row][1]
        except:
            pass
######################################        
## Write into fx rate historical curve        
sheet_name = "FX_Rate" 
sht = bk.sheets[sheet_name] 
fx_spot = [[ele["base"]+ele["currency"],ele["rate"],ele["currency"]] for ele in fx_spot]
for loc in range(len(fx_spot)):
    sht.range((loc+2,1),(loc+2,1)).value = fx_spot[loc][0]
    sht.range((loc+2,2),(loc+2,2)).value = fx_spot[loc][1]
    sht.range((loc+2,3),(loc+2,3)).value = fx_spot[loc][2]
##############################################    
## Write into volatility rate historical curve 
sheet_name = "Vol_Surface"
sht = bk.sheets[sheet_name]
vol_li_cf = [ "USD Normal C/F","EUR Normal C/F"]
cf_tenor = [1,2,3,4,5,7,10,12,15,20]
base_row = 4
base_col = 2
for sec in vol_li_cf:
    table = [ele for ele in vcub if ele["sec"] == sec]
    # Filling in strike 
    strikes = [sorted(set([ele["strike"] for ele in table]))]
    for loc in range(len(strikes)):
        sht.range((base_row-1,base_col+loc),(base_row-1,base_col+loc)).value = strikes[loc]
    for tenor in cf_tenor:
        sht.range((base_row,base_col-1),(base_row,base_col-1)).value = tenor
        row = sorted([ele for ele in table if ele["tenor"] == tenor], key=lambda x:x["strike"])
        for loc in range(len(row)):
            # Filling in a row vol number
            sht.range((base_row,loc+base_col),(base_row,loc+base_col)).value = row[loc]["vol"]
        base_row += 1
    base_row += 10 # Increase to next section
vol_li_sp = [ "USD Normal SWAP","EUR Normal SWAP"]
sp_tenor = [1,2,3,4,5,6,7,8,9,10,15,20,25,30]
base_row = 44
base_col = 2
for sec in vol_li_sp:
    table = [ele for ele in vcub if ele["sec"] == sec]
    # Filling in tenor 
    tenors = [sorted(set([ele["tenor"] for ele in table]))]
    for loc in range(len(tenors)):
        sht.range((base_row-1,base_col+loc),(base_row-1,base_col+loc)).value = tenors[loc]
    start_d = set(sorted([ele["start"] for ele in table]))
    for start in start_d:
        sht.range((base_row,base_col-1),(base_row,base_col-1)).value = start
        row = sorted([ele for ele in table if ele["start"] == start], key=lambda x:x["tenor"])
        for loc in range(len(row)):
            # Filling in a row vol number
            sht.range((base_row,loc+base_col),(base_row,loc+base_col)).value = row[loc]["vol"]
        base_row += 1
    base_row += 8 # Increase to next section


