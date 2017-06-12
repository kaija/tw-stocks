#!/usr/bin/env python2.7
import datetime
import httplib
import urllib
import os
from datetime import timedelta
import csv
import pandas as pd
import numpy as np
import sys
#now = datetime.datetime.now();
#today = now.strftime('%Y-%m-%d')
#print today
def saveDate(date=None):
    date_str = date.strftime("%m/%d/%Y")
    print('{} finished'.format(date_str))
    f = open('../tw-emerging-raw/last_update', 'w')
    f.write(date_str)

def loadDate():
    try:
        f = open('../tw-emerging-raw/last_update', 'r')
        date_str = f.readline()
        #default set to 4 PM
        return datetime.datetime.strptime(date_str + " 16:00:00", "%m/%d/%Y %H:%M:%S")
    except IOError:
        return datetime.datetime.strptime("7/1/2007 16:00:00", "%m/%d/%Y %H:%M:%S")

def convert():
    last_update = loadDate()

    #start_date = datetime.date(2016, 12, 20)
    #today = datetime.date(2016, 12, 30)
    #start_date = datetime.date(2009, 9, 25)
    #start_date = datetime.date(2004, 2, 11)

    #from last update

    start_date = last_update.date()
    today = datetime.date.today()
    one_day = timedelta(days=1)
    da = start_date
    y, m, d, h, min, sec, wd, yd, i = datetime.datetime.now().timetuple()
    end_time = today
    if h > 16:
        end_time = today + one_day
    print "from : " + start_date.strftime("%Y%m%d")
    #convert CSV file
    if True:
        while da < end_time:
            filePath = '../tw-emerging-raw/raw/' + da.strftime("%Y%m%d") + '.csv'
            convertCSV(filePath, da)
            da = da + one_day

def insertToEmg(stockid, row, date):
    try:
        date_str = date.strftime("%Y-%m-%d")
        df = pd.DataFrame.from_csv('../tw-emerging-raw/by-emerging/' + stockid + '.csv')
        #check if there is a key
        df.loc[date_str].count()
        #key already exist. skip it
    except KeyError:
        #no such key. insert it
        df = pd.concat([df, row])
        df.to_csv('../tw-emerging-raw/by-emerging/' + stockid + '.csv')
        #print df
    except IOError:
        print('stock id: {} not exist'.format(stockid))
        row.to_csv('../tw-emerging-raw/by-emerging/' + stockid + '.csv')


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def convfloat(value):
    try:
        return float(value)
    except ValueError:
        return -1

def download():
    today = datetime.date.today()
    one_day = timedelta(days=1);
    y, m, d, h, min, sec, wd, yd, i = datetime.datetime.now().timetuple()
    end_time = today
    if h > 16:
      end_time = today + one_day
    start_day = datetime.date(2007, 7, 1);

    print "Download from " + start_day.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d")

    dl_date = start_day



    while dl_date < end_time:
        file_name = "../tw-emerging-raw/raw/" + dl_date.strftime("%Y%m%d") + ".csv"
        if os.path.isfile(file_name):
            dl_date += one_day
            continue
        httpreq = httplib.HTTPConnection('www.tpex.org.tw')
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        date_str = str(dl_date.year - 1911 ) + dl_date.strftime("/%m/%d")
        #http://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_download.php?l=zh-tw&d=
        url = "/web/stock/aftertrading/daily_close_quotes/stk_quote_download.php?l=zh-tw&d=" + date_str+ "&s=0,asc,0"
        httpreq.request("GET", url, "", headers);
        httpres =  httpreq.getresponse()
        stock_csv =  httpres.read()
        file_name = "../tw-emerging-raw/raw/" + dl_date.strftime("%Y%m%d") + ".csv"
        print "downloading " + file_name
        f = open(file_name, "w")
        f.write(stock_csv)
        dl_date += one_day


    print "Download Finish!"


def convertCSV(file_path=None, date=None):
    print('convert csv {}'.format(file_path))
    with open(file_path, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:

            if len(row) < 17:
                #abnormal some column missing?
                continue
            if len(row) == 17:
                if not row[2][0].isdigit():
                    #skip column title
                    continue

                stockid=row[0].replace('=', '')
                stockid=stockid.replace('"', '')
                stockid=stockid.strip()
                TV=int(row[8].replace(',',''))
                TC=int(row[10].replace(',',''))
                TO=int(row[9].replace(',',''))
                RD=row[3]
                if RD[0] == '+' and RD[1].isdigit():
                    DF=float(row[3].replace('+',''))
                    RD=1
                elif RD[0] == '-' and RD[1].isdigit():
                    DF=0-float(row[3].replace('-',''))
                    RD=-1
                else:
                    DF=0
                    RD=0

                PE=float(row[15])
                try:
                    OP=float(row[4])
                    CP=float(row[2])
                    HP=float(row[5])
                    LP=float(row[6])
                except ValueError:
                    OP=None
                    CP=None
                    HP=None
                    LP=None
                #print(stockid)
                #print('OP:{}\nCP:{}\nHP:{}\nLP:{}\nDF:{}\nRD:{}\nTV:{}\nTC:{}\nTO:{}\n'.format( OP, CP, HP, LP, DF, RD, TV, TC, TO))
                cols = ['OP', 'CP', 'HP', 'LP', 'DF', 'RD', 'TV', 'TC', 'TO']
                date_index = pd.date_range(date.strftime("%m/%d/%Y"), periods=1)
                df1 = pd.DataFrame([[OP, CP, HP, LP, DF, RD, TV, TC, TO]], columns=cols)
                df1['date'] = date_index
                df1 = df1.set_index(['date'])
                insertToEmg(stockid, df1, date)
        saveDate(date)
#                self.insertToStock(stockid, df1, date)

if __name__ == "__main__":
    download()
    #convertCSV(file_path='emerging/20170426.csv')
    convert()
