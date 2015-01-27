#! /usr/bin/env python
# -*- coding:utf-8 -*-

import json, urllib2, urllib
import account

url = "http://jlp.yahooapis.jp/KeyphraseService/V1/extract"

def extract_keyphrase(sentence):
    try:
        print type(sentence)
        query = url + "?appid=" + account.y_app_id + "&output=json&sentence=" + urllib.quote_plus(sentence)
        print "GET: " + query
         
        c = urllib2.urlopen(query)
        json_str = c.read()
        res = json.loads(json_str)
        print "RESPONSE: " + json_str
        
        max_score = 0;
        ret = ""
        for keyword, score in sorted(res.items(), key=lambda x:x[1], reverse=True):
            print score, keyword.encode('utf-8')
            if max_score < score:
                max_score = score
                ret = keyword.encode("utf-8")
                
        print "キーワード" + ret
        return ret
    except:
        return ""

# print extract_keyphrase("あ〜こころがぴょんぴょんするんじゃ〜")
