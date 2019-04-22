# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 14:43:51 2018
Test function on writer object
@author: Shaolun Du
@Contact: Shaolun.du@gmail.com
"""
import IO.Writer as Writer

f_name = "Output.xlsx"
s_name = "Answer"
test_str = "This is a test message---> Hello World!"
writer = Writer.Writer( f_name )
writer.add_sheet(s_name)
writer.write_ticker( s_name,5,5,test_str)
writer.close()





