$(document).ready(function(){

    if ($(window).width() < 1000){
        $('.cookies').css('display','none'); //wrzuc ciastko jedno na dole :>
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
    
    $('.titles').mouseenter(function(){
        $(this).css({'color':'#ffffff' ,'background':'rgba(59, 25, 10, 1)'});
    });
    $('.titles').mouseleave(function(){
        $(this).css({'color':'rgba(209, 0, 0, 1)', 'background':'transparent'});
    });



/*$('.titles').css({'color':'rgba(209, 0, 0, 1)', 'text-decoration':'none'});

    $('.titles').mouseenter(function(){
        $(this).css({'color':'rgba(59, 25, 10, 1)' ,'text-decoration':'underline'});
    });

    $('.titles').mouseleave(function(){
        $(this).css({'color':'rgba(209, 0, 0, 1)', 'text-decoration':'none'});
    });
*/

 });