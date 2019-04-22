#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" This is the rates curve generator 
    campitable of handling both discount curve 
    as well as yield curve
    It maintains a book to record on all
    currently avaiable curve generates a new curve 
    whenver must to do
    @author: shaolundu
    @contacts: shaolun.du@gmail.com
"""
import pandas as pd
import datetime as dt
from datetime import date
###--- Tools Functions Below ---###
from Day_Counter import Day_Counter_func as Day_Count
import curve.Swap_Day_Convention as DC_SWAP
import curve.Boot_Strapping_ccy as BS_BT
import curve.Boot_Strap_Tools_Func as BS_TF
import DB.dbExecute as dbEx

class Curve_Keeper:
    """ Curve_Keeper is a stand alone object used to
        manage all current needed yield curve either for 
        discount or comput the interests rates in cash
        flow engine
    """
    def __init__( self, 
                  sdate, 
                  schema_name ):
        """ We store all potential data from DB 
            raw data is in dictionary
            for LIBOR = {"currency":
                            {
                             "cash":[...],
                             "future":[...],
                             "swap":[...],
                            }
                        }
            for OIS = {
                    "currency":[...]
                    }
            
        """
        self.sdate       = sdate
        self.schema_name = schema_name
        LIBOR_table      = "yield_curve"
        FX_table         = "fx_curve"
        OIS_table        = "ois_curve"
        other_table      = "other_rates"
        self.LIBOR_rates = self.get_raw_data( sdate, 
                                              schema_name, 
                                              LIBOR_table ) 
        self.FX_rates    = self.get_raw_data( sdate, 
                                              schema_name, 
                                              FX_table ) 
        self.OIS_rates   = self.get_raw_data( sdate, 
                                              schema_name, 
                                              OIS_table )
        self.Other_rates = self.get_other_data( sdate, 
                                                schema_name, 
                                                other_table )
        
        """ Used to remember all curves
        """ 
        self.curve_book  = {}
        
    def gen_fx_dic_li( self,
                       currency, 
                       shock_year, 
                       BPS,
                       spread,
                       Day_Counter ):
        """ This is special needs function for FX calculator
            we only take the discount factors annually
            at the end of the year
        """
        curve = self.gen_curve( currency, 
                                shock_year, 
                                BPS,
                                spread,
                                Day_Counter )
        curve = BS_TF.get_rates_ann_li( curve['LIBOR'] )
        ans_li= [ele[1] for ele in curve] 
        return ans_li
        
    def gen_curve_by_date( self, 
                           currency,
                           new_date,
                           Day_Counter ):
        """ gen_curve_by_date will generate Libor curve 
            used to calculate one period rates which is 
            fixed during this time
        """
        sdate = new_date
        ticker = currency.upper() +\
                 "_" + str(-1) + "_" + str(0) +\
                 "_" + str(0) +\
                 "_" + "LIBOR" +\
                 "_" + str(sdate) 
        if ticker in self.curve_book:
            return self.curve_book[ticker]
        LIBOR = self.get_raw_data( sdate, 
                                   self.schema_name, 
                                   "yield_curve" )

        FX = self.get_raw_data( sdate, 
                                self.schema_name, 
                                "fx_curve" )
        LIBOR_ans, OIS_ans, FX_ans = self.gen_cf_instruments( currency,
                                                              LIBOR,
                                                              self.OIS_rates,
                                                              FX )
        LIBOR_curve,OIS_Curve,FX_curve = self.get_yields_curve( LIBOR_ans, 
                                                                OIS_ans,
                                                                FX_ans,
                                                                sdate,
                                                                currency, 
                                                                -1, 
                                                                0, 
                                                                0,
                                                                Day_Counter )
        

        self.set_curves( sdate,
                         "LIBOR",
                         -1,
                         0,
                         0,
                         currency,
                         LIBOR_curve )
        self.set_curves( sdate,
                         "FX",
                         -1,
                         0,
                         0,
                         currency,
                         FX_curve )
        
        return LIBOR_curve
        
    def gen_curve( self,  
                   currency, 
                   shock_year, 
                   BPS,
                   spread,
                   Day_Counter ):
        """ gen_curve will generate both curve 
            in each calling since the time point for
            OIS curve is relative small which will not
            cause a huge burden on running time
        """
        sdate = self.sdate
        if isinstance( sdate, str ):
            for fmt in ( "%Y-%m-%d", "%m/%d/%Y" ):
                try:
                    sdate = dt.datetime.strptime(sdate, fmt).date()
                    break
                except ValueError:
                    pass
        ticker_l = currency.upper() +\
                 "_" + str(shock_year) + "_" + str(BPS) +\
                 "_" + str(spread) +\
                 "_" + "LIBOR" +\
                 "_" + str(sdate) 
        ticker_o = currency.upper() +\
                 "_" + str(shock_year) + "_" + str(BPS) +\
                 "_" + str(spread) +\
                 "_" + "OIS" +\
                 "_" + str(sdate) 
        ticker_f = currency.upper() +\
                 "_" + str(shock_year) + "_" + str(BPS) +\
                 "_" + str(spread) +\
                 "_" + "FX" +\
                 "_" + str(sdate) 
        if ticker_l in self.curve_book:
            LIBOR_curve = self.curve_book[ticker_l]
            OIS_Curve   = self.curve_book[ticker_o]
            FX_Curve   = self.curve_book[ticker_f]
            return { "LIBOR" : LIBOR_curve,
                     "FX"    : FX_Curve,
                     "OIS"   : OIS_Curve }
            
        """ If shock year = -1 that
            means no shocking 
        """
        LIBOR = self.LIBOR_rates
        FX    = self.FX_rates
        OIS   = self.OIS_rates
        LIBOR_ans, OIS_ans, FX_ans = self.gen_cf_instruments( currency,
                                                              LIBOR,
                                                              OIS,
                                                              FX )
        
        LIBOR_curve,OIS_Curve, FX_Curve = self.get_yields_curve( LIBOR_ans, 
                                                                 OIS_ans,
                                                                 FX_ans,                                            
                                                                 sdate,
                                                                 currency, 
                                                                 shock_year, 
                                                                 BPS, 
                                                                 spread,
                                                                 Day_Counter )

        """ Set current yield curve into 
            memory if it is the first 
            time to generate 
            Conditioned on shock_year == -1
        """
        if shock_year >= -1:
            self.set_curves( sdate,
                             "LIBOR",
                             shock_year,
                             BPS,
                             spread,
                             currency,
                             LIBOR_curve )
            self.set_curves( sdate,
                             "OIS",
                             shock_year,
                             BPS,
                             spread,
                             currency,
                             OIS_Curve )
            self.set_curves( sdate,
                             "FX",
                             shock_year,
                             BPS,
                             spread,
                             currency,
                             FX_Curve )
        return { "LIBOR" : LIBOR_curve, 
                 "OIS"   : OIS_Curve,
                 "FX"    : FX_Curve }
            
    def get_yields_curve( self,
                          LIBOR_ins, 
                          OIS_ins,
                          FX_ins,
                          sdate,
                          currency, 
                          shock_year, 
                          BPS, 
                          spread,
                          Day_Counter ):
        """ Bootstrapping calculation of yields curve
            shock_year = -1 means does not shock 
            shock_year = 0 means paralell shock
        """
        units    = 100
        BPS      = BPS/units
        OIS_ans  = [0]
        ans_book = {
                    "cash":[0,LIBOR_ins["cash"][1]],
                    "future":[0,LIBOR_ins["future"][1]],
                    "swap" :[0,LIBOR_ins["swap"][1]],
                    }
        fx_book = {
                    "cash":[0,FX_ins["cash"][1]],
                    "future":[0,FX_ins["future"][1]],
                    "swap" :[0,FX_ins["swap"][1]],
                    }
        
        ans_book["cash"][0]   = BS_TF.shock_inputs_curve( sdate,
                                                          LIBOR_ins["cash"][0],
                                                          "CASH",
                                                          shock_year,
                                                          BPS,
                                                          spread )
        ans_book["future"][0] = BS_TF.shock_inputs_curve( sdate,
                                                          LIBOR_ins["future"][0],
                                                          "FUTURE",
                                                          shock_year,
                                                          BPS,
                                                          spread )
        ans_book["swap"][0]   = BS_TF.shock_inputs_curve( sdate,
                                                          LIBOR_ins["swap"][0],
                                                          "SWAP",
                                                          shock_year,
                                                          BPS,
                                                          spread )
        fx_book["cash"][0]   = BS_TF.shock_inputs_curve(  sdate,
                                                          FX_ins["cash"][0],
                                                          "CASH",
                                                          shock_year,
                                                          BPS,
                                                          spread )
        fx_book["future"][0] = BS_TF.shock_inputs_curve(  sdate,
                                                          FX_ins["future"][0],
                                                          "FUTURE",
                                                          shock_year,
                                                          BPS,
                                                          spread )
        fx_book["swap"][0]   = BS_TF.shock_inputs_curve(  sdate,
                                                          FX_ins["swap"][0],
                                                          "SWAP",
                                                          shock_year,
                                                          BPS,
                                                          spread )
        OIS_ans               = BS_TF.shock_inputs_curve( sdate,
                                                          OIS_ins,
                                                          "OIS",
                                                          shock_year,
                                                          BPS,
                                                          spread )
        
        """ Since we are shocking the inputs instruments
            We have to rebootstrapping every time
        """
        if currency != "BRL":
            LIBOR_curve = BS_BT.boot_strapping_LIBOR_ccy( sdate,
                                                          currency, 
                                                          ans_book, 
                                                          Day_Counter )
            FX_curve = BS_BT.boot_strapping_LIBOR_ccy( sdate,
                                                       currency, 
                                                       fx_book, 
                                                       Day_Counter )
        else:
            LIBOR_curve = BS_BT.boot_strapping_Zero_ccy( sdate,
                                                         currency, 
                                                         ans_book, 
                                                         Day_Counter )
            FX_curve = BS_BT.boot_strapping_Zero_ccy( sdate,
                                                      currency, 
                                                      fx_book, 
                                                      Day_Counter )
        
        OIS_Curve   = BS_BT.boot_strapping_OIS_ccy( sdate,
                                                    currency, 
                                                    OIS_ans, 
                                                    Day_Counter )
        LIBOR_curve = [(ele[0],ele[1]) for ele in LIBOR_curve]
        FX_curve    = [(ele[0],ele[1]) for ele in FX_curve]
        OIS_Curve   = [(ele[0],ele[1]) for ele in OIS_Curve]
        
        return LIBOR_curve, OIS_Curve, FX_curve
    
    def gen_cf_instruments( self,
                            ccy,
                            LIBOR_rates,
                            OIS_rates,
                            FX_rates ):
        """ It will be called when 
            curve keeper is called 
            by other objects
        """
        LIBOR_ins= LIBOR_rates[ccy]
        OIS_ins  = OIS_rates[ccy]
        FX_ins   = FX_rates[ccy]
        return LIBOR_ins, OIS_ins, FX_ins
    
    def set_curves( self,
                    sdate,
                    ins_name,
                    shock_year,
                    BPS,
                    spread,
                    currency,
                    curve ):
        ticker = currency.upper() +\
                 "_" + str(shock_year) + "_" + str(BPS) +\
                 "_" + str(spread) +\
                 "_" + ins_name.upper() +\
                 "_" + str(sdate) 
        if not ticker in self.curve_book:
            self.curve_book[ticker] = curve  
            
    def get_other_by_type( self,
                           t_name ):
        data = [[ele["date"],ele["rate"]/100] for ele in self.Other_rates if ele["type"] == t_name]
        data = sorted(data, key = lambda x:x[0])
        return data
        
    def get_other_data( self,
                        sdate, 
                        schema_name, 
                        table_name ):
        """ Get data from DB and generate
            data annually for Others
            !NOTE we only consider data within 
            1 year!
        """
        if isinstance( sdate, str ):
            for fmt in ( "%Y-%m-%d", "%m/%d/%Y" ):
                try:
                    sdate = dt.datetime.strptime(sdate, fmt).date()
                    break
                except ValueError:
                    pass
            sdate = date(sdate.year-1,1,1)
            
        if type(sdate) is dt.date:
            sdate = sdate.strftime("%Y-%m-%d")
        
        sqlstring = "Select * from " + table_name + " where date >= \'" + sdate + "\'"
        raw_data  = dbEx.dbExecute( schema_name, sqlstring )
        if not raw_data:
            print("Worning cannot find corresponding data")
            print("Current date : "+sdate)
            print("Return zero...")
            return 0
        return raw_data
        
    def get_raw_data( self,
                      sdate, 
                      schema_name, 
                      table_name ):
        """ Get data from DB and generate
            data annually for SWAP and OIS
            !Important that is why we have
            augument_by_frequency functions
        """
        if type(sdate) is dt.date:
            sdate = sdate.strftime("%Y-%m-%d")
                
        sqlstring = "Select * from " + table_name + " where sdate = \'" + sdate + "\'"
      
        raw_data  = dbEx.dbExecute( schema_name, sqlstring )

        if not raw_data:
            exp_string = "Worning cannot find corresponding data"
            exp_string += ("Current date : "+sdate)
            raise Exception(exp_string)
            
        if table_name in ("yield_curve","fx_curve"):
            sqlstring = "Select * from curve_setting"
            raw_setting = dbEx.dbExecute( schema_name, sqlstring )
        
        all_ccy   = set([ele["currency"] for ele in raw_data])
        ans_book  = {}
        if table_name[:3].upper() == "OIS":
            for ccy in all_ccy:
                data = [(ele["maturity"],ele["rates"]) for ele in raw_data if ele["currency"].upper() == ccy]
                data = sorted(data, key=lambda tup: tup[0])
                data = BS_TF.augument_by_frequency( data, 12 )
                ans_book[ccy] = data
        elif table_name[:5].upper() == "YIELD" or table_name[:2].upper() == "FX":
            for ccy in all_ccy:
                Cash_Num   = [ele["number"] for ele in raw_setting \
                              if ele["currency"].upper() == ccy \
                              and ele["name"].upper() == "CASH"][0]
                Future_Num = [ele["number"] for ele in raw_setting \
                              if ele["currency"].upper() == ccy \
                              and ele["name"].upper() == "FUTURE"][0]
                Swap_Num   = [ele["number"] for ele in raw_setting \
                              if ele["currency"].upper() == ccy \
                              and ele["name"].upper() == "SWAP"][0]
                data = [ele for ele in raw_data if ele["currency"].upper() == ccy]
                data_CASH   = self.get_rates_by_type( data, "cash" )
                data_FUTURE = self.get_rates_by_type( data, "future" )
                data_SWAP   = self.get_rates_by_type( data, "swap" )
                data_SWAP   = BS_TF.augument_by_frequency( data_SWAP, 12 )
                ans_book[ccy] = {
                            "cash"  : [data_CASH,Cash_Num],
                            "future": [data_FUTURE,Future_Num],
                            "swap"  : [data_SWAP,Swap_Num],
                            }
        
        return ans_book

    def get_rates_by_type( self,
                           data_book = {},
                           ins_type  = "" ):
        
        """ data_book should be a list of dictionary record
            ins_type should be a string to search
            return value is still a list of dictionaries
        """
        data = [ele for ele in data_book if ele["type"].upper() == ins_type.upper()]
        sorted_by_date = sorted(data, key=lambda tup: tup["maturity"])
        ans = [[ele['maturity'], ele['rates']] for ele in sorted_by_date]
        
        return ans

##############################################
###--- output function for Curve_Keeper ---###
    def get_curve_by_ticker( self,
                             curve_details ):
        currency = curve_details[0]
        #curve_name = curve_details[2]
        ticker = currency.upper() +\
                 "_0" + "_0" +\
                 "_" + str(self.sdate) 
        ticker = currency + "_" + str(self.sdate)
        if not ticker in self.curve_book:
            print("Error in get_curve_by_name...")
            print("Curve name is not in dictionary")
            print("Return 0")
            return 0
        return self.curve_book[ticker]
    
    def get_curve_by_currency( self,
                               currency ):
        #curve_name = curve_details[2]
        ticker = currency.upper() + \
                 "_" + "LIBOR" + \
                 "_" + str(self.sdate)
        if not ticker in self.curve_book:
            print("Error in get_curve_by_name...")
            print("Curve name is not in dictionary")
            print("Return 0")
            return 0
        return self.curve_book[ticker]
    
    def to_string( self ):
        ans_string  = str(self.sdate)
        ans_string += ("Schema name = " + self.schema_name)
        ans_string += ("Table name = " + self.table_name)
        return ans_string

###############################################
###--- testinf function for Curve_Keeper ---###
    def gen_instruments_test_data( self, 
                                   file_name,
                                   curve_name ):
        # Generate instruments by test data
        instruments = BS_BT.get_rates_instrument_test( file_name,
                                                       curve_name)
        return instruments



