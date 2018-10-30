# coding:utf-8
from requests_oauthlib import OAuth1Session
from requests.exceptions import ConnectionError, ReadTimeout, SSLError
import json, datetime, time, pytz, re, sys,traceback, pymongo
#from pymongo import Connection     # Connection classは廃止されたのでMongoClientに変更 
from pymongo import MongoClient
from collections import defaultdict
import numpy as np

KEYS = { # 自分のアカウントで入手したキーを下記に記載
        'consumer_key':'U6OCU525mGe27DntCYQnIlp70',
        'consumer_secret':'mZeQ8HdILVbnZB3lRQJht1T8gB7yKmQMnJkkUMLGoLtDHvr6Qn',
        'access_token':'875272026281332737-nrx6TzruwZs7Pge90SXaAD89bxAbRoF',
        'access_secret':'wxSlu6NaXEhYpst7SeHL2fJLAh0a5McWzfL0zq6LLTbWg'
       }

twitter = None
connect = None
db      = None
tweetdata = None
meta    = None

def initialize(): # twitter接続情報や、mongoDBへの接続処理等initial処理実行
    global twitter, twitter, connect, db, tweetdata, meta
    twitter = OAuth1Session(KEYS['consumer_key'],KEYS['consumer_secret'],
                            KEYS['access_token'],KEYS['access_secret'])
#   connect = Connection('localhost', 27017)     # Connection classは廃止されたのでMongoClientに変更 
    connect = MongoClient('localhost', 27017) #(アドレス、ポート番号(MongoDBのデフォルトのポート番号は27017))
    db = connect.restaurant
    tweetdata = db.tweetdata
    meta = db.metadata

initialize()

# 検索ワードを指定して100件のTweetデータをTwitter REST APIsから取得する
def getTweetData(search_word, max_id, since_id):
    global twitter
    url = 'https://api.twitter.com/1.1/search/tweets.json' #???
    params = {'q': search_word,
              'count':'100',
    }
    # max_idの指定があれば設定する
    if max_id != -1:
        params['max_id'] = max_id
    # since_idの指定があれば設定する
    if since_id != -1:
        params['since_id'] = since_id

    req = twitter.get(url, params = params)   # Tweetデータの取得

    # 取得したデータの分解
    if req.status_code == 200: # 成功した場合
        timeline = json.loads(req.text)
        metadata = timeline['search_metadata']
        statuses = timeline['statuses']
        limit = req.headers['x-rate-limit-remaining'] if 'x-rate-limit-remaining' in req.headers else 0
        reset = req.headers['x-rate-limit-reset'] if 'x-rate-limit-reset' in req.headers else 0              
        return {"result":True, "metadata":metadata, "statuses":statuses, "limit":limit, "reset_time":datetime.datetime.fromtimestamp(float(reset)), "reset_time_unix":reset}
    else: # 失敗した場合
        print ("Error: %d" % req.status_code)
        return{"result":False, "status_code":req.status_code}

# 文字列を日本時間2タイムゾーンを合わせた日付型で返す
def str_to_date_jp(str_date):
    dts = datetime.datetime.strptime(str_date,'%a %b %d %H:%M:%S +0000 %Y')
    return pytz.utc.localize(dts).astimezone(pytz.timezone('Asia/Tokyo'))

# 現在時刻をUNIX Timeで返す
def now_unix_time():
    return time.mktime(datetime.datetime.now().timetuple())


#-------------繰り返しTweetデータを取得する-------------#
sid=-1
mid = -1 
count = 0

res = None
while(True):    
    try:
        count = count + 1
        sys.stdout.write("%d, "% count)
        res = getTweetData(u'岡山', max_id=mid, since_id=sid) #複数の検索ワードを必要とする場合35行目のsearch_wordを増やす必要がある？
        if res['result']==False:
            # 失敗したら終了する
            print "status_code", res['status_code']
            break

        if int(res['limit']) == 0:    # 回数制限に達したので休憩
            # 日付型の列'created_datetime'を付加する
            print "Adding created_at field."
            for d in tweetdata.find({'created_datetime':{ "$exists": False }},{'_id':1, 'created_at':1}):
                #print str_to_date_jp(d['created_at'])
                tweetdata.update({'_id' : d['_id']}, 
                     {'$set' : {'created_datetime' : str_to_date_jp(d['created_at'])}})
            #remove_duplicates()

            # 待ち時間の計算. リミット＋５秒後に再開する
            diff_sec = int(res['reset_time_unix']) - now_unix_time()
            print "sleep %d sec." % (diff_sec+5)
            if diff_sec > 0:
                time.sleep(diff_sec + 5)
        else:
            # metadata処理
            if len(res['statuses'])==0:
                sys.stdout.write("statuses is none. ")
            elif 'next_results' in res['metadata']:
                # 結果をmongoDBに格納する
                meta.insert({"metadata":res['metadata'], "insert_date": now_unix_time()})
                for s in res['statuses']:
                    tweetdata.insert(s)
                next_url = res['metadata']['next_results']
                pattern = r".*max_id=([0-9]*)\&.*"
                ite = re.finditer(pattern, next_url)
                for i in ite:
                    mid = i.group(1)
                    break
            else:
                sys.stdout.write("next is none. finished.")
                break
    except SSLError as (errno, request):
        print "SSLError({0}): {1}".format(errno, strerror)
        print "waiting 5mins"
        time.sleep(5*60)
    except ConnectionError as (errno, request):
        print "ConnectionError({0}): {1}".format(errno, strerror)
        print "waiting 5mins"
        time.sleep(5*60)
    except ReadTimeout as (errno, request):
        print "ReadTimeout({0}): {1}".format(errno, strerror)
        print "waiting 5mins"
        time.sleep(5*60)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        traceback.format_exc(sys.exc_info()[2])
        raise
    finally:
        info = sys.exc_info()
