# -*- coding: utf-8 -*-
"""
Created on Sat Nov 19 09:34:59 2016

@author: Linfa
"""

import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from abc import ABCMeta, abstractmethod
#from pandas.io.data import DataReader
from pandas_datareader.data import DataReader


class Strategy(object):
    """Strategy is an abstract base class providing an interface for
    all subsequent (inherited) trading strategies.

    The goal of a (derived) Strategy object is to output a list of signals,
    which has the form of a time series indexed pandas DataFrame.

    In this instance only a single symbol/instrument is supported."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def generate_signals(self):
        """An implementation is required to return the DataFrame of symbols 
        containing the signals to go long, short or hold (1, -1 or 0)."""
        raise NotImplementedError("Should implement generate_signals()!")


class MovingAverageCrossStrategy(Strategy):
    """    
    Requires:
    symbol - A stock symbol on which to form a strategy on.
    bars - A DataFrame of bars for the above symbol.
    short_window - Lookback period for short moving average.
    long_window - Lookback period for long moving average."""

    def __init__(self, symbol, bars, short_window=100, long_window=400):
        self.symbol = symbol
        self.bars = bars

        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self):
        """Returns the DataFrame of symbols containing the signals
        to go long, short or hold (1, -1 or 0)."""
        signals = pd.DataFrame(index=self.bars.index)
        signals['signal'] = 0.0

        # Create the set of short and long simple moving averages over the 
        # respective periods
        signals['short_mavg'] = bars['Close'].rolling(self.short_window, min_periods=1).mean()
        signals['long_mavg'] = bars['Close'].rolling(self.long_window, min_periods=1).mean()

        # Create a 'signal' (invested or not invested) when the short moving average crosses the long
        # moving average, but only for the period greater than the shortest moving average window
        signals['signal'][self.short_window:] = np.where(signals['short_mavg'][self.short_window:] 
            > signals['long_mavg'][self.short_window:], 1.0, 0.0)   
            
        # Take the difference of the signals in order to generate actual trading orders
        signals['sigdiff'] = signals['signal'].diff()
        return signals
        
        
class Portfolio(object):
    """An abstract base class representing a portfolio of 
    positions (including both instruments and cash), determined
    on the basis of a set of signals provided by a Strategy."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def generate_positions(self):
        """Provides the logic to determine how the portfolio 
        positions are allocated on the basis of forecasting
        signals and available cash."""
        raise NotImplementedError("Should implement generate_positions()!")

    @abstractmethod
    def backtest_portfolio(self):
        """Provides the logic to generate the trading orders
        and subsequent equity curve (i.e. growth of total equity),
        as a sum of holdings and cash, and the bar-period returns
        associated with this curve based on the 'positions' DataFrame.

        Produces a portfolio object that can be examined by 
        other classes/functions."""
        raise NotImplementedError("Should implement backtest_portfolio()!")
                
        
class MarketOnClosePortfolio(Portfolio):
    """Encapsulates the notion of a portfolio of positions based
    on a set of signals as provided by a Strategy.

    Requires:
    symbol - A stock symbol which forms the basis of the portfolio.
    bars - A DataFrame of bars for a symbol set.
    signals - A pandas DataFrame of signals (1, 0, -1) for each symbol.
    initial_capital - The amount in cash at the start of the portfolio."""

    def __init__(self, symbol, bars, signals, initial_capital=100000.0):
        self.symbol = symbol        
        self.bars = bars
        self.signals = signals
        self.initial_capital = float(initial_capital)
        self.positions = self.generate_positions()
        
    def generate_positions(self):
        pos = pd.DataFrame(index=signals.index)
        pos['share'] = 100*signals['signal']   # This strategy buys 100 shares
        pos['sharediff'] = pos['share'].diff()   # This strategy buys 100 shares
        pos['sharediff'][0]=0
        return pos
                    
    def backtest_portfolio(self):
        #portfolio = self.positions*self.bars['Adj Close']
        #pos_diff = self.positions['sharediff']
        returns = pd.DataFrame(index=self.bars.index).fillna(0.0)

        returns['share'] = self.positions['share']
        returns['Aclose'] = self.bars['Adj Close']
        returns['holdings'] = (self.positions['share']*self.bars['Adj Close'])
        returns['cash'] = self.initial_capital - (self.positions['sharediff']*self.bars['Adj Close']).cumsum()

        returns['total'] = returns['cash'] + returns['holdings']
        returns['ret_pct'] = returns['total'].pct_change()
        return returns
        
        
if __name__ == "__main__":
    # Obtain daily bars of AMZN from Yahoo Finance for the period
    # 1st Jan 2009 to 1st Jan 2014
    symbol = 'GE'
    bars = DataReader(symbol, "yahoo", datetime.datetime(2009,1,1), datetime.date.today())

    # Create a Moving Average Cross Strategy instance 
    # with short and long moving average windows,40,100
    mac = MovingAverageCrossStrategy(symbol, bars, short_window=40, long_window=100)
    signals = mac.generate_signals()

    # Create a portfolio of AMZN, with $100,000 initial capital
    portfolio = MarketOnClosePortfolio(symbol, bars, signals, initial_capital=100000.0)
    returns = portfolio.backtest_portfolio()

    # Plot two charts to assess trades and equity curve
    fig = plt.figure()
    fig.patch.set_facecolor('white')     # Set the outer colour to white
    ax1 = fig.add_subplot(211,  ylabel='Price in $')
    
    # Plot the AMZN closing price overlaid with the moving averages
    bars['Close'].plot(ax=ax1, color='r', lw=2.,figsize=(12,8))
    signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.)

    # Plot the "buy" trades against AMZN
    ax1.plot(signals.ix[signals.sigdiff == 1.0].index, 
             signals.short_mavg[signals.sigdiff == 1.0],
             '^', markersize=10, color='m')

    # Plot the "sell" trades against AMZN
    ax1.plot(signals.ix[signals.sigdiff == -1.0].index, 
             signals.short_mavg[signals.sigdiff == -1.0],
             'v', markersize=10, color='k')

    # Plot the equity curve in dollars
    ax2 = fig.add_subplot(212, ylabel='Portfolio value in $')
    returns['total'].plot(ax=ax2, lw=2.)

    # Plot the "buy" and "sell" trades against the equity curve
    ax2.plot(returns.ix[signals.sigdiff == 1.0].index, 
             returns.total[signals.sigdiff == 1.0],
             '^', markersize=10, color='m')
    ax2.plot(returns.ix[signals.sigdiff == -1.0].index, 
             returns.total[signals.sigdiff == -1.0],
             'v', markersize=10, color='k')

    # Plot the figure, seeems I don't need to use .show()
    #fig.show()
    print("final $ = ",returns['total'][-1])