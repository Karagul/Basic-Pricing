# -*- coding: utf-8 -*-
"""
Created on Sun Nov  4 12:34:17 2018
Cash Flow generation based on customized balance table

@author: shaol
"""
import pandas as pd
import Pricing.Swap_Tools  as Tools
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import datetime
import calendar

def Gen_FXTB_by_Input( Legx):
    """ Simple balance generator of FX
    """
    Noti  = Legx["Notional"]
    End = Legx["End"]
    bal_tb= []
    bal_tb.append( [End, Noti] )    
    return bal_tb

def Gen_TB_by_Input( Legx ):
    """ Generate schedule balance table based on
        start date, reset frequency and pay frequency
        NOTE: no amortization is included here!!!
    """
    Noti  = Legx["Notional"]
    begin = Legx["Sdate"]
    tenor = Legx["Tenor"]
    reset = Legx["Reset"]
    re_m  = get_fwd_month(reset)
    T_m   = int(tenor*12)
    bal_tb= [[begin, 0]]
    while T_m >= 0:
        bal_tb.append( [begin, Noti] )
        begin = add_months( begin, re_m )
        T_m = T_m - re_m
    bal_tb[-1][1] = 0
    return bal_tb

def Gen_OPTTB_by_Input( Legx ):
    """ Generate schedule balance table based on
        start date, reset frequency and pay frequency
        NOTE: no amortization is included here!!!
    """
    Noti  = Legx["Notional"]
    begin = Legx["Start"]
    end   = Legx["Maturity"] 
    reset = Legx["Reset"]
    re_m  = get_fwd_month(reset)
    bal_tb= []
    while begin < end:
        bal_tb.append( [begin, Noti] )
        begin = add_months( begin, re_m )
    return bal_tb


def CF_Gen( cf_insturments, 
            curve,
            cv_keeper,
            Day_Counter ):
    """ Here cash flow generator is a little complicated
        we have to consider accruing based cash flow generation
        which means we calculate cash flow but only paid
        at the payment date
        NOTE: Here the underlying condition is payment frequency
        should be a multiple of accruing frequency and assume the smallest
        unit is 1 month
        Also the balance table should be the begin balance on that period
    """
    """ cf_instruements = {  "currency":...,
                             "balance_tb":...,
                             "acc_cpn_detail":...,
                             "pay_convention":....,
                             "day_convention":....,}
        cf_insturments["acc_cpn_detail"] = [ [ period,"Rate_type",
                                              "xxx/xML",spread  ],
                                             [...],[...]... ]
    """
    currency   = cf_insturments["currency"]
    balance_tb = cf_insturments["balance_tb"]
    coupons    = cf_insturments["acc_cpn_detail"]
    pay_freq   = cf_insturments["pay_convention"]
    """ Looping through balance table and make a fixing
        on each accrued_freq date and we assume that balance table 
        is coincidence with fixing rate table
    """
    bal_tb  = []
    ans_li  = []
    loc_ind = 0
    bal_tb  = balance_tb.copy()  
    bal_tb.append(balance_tb[-1])
    r_type  = coupons[loc_ind][1]
    spreads = coupons[loc_ind][3]
    Rate_floor = float(coupons[loc_ind][4])
    Rate_cap   = float(coupons[loc_ind][5])

    for idx, ele in enumerate(bal_tb[:-1]):
        """ idx is the index number here it
            works as the period number
        """
        next_t = bal_tb[idx+1][0]
        year_frac = Day_Counter.yearfrac( ele[0], next_t )
        if idx > coupons[loc_ind][0]:
            loc_ind += 1
            r_type = coupons[loc_ind][1]
            spreads= coupons[loc_ind][3]
        if r_type == "CMS":
            cur_fwd_p = get_fwd_month(coupons[loc_ind][2])
            fwd_rate = Tools.get_CMS_rate( curve, 
                                           ele[0], 
                                           cur_fwd_p,
                                           Day_Counter,
                                           cv_keeper,
                                           currency )
        elif r_type.upper() == "LIBOR":
            cur_fwd_p = get_fwd_month(coupons[loc_ind][2])
            act_p = (next_t.year - ele[0].year) * 12 + next_t.month - ele[0].month
            cur_fwd_p = act_p
            fwd_rate = Tools.get_fwd_rate( curve, 
                                           ele[0], 
                                           cur_fwd_p,
                                           Day_Counter,
                                           cv_keeper,
                                           currency )
            if year_frac == 0:
                fwd_rate = 0
            else:
                fwd_rate = fwd_rate/year_frac
        elif r_type.upper() == "FIX":
            fwd_rate = coupons[loc_ind][2]
        """ Apply option effects onto fwd_rates
        """
        
        fwd_rate = max(Rate_floor,fwd_rate)
        fwd_rate = min(Rate_cap,fwd_rate)
        fwd_rate += spreads
        
        ints = ele[1]*fwd_rate*year_frac
        Principal = -(bal_tb[idx+1][1]-ele[1])
        ans_li.append( OrderedDict(
                        { "Beg_Time":    ele[0],
                          "End_Time":    next_t, 
                          "Beg_balance": ele[1],
                          "PMT":         ints + Principal,
                          "Principal":   Principal,
                          "Interests":   ints,
                          "Rates":       fwd_rate, }
                    ) )
    
    """ After accruing coupons we have to regroup them
        into actual paying coupons at the end of each payment period
    """
    ans_li = ans_li[:-1]
    ans_li = INT_resample( ans_li, pay_freq )
    return ans_li

def int_resample( cash_flow, 
                  pay_freq ):
    """ regrouping a given cash flow 
        to make a actual payment from accruing based
        payment sechdule
    """
    ans_li  = []
    loc_ind = 0
    cur_fwd_p = get_fwd_month(pay_freq[loc_ind][1])  
    next_pay_date = add_months(cash_flow[0]["Beg_Time"],cur_fwd_p)
    for idx, ele in enumerate(cash_flow):
        if idx > pay_freq[loc_ind][0]:
            """ Condition if we move one pay
                specification forward
            """
            loc_ind += 1
        if ele["End_Time"] <= next_pay_date or idx > len(cash_flow)-1:
            temp = OrderedDict({ "Beg_Time":    ele["Beg_Time"],
                                 "End_Time":    next_pay_date, 
                                 "Beg_balance": ele["Beg_balance"],
                                 "PMT":         ele["PMT"],
                                 "Principal":   ele["Principal"],
                                 "Interests":   ele["Interests"],
                                 "Rates":       ele["Rates"], })
            ans_li.append(temp)
        else:
            cur_fwd_p = get_fwd_month(pay_freq[loc_ind][1]) 
            next_pay_date = add_months(next_pay_date,cur_fwd_p)
            temp = OrderedDict({ "Beg_Time":    ele["Beg_Time"],
                                 "End_Time":    next_pay_date, 
                                 "Beg_balance": ele["Beg_balance"],
                                 "PMT":         ele["PMT"],
                                 "Principal":   ele["Principal"],
                                 "Interests":   ele["Interests"],
                                 "Rates":       ele["Rates"], })
            ans_li.append(temp)
    return ans_li


def INT_resample( cash_flow, 
                  pay_freq ):
    """ regrouping a given cash flow 
        to make a actual payment from accruing based
        payment sechdule
    """
    ans_li  = []
    loc_ind = 0
    cur_fwd_p = get_fwd_month(pay_freq[loc_ind][1])  
    next_pay_date = add_months(cash_flow[0]["Beg_Time"],cur_fwd_p)

    int_accru = 0
    for idx, ele in enumerate(cash_flow):
        if idx > pay_freq[loc_ind][0]:
            """ Condition if we move one pay
                specification forward
            """
            loc_ind += 1
        if ele["End_Time"] == next_pay_date or idx > len(cash_flow)-1:
            int_accru += ele["Interests"]
            temp = OrderedDict({ "Beg_Time":    ele["Beg_Time"],
                                 "End_Time":    ele["End_Time"], 
                                 "Beg_balance": ele["Beg_balance"],
                                 "PMT":         ele["Principal"] + int_accru,
                                 "Principal":   ele["Principal"],
                                 "Interests":   int_accru,
                                 "Rates":       ele["Rates"], })
            ans_li.append(temp)
            int_accru = 0
            cur_fwd_p = get_fwd_month(pay_freq[loc_ind][1]) 
            next_pay_date = add_months(next_pay_date,cur_fwd_p)
          
        elif ele["End_Time"] > next_pay_date or idx >= len(cash_flow)-1:
            temp = OrderedDict({ "Beg_Time":    ele["Beg_Time"],
                                 "End_Time":    ele["End_Time"], 
                                 "Beg_balance": ele["Beg_balance"],
                                 "PMT":         ele["Principal"] + int_accru,
                                 "Principal":   ele["Principal"],
                                 "Interests":   int_accru,
                                 "Rates":       ele["Rates"], })
            ans_li.append(temp)
            int_accru = ele["Interests"]
            cur_fwd_p = get_fwd_month(pay_freq[loc_ind][1])  
            next_pay_date = add_months(next_pay_date,cur_fwd_p)
          
        elif ele["End_Time"] < next_pay_date:
            int_accru += ele["Interests"]
            temp = OrderedDict({ "Beg_Time":    ele["Beg_Time"],
                                 "End_Time":    ele["End_Time"], 
                                 "Beg_balance": ele["Beg_balance"],
                                 "PMT":         ele["Principal"],
                                 "Principal":   ele["Principal"],
                                 "Interests":   0,
                                 "Rates":       ele["Rates"], })
            ans_li.append(temp)
    return ans_li

def cftb_resample( bal_tb, pay_freq):
    """ reasmple the cash flow table to 
        match exactly payment frequence in 
        fixed leg
    """
    ans_li  = []
    loc_ind = 0
    cur_fwd_p = get_fwd_month(pay_freq[loc_ind][1])  
    next_pay_date = bal_tb[0][0] + relativedelta( months = cur_fwd_p )
    flag = Tools.check_if_last_day_of_month(bal_tb[0][0])
    if flag:
        next_pay_date = Tools.last_day_of_month(next_pay_date)
    ans_li.append(bal_tb[0])
    for idx, ele in enumerate(bal_tb):
        if idx > pay_freq[loc_ind][0]:
            """ Condition if we move one pay
                specification forward
            """
            loc_ind += 1
        if ele[0] == next_pay_date or idx >= len(bal_tb)-1:
            ans_li.append(ele)
            cur_fwd_p = get_fwd_month(pay_freq[loc_ind][1]) 
            next_pay_date = ele[0] + relativedelta(months = cur_fwd_p)
            if flag:
                next_pay_date = Tools.last_day_of_month(next_pay_date)
        elif abs((next_pay_date-ele[0]).days <= 10) \
            or idx >= len(bal_tb)-1 :
            ans_li.append(ele)
            cur_fwd_p = get_fwd_month(pay_freq[loc_ind][1]) 
            next_pay_date = ele[0] + relativedelta(months = cur_fwd_p)
            if flag:
                next_pay_date = Tools.last_day_of_month(next_pay_date)
        
    return ans_li
    
    
        
def get_fwd_month( fwd_freq ):
    """ given inputs fwd_freq in the format of "XXM"
    """
    if fwd_freq[-1].upper() == "M":
        ans = int(fwd_freq[:-1])
    return ans 

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)


    
