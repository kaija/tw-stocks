import datetime
import httplib
import urllib
import os.path
import csv
import time
from datetime import timedelta
import pandas as pd
import numpy as np

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def totimestamp(dt, epoch=datetime.date(1970,1,1)):
    td = dt - epoch
    # return td.total_seconds()
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6 

class stockImport(object):
    def __init__(self
                 ):
        print ('setup stock importer')
    def saveDate(self, date=None):
        date_str = date.strftime("%m/%d/%Y")
        print('{} finished'.format(date_str))
        f = open('../tw-stock-raw/last_update', 'w')
        f.write(date_str)

    def loadDate(self):
        try:
            f = open('../tw-stock-raw/last_update', 'r')
            date_str = f.readline()
            #default set to 4 PM
            return datetime.datetime.strptime(date_str + " 16:00:00", "%m/%d/%Y %H:%M:%S")
        except IOError:
            return datetime.datetime.strptime("1/1/2010 16:00:00", "%m/%d/%Y %H:%M:%S")

    def downloadData(self):
        start_day = datetime.date(2004, 2, 11);
        today = datetime.date.today()
        one_day = timedelta(days=1)
        y, m, d, h, min, sec, wd, yd, i = datetime.datetime.now().timetuple()
        end_time = today
        if h > 16:
          end_time = today + one_day
        print "start download missing data"
        print "checking from " + start_day.strftime("%Y-%m-%d") + " to " + today.strftime("%Y-%m-%d")
        print "checking end time " + end_time.strftime("%Y-%m-%d")
        download_date = start_day
        while download_date < end_time:
            file_name = "../tw-stock-raw/raw/" + download_date.strftime("%Y%m%d") + ".csv"
            if os.path.isfile(file_name):
                download_date += one_day
                continue
            httpreq = httplib.HTTPConnection('www.twse.com.tw')
            #http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=20170526&type=ALL
            #headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            print 
            date_str = str(download_date.year - 1911 ) + download_date.strftime("/%m/%d")
            form = urllib.urlencode({'download': 'csv', 'qdate': date_str, 'selectType': 'ALLBUT0999'})
            #httpreq.request("POST", "/ch/trading/exchange/MI_INDEX/MI_INDEX.php", form, headers);
            full_url = "exchangeReport/MI_INDEX?response=csv&date=" + download_date.strftime("%Y%m%d") + "&type=ALL"
            print full_url
            httpreq.request("GET", "http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=" + download_date.strftime("%Y%m%d") + "&type=ALL");
            httpres =  httpreq.getresponse()
            stock_csv =  httpres.read()
            print "downloading " + file_name
            f = open(file_name, "w")
            f.write(stock_csv)
            download_date += one_day

    def insertToStock(self, stockid, row, date):
        try:
            date_str = date.strftime("%Y-%m-%d")
            df = pd.DataFrame.from_csv('../tw-stock-raw/by-stock/' + stockid + '.csv')
            #check if there is a key
            df.loc[date_str].count()
            #key already exist. skip it   
        except KeyError:
            #no such key. insert it
            df = pd.concat([df, row])
            df.to_csv('../tw-stock-raw/by-stock/' + stockid + '.csv')
            #print df
        except IOError:
            print('stock id: {} not exist'.format(stockid))
            row.to_csv('../tw-stock-raw/by-stock/' + stockid + '.csv')

    def prepcsv(self, csv):
        ret = []
        for i in csv:
            tmp = i
            tmp = tmp.replace(',', '')
            tmp = tmp.replace('\'', '')
            tmp = tmp.replace('\"', '')
            tmp = tmp.replace('=', '')
            ret.append(tmp)
        return ret

    def convertCSV(self, file_path=None, date=None):
        print('convert csv {}'.format(file_path))
        with open(file_path, 'rb') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in spamreader:
                if len(row) < 16:
                    #abnormal some column missing?
                    continue
                #if len(row) == 17:
                    #abnormal should not more than 16 column
                    #print(row)
                if len(row) == 17:
                    stockid=row[0].replace('=', '')
                    stockid=stockid.replace('"', '')
                    stockid=stockid.strip()
                    if stockid.startswith('('):
                        continue
                    checkrow = row[11].replace(',', '')
                    checkrow = checkrow.replace('"', '')
                    checkrow = checkrow.replace('=', '')
                    if not checkrow[0].isdigit():
                        #skip column title
                        continue
                    row = self.prepcsv(row)

                    TV=int(row[2])
                    TC=int(row[3])
                    TO=int(row[4])
                    RD=row[9]
                    if RD == '+':
                        DF=float(row[10])
                        RD=1
                    elif RD == '-':
                        DF=0-float(row[10])
                        RD=-1
                    else:
                        DF=0
                        RD=0

                    PE=float(row[15])
                    try:
                        OP=float(row[5])
                        CP=float(row[8])
                        HP=float(row[6])
                        LP=float(row[7])
                    except ValueError:
                        OP=None
                        CP=None
                        HP=None
                        LP=None
                    #print('OP:{} CP:{} HP:{} LP:{} DF:{} RD:{} TV:{} TC:{} TO:{}\n'.format( OP, CP, HP, LP, DF, RD, TV, TC, TO))
                    cols = ['OP', 'CP', 'HP', 'LP', 'DF', 'RD', 'TV', 'TC', 'TO']
                    date_index = pd.date_range(date.strftime("%m/%d/%Y"), periods=1)
                    df1 = pd.DataFrame([[OP, CP, HP, LP, DF, RD, TV, TC, TO]], columns=cols)
                    df1['date'] = date_index
                    df1 = df1.set_index(['date'])
                    #print stockid
                    #print df1
                    self.insertToStock(stockid, df1, date)
        self.saveDate(date)

    def getExpectCP(self, df, date):
        today = datetime.date.today()
        one_day = timedelta(days=1)
        if date > today:
            #print "over today"
            #print date.strftime("%Y-%m-%d")
            return None
        try:
            date_str = date.strftime("%Y-%m-%d")
            return df.loc[date_str, 'CP']
        except KeyError as e:
            return self.getExpectCP(df, date + one_day)
        

    def loadTrainDataById(self, stock_id, start_date, days, expect):
        one_day = timedelta(days=1)
        stop_date = start_date + one_day * days
        expect_date = start_date + one_day * (days + expect)
        today = datetime.date.today()
        if stop_date > today:
            return None
        try:
            start_date_str = start_date.strftime("%Y-%m-%d")
            stop_date_str = stop_date.strftime("%Y-%m-%d")
            expect_date_str = expect_date.strftime("%Y-%m-%d")
            df = pd.DataFrame.from_csv('../tw-stock-raw/by-stock/' + stock_id + '.csv')
            print "from:" + start_date_str + " to:" + stop_date_str
            dft = df.loc[start_date_str:stop_date_str]
            #print dft.as_matrix()
            #print dft.reset_index().values
            dfcp = df.loc[start_date_str:stop_date_str, 'CP']
            #print df.loc[start_date_str:expect_date_str, 'CP']
            expcp = self.getExpectCP(df, expect_date)
            if expcp == None:
                return
            #print dfcp
            print 'max during train:' + str(dfcp.max())
            print str(expect) + ' days ' + expect_date_str + ' close price' + str(expcp)
            if expcp > dfcp.max():
                print 'up'
            else:
                print 'down'
                
        except KeyError as e:
            print "out of range , try next day"
        except IOError:
            print "no such stock id"

    def loadTrainDataByIdFixedRow(self, stock_id, start_date, days, expect):
        one_day = timedelta(days=1)
        stop_date = start_date + one_day * days
        expect_date = start_date + one_day * (days + expect)
        today = datetime.date.today()
        res = 0
        if stop_date > today:
            return None, None
        try:
            start_date_str = start_date.strftime("%Y-%m-%d")
            stop_date_str = stop_date.strftime("%Y-%m-%d")
            expect_date_str = expect_date.strftime("%Y-%m-%d")
            today_date_str = datetime.date.today()
            #read data frame from stock file
            df = pd.DataFrame.from_csv('../tw-stock-raw/by-stock/' + stock_id + '.csv')
            #print "from:" + start_date_str + " to:" + stop_date_str
            #count total record from start to now, check if data record is enough
            dft = df.loc[start_date_str:today_date_str]
            if  dft['CP'].count() < days + expect:
                print 'data is not enough for train or validate'
                return None, None
            #retrive enough data record   days + expect days
            dft = dft[:days + expect]
            #get the expect date data record
            expcpdf = dft.tail(1)
            #print dft
            #print dft[:days]
            #print dft.as_matrix()
            #print dft.reset_index().values
            #first n days data record for training
            dfcp = dft[:days]
            #convert to matrix
            data = dfcp.as_matrix()
            #get expected close price
            expcp = expcpdf['CP'].max()
            #get max close price in training data
            tmax = dft[:days]['CP'].max()
            #print 'last price:' + str(expcpdf['CP'])
            #print 'max during train:' + str(tmax)
            #print str(expect) + ' days close price:' + str(expcp)
            if expcp > tmax:
                res = 1
                #print 'up'
            else:
                res = 0
                #print 'down'
            return data, res
                
        except KeyError as e:
            print "out of range , try next day"
        except IOError:
            print "no such stock id"

    def loadAllTrainDataByStock(self, stock_id, start_date, days, expect):
        today = datetime.date.today()
        one_day = timedelta(days=1)
        da = start_date
        X = []
        Y = []
        while da < today:
            da = da + one_day
            d, r = self.loadTrainDataByIdFixedRow(stock_id, da, days, expect)
            if d is None:
                break
            x = sum(d.tolist(), [])
            X.append(x)
            Y.append(r)
            #print("---------------------------------------------")
            #print x
            #print("---------------------------------------------")
            #print r
        return X,Y
