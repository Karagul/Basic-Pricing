# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 13:10:35 2018
Live Pricing Tools functions

@author: Shaolun Du
@contact: Shaolun.du@gmail.com
"""
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta

def augument_by_frequency( input_list, 
                           months ):
    """ Inputs dates should be at least half year seperated
    """
    ans_list  = []
    cur_date  = input_list[0][0]
    cur_value = input_list[0][1] 
    time_frequency = relativedelta( months = months )
    next_date = cur_date
    for i in range(1, len(input_list)):
        while next_date < input_list[i][0]:
            interp_rate = interpolation_act( next_date,
                                             cur_date,
                                             cur_value,
                                             input_list[i][0],
                                             input_list[i][1] )
            ans_list.append( (next_date,interp_rate) )
            next_date += time_frequency
            #next_date = last_day_of_month(next_date)
            
        cur_date  = input_list[i][0]
        cur_value = input_list[i][1] 
    
    return ans_list


def cal_npv( cash_flow, 
             disct_curve,
             val_date = ""):
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
def get_fwd_rate( Rates_Curve, 
                  cur_time, 
                  fwd_period,
                  Day_Counter,
                  cv_keeper,
                  currency ):
    if fwd_period <= 0:
        print("Error in get_fwd_rate---> Please Correct fwd_period! Current Value:{0}".format(fwd_period))
    """ Calculate annually forward rate based 
        on fwd_period at any given point on 
        the underlying yield curve
        With fwd_period = 0 returns current 
        annully interests rate
        Discount_curve is a ordered list"[]" 
        of tuple (time, discf)
        cur_time shoud be date data type
        fwd_period should be number by month
    """
    cur_discf, fwd_discf = 1, 1
    if cur_time < Rates_Curve[0][0] and \
        cur_time + relativedelta( months = fwd_period ) >= Rates_Curve[0][0]:
        """ This is the condition that we have to look back 
            and fix the first coupon
            The only thing we have to change is the 
            rate curve to make it start at cur_time
        """
        shift = dt.timedelta(max(1,(cur_time.weekday() + 6) % 7 - 3))
        cur_time = cur_time - shift
        #print("Fixing a Coupon at Date = "+str(cur_time))
        Rates_Curve = cv_keeper.gen_curve_by_date( currency,
                                                   cur_time,
                                                   Day_Counter )
        cur_time = Rates_Curve[0][0]
    elif cur_time < Rates_Curve[0][0]:
        """ Floating rate in the past is out of 
            consideration
        """
        return 0 
    
    fwd_time = cur_time + relativedelta( months = fwd_period )
    for loc in range(1, len(Rates_Curve)):
        ele     = Rates_Curve[loc]
        pre_ele = Rates_Curve[loc-1]
        """ Interpolation on yield curve if needed
        """
        if cur_time >= pre_ele[0] \
            and cur_time < ele[0]:
                cur_discf = interpolation_act( cur_time,
                                               pre_ele[0],
                                               pre_ele[1],
                                               ele[0],
                                               ele[1] )
        if fwd_time >= pre_ele[0] \
            and fwd_time < ele[0]:
                fwd_discf = interpolation_act( fwd_time,
                                               pre_ele[0],
                                               pre_ele[1],
                                               ele[0],
                                               ele[1] )
                break
  
   
    frac_0 = (fwd_time-cur_time).days/365
    #frac_0 = fwd_period/12
    rates  = (cur_discf/fwd_discf-1)/frac_0
    return rates

def get_CMS_rate( Rates_Curve, 
                  time_point, 
                  CMS_period_month,
                  Day_Counter,
                  cv_keeper,
                  currency ):
    if CMS_period_month < 12:
        print("Error in get_CMS_rate---> CMS period shoule at least be 1Year! Current value = {0} Month".format(CMS_period_month))
        print("Return 0 CMS rate when Error...")
        return 0
    discf_sum, discf_init, discf_end = 0, 0, 0
    """ Setup for swap frequency is 6M
    """
    swap_frq        = 6
    CMS_period_year = int(CMS_period_month/12)
    swap_frequency  = relativedelta( months = swap_frq )
    timer           = CMS_period_year*int(12/swap_frq)
    for loc in range(1, len(Rates_Curve)):
        """ DP-programming: Looping over discount curve only once to 
            Calculate CMS rates whenever get a hit
        """
        ele         = Rates_Curve[loc]
        pre_ele     = Rates_Curve[loc-1]
        while time_point >= pre_ele[0] \
            and time_point < ele[0]:
                """ Do interpolation whenever current date is not in curve
                """
                discf       = interpolation_act( time_point,
                                                 pre_ele[0],
                                                 pre_ele[1],
                                                 ele[0],
                                                 ele[1] )
                if timer == CMS_period_year*int(12/swap_frq):
                    """ Pre start point
                    """
                    discf_init = discf
                elif timer == 0:
                    """ End point
                    """
                    discf_sum += discf
                    discf_end  = discf
                    break
                else:
                    """ Points in between
                    """
                    discf_sum  += discf
                
                time_point += swap_frequency
                timer      -= 1 
    if discf_end == 0:
        """ Error Checking if get enough data
        """
        print("Error in get_CMS_rate---> Swap End time value OUT OFF BOUND!")
        print("Current date = {0}, Yield Curve max Date = {1}".format(time_point,Rates_Curve[-1][0]))
        print("Return 0 CMS rate when Error...")
        return 0
    CMS_rate = 2*((discf_init-discf_end)/discf_sum)
    ###--- Convexity adjustment ---###
    # CMS_rate = CMS_rate * convexfact(numyrswap, (timej - date_settle) / 365 * dayfact, implvol)
    return CMS_rate


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
    t_frac = (cur_time-start_time)/(end_time-start_time)
    ans = start_value + (end_value-start_value)*t_frac
    return ans

def last_day_of_month( any_day ):
    """ Move current date into next month
        Then subtract it from next month
    """
    next_month = any_day.replace(day=28) + dt.timedelta(days=4)  
    return next_month - dt.timedelta(days=next_month.day)

def Add_margin( cv_instrument, Margin ):
    """ Add margin into curve instruments
    """
    for ccy,data in cv_instrument.items():
        for d_type,dd in data.items():
            for ele in dd[0]:
                try:
                    ele[1] = ele[1]+Margin
                except:
                    pass
    return cv_instrument
            
