# -*- coding: utf-8 -*-
""" This function is used to do bootstrapping 
    based on three different type of inputs contracts:
            1\Cash rates (ex. LIBOR)
            2\Futures rates (ex. Eurodollar Futures)
            3\Swap rates (ex. par-swap rates)
    User can select how many contract will be used 
    within each groups by that means we will keep the 
    corresponding contract value exact in the output yield curve.
    NOTE: For example, if we are not selecting the 6M LIBOR rate then 
    the value of 6M rate will be interpolated based on linear function 
    of discount factors which means, in this case, if we input a 6M LIBOR
    to do pricing the result will not be par-value probablly.
    So the more exact number of contracts we are using the more
    exact value we can get from market instruments pricing however,
    the output yiled curve sometimes will looks not soomth, in this case.
    
    Author: Alan
    Contact: Shaolun.du@gmail.com
    Date: 12/31/2018
"""
import pandas as pd
import numpy as np
from datetime import datetime as datetime
from dateutil.relativedelta import relativedelta
##################################
###--- Tools Function Below ---###
import curve.Boot_Strap_Tools_Func as BS_TF
from curve.Boot_Strap_Convention import BS_Con as BS_Con
def reset_cash_rate_3M( sdate, 
                        instruments ):
    """ Reset cash rate to only take 3M deposit rate
    """
    ans = []
    cash_t = instruments["cash"]
    for item in cash_t[0]:
        if (item[0]-sdate).days <= 100 and (item[0]-sdate).days >= 80:
            ans = [[item],1]
    if not ans:
        ans = [[cash_t[-1]],1]
    instruments["cash"] = ans
    
    return instruments

def boot_strapping_LIBOR_ccy( sdate,
                              ccy,
                              instruments,
                              Day_Counter ):
    """ Preliminary paramaters set ups
        instruments = {"Cash":[[date,rate],num],
                       "future":[[date,rate],num],
                       "swap":[[date,rate],num] }
    """
    instruments = reset_cash_rate_3M( sdate, instruments )
    convention  = BS_Con[ccy]
    years_days_cash   = convention["Cash_Day"]
    years_days_future = convention["Future_Day"]
    swap_freq   = convention["Swap_Freq"]
    Day_Counter.set_convention(convention["Swap"])
    instruments = BS_TF.check_instruments( instruments )
    
    sdate = str_2_date( sdate )
    
    flag = False
    if BS_TF.check_if_last_day_of_month( sdate ):
        flag = True
    """ Sdate stands for the begin of bootstrapping 
        Inputs structure instruments contains:
            1\cash rates list of tuple and number of contracts 
            2\future rates list of tuple and number of contracts
            3\swap rates list of tuple and number of contracts
        Structure of rate list looks like (time,rates)
    """
    Cash_Rate   = instruments["cash"][0]
    Cash_Num    = instruments["cash"][1]
    Future_Rate = instruments["future"][0]
    """ NOTE: inputs of futures rate should have one start row 
        with date and the discount factor is interpolated from 
        cash rate
    """
    Future_Num  = instruments["future"][1]
    Swap_Rate   = instruments["swap"][0]
    units       = 100
    
    future_1st_df  = 1
    discount_curve = []
    ans_curve = []
    discount_curve.append( [sdate,1] )
    ans_curve.append([sdate,1])
    """ Remeber par swap key dates location in discount_curve
    """
    if Future_Num == 0:
        Cash_Num = len(Cash_Rate)
    
    for i in range( 0, int(Cash_Num) ):
        """ Begin bootstrapping from Cash rates
        """
        yearfrac = (Cash_Rate[i][0]-sdate).days/years_days_cash
        DF = 1.0/(1.0+Cash_Rate[i][1]/units*yearfrac)
        discount_curve.append([Cash_Rate[i][0],DF])
        if (Cash_Rate[i][0]-sdate).days <= 200:
            ans_curve.append([Cash_Rate[i][0],DF])

    if Future_Num > 0:
        """ If future item number > 0
            means we have to do interpolation
            for future rates
        """
        cur_date = Future_Rate[0][0] - relativedelta( months = 3 )
        cur_date = BS_TF.getIMMDate(cur_date)
        if cur_date >= discount_curve[0][0]:
            for i in range(1, len(discount_curve)):
                if cur_date >= discount_curve[i-1][0]\
                    and cur_date < discount_curve[i][0]:
                        future_1st_df = BS_TF.interpolation_act(cur_date,
                                                                discount_curve[i-1][0],
                                                                discount_curve[i-1][1],
                                                                discount_curve[i][0],
                                                                discount_curve[i][1])
                        future_1st_df = future_1st_df*1/(1.0+(Future_Rate[0][1]/units*(Future_Rate[1][0]-Future_Rate[0][0]).days/years_days_future))
                        
        else:
            future_1st_df = 1/(1.0+(Future_Rate[0][1]/units*(Future_Rate[0][0]-sdate).days/years_days_future))
        cur_df = future_1st_df
        discount_curve.append( [Future_Rate[0][0],cur_df] )
        for i in range(1, Future_Num):
            """ Accumulate through futures rates
            """
            if cur_df == 1:
                print("Warning did not get the first discount factor for future's data.")
            """ We have an header row in first position skip it...
            """
            new_df = cur_df/(1.0+(Future_Rate[i][1]/units*(Future_Rate[i][0]-Future_Rate[i-1][0]).days/years_days_future))
            discount_curve.append([Future_Rate[i][0],new_df])
            cur_df   = new_df
    Swap_Rate = BS_TF.augument_by_frequency( Swap_Rate, int(12/swap_freq) )
    
    """ Only do interpolation for 
        the first three swaps 
        0.5y, 1y and 1.5y
    """
    """ Pre-calculate the sum of discount 
        factors of 0.5y, 1y and 1.5y based 
        on the current discount curve we have 
    """
    sum_df = 0
    swap_frequency = relativedelta( months = int(12/swap_freq) )
    """ Move cur_date back to do bootstrapping
    """
    cur_date = sdate
    for i in range( 1, len(discount_curve) ):
        while cur_date+swap_frequency < Swap_Rate[0][0] \
            and cur_date >= discount_curve[i-1][0] \
            and cur_date < discount_curve[i][0]:
                nxt_date = cur_date+swap_frequency
                if flag:
                    nxt_date = BS_TF.last_day_of_month(cur_date+swap_frequency)
                yearfrac = Day_Counter.yearfrac( cur_date, nxt_date )
                DF = BS_TF.interpolation_act( nxt_date,
                                              discount_curve[i-1][0],
						                                  discount_curve[i-1][1],
									                            discount_curve[i][0],
									                            discount_curve[i][1] )
                sum_df   += DF*yearfrac
                ans_curve.append([nxt_date,DF])
                cur_date += swap_frequency
                if flag:
                    cur_date = BS_TF.last_day_of_month(cur_date)
                
    cur_date = Swap_Rate[0][0]
              
    for i in range( 0, len(Swap_Rate) ):
        if sum_df == 0:
            print("Warning Cannot get correct 0.5y, 1y and 1.5y discount factors...")
            print("Current Date:"+str(cur_date))
            print(ccy)
            print(ans_curve)
        """ Sum of previous discount 
            factors stored in "sum_df"
        """
        nxt_date = cur_date+swap_frequency
        if flag:
            nxt_date = BS_TF.last_day_of_month(nxt_date)
        yearfrac = Day_Counter.yearfrac( cur_date, nxt_date )
        rates    = Swap_Rate[i][1]
        cur_DF   = (100-sum_df*rates)/(100+rates*yearfrac)
        discount_curve.append([cur_date,cur_DF])
        ans_curve.append([cur_date,cur_DF])
        sum_df   += cur_DF*yearfrac
        cur_date += swap_frequency
        if flag:
            cur_date = BS_TF.last_day_of_month(cur_date)
        
    sorted_discount_curve = sorted( ans_curve, key = lambda tup: tup[0] )
    return sorted_discount_curve

def boot_strapping_Zero_ccy( sdate, 
                             ccy,
                             instruments, 
                             Day_Counter ):
    sdate = str_2_date( sdate )
    """ Special case for construction of 
        zero coupon swap insturments as inputs
        for yield curve construction
    """
    Cash_Rate   = instruments["cash"][0]
    Cash_Num    = instruments["cash"][1]
    """ NOTE: inputs of futures rate should have one start row 
        with date and the discount factor is interpolated from 
        cash rate
    """
    Future_Num = instruments["future"][1]
    Swap_Rate  = instruments["swap"][0]
    units      = 100
    years_days_cash= 365
    discount_curve = []
    discount_curve.append( [sdate,1] )
    """ Remeber par swap key dates location in discount_curve
    """
    if Future_Num == 0:
        Cash_Num = len(Cash_Rate)
    
    for i in range( 0, int(Cash_Num) ):
        """ Begin bootstrapping from Cash rates
        """
        yearfrac = (Cash_Rate[i][0]-sdate).days/years_days_cash
        #yearfrac = Day_Counter.yearfrac( sdate, Cash_Rate[i][0] )
        DF = 1.0/(1.0+Cash_Rate[i][1]/units*yearfrac)
        discount_curve.append([Cash_Rate[i][0],DF])
    for ele in Swap_Rate:
        frac_day = np.busday_count(sdate, ele[0])/252
        DF = 1/(1+ele[1]/100)**frac_day
        discount_curve.append([ele[0],DF])
    sorted_discount_curve = sorted( discount_curve, key = lambda tup: tup[0] )
    return sorted_discount_curve

def boot_strapping_OIS_ccy( sdate, 
                            ccy,
                            instruments, 
                            Day_Counter ):
    convention = BS_Con[ccy]
    years_days_cash = convention["Cash_Day"]
    Day_Counter.set_convention(convention["OIS_day_count"])
    sdate = str_2_date( sdate )
    """ Sdate stands for the begin of bootstrapping OIS
        Inputs structure instruments are all daily compounded 
        rates from sdate to some time in the future
        Structure of rate list looks like (time,rates)
    """
    num_month = 12
    swap_frequency = relativedelta( months = num_month )
    cash_rate = [point for point in instruments if (point[0]-sdate).days <= 366]
    swap_rate = [point for point in instruments if (point[0]-sdate).days > 366]

    discount_sum = 0
    discf_curve = []
    discf_curve.append( [sdate,1] )
    for point in cash_rate:
        yearf = (point[0] - sdate).days/years_days_cash
        discf = BS_TF.rate_2_discf( yearf, point[1]/100 )
        discf_curve.append( [point[0], discf] )
    
    discount_sum += discf_curve[-1][1]* Day_Counter.yearfrac( swap_rate[0][0]-swap_frequency,
                                                              swap_rate[0][0] )
    for i in range( 0, len(swap_rate) ):
        cur_rate     = swap_rate[i][1]
        cur_mat_date = swap_rate[i][0]
        """ Sum of previous discount 
            factors stored in "sum_df"   
        """
        y_frac     = Day_Counter.yearfrac( cur_mat_date-swap_frequency,
                                           cur_mat_date )
        
        sum_fixed  = cur_rate*discount_sum
        cur_DF     = (100 - sum_fixed)/(100 + cur_rate*y_frac)
        discf_curve.append( [cur_mat_date,cur_DF] )
        discount_sum += cur_DF*y_frac
    
    return discf_curve

def str_2_date( sdate ):
    """ Convet date string into datatime
    """
    if isinstance( sdate, str ):
        for fmt in ( "%Y-%m-%d", "%m/%d/%Y" ):
            try:
                return datetime.strptime( sdate, fmt ).date()
            except ValueError:
                pass
    else:
        return sdate