
$(document).ready(function(){
  
    //Slide up and down on click
    $(".title-show-button").click(function(){
      $(this).parent().siblings(".blog-text").slideToggle("fast");
  });

	$.ajax({
      url: "http://amcrowcroft.appspot.com/blog.json",
      success: function( data ) {
        $( "#alice-blog" ).html('hello dave');
        }
	});
});