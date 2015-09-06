#! /usr/bin/env python
# -*- coding:utf-8 -*-

import sys, random, threading, re, time, os
import tweepy, twitter, MeCab
import account, yahoo_keyphrase
import daemon.runner
from collections import defaultdict

twitter_api =twitter.Api(account.consumerKey, account.consumerSecret, account.accessToken, account.accessTokenSecret, cache=None)
tweepy_auth = tweepy.OAuthHandler(account.consumerKey, account.consumerSecret)
tweepy_auth.set_access_token(account.accessToken, account.accessTokenSecret)
tweepy_api = tweepy.API(tweepy_auth)

dict = [] # 形態素解析結果を格納する辞書
nouns = [] # 名詞のみを突っ込む
karas = [] # 理由的な文章を突っ込む
places = [] # 場所的なものを突っ込む
times = [] # 場所情報的なものを突っ込む
keyphrase_count = defaultdict(int) 
fixed_tweet_interval = 60 # 平常時ツイートの間隔（分）

# ここが最初に呼ばれる
class ZolfBotDaemon:
    def __init__(self):
        self.pidfile_timeout = 10
        self.stdin_path = "/dev/null"
        self.stdout_path = "out.txt"
        self.stderr_path = "err.txt"
        self.directory = os.path.expanduser("~/zolf_bot/")
        self.pidfile_path = os.path.join(self.directory, "pid.txt")
    
    def run(self):
        thread = threading.Thread(target=fixedTweet)
        thread.start()
        userStream()


# UserStreamに接続
def userStream():
    print "UserStreamに接続します"
    stream = tweepy.Stream(tweepy_auth, UserStreamListener(), secure=True)
    stream.timeout = None
    stream.userstream()


class UserStreamListener(tweepy.streaming.StreamListener):
    # print "UserStreamListener"
    # 初期化
    def __init__(self):
        super(UserStreamListener,self).__init__()

    # tweetを取得した時
    def on_status(self, status):
        # 自分のツイートは無視する
        if status.author.screen_name == "zolf_bot":
            return
        
        # トレンドワード的なもの抽出
        encoded_text = status.text.encode("utf-8")
        keyphrase = yahoo_keyphrase.extract_keyphrase(encoded_text)
        if len(keyphrase) > 0:
            keyphrase_count[keyphrase] += 1
            if keyphrase_count[keyphrase] >= 3:
                a = ["か", "", "！", "なう"]
                text = keyphrase + a[random.randint(0,len(a)-1)]
                try:
                    tweepy_api.update_status(status=text)
                except:
                    keyphrase_count[keyphrase] = 0
                keyphrase_count[keyphrase] = 0

        print "@" + status.author.screen_name + ": " + status.text
        if status.in_reply_to_screen_name == "zolf_bot":
            print "リプライを受け取りました"
            print "テキストのエンコードに成功"
            
            # 何故？に対して〜からという文章で答える
            if len(karas) > 0 and (encoded_text.find("なぜ") >= 0 or encoded_text.find("何故") >= 0 or encoded_text.find("なんで") >= 0 or encoded_text.find("何で") >= 0):
                print "理由の文章と判定"
                text = karas[random.randint(0, len(karas)-1)]
                text = "@" + status.author.screen_name.encode("utf-8") + " " + text
                tweepy_api.update_status(status=text, in_reply_to_status_id=status.id)

            # 「どこ」に対して場所で答える
            elif len(places) > 0 and (encoded_text.find("どこ") >= 0 or encoded_text.find("何処") >= 0):
                print "場所の文章と判定"
                text = places[random.randint(0, len(places)-1)]
                text = "@" + status.author.screen_name.encode("utf-8") + " " + text
                tweepy_api.update_status(status=text, in_reply_to_status_id=status.id)

            # 時間を答える
            elif len(times) > 0 and (encoded_text.find("いつ") >= 0 or encoded_text.find("何時") >= 0):
                text = times[random.randint(0, len(times)-1)]
                text = "@" + status.author.screen_name.encode("utf-8") + " " + text
                tweepy_api.update_status(status=text, in_reply_to_status_id=status.id)

            # 何？に対して名詞で答える
            elif len(nouns) > 0 and (encoded_text.find("なに") >= 0 or encoded_text.find("何") >= 0):
                print "何？の文章と判定"
                text = nouns[random.randint(0, len(nouns)-1)]
                text = "@" + status.author.screen_name.encode("utf-8") + " " + text
                tweepy_api.update_status(status=text, in_reply_to_status_id=status.id)

            else:
                # @部分を取り除く
                ascii_text = status.text
                ascii_text = ascii_text.replace("@zolf_bot", "")
                encoded_text = ascii_text.encode("utf-8")
                
                # リプライのテキストも学習させる
                learn(encoded_text)
                
                # リプライのテキストからキーフレーズを抽出させる
                tweet_text = "@" + status.author.screen_name.encode("utf-8") + " " + marcovReply(encoded_text)
                tweepy_api.update_status(status=tweet_text, in_reply_to_status_id=status.id)

        # おはようツイート
        elif encoded_text.find("おはよ") >= 0 or encoded_text.find("起きた") >= 0 or encoded_text.find("おきた") >= 0:
            text = "@" + status.author.screen_name.encode("utf-8") + " おはよう。"
            tweepy_api.update_status(status=text, in_reply_to_status_id=status.id)

        # おやすみツイート
        elif encoded_text.find("おやすみ") >= 0 or encoded_text.find("お休み") >= 0 or encoded_text.find("寝る") >= 0 or encoded_text.find("ねる") >= 0:
            text = "@" + status.author.screen_name.encode("utf-8") + " おやすみ"
            tweepy_api.update_status(status=text, in_reply_to_status_id=status.id)


        elif encoded_text.find("@") == -1 and encoded_text.find("http:") == -1 and random.randint(1,200) == 1:
            # リプライじゃない場合もたまにリプ飛ばす
            encoded_text = status.text.encode("utf-8")
            learn(encoded_text)
            tweet_text = "@" + status.author.screen_name.encode("utf-8") + " " + marcovReply(encoded_text)
            tweepy_api.update_status(status=tweet_text, in_reply_to_status_id=status.id)

def marcovReply(source_text):
    keyword = yahoo_keyphrase.extract_keyphrase(source_text)
    if len(keyword) == 0:
        tweet_text = marcov("" ,"", "")
    else:
        a = ["は", "が", "も", "の"]
        b = ["係助詞", "格助詞", "係助詞", "連体化"]
        r = random.randint(0, len(a) - 1)
        tweet_text = marcov(keyword + a[r], a[r], b[r])
    return tweet_text
        

def fixedTweet():
    print "start fixedTweet"
    while True:
        normalTweet()
        time.sleep(fixed_tweet_interval * 60)

# マルコフ連鎖からツイートする時
def normalTweet():
    # zolj_j のツイートからリプライじゃないものだけ拾ってくる
    zolf_tl = twitter_api.GetUserTimeline(screen_name="zolf_j", count=200)
    nonreply_tweets = []
    for s in zolf_tl:
        encoded_s = s.text.encode("utf-8")
        # 【マイリスト】の文字を含むものは除去したい
        # URLを含むものはとりあえず除去
        if s.text[0] !='@' and len(s.urls) == 0 and encoded_s.find("RT") == -1:
            nonreply_tweets.append(s.text)
            # print(t.text)

    # 辞書を初期化して最近のツイートから学習する
    dict = []
    nouns = []
    karas = []
    places = []
    times = []
    for s in nonreply_tweets:
        encoded_s = s.encode("utf-8")
        # print encoded_s
        learn(encoded_s)
        # とりあえず keyphrase を place に追加しておく
        keyphrase = yahoo_keyphrase.extract_keyphrase(encoded_s)
        if len(keyphrase) > 0:
            places.append(keyphrase)

    keyphrase_count = defaultdict(int)
    
    # print "kara",
    # print len(karas)
    # for kara in karas:
    #     print "kara: " + kara
    #  
    # print "noun",
    # print len(nouns)
    # for noun in nouns:
    #     print "noun: " + noun
    

    # マルコフ連鎖でテキスト生成
    text = marcov("","","")
    print "Tweet: " + text

    # ツイート
    if __name__ == "__main__":
        try:
            twitter_api.PostUpdate(text)    
        except:
            print "再生成します"
            normalTweet()
            



# str の内容を学習する
def learn(str):
    print "Learn:  " + str

    # 形態素解析
    mt = MeCab.Tagger("mecabrc")
    res = mt.parseToNode(str)

    begin = ""
    begintype = ""
    buff = ""
    end = ""
    endtype = ""
    kara_hist = ""

    while res:
        if len(res.surface) != 0:
            print res.surface,
            print res.feature
            a = res.feature.split(",")
            surf = res.surface
            kara_hist += surf # ここまでの文章
            type = a[0]
            
            if (type == "助詞" and a[1].find("終助詞") == -1) or a[1] == "読点":
                end = surf
                endtype = a[1]
                dict.append([begin, buff, end, begintype, endtype])
                begin = end
                begintype = endtype
                buff = ""
            elif a[1] == "句点" or surf == "！":
                buff += surf;
                end = ""
                endtype = ""
                if(len(buff) > 1): #「。」一文字とかを弾くため
                    dict.append([begin, buff, end, begintype, endtype])
                begin = ""
                begintype = ""
                buff = ""
                kara_hist = ""
            elif type == "名詞" and a[1] != "サ変接続" and a[1] != "数" and len(keyphrase_count) > 0 and random.randint(1, 5) == 1:
                keys = keyphrase_count.keys()
                surf = keys[random.randint(0,len(keys)-1)]
                buff += surf
            else:
                buff += surf

            # 何？と聞かれた時に返す名詞を突っ込む
            if type == "名詞" and a[1] != "サ変接続" and a[1] != "数":
                print "名詞を追加: " + surf
                nouns.append(surf)

            # 理由的な文章を抽出する
            if surf == "から" and a[1] == "接続助詞":
                print "理由文書を追加: " + kara_hist
                karas.append(kara_hist)
                kara_hist = ""

            # 時間的な単語を抽出する
            if a[1] == "副詞可能":
                print "時間的単語を追加: "
                times.append(surf)

        res = res.next
    if(len(buff) > 1): # 「。」一文字とかを弾くため
        dict.append([begin, buff, "", begintype, ""])

# マルコフ連鎖生成
def marcov(text, next, nexttype):
    while True:
        # 次につながる候補を探していく
        candidate = []
        print "候補: " + next + "(" + nexttype + ")"
        for a in dict:
            if a[0] == next and a[3] == nexttype:
                candidate.append(a)
                print a[0] + "(" + a[3] + ")\t" + a[1] + "\t" + a[2] + "(" + a[4] + ")"
                
        
        selected = candidate[random.randint(0, len(candidate) - 1)]
        print "選択: " + selected[0] + "(" + selected[3] + ")\t" + selected[1] + "\t" + selected[2] + "(" + selected[4] + ")"
        text += selected[1] + selected[2]
        next = selected[2]
        nexttype = selected[4]
        if len(next) == 0:
            break

    # print text
    return text

if __name__ == "__main__":
    daemon_runner = daemon.runner.DaemonRunner(ZolfBotDaemon())
    daemon_runner.do_action()
