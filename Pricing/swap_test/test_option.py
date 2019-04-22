# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 16:52:21 2019
Live pricing option test
@author: Shaolun Du
@contact: Shaolun.du@gmail.com
"""
import DB.dbExecute as dbEx
from IO import Reader as Reader
from Live_Pricing import Vol_Live as Vol
from Live_Pricing import OPT_Pricer as OPT
# Step one load current market vol data
# also load current market rates data
f_name = "Live Pricing.xlsm"
s_name = "Vol_Surface"
sdate  = "2019-03-25" 
schema_name = "Yield_Curve" 
tb_opt = "vcub"
opt_source = "LIVE"
num = 4
Reader = Reader.excel_reader(f_name)
data   = Reader.read_vol( s_name, num )

vol_s = Vol.Val_Surface( sdate,
                         schema_name,
                         tb_opt )
vol_s.get_raw_data( opt_source, data )

# Step two load option/swaption balance schedule
balance_name = "Schedule"
Reader.read( balance_name )
name, raw_data = Reader.get_raw_data()
cv_instrument  = Reader.read_instruments("Rate_Live", 8)
disc_cv_details = { "type" : "LIBOR",
                    "spread" : 0 }

# Step three option/swaption pricing
OPT = OPT.OPTer( cv_instrument,
                 vol_s ) 

for nn in name:
    if raw_data[nn]["itype"] in ("Floor","Cap"):
        OPT.add( nn, raw_data[nn], disc_cv_details )
        print(OPT.price_opt( nn, sdate ))
