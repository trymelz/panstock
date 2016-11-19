# -*- coding: utf-8 -*-
"""
#http://pandas-datareader.readthedocs.io/en/latest/remote_data.html
#pip install pandas-datareader  (installed 0.2.1)
Created on Fri Nov 18 19:22:19 2016

@author: Linfa
"""

import pandas as pd
#import pandas.io.data as web
import pandas_datareader.data as web
import datetime


import requests_cache
expire_after = datetime.timedelta(days=3)
session = requests_cache.CachedSession(cache_name='cache', backend='sqlite', expire_after=expire_after)



#stock price from yahoo
sta=datetime.datetime(2016,10,1)
end=datetime.date.today()
io=web.DataReader("IO","yahoo",sta,end)

#print(io.info())
print(io)
#io['Close'].plot(figsize=(12,6),grid=True)

#print(pd.isnull(io).head())
print(io.isnull().values.any())

iochg=io.Close.diff()
io['Chg']=iochg
#iochgpct=iochg/io.Close*100
#io['Chgpct']=iochgpct

iochg=io.Volume.diff()
io['VChg']=iochg

#iosort=io.sort_values(by='Chg',ascending=False)
#format = lambda x: '%.2f' % x
#iosort = iosort.applymap(format)

print(io)

'''
#stock price from google
sta=datetime.datetime(2016,1,1)
end=datetime.date.today()
appleg=web.DataReader("AAPL","google",sta,end)

print(appleg.info())
print(appleg.tail())
#appleg['Close'].plot(figsize=(12,6),grid=False)

q = web.get_quote_yahoo(['APPL','GOOG','IO','DBO'])
print(q)

#qq = web.YahooDailyReader()
#print(qq)
'''