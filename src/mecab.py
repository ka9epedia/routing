# coding:utf-8
import MeCab as mc

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
    res = mecab_analysis(unicodedata.normalize('NFKC', d['text'])) # 半角カナを全角カナに

    # 品詞毎にフィールド分けして入れ込んでいく
    for k in res.keys():
        if k == u'形容詞': # adjective  
            adjective_list = []    
            for w in res[k]:                adjective_list.append(w)
            tweetdata.update({'_id' : d['_id']},{'$push': {'adjective':{'$each':adjective_list}}})
        elif k == u'動詞': # verb
            verb_list = []
            for w in res[k]:
                verb_list.append(w)
            tweetdata.update({'_id' : d['_id']},{'$push': {'verb':{'$each':verb_list}}})
        elif k == u'名詞': # noun
            noun_list = []
            for w in res[k]:                noun_list.append(w)
            tweetdata.update({'_id' : d['_id']},{'$push': {'noun':{'$each':noun_list}}})
        elif k == u'副詞': # adverb
            adverb_list = []
            for w in res[k]:
                adverb_list.append(w)
            tweetdata.update({'_id' : d['_id']},{'$push': {'adverb':{'$each':adverb_list}}})
    # 形態素解析済みのツイートにMecabedフラグの追加
    tweetdata.update({'_id' : d['_id']},{'$set': {'mecabed':True}})
