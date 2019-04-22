# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 14:48:50 2019
Special bootstrapping function for back testing 
@author: Shaolun Du
@Contacts: Shaolun.du@gmail.com
"""
import numpy as np
from datetime import datetime as datetime
from dateutil.relativedelta import relativedelta
##################################
###--- Tools Function Below ---###
import curve.Boot_Strap_Tools_Func as BS_TF
from curve.Boot_Strap_Convention import BS_Con as BS_Con

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
    
def boot_strap_back_ccy( sdate,
                         ccy,
                         instruments,
                         Day_Counter ):
    """ Preliminary paramaters set ups
        instruments = {"Cash":[[date,rate],num],
                       "future":[[date,rate],num],
                       "swap":[[date,rate],num] }
    """
    convention  = BS_Con[ccy]
    years_days_cash   = convention["Cash_Day"]
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
    Cash_Num    = len(Cash_Rate)
    """ NOTE: inputs of futures rate should have one start row 
        with date and the discount factor is interpolated from 
        cash rate
    """
    Swap_Rate   = instruments["swap"][0]
    units       = 100

    discount_curve = []
    ans_curve = []
    discount_curve.append( [sdate,1] )
    ans_curve.append([sdate,1])
    """ Remeber par swap key dates location in discount_curve
    """
    
    for i in range( 0, int(Cash_Num) ):
        """ Begin bootstrapping from Cash rates
        """
        yearfrac = (Cash_Rate[i][0]-sdate).days/years_days_cash
        DF = 1.0/(1.0+Cash_Rate[i][1]/units*yearfrac)
        discount_curve.append([Cash_Rate[i][0],DF])
        if (Cash_Rate[i][0]-sdate).days <= 200:
            ans_curve.append([Cash_Rate[i][0],DF])

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
#        if sum_df == 0:
#            print("Warning Cannot get correct 0.5y, 1y and 1.5y discount factors...")
#            print("Current Date:"+str(cur_date))
#            print(ccy)
#            print(ans_curve)
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
