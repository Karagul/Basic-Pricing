# -*- coding: utf-8 -*-
""" Day Counter Object handle all day counting issue 
    Given convention
    
    @author: Alan
    @contacts: Shaolun.du@gmail.com
"""

import datetime
import calendar

class Day_Counter:
    _dc_norm = dict( {
        '30/360': '30/360',
        '30/360 US': '30/360 US',
        '30U/360': '30/360 US',
        '360/360': '30/360 US',
        'BOND BASIS': '30/360 US',
        '30E/360': '30E/360',
        '30/360 ICMA': '30E/360',
        '30S/360 ICMA': '30E/360',
        'EUROBOND BASIS (ISDA 2006)': '30E/360',
        'SPECIAL GERMAN': '30E/360',
        '30E/360 ISDA': '30E/360 ISDA',
        'EUROBOND BASIS (ISDA 2000)': '30E/360 ISDA',
        'GERMAN': '30E/360 ISDA',
        '30E+/360': '30E+/360',
        'ACTUAL/ACTUAL ISDA': 'ACTUAL/ACTUAL ISDA',
        'ACTUAL/365': 'ACTUAL/ACTUAL ISDA',
        'ACT/365': 'ACTUAL/ACTUAL ISDA',
        'ACT/ACT': 'ACTUAL/ACTUAL ISDA',
        'ACTUAL/ACTUAL': 'ACTUAL/ACTUAL ISDA',
        'ACTUAL/365 FIXED': 'ACTUAL/365 FIXED',
        'ACT/365 FIXED': 'ACTUAL/365 FIXED',
        'A/365F': 'ACTUAL/365 FIXED',
        'ENGLISH': 'ACTUAL/365 FIXED',
        'ACTUAL/360': 'ACTUAL/360',
        'A/360': 'ACTUAL/360',
        'ACT/360': 'ACTUAL/360',
        'FRENCH': 'ACTUAL/360',
        'ACTUAL/365L': 'ACTUAL/365L',
        'ISMA-YEAR': 'ACTUAL/365L',
        'ACTUAL/ACTUAL AFB': 'ACTUAL/ACTUAL AFB',
        'ACT/ACT AFB': 'ACTUAL/ACTUAL AFB',
        } )
    def __init__( self,
                  convention):
        self.convention = convention
    def set_convention( self, 
                        convention ):
        self.convention = convention
    def set_convention_by_ccy( self,
                               ccy ):
        if ccy.upper() in ("USD","EUR","GBP"):
            self.convention = '30/360'
        elif ccy.upper() in ("COP","CHF"):
            self.convention = 'ACT/360'
        elif ccy.upper() in ("JPY"):
            self.convention = 'ACT/365'
        elif ccy.upper() in ("BRL"):
            self.convention = 'ACT/252'
        
    def yearfrac( self, 
                  dt1, 
                  dt2, 
                  convention="", 
                  **kwargs):
        """ Fractional number of years between two dates 
            according to a given daycount convention
            It can take inputs convention 
            Otherwise use default convention
        """
        return self._daycount_parameters( dt1, 
                                          dt2, 
                                          self.convention, 
                                          **kwargs)[2]
    
    def _daycount_parameters( self, 
                              dt1, 
                              dt2, 
                              convention, 
                              **kwargs):
        """ Return number of days and total 
            number of days (i.e. numerator and
            denominator in the counting of year 
            fraction between dates
        """
        convention = convention.upper()
        convention = self._normalize_daycount_convention( convention )
        y1, m1, d1 = dt1.year, dt1.month, dt1.day
        y2, m2, d2 = dt2.year, dt2.month, dt2.day
        factor = None
    
        if convention in {'30/360','30/360 US', '30E/360', '30E/360 ISDA', '30E+/360'}:
            if convention == '30/360':
                d1 = min (d1,30)
                if d1 == 30:
                    d2 = min(d2,30)
            elif convention == '30/360 US':
                # US adjustments
                if m1 == 2 and d1 >= 28:
                    d1 = 30
                if m2 == 2 and d2 >= 28:
                    d2 = 30
                if d2 == 31 and d1 >= 30:
                    d2 = 30
                if d1 == 31:
                    d1 = 30
            elif convention == '30E+/360':
                if d1 == 31:
                    d1 = 30
                if d2 == 31:
                    m2 += 1
                    if m2 == 13:
                        m2 = 1
                        y2 += 1
                    d2 = 1
    
            num_days  = (360*(y2-y1)+30*(m2-m1)+(d2-d1))
            year_days = 360
        elif convention in {'ACTUAL/365 FIXED', 'ACTUAL/365'}:
            num_days  = (dt2-dt1).days
            year_days = 365
        elif convention == 'ACTUAL/360':
            num_days  = (dt2-dt1).days
            year_days = 360
        elif convention == 'ACTUAL/365L':
            yearly_frequency = 'frequency' in kwargs and kwargs['frequency'] =='yearly'
            if yearly_frequency:
                year_days = 366 if self._period_has_29feb(dt1, dt2) else 365
            else:
                year_days = 366 if calendar.isleap(dt2) else 365
            num_days = (dt2-dt1).days
        elif convention == 'ACTUAL/ACTUAL AFB':
            year_days = 366 if self._period_has_29feb(dt1, dt2) else 365
            num_days  = (dt2-dt1).days
            
        elif convention == 'ACTUAL/ACTUAL ISDA':
            num_days  = 0
            year_days = 0
            if y2 == y1:
                num_days  = (dt2 - dt1).days
                year_days = 365.25
            else:
                """ we need to calculate factor properly
                """
                factor = 0.0
                """ full years between y1 and y2 exclusive
                """
                for y in range(y1+1, y2):
                    yd = 365.25
                    num_days  += yd
                    year_days += yd
                    factor += float(num_days)/year_days
                """ Days in the remaining part of the first year
                """
                num = (datetime.datetime(y1+1, 1, 1).date() - dt1).days
                den = 365.25
                num_days  += num
                year_days += den
                factor += float(num)/den
                """ Days in the beginning of the last year
                """
                num = (dt2 - datetime.datetime(y2, 1, 1).date()).days
                den = 365.25
                num_days += num
                year_days += den
                factor += float(num)/den
        else:
            raise ValueError('Unknown daycount convention \'%s\'' % convention)
    
        if factor is None:
            factor = float(num_days)/year_days
    
        return num_days, year_days, factor

    def _normalize_daycount_convention( self, 
                                        convention ):
        convention = convention.upper()
        return self._dc_norm[convention]
    
    def _period_has_29feb( self, 
                           dt1, 
                           dt2 ):
        have_29_feb = False
        y1 = dt1.year
        y2 = dt2.year
        for y in range(y1, y2+1):
            if calendar.isleap(y) and (
                (y!=y1 and y!=y2)
                or (y == y1 and dt1<datetime.datetime(y1, 2, 29))
                or (y == y2 and datetime.datetime(y2, 2, 29) <= dt2)):
                have_29_feb = True
        return have_29_feb    
    def daydiff( self, 
                 dt1, 
                 dt2, 
                 convention, 
                 **kwargs ):
        """ Calculate difference in days between tow days according to a given
            daycount convention
        """
        return self._daycount_parameters( dt1, 
                                          dt2, 
                                          convention, 
                                          **kwargs )[0]



##################################   
###--- Below is for testing ---###
#Day_Counter = Day_Counter()
#date1 = "08/06/2018"
#date1 = datetime.datetime.strptime(date1, "%m/%d/%Y")
#date2 = "10/06/2019"
#date2 = datetime.datetime.strptime(date2, "%m/%d/%Y")
#convention = '30/360 US'
#print(Day_Counter.daydiff(date1,date2,convention))

