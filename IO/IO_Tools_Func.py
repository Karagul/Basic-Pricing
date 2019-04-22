# -*- coding: utf-8 -*-
"""
Helper functions for GUI output contains
dataframe adjustments and excel formating

@author: Alan
@contacts: Shaolun.du@gmail.com
@date: 07/31/2018
"""
import pandas as pd
import numpy as np
from collections import OrderedDict
from datetime import timedelta,datetime
###################################
###--- Formating rules below ---###
def is_num(value):
  try:
    return float(value)
  except:
    return str(value)

def custom_groupby(df):
    col_names = list(df.columns.values)
    temp_dict = {}
    def wm(x):
        try: 
            return np.average(x, weights=df.loc[x.index, "Notional(K)"])
        except ZeroDivisionError:
            return 0
    #wm = lambda x: np.average(x, weights=df.loc[x.index, "Notional(K)"])
    for name in col_names:
        if name == "CF_WAL(Y)":
            temp_dict[name] = wm
        elif name[:2] == "CF" or name[:3] == "KRD":
            temp_dict[name] = "sum"
        elif name in ( "Notional(K)", "NPV(k)",\
                       "PV01(k)", "FX01(k/%)",\
                       "DCF_CFSen(k)","DCF_FXSen(k)"):
            temp_dict[name] = "sum"
        elif name == "Discount":
            temp_dict[name] = discount_label
    
    df = df.groupby(["Type"],as_index = True).agg(temp_dict)
    df = df.reset_index()

    return df

    
def sort_pd(key=None,reverse=False,cmp=None):
    def sorter(series):
        series_list = list(series)
        return [series_list.index(i) 
           for i in sorted(series_list,key=key,reverse=reverse,cmp=cmp)]
    return sorter

def discount_label(series):
    temp  = [ele.split("+") for ele in series]
    label = temp[0][0]
    i_sum = 0
    for label,spread in temp:
        i_sum += int(float(spread)*100)/100

    spread = round(i_sum/len(temp)*100,0)
    ans    = label+"+"+str(spread)+"%"
    
    return ans


def Add_Sum_Row_df( df,
                    ccy = "ALL" ):
    """ Add one more summary row into current dataframe
        !important please be sure the input dataframe is
        numeric_only like float or int!
    """
    if df.empty:
        return df
    df = df.append( df.sum(numeric_only = True), ignore_index = True )
    df.iloc[-1,0] = "Summary"
    if ccy == "NAN":
        df.iloc[-1,2] = ""
        pass
    else:
        if ccy == "ALL":
            df.iloc[-1,3] = "LCL"
        else:
            df.iloc[-1,3] = ccy
    return df 

def get_format():
    i_format = {
                "font_size": 11,
                "bold": True,
                "text_wrap": True,
                "fg_color": '#ddebf7',
                "border": 1,
                "align": "center",
                'valign':"center",
                }
    return i_format

def get_num_k_format():
    i_format = {
                "font_size": 10,
                "num_format": '#,##0',
                "align": "center",
                }
    return i_format

def get_num_2d_format():
    i_format = {
                "font_size": 10,
                "num_format": '0.00',
                "align": "center",
                }
    return i_format

def get_num_1d_format():
    i_format = {
                "font_size": 10,
                "num_format": '0.0',
                "align": "center",
                }
    return i_format


def get_num_pct_format():
    i_format = {
            'font_size': 10,
            'num_format': '0.000%',
            }
    return i_format

def get_ticker_format():
    i_format = {
            'font_size': 14,
            'bold': True,
            'font_color': '#2f75b5',
            "align": "left",
            }
    return i_format

def get_format_no_wrap():
    i_format = {
                'font_size': 11,
                'bold': True,
                'fg_color': '#ddebf7',
                'border': 1,
                "align": "center",
                }
    return i_format
def get_num_BPS_format():
    i_format = {
                "font_size": 10,
                "text_wrap": True,
                "align": "center",
                "num_format": '#,##0',
                }
    return i_format

def get_format_bold():
    i_format = {
                "font_size": 11,
                "bold": True,
                "text_wrap": True,
                "align": "center",
                "num_format": '#,##0',
                }
    return i_format

def build_inputs_df( ccy,
                     data ):
    col_names = [ "Date", "O/N", "1M", "3M", "6M", 
                  "1Y", "3Y",	"5Y",	"7Y",	"10Y", 
                  "15Y", "20Y", "25Y", "30Y" ]
    data = data[ccy]
    df = pd.DataFrame(data)[col_names]
    
    return df

def diff_2_dates( date1, 
                  date2 ):
    day_diff = (date2-date1).days
    month_label = [1,3,6,9,12]
    year_label  = [1,2,3,5,7,10,15,20,25,30]
    label = ""
    if day_diff >= 1 and day_diff <= 10:
        label = "O/N"
    for m in month_label:
        if day_diff/30 > (m-0.2) \
            and day_diff/30 < (m+0.2):
            label = str(m)+"M"
    for y in year_label:
        if day_diff/365 > (y-0.1) \
            and day_diff/365 < (y+0.1):
            label = str(y)+"Y"
    
    return label

def reformat_rates( ccy,
                    order,
                    raw_data ):
    """ data_book should be a list of dictionary record
        ins_type should be a string to search
        return value is still a list of dictionaries
    """
    data_book = [ele for ele in raw_data if ele["currency"].upper() == ccy and ele["type"].upper() != "FUTURE"]
    sorted_by_date = sorted(data_book, key=lambda tup: tup["maturity"])
    ans_book = OrderedDict()
    if order == 0:
        ans_book["Date"] = "Current"
    elif order == 1:
        ans_book["Date"] = "Pre-Day"
    elif order == 7:
        ans_book["Date"] = "Pre-Month"

    for ele in sorted_by_date:
        tenor = diff_2_dates(ele['sdate'],ele['maturity'])
        if tenor != "":
            ans_book[tenor] = ele["rates"]/100

    return ans_book

def sql_raw_data( sdate, 
                  order,
                  schema_name, 
                  table_name ):
    """ This function is used for GUI cover page output
        We can change the sdate in order to bakcdate the 
        historical data
    """
    sqlstring = "Select * from " + table_name + " where sdate = \'" + sdate + "\'"
    raw_data  = dbEx.dbExecute( schema_name, sqlstring )
    all_ccy   = set([ele["currency"] for ele in raw_data])
    ans_book  = {}
    for ccy in all_ccy:
        data = reformat_rates( ccy, order, raw_data )
        ans_book[ccy] = data
        
    return ans_book, all_ccy

def get_all_raw_date( sdate,
                      schema_name, 
                      table_name ):
    sdate_d   = str_2_date(sdate)
    sdate_1day= pre_bus_date( sdate_d, -1)
    sdate_1m  = pre_bus_date( sdate_d, -30)
    data_0,ccy_li = sql_raw_data( sdate, 
                                  0,
                                  schema_name, 
                                  table_name )
    data_1,_      = sql_raw_data( sdate_1day, 
                                  1,
                                  schema_name, 
                                  table_name )
    data_2,_      = sql_raw_data( sdate_1m,
                                  7,
                                  schema_name, 
                                  table_name )
    
    ans_book = {}
    for ccy in ccy_li:
        dt_0 = data_0[ccy]
        dt_1 = data_1[ccy]
        dt_2 = data_2[ccy]
        del_1 = delta_2_dicts("Delta-Day", dt_0, dt_1)
        del_2 = delta_2_dicts("Delta-Month", dt_0, dt_2)
        ans_book[ccy] = [dt_0, dt_1, dt_2, del_1, del_2]
    return ans_book

    
def delta_2_dicts( tenor,
                   dict1, 
                   dict2 ):
    ans = OrderedDict()
    for key, value in dict1.items():
        if key == "Date":
            ans[key] = tenor
        else:
            if key in dict1 and key in dict2:
                ans[key] = dict1[key]-dict2[key]
    return ans

def pre_bus_date( sdate,
                  num_day ):
    while (sdate + timedelta(days=num_day)).weekday() in (5,6):
        num_day -= 1
    return (sdate + timedelta(days=num_day)).strftime("%Y-%m-%d")

def str_2_date( sdate ):
    if isinstance( sdate, str ):
        for fmt in ( "%Y-%m-%d", "%m/%d/%Y" ):
            try:
                return datetime.strptime( sdate, fmt ).date()
            except ValueError:
                pass
    else:
        return sdate


    