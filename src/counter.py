from sklearn.feature_extraction.text import CountVectorizer
from pymongo import Connection
import numpy as np
from collections import defaultdict
import sys, datetime

connect = Connection('localhost', 27017)
db = connect.youtuber
tweetdata = db.tweetdata


def str_to_date_jp_utc(str_date):
    if str_date is not None:
        return datetime.datetime.strptime(str_date,'%Y-%m-%d %H:%M:%S') - datetime.timedelta(hours=9)
    else:
        return None
