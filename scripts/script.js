$(document).ready(function(){

    // on reload
    $('.opo-content').css({'display': 'none'});
    if (typeof sessionStorage.opo_var !== 'undefined') {
        $(sessionStorage.opo_var + " .opo-content").css({'display': 'block'});
    } else {
        $("#opo1 .opo-content").css({'display': 'block'});
    };
    // zakladka on revisit
    if ((typeof localStorage.page_var !== 'undefined') && (typeof localStorage.height_var !== 'undefined')) {
      if (localStorage.page_var == window.location.pathname) {
        window.scrollTo(0,localStorage.height_var);
      }
      if (window.location.pathname == '/') {
        document.getElementById("teraz_czytasz").innerHTML = "Teraz czytasz: " + localStorage.page_var;
        document.getElementById("teraz_czytasz").href = 'https://brydzenie.appspot.com' + localStorage.page_var;
      }
    };


    // mobile
    if ($(window).width() < 1000){
        $('.cookies').css('display','none');
        $('.bar').css('float','none');
        $('#opo').css('margin','90px 10px 100px 10px');
        //button show-navbar
        var img = new Image(50,50);
        img.setAttribute('id', 'button');
        img.src = '../stylesheets/images/file-text.png';
        img.alt = 'pokaz/ukryj nawigacje';
        img.style.position = 'relative';
        img.style.cssFloat = "right";
        img.style.top = 12 + 'px';
        img.style.right = 10 + 'px';
        document.getElementById('navbar').appendChild(img);
        // zakladka
        $('.zakladka').css({'right': '0px', 'top': '150px', 'font-size': '40px'});
        $('.arrow-left').css({'border-top': '20px solid transparent',
                              'border-bottom': '20px solid transparent',
                              'border-right': '20px solid orange'});
        // zamiast z boku wrzuc jedno ciastko na dole :>
        var img2 = new Image(330,300);
        img2.src = '../stylesheets/images/cookie.png';
        img2.style.display = 'block';
        img2.style.margin = 'auto';
        document.getElementById('container').appendChild(img2);
        //images in opo text
        $('#opoimg').css({'width': '90%', 'text-indent': '0px'});
    }
    //navbar show-hide
    $("#button").click(function() {
        $(".bar").toggle();
    });

    if (navigator.userAgent.indexOf("Chrome") > -1){
        $('.header').css('margin-top','10px');
    }
    if (navigator.userAgent.indexOf("Opera") > -1){
        $('.header').css('margin-top','10px');
    }

    if (window.location.href.match('zartem|serio|zakalec|okruchy')){
        $('#topButton').show();
        $('#zakladka').show();
    } else {
        $('#topButton').hide();
        $('#zakladka').hide();
    }
 });

//opo-content show-hide
$(document).on('click', '#opo1', function() {
    $('.opo-content').css({'display': 'none'});
    $("#opo1 .opo-content").css({'display': 'block'});
    sessionStorage.opo_var = "#opo1";
});

$(document).on('click', '#opo2', function() {
    $('.opo-content').css({'display': 'none'});
    $("#opo2 .opo-content").css({'display': 'block'});
    sessionStorage.opo_var = "#opo2";
});

$(document).on('click', '#opo3', function() {
    $('.opo-content').css({'display': 'none'});
    $("#opo3 .opo-content").css({'display': 'block'});
    sessionStorage.opo_var = "#opo3";
});

$(document).on('click', '#opo4', function() {
    $('.opo-content').css({'display': 'none'});
    $("#opo4 .opo-content").css({'display': 'block'});
    sessionStorage.opo_var = "#opo4";
});

$(document).on('click', '#opo5', function() {
    $('.opo-content').css({'display': 'none'});
    $("#opo5 .opo-content").css({'display': 'block'});
    sessionStorage.opo_var = "#opo5";
});

// https://www.w3schools.com/html/html5_webstorage.asp
// https://diveintohtml5.info/storage.html

//zakladka - save position
$(document).on('click', '#zakladka', function() {
    localStorage.page_var = window.location.pathname;
    localStorage.height_var = window.pageYOffset;
    //dymek - zapisane!
    $('#alarmmsg').css({'top': '30px', 'right': '30px'}).show();
    setTimeout(function(){ $('#alarmmsg').hide(); }, 2000);
});
// https://javascript.info/size-and-scroll-window

$(document).on('click', '#topButton', function() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
});
