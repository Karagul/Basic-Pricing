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
from Pricing.Cash_Flow_Gen import CF_Gen as CF_Gen
from Pricing.Cash_Flow_Gen import Gen_TB_by_Input as Gen_TB_by_Input
class SWAPer():
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
            
    def gen_swap_instruments( self,
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
        if instrument["Leg1"]["Index"].upper() == "LIBOR":
            leg1["acc_cpn_detail"] = [[1000,"LIBOR",instrument["Leg1"]["Reset"],instrument["Leg1"]["Rate"],-100,100]]
        else:
            leg1["acc_cpn_detail"] = [[1000,"FIX",instrument["Leg1"]["Rate"],0,-100,100]]
        leg1["pay_convention"] = [[1000,instrument["Leg1"]["Pay"]]]
        leg1["balance_tb"] = Gen_TB_by_Input(instrument["Leg1"])
        leg1["day_convention"] = instrument["Leg1"]["DC"]
        
        leg2 = OrderedDict()
        leg2["currency"] = instrument["Leg2"]["Currency"]
        if instrument["Leg2"]["Index"].upper() == "LIBOR":
            leg2["acc_cpn_detail"] = [[1000,"LIBOR",instrument["Leg2"]["Reset"],instrument["Leg2"]["Rate"],-100,100]]
        else:
            leg2["acc_cpn_detail"] = [[1000,"FIX",instrument["Leg2"]["Rate"],0,-100,100]]
        
        leg2["pay_convention"] = [[1000,instrument["Leg2"]["Pay"]]]
        leg2["balance_tb"] = Gen_TB_by_Input(instrument["Leg2"])
        leg2["day_convention"] = instrument["Leg2"]["DC"]
        swap_instrument["leg1"] = leg1
        swap_instrument["leg2"] = leg2
        
        if leg1["currency"] != leg2["currency"]:
            # Check if a cross currency swap
            swap_instrument["type"] = "XCS"

        return swap_instrument 

    def get_ans( self,
                 instr,
                 Cur_NPV,
                 cv_date,
                 val_date ):
        """ Calculate PV01 on given date based on instr
            PV01 is calculated by shifting par swap rate up by 1 bps
        """
        # Shitfing up by 1 bps
        bps = 1
        rate,npv = self.price_swap(instr,Cur_NPV,cv_date, val_date)
        self.shift_all_cvs(bps) # Shift curve up 1bps
        xx,npv_up = self.price_swap(instr,Cur_NPV,cv_date, val_date)
        self.shift_all_cvs(-bps) # Shift curve down 1bps
        PV01 = npv-npv_up
        KRDs = []
        krd_loc = range(1,40)
        for y_loc in krd_loc:
            self.shift_all_cvs(bps,y_loc)
            rate,npv_x = self.price_swap(instr,Cur_NPV,cv_date, val_date)
            self.shift_all_cvs(-bps,y_loc)
            KRDs.append(npv-npv_x)
        KRDs = Tools.KRD_regroup(KRDs)
        return npv,PV01,rate,KRDs  

    def price_swap( self,
                    instr,
                    Cur_NPV,
                    cv_date,
                    val_date ):
        """ Pricing a swap based on the 
            valuation date and the corrresponding
            swap name
        """
        ccy1_spot = self.fx_spot[instr["leg1"]["currency"]]
        ccy2_spot = self.fx_spot[instr["leg2"]["currency"]]
        fx_spot   = ccy1_spot/ccy2_spot
        L1_INT,L1_PRI = self.get_NPVs( "leg1",
                                       cv_date,
                                       instr,
                                       val_date )
        L2_INT,L2_PRI = self.get_NPVs( "leg2",
                                       cv_date,
                                       instr,
                                       val_date )
        if instr["leg2"]["acc_cpn_detail"][0][2] == 1:
            npv = 0
        else:
            npv = L1_INT+L1_PRI-L2_PRI*fx_spot-L2_INT*fx_spot
        try:
            pre_rate = instr["leg1"]["acc_cpn_detail"][0][2]
            fixed_rate = (L2_INT+L2_PRI-L1_PRI*fx_spot+Cur_NPV)/(L1_INT/pre_rate*fx_spot)
        except:
            pre_rate = instr["leg2"]["acc_cpn_detail"][0][2]
            fixed_rate = (L1_INT+L1_PRI-L2_PRI*fx_spot-Cur_NPV)/(L2_INT/pre_rate*fx_spot)
        
        return fixed_rate,npv
    
    
    def shift_all_cvs( self,
                       bps,
                       y_loc = -1):
        """ Shift all curves up by bps
            bps change to units of percentage (%)
            NOTE: bps/100 = bps in %
        """
        y_loc = y_loc*365
        # Shock LIBOR cuvre
        self.shock_cv( self.curve_instrument,
                       bps,
                       y_loc )
        # Shock FX adjusted libor cuvre
        self.shock_cv( self.cv_fx_instrument,
                       bps,
                       y_loc )
    
    def shock_cv( self,
                  cv_inst,
                  bps,
                  y_loc ):
        """ Shock curve instruments by type
        """
        for ccy,ccy_int in cv_inst.items():
            # Loop thourgh currency
            cv_sdate = ccy_int["cash"][0][0][0]
            for xx,data in ccy_int.items():
                # Loop thourgh instruments
                for ele in data[0]:
                    period = (ele[0]-cv_sdate).days
                    if y_loc < 0:
                        # Shock all term
                        try:
                            ele[1] = ele[1] + bps/100 
                        except:
                            ele[1] = ele[1]
                    elif abs(period-y_loc) <= 360:
                        # Shock specified term
                        factor = 1-abs(period-y_loc)/360
                        try:
                            ele[1] = ele[1] + factor*bps/100 
                        except:
                            ele[1] = ele[1]  
                        
    def get_NPVs( self,
                  leg,
                  curve_date,
                  instrument,
                  value_date = ""):
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
        if value_date == "":
            value_date = curve_date
        legx = instrument[leg]
        Day_Counter   = Day_Count.Day_Counter(legx["day_convention"])
        currency      = legx["currency"]
        #convention    = self.convention[currency]
        cv_instrument = self.curve_instrument[currency]
        fx_instrument = self.cv_fx_instrument[currency]
        """ Discounting Curve settings below
        """
        if instrument["type"].upper() == "XCS":
            """ For XCS calculation we have to use 
                dual curves method libor curve for 
                coupon calculation and basis adjusted
                curve for discounting 
            """
            cv_dis = self.gen_swap_curve( curve_date,
                                          currency,
                                          fx_instrument,
                                          Day_Counter )
            instrument["type"] = "SWAP"
            cv_fwd = self.gen_swap_curve( curve_date,
                                          currency,
                                          cv_instrument,
                                          Day_Counter )
            instrument["type"] = "XCS"
        else:
            Day_Counter.set_convention_by_ccy(currency)
            cv_fwd = self.gen_swap_curve( curve_date,
                                          currency,
                                          cv_instrument,
                                          Day_Counter )
            cv_dis = cv_fwd
            
        Day_Counter.set_convention(legx["day_convention"])
        cf_tb  = CF_Gen( legx, 
                         cv_fwd,
                         self.cv_keeper,
                         Day_Counter )
        df0 = self.get_df0( cv_dis, value_date )
        INT_flow = [[ele["End_Time"],ele["Interests"]] for ele in cf_tb]
        NPV_INT  = Tools.cal_npv( INT_flow, cv_dis, Day_Counter )
        PRI_flow = [[ele["End_Time"],ele["Principal"]] for ele in cf_tb]
        NPV_PRI  = Tools.cal_npv( PRI_flow, cv_dis, Day_Counter )
        return NPV_INT/df0,NPV_PRI/df0
        
    def get_df0( self,
                 cv_dis,
                 s_date ):
        """ Get df0 factor
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
