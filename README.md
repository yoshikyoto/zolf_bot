# zolf_bot

## 動作環境

* python2
* urllib3
* requests 2.5.3
* module
* tweepy
* python-twitter
* MeCab

## urllib3

```
$ sudo pip install urllib3
```

# requests 2.5.3

```
$sudo pip install requests=2.5.3
```

## module

```
$ sudo pip install module
```

## tweepy

```
$ sudo pip install tweepy
```

## python-twitter

```
$ sudo pip install python-twitter
```

`twitter` ではありません。twitterをインストールしている場合は、競合するっぽいので、

```
$ sudo pip uninstall twitter
```

してください。

## MeCab

* http://qiita.com/yoshikyoto/items/1a6de08a639f053b2d0a


# 動作するまで

## account.py の作成

`account.py.sample` を参考に、`account.py` を作成してください。


## debug.py による動作確認

```
$ python debug.py
```

としてツイートが表示されることを確認してください。


## 実行

まずは `zolf_bot.py` に実行権限を与えてください。

```
$ chmod 755 zolf_bot.py
```

あとは、daemonとして起動してください。
起動できない場合は `python-daemon` が使えるかを確認してください。

```
$ ./zolf_bot.py start
```

`./zolf_bot.py stop` で止まります。

## ソースコードについて

* zolf_bot.py
  * zolf_bot本体。デーモンとして動作します。
* debug.py
  * `python debug.py` とすると平常時のツイートが出力されます。

