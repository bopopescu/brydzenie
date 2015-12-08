$(document).ready(function(){

    if (navigator.userAgent.indexOf("Chrome") > -1){
        $('.header').css('margin-top','10px');
    }
    if (navigator.userAgent.indexOf("Opera") > -1){
        $('.header').css('margin-top','10px');
    }
    
/*$('.titles').css({'color':'rgba(209, 0, 0, 1)', 'text-decoration':'none'});

    $('.titles').mouseenter(function(){
        $(this).css({'color':'rgba(59, 25, 10, 1)' ,'text-decoration':'underline'});
    });

    $('.titles').mouseleave(function(){
        $(this).css({'color':'rgba(209, 0, 0, 1)', 'text-decoration':'none'});
    });
*/

    $('.titles').mouseenter(function(){
        $(this).css({'color':'#ffffff' ,'background':'rgba(59, 25, 10, 1)'});
    });

    $('.titles').mouseleave(function(){
        $(this).css({'color':'rgba(209, 0, 0, 1)', 'background':'transparent'});
    });

 });
