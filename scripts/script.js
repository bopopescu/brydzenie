$(document).ready(function(){

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
        // zamiast z boku wrzuc jedno ciastko na dole :>
        var img2 = new Image(330,300);
        img2.src = '../stylesheets/images/cookie.png';
        img2.style.display = 'block';
        img2.style.margin = 'auto';
        document.getElementById('container').appendChild(img2);
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

 });
