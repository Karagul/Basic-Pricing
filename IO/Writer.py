# -*- coding: utf-8 -*-
"""
Created on Thu Nov 15 12:51:44 2018
Write to excel function
@author: ACM05
"""
import pandas as pd
import IO.IO_Tools_Func as IO_TF

class Writer():
    def __init__( self,
                  f_name ):
        """ Writer object for 
            defined format 
        """
        self.f_name = f_name
        self.writer = pd.ExcelWriter( f_name,
                                      engine='xlsxwriter',
                                      options={'nan_inf_to_errors': True})
        self.book   = self.writer.book
        """ Loading all format settings
        """
        self.header_format   = self.book.add_format(IO_TF.get_format())
        self.ticker_format   = self.book.add_format(IO_TF.get_ticker_format())
        self.thousand_format = self.book.add_format(IO_TF.get_num_k_format())
        self.bold_format = self.book.add_format(IO_TF.get_format_bold())
        self.pct_format  = self.book.add_format(IO_TF.get_num_pct_format())
        self.BPS_format  = self.book.add_format(IO_TF.get_num_BPS_format())
        
    def add_sheet( self,
                   s_name ):
        """ Add sheets into this workbook
            Please pre define all worksheet names
        """
        workbook = self.writer.book
        worksheet  = workbook.add_worksheet( s_name )
        self.writer.sheets[s_name] = worksheet
    
    def write_ticker( self,
                      s_name,
                      i_row,
                      i_col,
                      i_string ):
        """ Write tickers with defined formatting
        """
        worksheet = self.writer.sheets[s_name]
        worksheet.write( i_row, i_col, 
                         i_string, self.ticker_format )
        
    def write_raw( self,
                   s_name,
                   i_row,
                   i_col,
                   i_string ):
        """ Write string into given file with sheet name
            raw data without design
        """
        worksheet = self.writer.sheets[s_name]
        worksheet.write( i_row, i_col, 
                         i_string, self.bold_format )
    
    def write_df( self,
                  i_row,
                  i_col,
                  df,
                  s_name ):
        """ Write to excel given
            file name and sheet name
        """
        """ Step one load formatting
        """
        worksheet = self.writer.sheets[s_name]
        """ Step two write df into this work sheet
        """
        df = df.reset_index()
        df = IO_TF.Add_Sum_Row_df(df, "NAN")
        df.to_excel( self.writer,
                     s_name, 
                     startrow  = i_row,
                     startcol  = i_col,
                     index = False )
        for col, value in enumerate(df.columns.values):
            worksheet.write( i_row, col+i_col, 
                             value, self.header_format )
        for col, value in enumerate(df.iloc[-1]):
            if value == value:
                worksheet.write( i_row+df.shape[0], col+i_col, 
                                 value, self.bold_format )
            else:
                worksheet.write( i_row+df.shape[0], col+i_col, 
                                 "", self.bold_format )    
    def write_tb_raw( self,
                      i_row,
                      i_col,
                      tb,
                      s_name ):
        """ Write to excel given
            file name and sheet name
        """
        worksheet = self.writer.sheets[s_name]
        for i in range(len(tb)):
            for j in range(len(tb[i])):
                value =tb[i][j]
                worksheet.write( i_row+i, i_col+j, 
                                 value )
            
    def close( self ):
        self.writer.save()
                
        
