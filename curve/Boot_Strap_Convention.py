# -*- coding: utf-8 -*-
"""
Created on Mon Dec 31 10:21:00 2018

@author: Shaolun Du
@contacts: Shaolun.du@gmail.com
"""
""" This is the boot strap convention file
"""
BS_Con = { 
    "USD":{ "Cash_Day":   360,
            "Future_Day": 360,
            "Swap":   "30/360",
            "Swap_Freq": 2,
            "OIS_day_count":"ACT/360", },
    "EUR":{ "Cash_Day":   360,
            "Future_Day": 360,
            "Swap":   "30/360",
            "Swap_Freq": 1,
            "OIS_day_count":"ACT/360", },
    "GBP":{ "Cash_Day":   360,
            "Future_Day": 360,
            "Swap":   "30/360",
            "Swap_Freq": 2,
            "OIS_day_count":"ACT/360", },
    "JPY":{ "Cash_Day":   360,
            "Future_Day": 360,
            "Swap":   "ACT/365",
            "Swap_Freq": 2,
            "OIS_day_count":"ACT/360", },
    "COP":{ "Cash_Day":   360,
            "Future_Day": 360,
            "Swap":   "ACT/360",
            "Swap_Freq": 4,
            "OIS_day_count":"ACT/360", },
    "BRL":{ "Cash_Day":   252,
            "Future_Day": 252,
            "Swap":   "ACT/252",
            "Swap_Freq": 2,
            "OIS_day_count":"ACT/360", },
    "CHF":{ "Cash_Day":   360,
            "Future_Day": 360,
            "Swap":   "ACT/360",
            "Swap_Freq": 1,
            "OIS_day_count":"ACT/360", },
    
    'CAD':{ "Cash_Day":   360,
            "Future_Day": 360,
            "Swap":   "ACT/365",
            "Swap_Freq": 2,
            "OIS_day_count":"ACT/365", },
    
    }

