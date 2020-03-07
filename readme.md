# tweet-image-finder

流れ行くTLを逃さず全部保存してしまう

## なにができる

- TLを全部DBに保存できる
- 画像・動画を保存できる
- pinterestライクなwebビューアでTLの画像だけを表示できる

## 使い方

1. git cloneします
2. env_sample.py を env.py に名前変更して必要な変数に値を書きます
3. docker-compose.yml で画像を保存するディレクトリの場所を書きます  
4. docker-compose up します  
5. ちょっと時間がたったらpythonコンテナが起動してtweetを取得します
6. tweet取得が終わったら画像ビューアが見れます (localhost:8080/tweet_viewer.php)
7. cron でpythonのコンテナを5分おきくらいでdocker restartするよう設定すればおしまいです

## いつかやるTODOリスト

- ビューアがいまいちイケてないのでイケてるようにする
- python のスクリプトみなおす(一部動画が取得できてない)
- 統計結果を出す
