# coding: utf-8
from requests_oauthlib import OAuth1Session
from requests.exceptions import ConnectionError, ReadTimeout, SSLError
import json, datetime, time, pytz, re, sys, traceback, pymongo
from pymongo import MongoClient
from collections import defaultdict
from pprint import pprint
import numpy as np
import unicodedata
import MeCab as mc

import codecs
import nltk

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

freqwords = {}
freqpair = {}
max = 0

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

def mecab_analysis(sentence):
    t = mc.Tagger('-Ochasen -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd/')
    sentence = sentence.replace('\n', ' ')
    text = sentence.encode('utf-8') 
    node = t.parseToNode(text) 
    result_dict = defaultdict(list)
    for i in range(140):  # ツイートなのでMAX140文字
        if node.surface != "":  # ヘッダとフッタを除外
            word_type = node.feature.split(",")[0]
            if word_type in ["名詞", "形容詞", "動詞"]:
                plain_word = node.feature.split(",")[6]
                if plain_word !="*":
                    result_dict[word_type.decode('utf-8')].append(plain_word.decode('utf-8'))
        node = node.next
        if node is None:
            break
    return result_dict

#全てのTweetデータに対して形態素に分けていく処理
for d in tweetdata.find({},{'_id':1, 'id':1, 'text':1,'noun':1,'verb':1,'adjective':1,'adverb':1}):
    freqwords = {}
    freqpair = {}
    max = 0

    res = mecab_analysis(unicodedata.normalize('NFKC', d['text'])) # 半角カナを全角カナに

    # 品詞毎にフィールド分けして入れ込んでいく
    for k in res.keys():
        if k == u'形容詞': # adjective  
            adjective_list = []    
            for w in res[k]:
                adjective_list.append(w)
            tweetdata.update({'_id' : d['_id']},{'$push': {'adjective':{'$each':adjective_list}}})
        elif k == u'動詞': # verb
            verb_list = []
            for w in res[k]:
                verb_list.append(w)
            tweetdata.update({'_id' : d['_id']},{'$push': {'verb':{'$each':verb_list}}})
        elif k == u'名詞': # noun
            noun_list = []
            for w in res[k]:
                noun_list.append(w)
            tweetdata.update({'_id' : d['_id']},{'$push': {'noun':{'$each':noun_list}}})
        elif k == u'副詞': # adverb
            adverb_list = []
            for w in res[k]:
                adverb_list.append(w)
            tweetdata.update({'_id' : d['_id']},{'$push': {'adverb':{'$each':adverb_list}}})
            print k,w

#def collocations_and_freq_words(text, freq=25):
	#tokens = mecab_tokenizer.tokenize(text)
	#corpus = nltk.Text(tokens)

        freq = 1
        tokens = w
        corpus = nltk.Text(w)

	print(u"-----最頻語（頻度%d回以上）-----" % freq)

	fdist1 = nltk.FreqDist(tokens)
	saihin1 = fdist1.keys()
        print "test",fdist1,saihin1
	for voc in saihin1:
	    if fdist1[voc] >= freq:
	        print "%s\t%s" % (voc, fdist1[voc])

	print(u"")
	print(u"-----共起関係（共起頻度%d回以上）-----" % freq)

	bigrams = nltk.bigrams(corpus)
	cfd = nltk.ConditionalFreqDist(bigrams)
	kyouki = cfd.keys()
	for voc in kyouki:
	    for (key, value) in list(cfd[voc].viewitems()):
	        if value >= freq:
	            print("%s\t%s\t%s" % (voc, key, value)) 
