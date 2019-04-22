# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 16:37:13 2018
This is the function to read data from
excel 
@author: Shaolun Du
@contacts: Shaolun.du@gmail.com
"""
import xlrd
import IO.IO_Tools_Func as IO_TF
from collections import OrderedDict

class excel_reader():
    """ This is the excel reader take the 
        given structure
    """
    def __init__( self,
                  f_name ):
        self.f_name = f_name
        self.workbook = xlrd.open_workbook(self.f_name)
        self.raw_data = OrderedDict()
        
    def close( self ):
        self.workbook.release_resources()
        del self.workbook
        
    def read_basic_mkt_input( self,
                              s_name ):
        """ Get corresponding BBG Source
            given sheet name
        """
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        ans_bk = {}
        ans_bk["source"]     = worksheet.cell(4,1).value
        ans_bk["curve date"] = worksheet.cell(3,1).value
        ans_bk["value date"] = ans_bk["curve date"]

        # Reformatting below
        ans_bk["curve date"]    = xlrd.xldate.xldate_as_datetime(ans_bk["curve date"], workbook.datemode).date()
        ans_bk["value date"]    = xlrd.xldate.xldate_as_datetime(ans_bk["value date"], workbook.datemode).date()

        return ans_bk

        
    def read_basic_swap_input( self,
                               s_name ):
        """ Get corresponding BBG Source
            given sheet name
        """
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        ans_bk = {}
        ans_bk["source"]     = worksheet.cell(4,1).value
        ans_bk["curve date"] = worksheet.cell(3,1).value
        ans_bk["value date"] = worksheet.cell(11,5).value
        ans_bk["Cur_NPV"]    = worksheet.cell(12,5).value
        if ans_bk["Cur_NPV"] == "":
            ans_bk["Cur_NPV"] = 0
        ans_bk["Leg1"] = {}
        ans_bk["Leg2"] = {}
        key_li = ["Currency","Notional","Sdate","Tenor","Rate","Index","Reset","Pay","DC"]
        for i_row in range(11,20):
            ans_bk["Leg1"][key_li[i_row-11]] = worksheet.cell(i_row,1).value
            ans_bk["Leg2"][key_li[i_row-11]] = worksheet.cell(i_row,3).value
        # Reformatting below
        ans_bk["curve date"]    = xlrd.xldate.xldate_as_datetime(ans_bk["curve date"], workbook.datemode).date()
        ans_bk["value date"]    = xlrd.xldate.xldate_as_datetime(ans_bk["value date"], workbook.datemode).date()
        ans_bk["Leg1"]["Sdate"] = xlrd.xldate.xldate_as_datetime(ans_bk["Leg1"]["Sdate"], workbook.datemode).date()
        ans_bk["Leg2"]["Sdate"] = ans_bk["Leg1"]["Sdate"]
        
        return ans_bk
    
    def read_basic_fx_input( self,
                             s_name ):
        """ Get corresponding BBG Source
            given sheet name
        """
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        ans_bk = {}
        ans_bk["source"]     = worksheet.cell(4,1).value
        ans_bk["cv date"] = worksheet.cell(3,1).value
        ans_bk["value date"] = worksheet.cell(26,5).value
        ans_bk["Leg1"] = {}
        ans_bk["Leg2"] = {}
        key_li = ["Currency","Notional","End"]
        for i_row in range(26,29):
            ans_bk["Leg1"][key_li[i_row-26]] = worksheet.cell(i_row,1).value
            ans_bk["Leg2"][key_li[i_row-26]] = worksheet.cell(i_row,3).value
        # Reformatting below
        ans_bk["value date"] = xlrd.xldate.xldate_as_datetime(ans_bk["value date"], workbook.datemode).date()
        ans_bk["cv date"]    = xlrd.xldate.xldate_as_datetime(ans_bk["cv date"], workbook.datemode).date()
        ans_bk["Leg1"]["End"] = xlrd.xldate.xldate_as_datetime(ans_bk["Leg1"]["End"], workbook.datemode).date()
        ans_bk["Leg2"]["End"] = ans_bk["Leg1"]["End"]
        
        return ans_bk
    
    def read_basic_opt_input( self,
                              s_name ):
        """ Get corresponding BBG Source
            given sheet name
        """
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        ans_bk = {}
        ans_bk["source"]     = worksheet.cell(4,1).value
        ans_bk["curve date"] = worksheet.cell(3,1).value
        ans_bk["value date"] = worksheet.cell(41,5).value
        ans_bk["Leg1"] = {}
        ans_bk["Leg2"] = {}
        key_li = ["Type","Currency","Notional","Strike","Settle","Start","Maturity","Reset"]
        for i_row in range(41,49):
            ans_bk["Leg1"][key_li[i_row-41]] = worksheet.cell(i_row,1).value
        # Reformatting below
        ans_bk["value date"]       = xlrd.xldate.xldate_as_datetime(ans_bk["value date"], workbook.datemode).date()
        ans_bk["curve date"]       = xlrd.xldate.xldate_as_datetime(ans_bk["curve date"], workbook.datemode).date()
        ans_bk["Leg1"]["Settle"]   = xlrd.xldate.xldate_as_datetime(ans_bk["Leg1"]["Settle"], workbook.datemode).date()
        ans_bk["Leg1"]["Start"]    = xlrd.xldate.xldate_as_datetime(ans_bk["Leg1"]["Start"], workbook.datemode).date()
        ans_bk["Leg1"]["Maturity"] = xlrd.xldate.xldate_as_datetime(ans_bk["Leg1"]["Maturity"], workbook.datemode).date()
        ans_bk["Leg2"] = ans_bk["Leg1"]
        return ans_bk
    
    def read_value_date( self,
                         s_name ):
        """ Get corresponding value date
            given sheet name
        """
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        return xlrd.xldate.xldate_as_datetime(worksheet.cell(3,1).value, workbook.datemode).date()
    
    def read_instruments( self,
                          s_name,
                          ccy_num ):
        """ Raed instuemtns from inputs excel 
            special to handle live data pricing
            Output is set of rates which will be feed
            into boot strapping
        """
        ans = {}
        i_row,i_col,t_row = 0,0,0
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        num_rows  = worksheet.nrows
        for i_row in range(ccy_num):
            Cash = []
            Future = [] 
            Swap = [] 
            i_col = 0
            currency = worksheet.cell(3+i_row*25,i_col).value
            num_cash = worksheet.cell(3+i_row*25,i_col+1).value
            fut_cash = worksheet.cell(3+i_row*25,i_col+3).value
            swp_cash = worksheet.cell(3+i_row*25,i_col+5).value
            t_row = 5+i_row*25
            while worksheet.cell(t_row,i_col).value != "":
                date = xlrd.xldate.xldate_as_datetime(worksheet.cell(t_row,i_col).value, workbook.datemode)
                rate = worksheet.cell(t_row,i_col+1).value
                Cash.append([date.date(),rate])
                t_row += 1
            t_row = 5+i_row*25
            i_col += 2
            while worksheet.cell(t_row,i_col).value != "":
                date = xlrd.xldate.xldate_as_datetime(worksheet.cell(t_row,i_col).value, workbook.datemode)
                rate = worksheet.cell(t_row,i_col+1).value
                Future.append([date.date(),rate])
                t_row += 1
            i_col += 2
            t_row = 5+i_row*25
            while worksheet.cell(t_row,i_col).value != "":
                date = xlrd.xldate.xldate_as_datetime(worksheet.cell(t_row,i_col).value, workbook.datemode)
                rate = worksheet.cell(t_row,i_col+1).value
                Swap.append([date.date(),rate])
                t_row += 1
                if t_row >= num_rows:
                    break
            ans[currency] = {}
            ans[currency]["cash"]   = [ Cash, int(num_cash) ]
            ans[currency]["future"] = [ Future, int(fut_cash) ]
            ans[currency]["swap"]   = [ Swap, int(swp_cash) ]
        return ans
    
    def read_vol( self,
                  s_name,
                  num ):
        """ read vol surface inputs
        """
        ans = []
        t_row, t_row = 0, 0
        shift = 20
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        sdate = xlrd.xldate.xldate_as_datetime(worksheet.cell(1,0).value, workbook.datemode).date()
        for idx in range(num):
            t_row = 3+idx*shift
            name = worksheet.cell(t_row-3,0).value
            while worksheet.cell(t_row,0).value != "":
                t_col = 1
                while worksheet.cell(t_row,t_col).value != "":
                    strike = worksheet.cell(2+idx*shift,t_col).value
                    tenor = worksheet.cell(t_row,0).value
                    if "SWAP" in name.upper():
                        start = xlrd.xldate.xldate_as_datetime(tenor, workbook.datemode).date()
                        tenor = strike
                    else:
                        start = sdate
                        tenor = int(tenor)
                    vol = worksheet.cell(t_row,t_col).value
                    temp = { "sec":name, "sdate":sdate,
                             "start":start, "tenor":tenor,
                             "strike":strike, "vol":vol }
                    ans.append(temp)
                    t_col = t_col + 1
                t_row = t_row + 1
        return ans
    
    def read_FX_rates( self,
                       s_name ):
        """ read fx spot rates from excel
            s_name = sheet name
        """
        ans       = {}
        i_row     = 1
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        num_rows  = worksheet.nrows - 1
        while i_row <= num_rows:
            currency = worksheet.cell(i_row,2).value
            spot     = worksheet.cell(i_row,1).value
            ans[currency] = spot
            i_row += 1
        return ans

    def gen_instruments( self, 
                         itype,
                         name,
                         leg1_ccy,
                         leg2_ccy,
                         leg1_cpn_detail,
                         leg2_cpn_detail,
                         leg1_pay_convention,
                         leg2_pay_convention,
                         day_convention,
                         balance_tb_1,
                         balance_tb_2 ):
        """ Resturcture raw data into swap 
            instrument structure
        """
        ibook = OrderedDict()
        ibook["itype"] = itype
        ibook["leg1_ccy"] = leg1_ccy
        ibook["leg2_ccy"] = leg2_ccy
        ibook["leg1_cpn_detail"] = leg1_cpn_detail
        ibook["leg2_cpn_detail"] = leg2_cpn_detail
        ibook["leg1_pay_convention"] = leg1_pay_convention
        ibook["leg2_pay_convention"] = leg2_pay_convention
        ibook["leg1_day_convention"] = day_convention[0][0]
        ibook["leg2_day_convention"] = day_convention[0][1]
        ibook["balance_tb_1"] = balance_tb_1
        ibook["balance_tb_2"] = balance_tb_2
        self.raw_data[name] = ibook
        
        
    
    def get_schedule( self,
                      wb,
                      worksheet,
                      s_row,
                      s_col,
                      num_row ):
        """ Generate full schedule given location
        """
        balance_tb = []
        for row in range(s_row,num_row+1):
            if worksheet.cell(row,s_col).value != "":
                dates = xlrd.xldate.xldate_as_datetime(worksheet.cell(row,s_col).value, wb.datemode)
                balance_tb.append([dates.date(),worksheet.cell(row,s_col+1).value])
            else:
                break
        return balance_tb
    
    def read_opt( self,
                  s_name ):
        # Test function for option pricing
        """ reorginzed the inputs into option
            style
        """
        self.read(s_name)
        ans = {}
        for key,vals in self.raw_data.items():
            temp = {}
            temp["itype"] = vals["itype"]
            temp["currency"] = vals["leg1_ccy"]
            temp["strike"] = vals["leg1_cpn_detail"][0][0]
            temp["balance"] = vals["balance_tb_1"]
            ans[key] = temp
        return ans
    def read_DFs(self, s_name):
        """ Read from discount factors
        """
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        EoM  = worksheet.cell(5,1).value
        Freq = worksheet.cell(6,1).value
        Marg = worksheet.cell(7,1).value*100
        return Freq,EoM,Marg
    def convert_2_list( self,
                        inputs ):
        inputs = inputs.split("$")
        ans = []
        for ele in inputs:
            ele = ele[1:-1]
            temp = ele.split(",")
            li = []
            for x in temp:
                x = IO_TF.is_num(x)
                li.append(x)
            ans.append(li)
        return ans
    
    def get_raw_data( self ):
        names = [ele[0] for ele in self.raw_data.items()]
        print("#############################################")
        print("###---Current Captures:"+str(len(names))+" items---###")
        print(names)
        print("#############################################")
        
        return names, self.raw_data
    
    def to_string( self ):
        ans = ""
        names = [ele[0] for ele in self.raw_data.items()]
        ans += "#############################################\n"
        ans += "###---Current Captures:"+str(len(names))+" items---###\n"
        ans += ";".join(names)
        ans += "\n#############################################\n"
        return ans
    

        







