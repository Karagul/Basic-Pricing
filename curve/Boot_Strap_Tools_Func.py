# -*- coding: utf-8 -*-
"""
This file contains all helper function
used in boot strap program
@author: Alan
@Contacts: Shaolun.du@gmail.com
"""
import pandas as pd 
from math import log, exp
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta
import datetime as dt

def augument_by_frequency( input_list, 
                           months ):
    """ Inputs dates should be at least half year seperated
    """
    ans_list  = []
    cur_date  = input_list[0][0]
    cur_value = input_list[0][1] 
    flag = False
    if check_if_last_day_of_month(cur_date):
        flag = True
    interp_rate = cur_value
    time_frequency = relativedelta( months = months )
    ans_list.append((cur_date,cur_value))
    next_date = cur_date + time_frequency
    if flag:
        next_date = last_day_of_month(next_date)
    for i in range(1, len(input_list)):
        while next_date <= input_list[i][0]:
            interp_rate = interpolation_act( next_date,
                                             cur_date,
                                             cur_value,
                                             input_list[i][0],
                                             input_list[i][1] )
            ans_list.append( (next_date,interp_rate) )
            next_date += time_frequency
            if flag:
                next_date = last_day_of_month(next_date)
        cur_date  = input_list[i][0]
        cur_value = input_list[i][1]
    
    return ans_list

def get_rates_ann_li( input_list ):
    """ Inputs dates should be at least half year seperated
    """
    ans_list  = []
    cur_date  = input_list[0][0]
    cur_value = input_list[0][1] 
    time_frequency = relativedelta( months = 12 )
    next_date = cur_date + time_frequency
    ans_list.append((cur_date,cur_value))
    for i in range(1, len(input_list)):
        cur_value = input_list[i][1] 
        while next_date <= input_list[i][0]:
            interp_rate = interpolation_act( next_date,
                                             cur_date,
                                             cur_value,
                                             input_list[i][0],
                                             input_list[i][1] )
            ans_list.append( (next_date,interp_rate) )
            next_date += time_frequency
    return ans_list


def get_yield_cv_by_frequency( yield_curve,
                               frequency ):
    """ Function returns interpolated yield by frequency
        ex freq = 12 means monthly data
    """
    ans_list = {}
    ans_list["Date"] = []
    ans_list["DF"]   = []
    yield_frequency = relativedelta( months = int(12/frequency) )
    cur_date        = yield_curve["Date"][0]
    for i in range(1, len(yield_curve["Date"])):
        sdate  = yield_curve["Date"][i-1]
        svalue = yield_curve["DF"][i-1]
        edate  = yield_curve["Date"][i]
        evalue = yield_curve["DF"][i]
        while cur_date >= sdate\
            and cur_date <= edate:
                interp_df = interpolation_act(cur_date,sdate,svalue,edate,evalue)
                ans_list["Date"].append(cur_date)
                ans_list["DF"].append(interp_df)
                cur_date += yield_frequency
    return ans_list

def shock_inputs_curve( sdate,
                        curve,
                        name,
                        shock_year,
                        BPS,
                        spread ):
    """ Check and make linear decay shock 
        on inputs curves
        When shock year is 0 means parelle shocks
        Otherwise is the Key rate shocks
    """
    ans = [] 
    curve_loc = [(ele[0], ele[1] + spread) for ele in curve]
    if shock_year == 0:
        ans = [(ele[0], ele[1] + BPS) for ele in curve_loc]
    else:
        if name == "CASH":
            for ele in curve_loc:
                if shock_year == 1:
                    ans.append((ele[0], ele[1] + BPS))
                else:
                    ans.append((ele[0], ele[1]))
        elif name == "SWAP":
            for ele in curve_loc:
                days = abs((ele[0]-sdate).days - shock_year*365)
                if days < 365:
                    ans.append((ele[0],ele[1] + BPS*(1-days/365)))
                else:
                    ans.append((ele[0],ele[1]))
        elif name == "FUTURE":
            for ele in curve_loc:
                days = (ele[0]-sdate).days - shock_year*365
                if shock_year == 1 and days <= 30:
                    ans.append( (ele[0],ele[1] + BPS) )
                else:
                    ans.append( (ele[0],ele[1]) )
        elif name == "OIS":
            for ele in curve_loc:
                days = abs((ele[0]-sdate).days - shock_year*365)
                if days < 365:
                    ans.append((ele[0],ele[1] + BPS*(1-days/365)))
                else:
                    ans.append((ele[0],ele[1]))
    return ans
                
    

def shock_point_by_discf( yearfrac, 
                          discf, 
                          BPS ):
    """ Calculate new discf after shocking
    """
    rate  = discf_2_rate( yearfrac, discf )
    rate += BPS
    discf = rate_2_discf( yearfrac, rate )

    return discf

def discf_2_rate( yearfrac, discf ):
    if yearfrac == 0:
        rate = 0
    else:
        rate = -log(discf)/yearfrac
    return rate     
   
def rate_2_discf( yearfrac, rate ):
    if yearfrac == 0:
        discf = 1
    else:
        discf = exp(-rate*yearfrac)
    return discf 

def interpolation_act( cur_time, 
                       start_time, 
                       start_value, 
                       end_time, 
                       end_value ):
    """ Interpolation function based on time location
    """
    return start_value + \
        (end_value-start_value)*(cur_time-start_time)/(end_time-start_time)

def last_day_of_month( any_day ):
    """ Move current date into next month
        Then subtract it from next month
    """
    next_month = any_day.replace(day=28) + dt.timedelta(days=4)  
    return next_month - dt.timedelta(days=next_month.day)

def getIMMDate(idate):
    """ Takes 2 digit IMM code and returns effective date 
        as datetime object
    """    
    idate = datetime(idate.year, idate.month, idate.day)
    year = idate.year
    month = idate.month
    the_date = datetime(year, month, 1)
    temp = the_date.replace(day=1)
    nth_week = 3
    week_day = 2
    adj = (week_day - temp.weekday()) % 7
    temp += timedelta(days=adj)
    temp += timedelta(weeks=nth_week - 1)
    if temp < idate:
        year = idate.year
        the_date = datetime(year, month, 1)
        temp = the_date.replace(day=1)
        nth_week = 3
        week_day = 2
        adj = (week_day - temp.weekday()) % 7
        temp += timedelta(days=adj)
        temp += timedelta(weeks=nth_week - 1)
    temp = temp.date()
    return temp

def check_instruments(instruments):
    """ instruments inputed by a set of market rates
        structure = {
                "cash":[[...set of rates],number of valid cash items]
                "future":[[...set of rates],number of valid future items]
                "swap":[[...set of rates],number of valid swap items]
            }
    """
    
    return instruments

def check_if_last_day_of_month(idate):
    import datetime
    import calendar
    #  calendar.monthrange return a tuple (weekday of first day of the 
    #  month, number  
    #  of days in month)
    last_day_of_month = calendar.monthrange(idate.year, idate.month)[1]
    # here i check if date is last day of month
    if idate == datetime.date(idate.year, idate.month, last_day_of_month):
        return True
    return False

