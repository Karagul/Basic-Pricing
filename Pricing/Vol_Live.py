# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 10:33:46 2019
Object of volatility surface calculating and storing
@author: Shaolun Du
@contacts: shaolun.du@gmail.com
"""
from scipy.interpolate import interp1d
from scipy import interpolate
import datetime as dt
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt

class Val_Surface():
    def __init__( self,
                  sdate,
                  vol_instrument ):
        # Generate volitility surface 
        # given market date
        self.sdate = sdate
        if type(self.sdate) is dt.date:
            self.sdate = self.sdate.strftime("%Y-%m-%d")
        self.raw_data = vol_instrument
        
    def vol_lookup_swap( self,
                         SEC_ID,
                         start,
                         tenor ):
        # Lookup volatility of swap 
        # Currently not considering the vol smile 
        # for swaption since lacking of inputs
        # data so this look up is not accurate currently
        curve = self.get_curve_by_forward( SEC_ID, start )
        tck = interpolate.splrep([ele[0] for ele in curve],[ele[1] for ele in curve])
        vol = interpolate.splev(tenor,tck)
        return vol
    
    def vol_lookup( self,
                    SEC_ID,
                    strike,
                    start,
                    end ):
        """ Volatility lookup by strike and tenor
            Inputs start and end integer in terms of years
            Given condition period of forward volatility
            is less than 1 year
        """
        vol_curve = self.get_curve_by_s( SEC_ID, strike )
        vol_curve.append([0,vol_curve[0][1]])
        vol_curve = sorted(vol_curve, key=lambda x:x[0])
        vol_fwd = self.gen_fwd_vol(vol_curve)
        f = interp1d( [ele[0] for ele in vol_fwd],
                      [ele[1] for ele in vol_fwd],
                      kind='nearest')
        
        # Interpolating forward vol
        f_vol = f(math.floor(end))
        
        ans = { "spot_vol":f_vol,
                "f_vol":f_vol }
        return ans
    def gen_fwd_vol(self, vol_curve):
        """ Generate forward volatility curve
            annually data output
            given spot vol curve
        """
        ans = [[0,vol_curve[0][1]]]
        f = interp1d([ele[0] for ele in vol_curve],
                     [ele[1] for ele in vol_curve],
                     kind='linear')
        i_loc = list(range(1,20))
        for loc in i_loc:
            cur_vol = f(loc)
            nxt_vol = f(loc+1)
            try:
                ans.append([loc,math.sqrt(nxt_vol*nxt_vol*(loc)-cur_vol*cur_vol*(loc-1))])
            except:
                ans.append([loc,ans[-1][1]])
        return ans
    
    def get_curve_by_s( self, SEC_ID, strike ):
        """ build volatility surface 
            by cubic spline interpolation 
            on single maturity vol curve (1D)
        """
        surface = self.gen_surface_ID( SEC_ID )
        # Look up volatility by interpolation method
        vol_curve = []
        all_m = set([ele["tenor"] for ele in surface])
        for m in all_m:
            # Build volatility curve with standard maturity
            temp_li = [[ele["strike"],ele["vol"]] for ele in surface if ele["tenor"]==m]
            x = [ele[0] for ele in temp_li]
            y = [ele[1] for ele in temp_li]
            tck = interpolate.splrep(x,y)
            spot_vol = interpolate.splev(strike,tck)
            vol_curve.append([m,float(spot_vol)])
        vol_curve = sorted(vol_curve, key=lambda x:x[0])
        
        return vol_curve
    
    def get_curve_by_forward( self, SEC_ID, start ):
        surface = self.gen_surface_ID( SEC_ID )
        all_f_time = sorted(list(set([ele["start"] for ele in surface])))
        for idx in range(len(all_f_time)-1):
            if start >= all_f_time[idx] and start < all_f_time[idx+1]:
                t_time = all_f_time[idx]
        data = [[ele["tenor"], ele["vol"]] for ele in surface if ele["start"] == t_time]
        data = sorted(data,key=lambda x:x[0])
        return data
    
    def gen_surface_ID( self, SEC_ID):
        """ generate vol surface by sec id
        """
        if not self.raw_data:
            raise Exception("Cannot get raw data in Vol surface...")
        data = [ele for ele in self.raw_data if ele["sec"] == SEC_ID]
        return data
       
    def check_vol_surface( self, SEC_ID ):
        """ Check volatility surface given SEC ID
        """
        # Output : figure object
        from scipy.interpolate import griddata
        from mpl_toolkits.mplot3d import Axes3D
        from matplotlib import cm
        if not self.raw_data:
            raise Exception("Cannot get raw data in Vol surface...")
        data = [ele for ele in self.raw_data if ele["sec"] == SEC_ID]
        s_min = int(min([ele["strike"] for ele in data])*1000)
        s_max = int(max([ele["strike"] for ele in data])*1000)
        temp = []
        for s in range(s_min,s_max,1):
            strike = s/1000
            ans = self.get_curve_by_s( SEC_ID, strike )
            for ele in ans:
                temp.append({"strike":strike,"tenor":ele[0],"vol":ele[1]})
        df = pd.DataFrame(temp)
        x1 = np.linspace(df['strike'].min(), df['strike'].max(), len(df['strike'].unique()))
        y1 = np.linspace(df['tenor'].min(), df['tenor'].max(), len(df['tenor'].unique()))
        x2, y2 = np.meshgrid(x1, y1)
        z2 = griddata((df['strike'], df['tenor']), df['vol'], (x2, y2), method='cubic')    
        fig = plt.figure()
        ax = Axes3D( fig )
        surf = ax.plot_surface( x2, y2, z2, 
                                cmap=cm.rainbow, 
                                rstride=1, 
                                cstride=1 )
        return surf
    
        
###########################
###--- Testing below ---###   
#sdate = "2019-02-14"
#schema_name = "Yield_Curve"
#tb_name = "vcub"
#SEC_ID  = "USD Normal SWAP"
#start = "2019-05-14"
#start = dt.datetime.strptime(start, '%Y-%m-%d').date()
#tenor = 3.5
#val_s = Val_Surface( sdate,
#                     schema_name,
#                     tb_name )
#val_s.get_raw_data()
##fig = val_s.check_vol_surface(SEC_ID)
#ans = val_s.vol_lookup_swap( SEC_ID,
#                             start,
#                             tenor )
#print(ans)


