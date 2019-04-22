# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 10:21:34 2018
Test function for swap object

@author: Shaolun Du
@Contacts: Shaolun.du@gmail.com
"""
import pandas as pd
import swap.Swaper as Swaper
import curve.Curve_Keeper as CK
from collections import OrderedDict
from datetime import datetime

name = "Test" 
cur_date = "2018-10-30"
curve_keeper = CK.Curve_Keeper( cur_date, 
                                "Yield_Curve" )
swaper = Swaper.Swaper( cur_date, 
                        curve_keeper )

instrument = OrderedDict()
instrument["leg1_ccy"] = "USD"
instrument["leg1_cpn_detail"] = [[1000,"LIBOR","6M",0,-100,100]]
instrument["leg1_pay_convention"] = [[1000,"6M"]]

instrument["balance_tb_1"] = [["6/30/2018",1728147],
                              ["12/30/2018",1676702],
                              ["6/30/2019",1605788],
                              ["12/30/2019",1552758],
                              ["6/30/2020",1479972],
                              ["12/30/2020",1424826],
                              ["6/30/2021",1349297],
                              ["12/30/2021",1291115],
                              ["6/30/2022",1212665],
                              ["12/30/2022",1152020],
                              ["6/30/2023",1070391],
                              ["12/30/2023",1006635],
                              ["6/30/2024",921444],
                              ["12/30/2024",854610],
                              ["6/30/2025",765127],
                              ["12/30/2025",693909],
                              ["6/30/2026",599126],
                              ["12/30/2026",522641],
                              ["6/30/2027",422995],
                              ["12/30/2027",342496],
                              ["6/30/2028",238362],
                              ["12/30/2028",153529],
                              ["6/30/2029",44546],
                              ["12/30/2029",0]]
for ele in instrument["balance_tb_1"]:
    ele[0] = datetime.strptime(ele[0],"%m/%d/%Y").date()
    
instrument["leg2_ccy"] = "USD"
instrument["leg2_cpn_detail"] = [[1000,"Fix",0.03,0,-100,100]]
instrument["leg2_pay_convention"] = [[1000,"6M"]]
instrument["balance_tb_2"] = [["6/30/2018",1728147],
                              ["12/30/2018",1676702],
                              ["6/30/2019",1605788],
                              ["12/30/2019",1552758],
                              ["6/30/2020",1479972],
                              ["12/30/2020",1424826],
                              ["6/30/2021",1349297],
                              ["12/30/2021",1291115],
                              ["6/30/2022",1212665],
                              ["12/30/2022",1152020],
                              ["6/30/2023",1070391],
                              ["12/30/2023",1006635],
                              ["6/30/2024",921444],
                              ["12/30/2024",854610],
                              ["6/30/2025",765127],
                              ["12/30/2025",693909],
                              ["6/30/2026",599126],
                              ["12/30/2026",522641],
                              ["6/30/2027",422995],
                              ["12/30/2027",342496],
                              ["6/30/2028",238362],
                              ["12/30/2028",153529],
                              ["6/30/2029",44546],
                              ["12/30/2029",0]]
for ele in instrument["balance_tb_2"]:
    ele[0] = datetime.strptime(ele[0],"%m/%d/%Y").date()
instrument["day_convention"] = "ACT/360"

disc_cv_details = { "type"  : "SWAP",
                    "spread": 0 }

swaper.add( name, instrument, disc_cv_details )

swaper.cal_swap( cur_date )

ans = swaper.answer_bk
for key,val in ans.items():  
    print("Name of Position:")
    print(key)
    for k,v in val.items():
        print(k)
        if "CF" in k:
            print(pd.DataFrame(v["Leg1"]))
            print(pd.DataFrame(v["Leg2"]))
        elif k == "Schedule":
            print(pd.DataFrame(v["Leg1"]))
            print(pd.DataFrame(v["Leg2"]))
        else:
            print(v)

