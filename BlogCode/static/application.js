
$(document).ready(function(){
  
    //Slide up and down on click
    $(".title-show-button").click(function(){
      $(this).parent().siblings(".blog-text").slideToggle("fast");
  });

});