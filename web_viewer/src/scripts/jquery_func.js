/**
 * Infinite Scroll + Masonry + ImagesLoaded
 */
jQuery(
(function() {

  	//コンテンツを囲む要素をidで指定
	var $container = $('#gallery');

	// Masonry + ImagesLoaded
	$container.imagesLoaded(function(){
	$container.masonry({
      itemSelector: '.item', //コンテンツのclass名
      isFitWidth: true, //コンテナの親要素のサイズに基づいて、コンテンツのカラムを自動調節します。
	  percentPosition: true, 
	  gutter: 1
		});
	});

	// Infinite Scroll
	$container.infinitescroll({
		// selector for the paged navigation (it will be hidden) //リンクを囲む要素指定
		navSelector  : ".navigation",
		// selector for the NEXT link (to page 2) リンク要素自体指定
		nextSelector : ".nav-previous a",
		// selector for all items you'll retrieve 表示要素指定
		itemSelector : ".item"
    },
  
		// Trigger Masonry as a callback
		function( newElements ) {
			// hide new items while they are loading
			var $newElems = $( newElements ).css({ opacity: 0 });
			// ensure that images load before adding to masonry layout
			$newElems.imagesLoaded(function(){
				// show elems now they're ready
				$newElems.animate({ opacity: 1 });
				$container.masonry( 'appended', $newElems, true );
			});

	});
  

	/**
	 * OPTIONAL!
	 * Load new pages by clicking a link


	// Pause Infinite Scroll
	$(window).unbind('.infscr');

	// Resume Infinite Scroll
	$('.nav-previous a').click(function(){
		$container.infinitescroll('retrieve');
		return false;
	});
	 */
}));



jQuery(
	(function($) {
	  //WindowHeight = $(window).height();
	  //$('.drawr').css('height', WindowHeight); //メニューをwindowの高さいっぱいにする
	
	$(document).ready(function() {
		$('.menu-trigger').click(function(){ //クリックしたら
		$(this).toggleClass("active"); //ハンバーガーの動き
		$('.gblnv_block').toggleClass('open');
		return false;
		});
	});
	
	//別領域をクリックでメニューを閉じる
	$(document).click(function(event) {
	  if (!$(event.target).closest('.drawr').length) {
		$('.btn').removeClass('peke');
		$('.drawr').hide();
	  }
	});
	
	}));