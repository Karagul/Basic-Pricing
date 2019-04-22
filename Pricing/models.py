# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 14:04:10 2019
Black-76 formular on caplets or floorlets pricing
@author: Alan
@contact: Shaolun.du@gmail.com
"""
import math
from scipy.stats import norm

def BLK76( paras ):
    """
    Black formula to calculate option price on
    forwards or futures
        "f" : Forward price
        "K" : Strike price
        "vol": sigma of underlying
        "r":  interest rate annualy
        "year_frac": year fraction of T-t
        "N" : Notional
        "isCap" : Caplet or Floorlet
    """
    try:
        f = paras["f"]
        K = paras["K"]
        vol = paras["vol"]
        year_frac = paras["year_frac"]
        live_t = paras["live_t"]
        N = paras["N"]
    except KeyError:
        raise Exception("Missing keys for BLK76 inputs pars...")

    d1 = (math.log(f/K) + (vol*vol/2*live_t))/(vol*math.sqrt(live_t))
    d2 = d1 - vol*math.sqrt(live_t)
    if paras["isCap"]:
        fv    = N*year_frac*(f*norm.cdf(d1)-K*norm.cdf(d2))
        delta = norm.cdf(d1)
        gama  = norm.cdf(d1)/(f*vol*math.sqrt(live_t))
        vega  = f*norm.cdf(d1)*math.sqrt(live_t)
        #theta = -f*norm.cdf(d1)*vol/(2*math.sqrt(live_t))+r*
        rho = -live_t*fv
    else:
        fv    = N*year_frac*(K*norm.cdf(-d2)-f*norm.cdf(-d1))
        delta = norm.cdf(d1)-1
        gama  = norm.cdf(d1)/(f*vol*math.sqrt(live_t))
        vega  = f*norm.cdf(d1)*math.sqrt(live_t)
        #theta = -f*norm.cdf(d1)*vol/(2*math.sqrt(live_t))+r*
        rho   = -live_t*fv
        
    return { "val":fv,
             "delta":delta,
             "gama":gama,
             "vega":vega,
             "rho":rho,
             "theta": 0}
    

def Bachelier( paras ):
    """
    Black formula to calculate option price on
    forwards or futures
        "f" : Forward price
        "K" : Strike price
        "vol": sigma of underlying
        "r":  interest rate annualy
        "year_frac": year fraction of T-t
        "N" : Notional
        "isCap" : Caplet or Floorlet
    """
    try:
        f = paras["f"]
        K = paras["K"]
        vol = paras["vol"]
        year_frac = paras["year_frac"]
        live_t = paras["live_t"]
        N = paras["N"]
        spot_r = paras["spot_r"]
    except KeyError:
        raise Exception("Missing keys for BLK76 inputs pars...")
    ans = 0
    BPS_Unit = 10000
    vol = vol/100
    d = (f-K)/(vol*math.sqrt(live_t))
    if paras["isCap"]:
        ans   = (f-K)*norm.cdf(d)+vol*math.sqrt(live_t)/math.sqrt(2*math.pi)*math.exp(-d*d/2)
        delta = norm.cdf(d)/BPS_Unit
        gama  = norm.pdf(d*d)/(vol*BPS_Unit*math.sqrt(live_t))/BPS_Unit
        vega  = norm.pdf(d*d)*math.sqrt(live_t)/BPS_Unit
        theta = -spot_r*ans-norm.pdf(d*d)*vol/2*100
        rho   = -live_t*ans/BPS_Unit
    else:
        ans   = (K-f)*norm.cdf(-d)+vol*math.sqrt(live_t)/math.sqrt(2*math.pi)*math.exp(-d*d/2)
        delta = -norm.cdf(-d)/BPS_Unit
        gama  = norm.pdf(d)/(vol*math.sqrt(live_t))/BPS_Unit
        vega  = norm.pdf(d)*math.sqrt(live_t)/BPS_Unit
        theta = -spot_r*ans-norm.pdf(d*d)*vol/2*100
        rho   = -live_t*ans/BPS_Unit
        
    return { "val":ans*N*year_frac,
             "delta":delta*N*year_frac,
             "gama":gama*N*year_frac,
             "vega":vega*N*year_frac,
             "rho":rho*N*year_frac,
             "theta": theta }

def BLK_SWAP( paras ):
    """
    Black formula to calculate option price on
    forwards or futures
        "f" : Forward price
        "K" : Strike price
        "vol": sigma of underlying
        "r":  interest rate annualy
        "year_frac": year fraction of T-t
        "N" : Notional
        "isCap" : Caplet or Floorlet
    """
    try:
        f = paras["f"]
        K = paras["K"]
        vol = paras["vol"]
        year_frac = paras["year_frac"]
        live_t = paras["live_t"]
        sum_N = paras["N"]
    except KeyError:
        raise Exception("Missing keys for BLKSWAP inputs pars...")

    d1 = (math.log(f/K) + (vol*vol/2*live_t))/(vol*math.sqrt(live_t))
    d2 = d1 - vol*math.sqrt(live_t)
    if paras["isPay"]:
        fv = sum_N*year_frac*(f*norm.cdf(d1)-K*norm.cdf(d2))
        delta = 0
        gama = 0
        vega = 0
        #theta = -f*norm.cdf(d1)*vol/(2*math.sqrt(live_t))+r*
        rho = 0
    else:
        fv = sum_N*year_frac*(K*norm.cdf(-d2)-f*norm.cdf(-d1))
        delta = 0
        gama = 0
        vega = 0
        #theta = -f*norm.cdf(d1)*vol/(2*math.sqrt(live_t))+r*
        rho = 0
    return { "val":fv,
             "delta":delta,
             "gama":gama,
             "vega":vega,
             "rho":rho,
             "theta": 0}

def NML_SWAP( paras ):
    """
    Black formula to calculate option price on
    forwards or futures
        "f" : Forward price
        "K" : Strike price
        "vol": sigma of underlying
        "r":  interest rate annualy
        "year_frac": year fraction of T-t
        "N" : Notional
        "isCap" : Caplet or Floorlet
    """
    try:
        f = paras["f"]
        K = paras["K"]
        vol = paras["vol"]
        live_t = paras["live_t"]
    except KeyError:
        raise Exception("Missing keys for BLKSWAP inputs pars...")
    ans = 0
    vol = vol/100
    d = (f-K)/(vol*math.sqrt(live_t))
    if paras["isPay"]:
        ans = (f-K)*norm.cdf(d)+vol*math.sqrt(live_t)/math.sqrt(2*math.pi)*math.exp(-d*d/2)
    else:
        ans = (K-f)*norm.cdf(-d)+vol*math.sqrt(live_t)/math.sqrt(2*math.pi)*math.exp(-d*d/2)
    
    return { "val":ans,
             "delta":0,
             "gama":0,
             "vega":0,
             "rho":0,
             "theta": 0}


