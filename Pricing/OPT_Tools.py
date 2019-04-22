# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 17:09:51 2018
This is the tools function for option
pricing module 
It also relies on the Monte Carlo generation 
object to get sample path 
@author: Shaolun Du
@contacts: Shaolun.du@gmail.com
"""
import numpy as np
import scipy.stats as si

from Pricing import Cash_Flow_Gen_OPT as CF_Gen

def Cal_OPT_Rate( table, curve, opt_npv, Day_Counter ):
    # Calculate optioned swap rate based on cf table
    sum_fixed, sum_float = 0, 0 
    try:
        Df_0 = table[0]["DFs"]
    except:
        Df_0 = 1
    for idx in range(len(table)-1):
        y_frac = Day_Counter.yearfrac(table[idx]["Beg_Time"],table[idx]["End_Time"])
        sum_fixed += table[idx]["Beg_balance"]*table[idx+1]["DFs"]/Df_0*y_frac
        sum_float += table[idx]["Beg_balance"]*table[idx]["Rates"]*table[idx+1]["DFs"]/Df_0*y_frac
    rate = (sum_float+opt_npv)/sum_fixed
    return rate

def cal_cf_val( data, curve, val_s, dc):
    # Calculate cap or floor option value
    s_book = data["schedule"]
    data["schedule"] = [ele for ele in s_book if ele[0]>curve[0][0]]
    ans_li = CF_Gen.Val_Gen_OPT( data,
                                 curve,
                                 val_s,
                                 dc )
    return ans_li
def cal_cp_val( data, curve, val_s, dc):
    # Calculate call or put option value
    return 0 

def cal_swap_val( data, curve, val_s, dc):
    # Calculate swaption option value
    s_book = data["schedule"]
    data["schedule"] = [ele for ele in s_book if ele[0]>curve[0][0]]
    ans_li = CF_Gen.Val_Gen_SWAP( data,
                                  curve,
                                  val_s,
                                  dc )
    return ans_li 

def get_sec_id( ccy, itype, method ):
    # get sec id given currency and type
    if itype.upper() in ("FLOOR","CAP"):
        sec_id = ccy+" "+method +" C/F"
    else:
        sec_id = ccy+" "+method + " SWAP"
    return sec_id


def cal_npv( cash_flow, 
             disct_curve,
             val_date = "" ):
    """ Calculate NPV given time delta
        Please first run cal_cash_flow beforehand
        we are calculating NPV based on the cash flow 
        schedule to get all discount factors 
        then we do * times and summing up
        val_date is the date that we want to value it
    """
    if len(cash_flow) == 0:
        print("Error in Portfolio--->cal_key_dv01...")
        print("Cannot find cash flow table...")
        print("Please first run cal_cash_flow...")
        print("Return 0...")
        return 0
    NPV      = 0
    cf_loc   = 0
    if val_date == "":
        curve_start = disct_curve[0][0]
        base_df = 1
    else:
        curve_start = val_date
        loc = 0
        while val_date > disct_curve[loc][0]:
            loc += 1
        pre_point = disct_curve[loc-1]
        cur_point = disct_curve[loc]
        base_df = interpolation_act( val_date,
                                     pre_point[0],
                                     pre_point[1],
                                     cur_point[0],
                                     cur_point[1] )
    while cash_flow[cf_loc][0] < curve_start:
        """ Cash flow may start back dated 
            make sure NPV caculation only
            starts when cash flow is in the current range
        """
        cf_loc += 1
        
    for loc in range(1, len(disct_curve)):
        pre_point = disct_curve[loc-1]
        cur_point = disct_curve[loc]
        if cf_loc < len(cash_flow):
            cf_point  = cash_flow[cf_loc] 
        else:
            break
        """ Whenever get a hit walking through all suitable cases
        """
        while cf_point[0] >= pre_point[0] \
            and cf_point[0] < cur_point[0]:
                DF   = interpolation_act( cf_point[0],
                                          pre_point[0],
                                          pre_point[1],
                                          cur_point[0],
                                          cur_point[1] )
                NPV += DF*cf_point[1]/base_df
                if cf_loc + 1 >= len(cash_flow):
                    break
                cf_loc   += 1
                cf_point  = cash_flow[cf_loc] 
                
    return NPV 

def interpolation_act( cur_time, 
                       start_time, 
                       start_value, 
                       end_time, 
                       end_value ):
    # Interpolation function based on time location
    if end_time == start_time:
        print(end_time,start_time,cur_time)
        print("Error in interpolation_act-> Return 0")
        return 0
    up = (cur_time-start_time).days
    down = (end_time-start_time).days
    t_frac = up/down
    ans = start_value + (end_value-start_value)*t_frac
    return ans


###--- Old Code ---###
def BS_E_vanilla_div( instrument ):
    #S: spot price
    #K: strike price
    #T: time to maturity
    #r: interest rate
    #q: rate of continuous dividend paying asset 
    #sigma: volatility of underlying asset
    S = instrument["Spot"]
    K = instrument["Strike"]
    B = instrument["Start"]
    M = instrument["Maturity"]
    r = instrument["Interests"]
    q = instrument["Div"]
    sigma = instrument["Vol"]
    option = instrument["Type"]
    T = (M-B).days/365
    
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = (np.log(S / K) + (r - q - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    if option.upper() == "CALL":
        result = (S * np.exp(-q * T) * si.norm.cdf(d1, 0.0, 1.0) - K * np.exp(-r * T) * si.norm.cdf(d2, 0.0, 1.0))
    if option.upper() == "PUT":
        result = (K * np.exp(-r * T) * si.norm.cdf(-d2, 0.0, 1.0) - S * np.exp(-q * T) * si.norm.cdf(-d1, 0.0, 1.0))
    return result