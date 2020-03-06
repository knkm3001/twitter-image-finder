#! /usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import copy
import json
import time
import traceback
from time import sleep

import slackweb
import requests
import urllib.request
import mysql.connector


from requests_oauthlib import OAuth1Session
from datetime import datetime, timedelta, timezone


import env

# twitter
CK = env.CONSUMER_KEY
CS = env.CONSUMER_SECRET
AT = env.ACCESS_TOKEN
AS = env.ACCESSS_TOKEN_SECERT

# database
DB_HOST = env.DB_HOST
DB_PORT = env.DB_PORT
DB_USER = env.DB_USER
DB_PW   = env.DB_PW
DB_DBNAME = env.DB_DBNAME

# slack
SLACKURL = env.SLACKURL
slack = slackweb.Slack(SLACKURL)

DIR_PATH = "/home/timeline/timeline_" + datetime.now().strftime('%Y-%m%d')

Twitter_API_PALAM = {
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


    connect = connect_to_db()
    since_id = get_sinceid_from_db()

    # メディア保存先確認
    if not os.path.exists(DIR_PATH):
        os.makedirs(DIR_PATH)
        print('new dir: ',DIR_PATH)




    # 制御処理関係
    max_id = 1 #  とりあえず　
    inner_loop_status = True # 入れ子ループ
    tweets_counter = 0   # ツイートの総計
    media_counter = 0  # mediaの総計

    for loop_times in range(1,6):  # 200*5=1000
        if inner_loop_status == False:
            break  # 内側で問題があった時、外側のループからも外れる
        try:
            palams = Twitter_API_PALAM.copy()
            if loop_times >= 2 :
                palams["max_id"] = max_id - 1

            timeline = get_timeline(palams)

            for count,tweet in enumerate(timeline):
                # since_id チェック
                if since_id is not None and int(tweet["id"]) <= int(since_id):
                    print("Error: since_idに達しました。")
                    inner_loop_status = False
                    break
                else:
                    tweets_counter += 1
                    print('-------------------------------------------------------')
                    print(f"No.{loop_times}-{count+1}")
                    print("tweet sum:",tweets_counter)
                    print_tweet_content(tweet)
                    max_id = tweet["id"]
                
                try:
                    # 処理その1 メディアを取得
                    media_url_list,media_path_list = save_tweet_media(tweet)
                    media_counter += len(media_url_list)
                except Exception as e:
                    print ("Error: コンテンツ取得時にエラー。")
                    raise e

                try:
                    # 処理その2 DBにインサート
                    insert_tweet_into_db(connect,tweet,media_url_list,media_path_list)
                except Exception as e:
                    connect.rollback()
                    connect.close()
                    print ("Error: DBインサート時にエラー。")
                    raise e
        except:
            traceback.print_exc()
            break

    # slackに結果送信
    slackpost(start_time,tweets_counter,media_counter)


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


def connect_to_db():
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


def get_sinceid_from_db(connect):
    """
    テーブルの一番最新のレコードを取得
    """


    cursor = connect.cursor(dictionary=True,buffered=True)

    # テーブルの最新のツイートをlatest_tweetとして取得
    cursor.execute("select * from  timeline order by created_at desc limit 1")
    latest_tweet = cursor.fetchone()

    # latest_tweetのtweet_IDとcreated_atをそれぞれ取得
    if latest_tweet:
        since_id = latest_tweet["tweet_ID"]
        latest_tweet_date = latest_tweet["created_at"]
    else:
        since_id = None
        latest_tweet_date = None

    print("since_id: ",since_id)
    print("latest_tweet_date: ",latest_tweet_date)

    return since_id


def insert_tweet_into_db(connect,tweet,media_url_list,media_path_list):
    """
    tweetをDBへインサート
    """

    jst_date = convert_datetime_to_jst(tweet)
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
                    ({0});
              """.format(', '.join(['%s']*13))
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
                    ({0});
              """.format(', '.join(['%s']*9))

    cursor = connect.cursor(dictionary=True,buffered=True)

    cursor.execute(sql,vols)

    cursor.close()
    connect.commit()


def convert_datetime_to_jst(tweet):
    """
    created_atの表示修正
    twitter特有の表示形式に変更 "yyyy-mm-dd hh:mm:ss"
    """
    dt = datetime.strptime(str(tweet['created_at']), '%a %b %d %H:%M:%S +0000 %Y')
    jst_time = datetime(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second) + timedelta(hours=9)

    return jst_time


def save_tweet_media(tweet):
    """
    mediaのダウンロード
    """

    jst_time =  convert_datetime_to_jst(tweet).strftime('%Y-%m%d-%H%M%S')

    media_path_list = [] # mediaのpathを格納
    media_url_list = [] # mediaのurlを格納
    content_check = [] # mediaのjsonを格納

    if re.match('RT @', tweet["text"]):
        name = tweet["entities"]["user_mentions"][0]["screen_name"]
    else:
        name = tweet["user"]["screen_name"]

    if "extended_entities" not in tweet:
        pass  # mediaなし
    else:
        # 複数のmediaが添付されている場合の末尾につけるナンバリング
        counter = [""]
        if 1 < len(tweet["extended_entities"]["media"]):
            counter = ["_1","_2","_3","_4"]
        try:
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

    print(convert_datetime_to_jst(tweet))
    print(tweet["text"])


def slackpost(start_time,tweets_counter,media_counter):
    """
    slack 接続
    """

    # エラーメッセージを表示
    end_time = time.time()
    result_time = end_time - start_time

    end_text = str(tweets_counter) + " コのツイートをインサートしました。"+"\n" \
             + str(media_counter) + " コのツイートの media を取得しました。"+"\n" \
             + "全所要時間:" + f"{round(result_time//60)}分{round(result_time-result_time//60*60,2)}秒" +"\n"
    slack.notify(text=end_text)



if __name__ == "__main__":
    main()


