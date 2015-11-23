$(document).ready(function(){

//var orange_width = screen.width - $('.cookies').attr('style').replace('width: ','');
//$('.orange').css('width', orange_width+'px');


$('a').css({'color':'rgba(209, 0, 0, 1)', 'text-decoration':'none'});

    $('a').mouseenter(function(){
        $(this).css({'color':'rgba(59, 25, 10, 1)' ,'text-decoration':'underline'});
    });

    $('a').mouseleave(function(){
        $(this).css({'color':'rgba(209, 0, 0, 1)', 'text-decoration':'none'});
    });

  
  //rgba(59, 25, 10, 1)

    $('.titles').mouseenter(function(){
        $(this).css({'color':'#ffffff' ,'background':'rgba(59, 25, 10, 1)'});
    });

    $('.titles').mouseleave(function(){
        $(this).css({'color':'rgba(209, 0, 0, 1)', 'background':'transparent'});
    });



    $('.content div').css('display','none');
    $('.Super_Matematyk').css('display','block');
    
 });

