$('#show_trailer_box').css('display','none');
$().ready(function() {
    $('a.slick-toggle').click(function() {
        var a = $(this).attr("data-id");
        $("div[data-id=" + a + "].comment_hidden").toggle(100);
        return false
    });
    $('a.slick-toggle2').click(function() {
        var a = $(this).attr("data-id");
        $("div[data-id=" + a + "].music_item_hidden").toggle(100);
        return false
    })

	$('a[ref="show_trailer"]').click(function() {
		var a = $(this).attr('id');
		var b = $(this).attr('name');
		if ($('#show_trailer_box').css('display') == 'none') {
			$('#show_trailer_box').show()
		} else {
			$('#show_trailer_box').hide()
		}
	});
	$('a[ref="add_fav"]').click(function() {
		var b = $(this).parent().attr('ref');
		var c = $(this).attr('name');
		var d = $(this);
		$.get('./addtofavs.php', {
			id: b,
			whattodo: c,
			ajax: 1
		}, function(a) {
			d.parent().html(a)
		});
		return false
	});
	$('a[ref="vote"]').click(function() {
		var b = $(this).parent().parent().attr('ref');
		var c = $(this).attr('name');
		var d = $(this);
		$.get('/mysettings.php', {
			commentvote: b,
			dothis: c,
			ajax: 1
		}, function(a) {
			d.parent().parent().html(a)
		});
		return false
	});
	$('a[ref="vote_rev"]').click(function() {
		var b = $(this).parent().parent().attr('ref');
		var c = $(this).attr('name');
		var d = $(this);
		$.get('/mysettings.php', {
			reviewvote: b,
			dothis: c,
			ajax: 1
		}, function(a) {
			d.parent().parent().html(a)
		});
		return false
	});
});

function sendValue(b, c, d) {
    $.post("/show_comments.php", {
        sendToValue: b,
        movie_id: c,
        ep_id: d
    }, function(a) {
        $('#display' + b).html(a.returnFromValue)
    }, "json")
}

function addHit(a, b) {
    $.get("/spiderman.php", {
        version: a,
        part: b
    })
}

function toggle_visibility(a) {
    var e = document.getElementById(a);
    if (e.style.display == 'block') e.style.display = 'none';
    else e.style.display = 'block'
}

