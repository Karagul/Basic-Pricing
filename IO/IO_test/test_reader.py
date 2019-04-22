# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 14:43:51 2018
Test function on reader object
@author: Shaolun Du
@Contact: Shaolun.du@gmail.com
"""
import IO.Reader as Reader

f_name = "Inputs.xlsx"
s_name = [ "FX" ]
reader = Reader.excel_reader( f_name )
reader.read(s_name[0])
print(reader.to_string())
