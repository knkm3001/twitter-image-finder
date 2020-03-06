#! /usr/bin/env python
# -*- coding: utf-8 -*-


from requests_oauthlib import OAuth1Session
from datetime import datetime, timedelta, timezone
from time import sleep
import json
import time
import sys
import urllib.request
import re
import os
import mysql.connector
import slackweb
import requests
import copy
import traceback

import env

# twitter
CK = env.CONSUMER_KEY
CS = env.CONSUMER_SECRET
AT = env.ACCESS_TOKEN
AS = env.ACCESSS_TOKEN_SECERT

# database
DB_HOST = env.DB_HOST
DB_PORT = env.DB_PORT
DB_DBNAME = env.DB_DBNAME
DB_USER = env.DB_USER
DB_PW = env.DB_PW

# slack
SLACKURL = env.SLACKURL

slack = slackweb.Slack(SLACKURL)
CARENT_PATH = "/home/timeline/"
DIR_PATH = CARENT_PATH + "timeline_" + datetime.now().strftime('%Y-%m%d')

Teitter_API_PALAM = {
          "count" : 200,
          "include_entities" : True,
          "exclude_replies" : False,
          "include_rts" : True
          }


def main():
    """
    main関数
    """

    start_time = time.time()
    count_sum = 0   # ツイートの総計
    media_count = 0  # mediaの総計

    # DBからsince_id取得
    since_id = get_SinceID_fromDB()

    # メディア保存先確認
    if not os.path.exists(DIR_PATH):
        os.makedirs(DIR_PATH)
        print('new dir: ',DIR_PATH)

    # 制御処理関係
    i = 0  # 周回数
    max_id = 1 #  とりあえず　
    outer_loop_status = True #  入れ子のループの中で、内側のループ内で問題があった場合、外側のループから外れることができるよう

    print("mainはじめ")

    for i in range(1,6):  # 200*5=1000
        if outer_loop_status == False:
            break  # 内側で問題があった時、外側のループからも外れる
        try:
            palams = Teitter_API_PALAM.copy()
            if i >= 2 :
                palams["max_id"] = max_id - 1

            timeline = get_timeline(palams)

            for count,tweet in enumerate(timeline):
                # since_id チェック
                if since_id is not None and int(tweet["id"]) <= int(since_id):
                    print("Error: " + "since_idに達しました。")
                    outer_loop_status = False
                    break
                else:  # since_idにはまだ達していない
                    count_sum += 1 # ツイートの総計
                    print('-------------------------------------------------------')
                    print(f"No.{i}-{count+1}")
                    print("tweet sum:",count_sum)
                    print_tweet_content(tweet)
                    max_id = tweet["id"]
                
                try:
                    # 処理その1 メディアを取得
                    media_url_list,media_path_list = MediaGet(tweet)
                    media_count += len(media_url_list)
                except:
                    traceback.print_exc()
                    print ("Error: コンテンツ取得時にエラー。")

                try:
                    # 処理その2 DBにインサート
                    insert_tweet_into_DB(tweet,media_url_list,media_path_list)
                except:
                    traceback.print_exc()
                    print ("Error: DBインサート時にエラー。")
            
        except:
            traceback.print_exc()
            break

    # slackに送信
    slackpost(start_time,count_sum,media_count)


def get_timeline(params):
    """
    twitter api 呼び出し
    引数のパラメータで変えられる。
    """

    session = OAuth1Session(CK, CS, AT, AS)

    # Timeline用エンドポイント
    url = "https://api.twitter.com/1.1/statuses/home_timeline.json"

    res = session.get(url, params = params)
    timeline = json.loads(res.text)

    # APIアクセス情報表示
    print("\n+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+")
    print (f'アクセス可能回数 {res.headers["X-Rate-Limit-Remaining"]}')
    sec = int(res.headers["X-Rate-Limit-Reset"]) - time.mktime(datetime.now().timetuple())
    next_time = datetime.now() + timedelta(seconds=sec)
    print (f'リセットまで {sec} 秒')
    print (f'リセット時刻 {next_time.strftime("%H:%M:%S")}')
    print("+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+\n")

    return timeline


def connect_to_DB():
    """
    mariaDB 接続
    """
    connect = mysql.connector.connect(
        host = DB_HOST,
        port = DB_PORT,
        db = DB_DBNAME,
        user = DB_USER,
        password = DB_PW,
        charset = "utf8mb4"
    )
    return connect


def get_SinceID_fromDB():
    """
    テーブルの一番最新のレコードを取得
    """
    connect = connect_to_DB()
    cursor = connect.cursor(dictionary=True)

    latest_tweet = []
    # テーブルの最新のツイートをlatest_tweetとして取得
    cursor.execute("select * from  timeline order by created_at desc limit 1")
    latest_tweet = cursor.fetchall()

    # latest_tweetのtweet_IDとcreated_atをそれぞれ取得(latest_tweetが存在しなければNone)
    if len(latest_tweet) == 0:
        since_id = None
        latest_tweet_date = None
    else:
        since_id = latest_tweet[0]["tweet_ID"]
        latest_tweet_date = latest_tweet[0]["created_at"]


    print("since_id: ",since_id)
    print("latest_tweet_date: ",latest_tweet_date)

    return since_id


def slackpost(start_time,count_sum,media_count):
    """
    slack 接続 (エラー表示などテキストのpost)
    """
    # エラーメッセージを表示
    end_time = time.time()
    result_time = end_time - start_time

    end_text = str(count_sum) + " コのツイートをインサートしました。"+"\n" \
             + str(media_count) + " コのツイートの media を取得しました。"+"\n" \
             + "全所要時間:" + f"{round(result_time//60)}分{round(result_time-result_time//60*60,2)}秒" +"\n"
    slack.notify(text=end_text)



def insert_tweet_into_DB(tweet,media_url_list,media_path_list):
    """
    tweetをDBへインサート
    """
    jst_date = parse_date_format(tweet)
    now_time = datetime.now() # 今処理した時間

    # メディアのurlの処理
    media_url_list = str(media_url_list) if media_url_list else None
    media_path_list = str(media_path_list) if media_path_list else None


    if  re.match('RT @', tweet["text"]):
        # RTのとき
        original_prsn = tweet["entities"]["user_mentions"][0]
        vols=(
            str(tweet['id']),               # tweet_ID
            str(now_time),                  # insert_date
            original_prsn["name"],          # user_name
            original_prsn["screen_name"],   # user_screen_name
            str(original_prsn["id"]),       # user_ID
            1,                              # RT_flg
            tweet["user"]["name"],          # RTed_user_name
            tweet["user"]["screen_name"],   # RTed_user_screen_name
            str(tweet["user"]["id"]),       # RTed_user_ID
            str(jst_date),                  # created_at
            tweet["text"],                  # text
            media_url_list,                 # media_url
            media_path_list                 # media_path
          )
        sql = """
                INSERT INTO timeline
                    (tweet_ID,insert_date,user_name,user_screen_name,user_ID,RT_flg,RTed_user_name,
                    RTed_user_screen_name,RTed_user_ID,created_at,text,media_url,media_path)
                values
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
              """
    else:
        # RTじゃないとき
        vols=(
            str(tweet['id']),               # tweet_ID
            str(now_time),                  # insert_date
            tweet["user"]["name"],          # user_name
            tweet["user"]["screen_name"],   # user_screen_name
            str(tweet["user"]["id"]),       # user_ID
            str(jst_date),                  # created_at
            tweet["text"],                  # text
            media_url_list,                 # media_url
            media_path_list                 # media_path
          )
        sql = """
                INSERT INTO timeline
                    (tweet_ID,insert_date,user_name,user_screen_name,user_ID,created_at,text,media_url,media_path)
                values
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s);
              """

    connect = connect_to_DB()
    try:
        cursor = connect.cursor(dictionary=True)
    except:
        sys.exit()
    cursor.execute(sql,vols)

    cursor.close()
    connect.commit()


def parse_date_format(tweet):
    """
    created_atの表示修正
    twitter特有の表示形式に変更 "yyyy-mm-dd hh:mm:ss"
    """
    dt = datetime.strptime(str(tweet['created_at']), '%a %b %d %H:%M:%S +0000 %Y')
    jst_time = datetime(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second)  + timedelta(hours=9)
    return jst_time


def MediaGet(tweet):
    """
    mediaのダウンロード
    """

    jst_time =  parse_date_format(tweet).strftime('%Y-%m%d-%H%M%S')

    media_path_list = [] # mediaのpathを格納
    media_url_list = [] # mediaのurlを格納
    content_check = [] # mediaのjsonを格納

    if re.match('RT @', tweet["text"]):
        name = tweet["entities"]["user_mentions"][0]["screen_name"]
    else:
        name = tweet["user"]["screen_name"]

    if "extended_entities" not in tweet:
        pass  # mediaなしはなにもしない
    else:
        try:
            # 複数のmediaが添付されている場合の末尾につけるナンバリング
            counter = [""]
            if 1 < len(tweet["extended_entities"]["media"]):
                counter = ["_1","_2","_3","_4"]

            # 取得処理
            for index, content_check in enumerate(tweet["extended_entities"]["media"]):
                if "video_info" in content_check:
                    # 動画の場合
                    media_url = tweet["extended_entities"]["media"][index]["video_info"]["variants"][0]["url"]
                    media_url_list.append(media_url)
                    path = DIR_PATH +"/" +name+"_"+str(jst_time)+counter[index]+".mp4"
                    media_path_list.append(path.replace(CARENT_PATH, ""))
                    for url in media_url_list:
                        urllib.request.urlretrieve(url,path)
                else:
                    # 画像の場合
                    media_url = tweet["extended_entities"]["media"][index]["media_url"]
                    media_url_list.append(media_url)
                    path = DIR_PATH +"/" +name+"_"+str(jst_time)+counter[index]+".jpg"
                    media_path_list.append(path.replace(CARENT_PATH, ""))
                    for url in media_url_list:
                        urllib.request.urlretrieve(url,path)
                print("【mediaを取得しました！】")
        except:
            print("Error: メディアの取得処理失敗")
            traceback.print_exc()

    return media_url_list,media_path_list


def print_tweet_content(tweet):
    """
    tweetの表示
    """

    if re.match('RT @', tweet["text"]):
        print("RT from")
        print(tweet["entities"]["user_mentions"][0]["screen_name"])
        print(tweet["entities"]["user_mentions"][0]["name"])
    else:
        print(tweet["user"]["screen_name"])
        print(tweet["user"]["name"])

    print(parse_date_format(tweet))
    print(tweet["text"])

if __name__ == "__main__":
    main()

