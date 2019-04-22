# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 16:01:49 2018
This is the module of option pricing
OPTer takes option type and style type 
to initialize and incorprate both 
black scholes formula and MC simulation method 
to calculation option pricing 
also has the method risk_cal to generate
all greek letters
@author: Shaolun Du
@Contact: Shaolun.du@gmail.com
"""
from collections import OrderedDict
import datetime as dt

from Pricing import models as opt_model
from curve import Boot_Strap_Tools_Func as bt_tool
from Day_Counter import Day_Counter_func as counter
from curve import Boot_Strapping_ccy as B_S
from Pricing.Cash_Flow_Gen import Gen_OPTTB_by_Input as Gen_OPTTB_by_Input
from Pricing import OPT_Tools as opt_t

class OPTer():
    def __init__( self,
                  curve_instrument,
                  Val_Surface ):
        """ Initial settings for OPTer
            opt_instrument will contain all
            information needed to do pricing
            as well as risk analysis
            opt_instrument = {  "name":....,
                                "type":....,
                                "style":... }
            style = {"Euro","Amer","Berm"...}
            type  = {"cap","floor","swaption","stock","forward","fx","irs"}
            opt_direction = {"Put","Call"}
        """
        self.Day_Counter = counter.Day_Counter("ACT/360")
        self.val_surface = Val_Surface
        self.curve_instrument = curve_instrument
        self.answer_bk = OrderedDict()
        self.instruments = OrderedDict()
        
    def gen_opt_instruments( self,
                             instrument ):
        """ generate option instrument from 
            general instrument
        """
        opt_inst = OrderedDict()
        opt_inst["currency"] = instrument["Leg1"]["Currency"]
        SEC_ID = opt_t.get_sec_id(instrument["Leg1"]["Currency"],instrument["Leg1"]["Type"], "Normal")
        opt_inst["sec_id"]   = SEC_ID
        opt_inst["style"]    = instrument["Leg1"]["Type"]
        opt_inst["strike"]   = instrument["Leg1"]["Strike"]
        opt_inst["schedule"] = Gen_OPTTB_by_Input(instrument["Leg1"])
        if opt_inst["style"].upper() in ("CAP","FLOOR"):
            if "BLACK" in SEC_ID.upper():
                opt_inst["model"] = opt_model.BLK76
            if "NORMAL" in SEC_ID.upper():
                opt_inst["model"] = opt_model.Bachelier
        elif opt_inst["style"].upper() in ("SWAP PAY","SWAP REC"):
            opt_inst["model"] = opt_model.NML_SWAP
        return opt_inst       
    
    def price_opt( self,
                   instrument,
                   val_date ):
        """ Pricing a option on valuation date
        """
        if isinstance( val_date, str ):
            for fmt in ( "%Y-%m-%d", "%m/%d/%Y" ):
                try:
                    val_date = dt.datetime.strptime(val_date, fmt).date()
                    break
                except ValueError:
                    pass
        npv_ans,inst = self.cal_opt_rate( val_date, instrument )
        return npv_ans
    
    def cal_opt_rate( self,
                      val_date,
                      instr ):
        # Calculate option value with vol surface
        Day_Counter = counter.Day_Counter("ACT/360")
        #Day_Counter.set_convention_by_ccy(instr["currency"])
        curve = self.gen_curve( val_date, 
                                instr["currency"],
                                self.curve_instrument,
                                Day_Counter )
        # Curve smoothing
        curve = bt_tool.augument_by_frequency( curve, 1 )
        if instr["style"].upper() in ("CAP","FLOOR"):
            # Cap/Floor case
            val_tb = opt_t.cal_cf_val( instr, curve, self.val_surface, Day_Counter )
        elif instr["style"].upper() in ("CALL","PUT"):
            val_tb = opt_t.cal_cp_val( instr, curve, self.val_surface, Day_Counter )
        elif instr["style"].upper() in ("SWAP PAY","SWAP REC"):
            val_tb = opt_t.cal_swap_val( instr, curve, self.val_surface, Day_Counter )
        fv_li = [[ele["End_Time"],ele["PMT"]] for ele in val_tb]
        delta_li = [[ele["End_Time"],ele["delta"]] for ele in val_tb]
        gama_li  = [[ele["End_Time"],ele["gama"]] for ele in val_tb]
        vega_li  = [[ele["End_Time"],ele["vega"]] for ele in val_tb]
        rho_li   = [[ele["End_Time"],ele["rho"]] for ele in val_tb]
        theta_li = [[ele["End_Time"],ele["theta"]] for ele in val_tb]
        NPV   = opt_t.cal_npv( fv_li, curve )
        delta = opt_t.cal_npv( delta_li, curve )
        gama = opt_t.cal_npv( gama_li, curve )
        vega = opt_t.cal_npv( vega_li, curve )
        rho = opt_t.cal_npv( rho_li, curve )
        theta = opt_t.cal_npv( theta_li, curve )
        rate  = opt_t.Cal_OPT_Rate(val_tb, curve, NPV, Day_Counter)
        
        return {"NPV":NPV,"Rate":rate,"delta":delta,"vega":vega,"rho":rho,"gamma":gama,"theta":theta},instr["schedule"]

    
    def gen_curve( self,
                   value_date,
                   ccy,
                   instrument,
                   Day_Counter ):
        """ Wrapper function:
            Generate swap curve depends on 
            disc_cv_details is either 
            XCS or LIBOR
        """
        instrument = instrument[ccy]
        curve = B_S.boot_strapping_LIBOR_ccy( value_date, 
                                              ccy,
                                              instrument, 
                                              Day_Counter )
        return curve    
    
    def get_answer( self ):
       return self.instruments, self.answer_bk
