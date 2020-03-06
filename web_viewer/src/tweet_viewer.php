<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>tweet-viewer</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/cdn.css">
    <link rel="stylesheet" href="css/menu.css">

    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
    <script src="scripts/jquery_func.js"></script>
    <?php require('php_funcs.php'); ?>

</head>


<div class="gblnv_box">
    <a class="menu-trigger" href="#"> <!-- ←ハンバーガーボタン -->
    	<span></span>
    	<span></span>
    	<span></span>
    </a>
    <div class="gblnv_block">
    	<ul class="gblnv_list"> <!-- ←ハンバーガーボタン内、グローバルメニュー -->
            <form action="./tweet_viewer.php" method="get" name='searchform'>
                <p><label for="user_screen_name" size=20></label><input type="text" name="user_screen_name" size=20 placeholder="@user ID "></p>
                <p><label for="user_name" size=20></label><input type="text" name="user_name" size=20 placeholder="user name"></p>
                <input type="hidden" name="RT_flg" value="0">
                <p><label for="RT_flg" class="nav_exp">exclude RT <input type="checkbox" name="RT_flg" value="1" size=8></label></p>
                <p><label for="from_date" class="nav_exp">from date <input type="date"  value="<?php echo date('Y-m-d'); ?>" name="from_date" min="2017-01-01" max="2022-12-31"></p>
                <p><label for="since_date" class="nav_exp">since date <input type="date"  name="since_date" min="2017-01-01" max="2022-12-31"></p>
            <input type="submit" value="送信"></li>
    	</ul>
    </div>

    <!-- スクロールボタン -->
    <div class='movetop' onclick='scrollTo(0, 0)'><a href="#" class='scrollicon'><span></span></a></div>
</div>


<div class="container" id="gallery">
    <!-- 画像の描写 -->
    <?php draw_image_boxes()?>
</div>

<div class="navigation">
    <?php
        //next_pageの設定
        
        if (isset($_GET["page"]) && (int)$_GET["page"] > 0) {
            $next_page = (int)$_GET["page"]+1;
        }else {
            $next_page = 2;
        }
        

        $next_url="/tweet_viewer.php?page={$next_page}";

        //getパラメータを引き継がせる
        foreach($_GET as $k => $v){
            if($k !== "page" && isset($v)){
                $next_url .= '&'.$k."=".$v;
            }
        }
    
    ?>
    <p class="nav-previous"><a href="<?php echo($next_url)?>"></a></p>
</div>


    <!--CDN関連-->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/lightbox2/2.7.1/js/lightbox.min.js" type="text/javascript"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/lightbox2/2.7.1/css/lightbox.css" rel="stylesheet">

    <script src="//cdnjs.cloudflare.com/ajax/libs/jquery/2.1.0/jquery.min.js"></script>
    <script src="//cdnjs.cloudflare.com/ajax/libs/jquery-infinitescroll/2.0b2.120519/jquery.infinitescroll.min.js"></script>
    <script src="//cdnjs.cloudflare.com/ajax/libs/masonry/3.1.2/masonry.pkgd.js"></script>
    <script src="//cdnjs.cloudflare.com/ajax/libs/jquery.imagesloaded/3.0.4/jquery.imagesloaded.min.js"></script>
</body>

</html>
