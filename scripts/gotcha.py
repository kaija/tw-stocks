#!/usr/bin/env python2.7
import pandas as pd
import numpy as np
import os
import datetime
from datetime import timedelta
import argparse
import math
import json

def save_hits(hits, prices):
    today = datetime.date.today()
    today_str = today.strftime("%Y%m%d")
    f = open('../results/stockid-' + today_str + '.json', 'w')
    f.write(json.dumps(hits))
    f = open('../results/prices-' + today_str + '.json', 'w')
    f.write(json.dumps(prices))

def filter(data):
    del data['TO']
    del data['HP']
    del data['LP']
    del data['TC']
    WIND=5
    hit = False
    total_len = len(data.index)
    data['tv_mean'] = data['TV'].rolling(WIND).mean().shift(1)
    #return(0)
    waves = []
    waves_start_price = []
    drop_counter = 0
    idx = 0
    for i, row in data.iterrows():
        #print i
        #print "TV:" + str(row['TV']) + " TV mean:" + str(row['tv_mean'])
        #print "CR:" + str(row['CR'])
        if (row['TV'] > 2 * row['tv_mean'] and row['CR'] > 5) or row['OR'] == 10:
            #wave first day
            waves_start_price.append(row['CP'])
            waves.append(i)
            continue
        if len(waves_start_price) > 0 and waves_start_price[-1] * 0.95 > row['CP']:
            drop_counter = drop_counter  + 1
    #print waves
    #print waves_start_price
    #print waves[-1]
    if len(waves) > 0 and drop_counter == 0:
        
        hit = True
    return hit, waves_start_price
    #print data

def prefilter(sid):
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    weekago = today - timedelta(days=7)
    weekago_str = weekago.strftime("%Y-%m-%d")
    df = pd.DataFrame.from_csv('../tw-stock-raw/by-stock/' + sid + ".csv")
    ndf = df.loc[weekago_str :  today_str]
    if ndf['OP'].count() > 0:
        return True
    return False
    
    
def main(days=30, sid=None, date_from=None):
    hits = []
    prices = []
    for root, dirs, files in os.walk("../tw-stock-raw/by-stock/"):
        path = root.split(os.sep)
        for f in files:
            stockid = f.split('.')[0]
            #filter 4 digit stock
            if len(f) != 8:
                continue
            #filter out of market
            if not prefilter(sid=stockid):
                continue
            #print "processing..." + stockid
            df = preprocess(days=days, sid=stockid, date_from=date_from)
            res, prices =  filter(df)
            if res:
                df = preprocess(days=90, sid=stockid, date_from=date_from)
                wave_max = max(prices)
                prev_max = df.head(60)['CP'].max()
                print wave_max
                print prev_max
                if prev_max > wave_max:
                    continue
                print "https://tw.stock.yahoo.com/q/ta?s="+stockid
                hits.append(stockid)
                prices.append(df.tail(1)['CP'].values[0])
            #else:
            #    print "BYE"
    print "======================"
    print hits
    print "======================"
    save_hits(hits, prices)
    return 0

def preprocess(days=30, sid=None, date_from=None):

    res = pd.DataFrame(columns=('id', 'rate'))
    try:
        if date_from == "today":
            df = pd.DataFrame.from_csv('../tw-stock-raw/by-stock/' + sid + ".csv")
        else:
            dfo = pd.DataFrame.from_csv('../tw-stock-raw/by-stock/' + sid + ".csv")
            fdate = datetime.datetime.strptime(date_from, "%Y%m%d")
            df = dfo["20100101":fdate.strftime("%Y-%m-%d")]
            #df = dfo[]
        subset = df.tail(days + 1)
        #print subset
        last_cp = 0
        #initial some rate filed
        df_r = subset[0:0]
        df_r['YP'] = pd.Series(np.random.randn(0), index=df_r.index)
        df_f = subset[0:0]
        df_f['HR'] = pd.Series(np.random.randn(0), index=df_f.index)
        df_f['LR'] = pd.Series(np.random.randn(0), index=df_f.index)
        df_f['OR'] = pd.Series(np.random.randn(0), index=df_f.index)
        df_f['CR'] = pd.Series(np.random.randn(0), index=df_f.index)
        #copy the yesterday clode price to next day  (yesterday price)YP
        for idx,row in subset.iterrows():
            row['TV'] = int(row['TV'] / 1000)
            row['YP'] = last_cp
            df_r.loc[idx] = row
            last_cp = row['CP']
        #calculate rate field from YP
        for idx,row in df_r.iterrows():
            row['HR'] = (row['HP'] - row['YP']) * 100/row['YP']
            row['LR'] = (row['LP'] - row['YP']) * 100/row['YP']
            row['OR'] = (row['OP'] - row['YP']) * 100/row['YP']
            row['CR'] = (row['CP'] - row['YP']) * 100/row['YP']
            df_f.loc[idx] = row
        #remove the first row
        final = df_f.tail(days)
        #
        #final['TV'] = final.apply(lambda x: x/1000 )
        final['HR'] = final['HR'].apply(lambda x: float('%.2f' % x ))
        final['LR'] = final['LR'].apply(lambda x: float('%.2f' % x ))
        final['OR'] = final['OR'].apply(lambda x: float('%.2f' % x ))
        final['CR'] = final['CR'].apply(lambda x: float('%.2f' % x ))
        #final['HR'] = final.apply(lambda x: '%.2f' % x)
        #print final
        return final
        #print filter1(final)
        #print "https://tw.stock.yahoo.com/q/ta?s=" + sid
        #print subset 
        #print df.tail(days)
    except Exception as e:
        print e
        a = 1


    #print res.sort(['rate'])
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("-i", "--stockid", type=str, default="",
                    help="The stock id")
    parser.add_argument("-d", "--days", type=int, default=50,
                    help="The n days")
    parser.add_argument("-f", "--fromdate", type=str, default="today",
                    help="The analyzed date string")

    args = parser.parse_args()
    main(days=args.days, sid = args.stockid, date_from=args.fromdate)
