# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 13:41:37 2019
Another version of Swaper
@author: Shaolun Du
@contacts: Shaolun.du@gmail.com
"""
from collections import OrderedDict
from Day_Counter import Day_Counter_func as Day_Count
from curve import Boot_Strapping_ccy as B_S
from Pricing import Swap_Tools  as Tools
from Pricing.Cash_Flow_Gen import Gen_FXTB_by_Input as Gen_FXTB_by_Input

class FXer():
    def __init__( self,
                  curve_instrument,
                  cv_fx_instrument,
                  fx_spot,
                  cv_keeper = "" ):
        """ Initial settings for swaper
            swap_instrument will contain all
            information needed to do pricing
            as well as risk analysis
            swap_instrument = { "name":....,
                                "leg1":....,
                                "leg2":... }
            curve_instrument = {"currency":[...curve instrumentss]}
        """
        self.fx_spot     = fx_spot
        self.cv_keeper   = cv_keeper
        self.answer_bk   = OrderedDict()
        self.instruments = OrderedDict()
        self.curve_instrument = curve_instrument
        self.cv_fx_instrument = cv_fx_instrument
        self.convention = {
            'USD':{ 'fix':{ 'freq':2,},
                    'float':{'freq':4,},
                    'LIBOR_day_count':'30/360',
                    'OIS_day_count':'ACT/360', },
            'EUR':{ 'fix':{ 'freq':1, },
                    'float':{ 'freq':2,},
                    'LIBOR_day_count':'30/360',
                    'OIS_day_count':'ACT/360',},
            'GBP':{ 'fix':{ 'freq':2,},
                    'float':{ 'freq':2,},
                    'LIBOR_day_count':'ACT/365',
                    'OIS_day_count':'ACT/365',},
            'JPY':{ 'fix':{ 'freq':2,},
                    'float':{ 'freq':2,},
                    'LIBOR_day_count':'ACT/365',
                    'OIS_day_count':'ACT/365', },
            'CAD':{ 'fix':{ 'freq':2,},
                    'float':{ 'freq':2,},
                    'LIBOR_day_count':'ACT/365',
                    'OIS_day_count':'ACT/365', },
            'CHF':{ 'fix':{ 'freq':1,},
                    'float':{ 'freq':2,},
                    'LIBOR_day_count':'30/360',
                    'OIS_day_count':'ACT/360', },
            'BRL':{ 'fix':{ 'freq':2,},
                    'float':{ 'freq':2,},
                    'LIBOR_day_count':'30/360',
                    'OIS_day_count':'ACT/360',},
            'COP':{ 'fix':{ 'freq':4,},
                    'float':{ 'freq':4,},
                    'LIBOR_day_count':'ACT/360',
                    'OIS_day_count':'ACT/360',},
        }
            
    def gen_fx_instruments( self,
                            instrument ):
        """ generate swap instrument from 
            general instrument 
            NOTE this implementation derived from
            Basic pricing engine which is 
            totaly different from liv pricing engine
        """
        swap_instrument = OrderedDict()
        swap_instrument["type"] = "LIBOR"
        
        leg1 = OrderedDict()
        leg1["currency"] = instrument["Leg1"]["Currency"]
        leg1["acc_cpn_detail"] = [[1000,"Fix",0,0,-100,100]]
        leg1["balance_tb"] = Gen_FXTB_by_Input(instrument["Leg1"])
        leg1["day_convention"] = "ACT/360"
        
        leg2 = OrderedDict()
        leg2["currency"] = instrument["Leg2"]["Currency"]
        leg2["acc_cpn_detail"] = [[1000,"Fix",0,0,-100,100]]
        leg2["balance_tb"] = Gen_FXTB_by_Input(instrument["Leg2"])
        leg2["day_convention"] = "ACT/360"
        swap_instrument["leg1"] = leg1
        swap_instrument["leg2"] = leg2
        
        if leg1["currency"] != leg2["currency"]:
            # Check if a cross currency swap
            swap_instrument["type"] = "XCS"
        
        return swap_instrument 

    def get_ans( self,
                 instr,
                 value_date,
                 npv_date ):
        npv = self._price(instr,value_date,npv_date)
        return npv  

    def _price( self,
                instr,
                value_date,
                npv_date ):
        """ Pricing a swap based on the 
            valuation date and the corrresponding
            swap name
        """
        ccy1_spot = self.fx_spot[instr["leg1"]["currency"]]
        ccy2_spot = self.fx_spot[instr["leg2"]["currency"]]
        fx_spot   = ccy1_spot/ccy2_spot
        L1_PRI = self.get_NPVs( "leg1",
                                value_date,
                                instr,
                                npv_date )
        L2_PRI = self.get_NPVs( "leg2",
                                value_date,
                                instr,
                                npv_date )
        
        npv0 = L1_PRI-L2_PRI*fx_spot
        return npv0
    
    def get_NPVs( self,
                  leg,
                  value_date,
                  instrument,
                  s_date ):
        """ Disc_cv_details is the specification
            of which discounting curve to use
            when calculating NPV as well as risk analysis
            disc_cv_details = {
                                "type":...,
                                "spread":...,}
        """
        """ Step one cal of legx
            leg1 = { "currency":...,
                     "balance_tb":...,
                     "acc_cpn_detail":...,
                     "pay_convention":....,
                     "day_convention":....,}
        """
        legx = instrument[leg]
        Day_Counter   = Day_Count.Day_Counter("ACT/360")
        currency      = legx["currency"]
        fx_instrument = self.cv_fx_instrument[currency]
        """ Discounting Curve settings below
        """
        cv_dis = self.gen_swap_curve( value_date,
                                      currency,
                                      fx_instrument,
                                      Day_Counter )
        sdate_df = self.get_sdate_df( cv_dis,
                                      s_date )
        Day_Counter.set_convention(legx["day_convention"])
        PRI_flow = legx["balance_tb"]
        NPV_PRI  = Tools.cal_npv( PRI_flow, cv_dis, Day_Counter )
        return NPV_PRI/sdate_df
        
    def get_sdate_df( self,
                      cv_dis,
                      s_date ):
        """ Special function for FXer
            get discount factor on sdate
            forward starting measure
        """
        dfs = 1
        for loc in range(1,len(cv_dis)):
            cur_ele = cv_dis[loc-1]
            nxt_ele = cv_dis[loc]
            if cur_ele[0] <= s_date and nxt_ele[0] > s_date:
                dfs = (s_date-cur_ele[0]).days/(nxt_ele[0]-cur_ele[0]).days*(nxt_ele[1]-cur_ele[1])+cur_ele[1]
        return dfs        
        
    def gen_swap_curve( self,
                        value_date,
                        ccy,
                        instrument,
                        Day_Counter ):
        """ Wrapper function:
            Generate swap curve depends on 
            disc_cv_details is either 
            XCS or LIBOR
        """
        curve = B_S.boot_strapping_LIBOR_ccy( value_date, 
                                              ccy,
                                              instrument, 
                                              Day_Counter )
        return curve
    def gen_zero_curve( self,
                        value_date,
                        ccy,
                        instrument,
                        Day_Counter ):
        """ Wrapper function:
            Generate swap curve depends on
            disc_cv_details is either
            XCS or LIBOR
        """
        curve = B_S.boot_strapping_Zero_ccy( value_date, 
                                             ccy,
                                             instrument, 
                                             Day_Counter )
        return curve
    
    def get_raw_dfs( self,
                     value_date,
                     currency,
                     freq,
                     isEOM,
                     Margin ):
        """ Add on function to generate 
            both libor discount factors
            and fx (basis adjusted)
            disocunt factors
        """
        convention    = self.convention[currency]
        Day_Counter   = Day_Count.Day_Counter(convention["LIBOR_day_count"])
        cv_instrument = self.curve_instrument[currency]
        fx_instrument = self.cv_fx_instrument[currency]
        if currency.upper() != "BRL": 
            cv_dis = self.gen_swap_curve( value_date,
                                          currency,
                                          cv_instrument,
                                          Day_Counter )
            fx_dis = self.gen_swap_curve( value_date,
                                          currency,
                                          fx_instrument,
                                          Day_Counter )
        else:
            cv_dis = self.gen_zero_curve( value_date,
                                          currency,
                                          cv_instrument,
                                          Day_Counter )
            fx_dis = self.gen_zero_curve( value_date,
                                          currency,
                                          fx_instrument,
                                          Day_Counter )
            
        cv_dis = Tools.augument_by_frequency( cv_dis,
                                              freq,
                                              isEOM )
        fx_dis = Tools.augument_by_frequency( fx_dis,
                                              freq,
                                              isEOM )
        return cv_dis,fx_dis
        
    def to_string( self ):
        """ self.answer_bk is a dictionary with key = name
            value contains both valuetions and risks calculation
        """
        bk = self.answer_bk
        num = len([ele for ele in self.answer_bk.items()])
        
        key_str = "Swap Info:\n"
        key_str += "Current has: "+str(num) +" of Swaps.\n"
        key_str += "They are:\n"
        for name, val in self.instruments.items():
            ans = bk[name]
            key_str += name + ":\n"
            key_str += "###--- Values ---###\n"
            key_str += "NPV1="+str(ans["NPV1"]) + "\n"
            key_str += "NPV2="+str(ans["NPV2"]) + "\n"
            key_str += "NPV_Net="+str(ans["NPV_Net"]) + "\n"
            key_str += "###--- Risks ---###\n"
            key_str += "Net_PV01=" + str(ans["Net"]["PV01"]) +"\n"
            key_str += "####################\n"
        return key_str
