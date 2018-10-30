# coding:utf-8
from requests_oauthlib import OAuth1Session
from requests.exceptions import ConnectionError, ReadTimeout, SSLError
import json, datetime, time, pytz, re, sys, traceback, pymongo
from pymongo import MongoClient
from collections import defaultdict
from pprint import pprint
import numpy as np

KEYS = {
    'consumer_key': 'U6OCU525mGe27DntCYQnIlp70',
    'consumer_secret': 'mZeQ8HdILVbnZB3lRQJht1T8gB7yKmQMnJkkUMLGoLtDHvr6Qn',
    'access_token': '875272026281332737-nrx6TzruwZs7Pge90SXaAD89bxAbRoF',
    'access_secret': 'wxSlu6NaXEhYpst7SeHL2fJLAh0a5McWzfL0zq6LLTbWg'
}

twitter = None
connect = None
db      = None
tweetdata = None
meta    = None

# TwitterAPI, MongoDBへの接続設定
def initialize():
    global twitter, connect, db, tweetdata, meta
    twitter = OAuth1Session(KEYS['consumer_key'], KEYS['consumer_secret'],
                            KEYS['access_token'], KEYS['access_secret'])
    connect = MongoClient('localhost', 27017)
    db      = connect.youtuber
    tweetdata = db.tweetdata
    meta    = db.metadata

initialize()


# tweet検索
def getTweetData(search_word):
    global twitter
    url    = 'https://api.twitter.com/1.1/search/tweets.json'
    params = {
        'q': search_word, 
        'count': '100'
    }

    req = twitter.get(url, params = params)

    if req.status_code == 200:
        # 成功
        timeline = json.loads(req.text)
        metadata = timeline['search_metadata']
        statuses = timeline['statuses']
        limit    = req.headers['x-rate-limit-remaining'] if 'x-rate-limit-remaining' in req.headers else 0
        reset    = req.headers['x-rate-limit-reset'] if 'x-rate-limit-reset' in req.headers else 0
        return {
            "result": True,
            "metadata": metadata,
            "statuses": statuses,
            "limit": limit,
            "reset_time": datetime.datetime.fromtimestamp(float(reset)),
            "reset_time_unix": reset
        }
    else:
        # 失敗
        return {
            "result": False,
            "status_code": req.status_code
        }

# 文字列を日本時間にタイムゾーンを合わせた日付型で返す
def str_to_date_jp(str_date):
    dts = datetime.datetime.strptime(str_date, '%a %b %d %H:%M:%S +0000 %Y')
    return pytz.utc.localize(dts).astimezone(pytz.timezone('Asia/Tokyo'))

# 現在時刻をUNIX時間で返す
def now_unix_time():
    return time.mktime(datetime.datetime.now().timetuple())


#お店情報取得
res = getTweetData(u'YouTuber')

if res['result'] == False:
    # 取得に失敗
    print("Error! status code: {0:d}".format(res['status_code']))

if int(res['limit']) == 0:
    # API制限に達した。データはとれてきてる。
    print("API制限に達したっぽい")
else:
    print("API LIMIT:", res['limit'])
    if len(res['statuses']) == 0:
        # 例外投げる 検索結果0件
        pass
    else:
        # mongoDBに入れる
        meta.insert({"metadata":res['metadata'], "insert_date":now_unix_time()})
        for st in res['statuses']:
            tweetdata.insert(st)
