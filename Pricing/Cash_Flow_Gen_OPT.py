# -*- coding: utf-8 -*-
"""
Created on Sun Nov  4 12:34:17 2018
Cash Flow generation based on customized balance table

@author: shaol
"""
from collections import OrderedDict
import datetime as dt
from scipy.interpolate import interp1d
import calendar
from dateutil.relativedelta import relativedelta
import math

def Val_Gen_OPT( opt_model,
                 curve,
                 vol_surface,
                 Day_Counter ):
    """ opt_model = { "style":["cap","floor",...],
                      "strike": value,
                      "schedule":[amort. schdule],
                      "model": value function(ex. black function) 
                     }
        vol_surface is an object provides vol lookup
    """
    try:
        SEC_ID = opt_model["sec_id"]
        style  = opt_model["style"]
        K      = opt_model["strike"]
        bal_tb = opt_model["schedule"]
        model  = opt_model["model"]
        #sdate  = opt_model["sdate"]
        sdate  = curve[0][0]
        if isinstance( sdate, str ):
            for fmt in ( "%Y-%m-%d", "%m/%d/%Y","%Y/%mm/%dd" ):
                try:
                    sdate = dt.datetime.strptime(sdate, fmt).date()
                    break
                except ValueError:
                    pass
    except KeyError:
        print(opt_model)
        raise Exception("Missing par in CF_Gen_OPT")
        
    """ Looping through balance table and make a fixing
        on each accrued_freq date and we assume that balance table 
        is coincidence with fixing rate table
    """
    ans_li  = []
    for idx, ele in enumerate(bal_tb[1:]):
        """ idx is the index number here it
            works as the period number
        """
        pre_t = bal_tb[idx][0]
        y_freq = Day_Counter.yearfrac(pre_t,ele[0])
        # Rewrite get_fwd_rate function for option
        fwd_rate = get_fwd_rate_cubic( curve, 
                                       pre_t,
                                       ele[0],
                                       y_freq )
        dis    = get_dis( curve, ele[0] )
        live_t = Day_Counter.yearfrac( sdate, pre_t )
        end_t  = Day_Counter.yearfrac( sdate, ele[0] )
        spor_r = -math.log(dis)/end_t
        # volatility is provided by vol_surface
        # forward annualized volatility
        # unit in percentage %
        vol = vol_surface.vol_lookup( SEC_ID, 
                                      K, 
                                      live_t,
                                      end_t )["f_vol"]/100
        ans_bk = cal_opt_value( model,
                                style,
                                fwd_rate,
                                K,
                                vol,
                                dis,
                                y_freq,
                                live_t,
                                bal_tb[idx][1],
                                spor_r )
        ans_li.append(OrderedDict(
                       { "Beg_Time":    pre_t,
                         "End_Time":    ele[0], 
                         "Beg_balance": bal_tb[idx][1],
                         "PMT":         ans_bk["val"],
                         "vol":         vol,
                         "Rates":       fwd_rate,
                         "DFs":         dis,
                         "Day_Frac":    y_freq,
                         "delta":       ans_bk["delta"],
                         "gama":        ans_bk["gama"],
                         "vega":        ans_bk["vega"],
                         "rho":         ans_bk["rho"],
                         "theta":       ans_bk["theta"]
                         }
                      ))
    return ans_li

def Val_Gen_SWAP( opt_model,
                  curve,
                  vol_surface,
                  Day_Counter ):
    """ opt_model = { "style":["cap","floor",...],
                      "strike": value,
                      "schedule":[amort. schdule],
                      "model": value function(ex. black function) 
                     }
        vol_surface is an object provides vol lookup
    """
    try:
        SEC_ID = opt_model["sec_id"]
        style  = opt_model["style"]
        K      = opt_model["strike"]
        bal_tb = opt_model["schedule"]
        model  = opt_model["model"]
        sdate  = curve[0][0]
        if isinstance( sdate, str ):
            for fmt in ( "%Y-%m-%d", "%m/%d/%Y","%Y/%mm/%dd" ):
                try:
                    sdate = dt.datetime.strptime(sdate, fmt).date()
                    break
                except ValueError:
                    pass
    except KeyError:
        raise Exception("Missing par in CF_Gen_OPT")
        
    """ Looping through balance table and make a fixing
        on each accrued_freq date and we assume that balance table 
        is coincidence with fixing rate table
    """
    ans_li = []
    live_t = Day_Counter.yearfrac( sdate, bal_tb[0][0] )
    tenor = get_WAL( bal_tb ) # Recalculate wal = tenor to handle amortizaing
    y_freq = (bal_tb[1][0].year - bal_tb[0][0].year) * 12 + bal_tb[1][0].month - bal_tb[0][0].month
    y_freq = y_freq/12
    Sum_Dis = 0
    for idx in range(len(bal_tb)-1):
        cur_p = bal_tb[idx]
        nxt_p = bal_tb[idx+1]
        Sum_Dis += cur_p[1]*get_dis( curve, nxt_p[0] )
    # calculate forward par swap rate
    fwd_rate = get_fwd_rate_swap( curve, 
                                  bal_tb,
                                  y_freq )
    # Vol lookup for forward start time and tenor and strike
    vol = vol_surface.vol_lookup_swap( SEC_ID, 
                                       bal_tb[0][0],
                                       tenor )/100
    ans_bk = cal_opt_value( model,
                            style,
                            fwd_rate,
                            K,
                            vol,
                            0,
                            y_freq,
                            live_t,
                            Sum_Dis )
    
    swaption_val = ans_bk["val"]*y_freq*Sum_Dis
    
    ans_li.append( OrderedDict(
                   { "Beg_Time":    bal_tb[0][0],
                     "End_Time":    bal_tb[-1][0], 
                     "Beg_balance": bal_tb[0][1],
                     "PMT":         swaption_val,
                     "vol":         vol,
                     "Rates":       fwd_rate,
                     "delta":       ans_bk["delta"],
                     "gama":        ans_bk["gama"],
                     "vega":        ans_bk["vega"],
                     "rho":         ans_bk["rho"],
                     "theta":       ans_bk["theta"]
                    }
                  ))
    return ans_li

def cal_opt_value( model,
                   style,
                   fwd_rate,
                   K,
                   vol,
                   dis,
                   y_frac,
                   live_t,
                   N,
                   spot_r = ""):
    """ 
    """
    pars = {}
    pars["f"] = fwd_rate
    pars["K"] = K
    pars["vol"] = vol
    pars["dis"] = dis
    pars["year_frac"] = y_frac
    pars["live_t"] = live_t
    pars["N"] = N
    pars["spot_r"] = spot_r
    # Seperate call put 
    if style.upper() == "CAP":
        pars["isCap"] = True
    elif style.upper() == "FLOOR":
        pars["isCap"] = False
    # Seperate payer receiver     
    if style.upper() == "SWAP PAY":
        pars["isPay"] = True
    elif style.upper() == "SWAP REC":
        pars["isPay"] = False
    cf = model(pars)
    
    return cf

def get_fwd_rate_cubic( curve,
                        cur_t,
                        nxt_t,
                        y_frac ):
    # Scipy interpolation method to get forward rate
    curve = resample( curve, 1)
    x,y = [toTimestamp(ele[0]) for ele in curve],[ele[1] for ele in curve]
    f = interp1d(x, y, kind='linear')
    dis_cur = f(toTimestamp(cur_t))
    dis_nxt = f(toTimestamp(nxt_t))
    return (dis_cur/dis_nxt-1)/y_frac

def toTimestamp(d):
  return calendar.timegm(d.timetuple())

def resample( cv_li, freq ):
    # Resample a given according to frerquency
    cv_li = augument_by_frequency(cv_li , freq)
    return cv_li

def get_fwd_rate_swap( curve, 
                       bal_tb,
                       y_freq ):
    # return forward par swap rate given balance
#    x,y = [toTimestamp(ele[0]) for ele in curve],[ele[1] for ele in curve]
#    f = interp1d(x, y, kind='cubic')
#    dis_cur = f(toTimestamp(cur_t))
#    dis_nxt = f(toTimestamp(nxt_t))
    sum_fix, sum_float = 0, 0
    dis_start = get_dis( curve, bal_tb[0][0] )
    for idx in range(len(bal_tb)-1):
        nxt_dis = get_dis( curve, bal_tb[idx+1][0] )
        cur_dis = get_dis( curve, bal_tb[idx][0] )
        sum_float += (cur_dis/nxt_dis-1)*bal_tb[idx][1]*nxt_dis
        sum_fix += nxt_dis*bal_tb[idx][1]
    ans = sum_float/sum_fix/dis_start/y_freq
    return ans


def get_fwd_rate( curve,
                  cur_t,
                  nxt_t,
                  y_frac ):
    """ Get forward rate given yield curve and 
        time period
    """
    for loc in range(1, len(curve)):
        ele     = curve[loc]
        pre_ele = curve[loc-1]
        """ Interpolation on yield curve if needed
        """
        if cur_t >= pre_ele[0] \
            and cur_t < ele[0]:
                cur_discf = inter_linear( pre_ele[0],
                                          ele[0],
                                          pre_ele[1],
                                          ele[1],
                                          cur_t )
        if nxt_t >= pre_ele[0] \
            and nxt_t < ele[0]:
                fwd_discf = inter_linear( pre_ele[0],
                                          ele[0],
                                          pre_ele[1],
                                          ele[1],
                                          nxt_t )
                break
    rates  = (cur_discf/fwd_discf-1)/y_frac
    return rates

def get_WAL( balance ):
    # Calculate weighted average life on balance
    total = 0
    for idx in range(len(balance)-1):
        cur_p = balance[idx]
        nxt_p = balance[idx+1]
        total+= cur_p[1]*(nxt_p[0]-cur_p[0]).days
    wal = (total/balance[0][1])/365
    return wal

def get_dis( curve,
             cur_t ):
    """ Get current annulized interest
        rate given yield curve and time point
    """
    cur_dis = 0
    for idx, ele in enumerate(curve[1:]):
        pre_ele = curve[idx-1]
        if ele[0] >= cur_t and pre_ele[0] <= cur_t:
            cur_dis = inter_linear(pre_ele[0],ele[0],pre_ele[1],ele[1],cur_t)
            break
    return cur_dis

def inter_linear( pre_t, cur_t, pre_v, cur_v, t):
    return (t-pre_t).days/(cur_t-pre_t).days*(cur_v-pre_v)+cur_v


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
            interp_rate = inter_linear( cur_date,
                                        input_list[i][0],
                                        cur_value,
                                        input_list[i][1],
                                        next_date )
            ans_list.append( (next_date,interp_rate) )
            next_date += time_frequency
            if flag:
                next_date = last_day_of_month(next_date)
        cur_date  = input_list[i][0]
        cur_value = input_list[i][1]
    
    return ans_list

def last_day_of_month( any_day ):
    """ Move current date into next month
        Then subtract it from next month
    """
    next_month = any_day.replace(day=28) + dt.timedelta(days=4)  
    return next_month - dt.timedelta(days=next_month.day)


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
