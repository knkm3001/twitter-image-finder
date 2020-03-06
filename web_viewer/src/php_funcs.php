<?php

date_default_timezone_set('Asia/Tokyo');


/**
 * DBに接続し、その結果から画像の描写を行う。
 * TODO: ローカルのファイルから画像をとってくる
 */
function draw_image_boxes(){

    $db = make_inst();
    $stt = make_sql($db);
    $stt->execute();

    while ($row = $stt->fetch(PDO::FETCH_ASSOC)) {
        $media_url = preg_replace("/'/", "", $row['media_url']);
        $media_url = preg_replace("/(\[)/", "", $media_url);
        $media_url = preg_replace("/(\])/", "", $media_url);
        $url_arr = explode(",", $media_url);
        
        // 賢くないけど、メディアの一番最初が有効なURLならそれを描写するようにした
        // TODO ココ
        foreach ($url_arr as $img_url) {
            if(preg_match("/.jpg$/",$img_url)) {
                ?>
                <section class="item">
                    <a href="<?php echo h($img_url) ?>" data-lightbox="abc"
                       data-title="<?php echo h($row['user_name'].'<br>'.'@'.$row['user_screen_name']
                           .'<br>'.$row['created_at'].'<br>'.$row['text'])?>">
                        <img class="image" src="<?php echo h($img_url) ?>" alt="twitter_pics" onerror="this.remove()">
                    </a>
                </section>
                <?php
            }
        }
    }   
}


function rtn_sttscode($url)
{
	$ch = curl_init();
	curl_setopt($ch, CURLOPT_URL, $url); //URLの設定
    curl_setopt($ch, CURLOPT_HEADER, true); //  ヘッダ内容出力
    curl_setopt($ch, CURLOPT_NOBODY, true); // bodyは表示しない
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true); 
	curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false); //SSL証明みない
	$html = curl_exec($ch);
	$status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
	
	curl_close($ch);
	return $status;
}



/**
 * htmlspecialcharsの変換
 * "' はしない
 */
function h($argstr){
    return htmlspecialchars($argstr, ENT_NOQUOTES , "UTF-8");
}

/**
 * DBへの接続を確立し、PDOインスタンスをリターン
 */
function make_inst(){
    $dsn = "mysql:dbname=twitter;host=tweet_db;port=3306;charset=utf8mb4";
    $usr = "root";
    $passwd = "root";
    try{
        $db = new PDO($dsn, $usr, $passwd,[
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, # エラー時に例外を投げる
            PDO::ATTR_PERSISTENT => true, # 持続的な接続
            PDO::ATTR_EMULATE_PREPARES => false, # 静的プレースホルダ
            ]);
    }catch(PDOException $e){
        $error = $e->getMessage();
    }
    return $db;
}

/**
 * sqlクエリを発行し、実行する
 * 
 */
function make_sql($db){

    // WHERE句用作業領域とホワイトリスト
    $where_wk = [];
    $where_wlist = ['user_name', 'user_screen_name', 'picture_flg', 'RT_flg'];

    // where 以外の条件の作業領域とホワイトリスト
    $other_wk = [];
    $date_wlist = ['from_date','since_date'];

    // プレースホルダに充てるデータ用の作業配列
    $placeholder_data = [];

    // offsetはページから取得
    if (isset($_GET["page"]) && (int)$_GET["page"] > 0) {
        $page = (int)$_GET["page"];
        $placeholder_data[':offset'] = strval(($page-1)*20);
    }else {
        $placeholder_data[':offset'] = 0;
    }

    // SQLのベース
    $sql = 'SELECT * FROM twitter.timeline ';

    // プレースホルダ付きのSQL作成と、プレースホルダに代入する値の配列の作成
    foreach($where_wlist as $k) {
        if (isset($_GET[$k]) && $_GET[$k] !== "") {
            if($k=="RT_flg" && $_GET[$k] == 1){
                // RT_flgは1だとRTを除く仕様にした
                array_push($where_wk,"RT_flg = :RT_flg");
                $p_key = ":RT_flg";
                $placeholder_data[$p_key] = 0;
            }else{
                array_push($where_wk,"{$k} = :{$k}");
                $p_key = ":{$k}";
                $placeholder_data[$p_key] = $_GET[$k];
            }
        }
    }
    
    $sql .= " WHERE media_url != 'None' ";
    
    // WHERE句を結合していく
    if ($where_wk){
        $sql .= " AND " . implode(' AND ', $where_wk);
    }

    foreach($date_wlist as $k) {
        if ($_GET[$k]){
            list($Y, $m, $d) = explode('-', strval($_GET[$k]));
            if(checkdate($m, $d, $Y)) {
                if($k == "since_date"){
                    $sql .= ' AND created_at > :since_date ';
                    $p_key = ":{$k}";
                    $placeholder_data[$p_key] = $_GET[$k];
                }else if($k == "from_date"){
                    $sql .= ' AND created_at < :from_date ';
                    $p_key = ":{$k}";
                    $placeholder_data[$p_key] = date("Y-m-d",strtotime($_GET[$k].' +1 day'));
                }
            }
        }
    }

    $sql .=  ' ORDER BY tweet_ID DESC limit 20 offset :offset;';

    $stt = $db->prepare($sql);
	
    // プレースホルダに値を当て込む
    foreach($placeholder_data as $k => $v) {
        if(is_int($v)||is_float($v)){
            $type = PDO::PARAM_INT;
        }else{
            $type = PDO::PARAM_STR;
            // id:@hogehoge の@は取り除く
            if($k == ':user_screen_name' && mb_substr($v,0,1)=='@'){
                $v = mb_substr($v,1);
            }
        }
        $stt->bindValue($k, $v, $type);
    }

    echo('placeholder_data: '.print_r($placeholder_data,true));
    echo('stt: '.debug_console($stt));

    return $stt;
}

/**
 * console.log させる
 */
function debug_console($value){
    echo("<script>console.log( ".json_encode($value)." );</script>");
}
