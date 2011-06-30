// a few needed constants
False = false;
True = true;

// shared variables
previous_post = null;
player = null;
startup = true;

function connect(transport){
    connectViewer("method="+transport);
}

function disconnect(){
    disconnectViewer();
    $.get("/api/disconnect/"+$(".active-mode #stream-address").val());
}

function notsupported(transport){
    window.alert("Sorry but " + transport + " is not supported by your platform. You will need to run AIRi in Linux or Android to use this feature.");
}

function updateSensorData(data){
	$.each(data, function(index, value){
		if (index == "compass" || index=="gravitation"){
			var t = value.x+", "+value.y+", "+value.z;
			$(".active-mode #sensor-" +index).val(t)
		} else if (index == "magic"){
			$(".active-mode #sensor-" +index).val(
					'0x'+parseInt(value).toString(16)
			);
		}
		else
			$(".active-mode #sensor-" +index).val(value);
	});
}

function refreshButton(selector){
  var text = $(selector + " .ui-btn-text").text();
  $(selector + " > *").remove();
  var classes = "ui-btn ui-btn-up ui-btn-up-" + $(selector).jqmData("theme") +
    " ui-btn-inline "+
    " ui-btn-icon-left ui-btn-icon-right ui-btn-icon-top ui-btn-icon-bottom ui-btn-icon-notext" +
    " ui-icon-" + $(selector).jqmData("icon") +
    " ui-icon-shadow ui-btn-corner-all ui-shadow";
  $(selector).text(text).removeClass(classes).buttonMarkup();
}

function internalChangePage(target){
    console.log("internalChangePage " + target);
    $.mobile.changePage( target, {
        "changeHash": false,
        "reverse": false,
        "transition": "slide",
        "reloadPage": true,
    })
}

function goBack(){
    console.log("goBack")
    if ($.mobile.urlHistory.stack.length == 1)
        return true;

    if ($.mobile.urlHistory.activeIndex == 0)
        return true
    var target = $.mobile.urlHistory.getPrev();
    internalChangePage(target.page.attr("data-url"));
    $.mobile.urlHistory.stack.pop(); //this one is from changepage
    $.mobile.urlHistory.stack.pop(); //this one is back it self
    return true;
}

function goHome(){
    console.log("goHome");
    internalChangePage("/index.html"); // don't modify history
    return true;
}

function doReload(){
    console.log("doReload");
    internalChangePage($.mobile.activePage.attr("data-url"))
    $.mobile.urlHistory.stack.pop() // changePage created a new entry, take it out
}

function update_setup(){
    console.log("setup");
    $("#setup #exposure-text").remove()
    b = $("<label id='exposure-text' style='display: inline-block; width: 10%'>ms</label>")
    $(".ui-page-active #exposure[data-type=range]").after(b)
    $(".ui-page-active #exposure[data-type=range]").unbind("change")
    $(".ui-page-active #exposure[data-type=range]").bind("change", function(){
        var value = $(".ui-page-active #exposure").attr("value");
        if ( value == 0 ) value = 1;
        $(".ui-page-active #exposure-text").text(value*66+" ms")
    })
    $(".ui-page-active #exposure").trigger("change")
}

function getPlayerApi(){
	var a = $(".active-mode #video-content").data("flashembed");
	if ( a == null){
		console.log("no player found");
		return null
	}
	return a.getApi()
}

function doVoice(value){
	if (value==true) {
		if ($("#sco_holder").length > 0){
			console.log("Voice all ready enable, not doing again");
			return;
		}
		console.log("Enabling voice");
		var voice=$("<iframe />")
		voice.attr("id", "sco_holder");
		voice.attr("src", "/sco/"+$(".active-mode #stream-address").val());
		console.log(voice);
		voice.appendTo("#viewer");
	}
	else {
		$("#sco_holder").remove();
	}
}

function doConfigure(option, value){
	$.post("/api/doconfigure/", {
		"address": $(".active-mode #stream-address").val(),
		"option": option,
		"value": value
	})
/*	if (option=="voice"){
		var player = getPlayerApi();
		if (value==true)
			player.scoConnect();
		else
			player.scoDisconnect();
	}
*/
}

function switchResolution(size){
	return doConfigure("size", size);
}

function select_changed(){
  var option = this.id.split("-", 2)[1];
  var value = $("option:selected", this).attr("value");
  doConfigure(option, value)
  $(this).selectmenu("refresh");
}

function switchGeneric(option){
  doConfigure(option, ! eval($(".active-mode #stream-"+option).attr("data-state")));
}

function switchFlash(){
  switchGeneric("flash");
}

function switchVoice(){
  switchGeneric("voice");
}

function updateGeneric(option){
  if ( eval($(".active-mode #stream-"+option).attr("data-notsupported")) == true)
    return;

  if ( eval($(".active-mode #stream-"+option).attr("data-state"))==true )
    $(".active-mode #stream-"+option).attr("data-theme", "e")
  else
    $(".active-mode #stream-"+option).attr("data-theme", "a")
  $(".active-mode #stream-"+option).button()
}

function watch_device(){
  if (currentId() != "viewer"){
    return;
  }
  if (previous_post != null){
    previous_post.abort();
  }
  previous_post = $.post("/api/updates/",
    { 
      "address": $("#stream-address").val(),
    },
    function(data){
      previous_post = null;
      console.log(data)
      if (data.address != $("#stream-address").val()){
        return watch_device();
      }

      delete data.address
      $.each( data, function(index, element) {
        switch (index){
          case "size":
          case "pan":
            $(".active-mode #stream-"+index+" option:selected").removeAttr("selected");
            $(".active-mode #stream-"+index+" > option[value="+element+"]").attr("selected", "selected");
            $(".active-mode #stream-"+index).selectmenu("refresh");
            break;
          case "status":
            if (element==true){
              $(".active-mode #stream-disconnect").css("display", "")
              $(".active-mode #stream-connect").css("display", "none")
              connectViewer();
            } else if (element==false) {
              $(".active-mode #stream-connect").css("display", "")
              $(".active-mode #stream-disconnect").css("display", "none")
              disconnectViewer();
            }
            $(".active-mode #stream-" + index).val(element);
            break;
          case "flash":
          case "voice":
            $(".active-mode #stream-"+index).attr("data-state", element);
            updateGeneric(index)
            break;
          case "client_count":
            console.log("Client count " + element);
            $(".ui-page-active #header_extra").text(" | Viewed by " + element);
            $(".active-mode #stream-" + index).val(element);
            break;
          default:
            console.log("using default handler " + index);
            $("#stream-" + index).val(element);
          }
        }
      )
      return watch_device();
    }
  )
}


function update_viewer(){
  console.log("view");

/*  $(".active-mode #stream-size", $(".ui-page-active")).unbind("change")
  $(".active-mode #stream-size", $(".ui-page-active")).change(select_changed, {"origin": "stream-size"})
  $(".active-mode #stream-pan", $(".ui-page-active")).unbind("change")
  $(".active-mode #stream-pan", $(".ui-page-active")).change(select_changed, {"origin": "stream-pan"})
*/
  watch_device();

  player = $(".active-mode #video-content").flashembed(
      {
        src: "/media/airi.swf",
        quality: "low",
      },
      {
        //browser: window.navigator.userAgent,
      }
  )
//  updateGeneric("flash")
//  updateGeneric("voice")
}

function currentId(){
  return $(".ui-page-active").attr("id");
}

function pageshow(event, ui){
    var id = currentId();
    resize();
    console.log("show " + id);
    console.log("pagebeforecreate");
    $.each($(".ui-page").not(".ui-page-active"), 
        function(index, val) {
            console.log("removing: " + $(val).attr("id"))
    })
    $(".ui-page").not(".ui-page-active").remove();
    $("[data-rel=back]").remove()
    $("#" + id + " #back_button").
        attr("onclick", "javascript: goBack();").
        removeClass("ui-btn-active");
    $("#" + id + " #home_button").
        attr("onclick", "javascript: goHome();").
        removeClass("ui-btn-active");
    $("#" + id + " #reload_button").
        attr("onclick", "javascript: doReload();").
        removeClass("ui-btn-active");
    document.title = $(".ui-page-active div[data-role=header] h1").text();

    window.scrollTo(0, 1);

    if (startup){
        $.mobile.firstPage.attr("data-url", window.location.pathname+window.location.search);
        startup = False;
    }

    switch (id){
//        case "home":
//            return update_home();
        case "setup":
            return update_setup();
        case "viewer":
            return update_viewer();
    }
    console.log("show not known id " + id);
}

function pagehide(event, ui){
  var id = currentId();
  console.log("hide " + id);

  switch (id){
    case "setup":
      return hide_setup();
  }
  console.log("hide not known id " + id);

}

function create_exposure_slider(label, holder, real){
  holder=$(holder, $(".ui-page-active"));
  label=$(label, $(".ui-page-active"));
  real=$(real, $(".ui-page-active"));
}

function viewer_resize(event){
    var current = $("#viewer .active-mode").attr("data-airi")
    if ( current!=null ) {
        if ( $(window).width() > 768 && current == "desktop" ){
            return false;
        }
    }
    if ( $(window).width() > 768 ){
        $('#viewer [data-role="tabs"]').addClass("hide");
        $('#viewer [data-airi="mobile"]').addClass("hide").removeClass("active-mode");
        $('#viewer [data-airi="desktop"]').removeClass("hide").addClass("active-mode");
    } else {
        $('#viewer [data-role="tabs"]').removeClass("hide");
        $('#viewer [data-airi="mobile"]').removeClass("hide").addClass("active-mode");
        $('#viewer [data-airi="desktop"]').addClass("hide").removeClass("active-mode");
    }
    return true;
}

function viewer_create(event){
    var prepare = function(content){
    	console.log("viewer_create prepare");
        if (content.attr("id") == "video")
            $("#viewer .ui-content .active-mode").addClass("ui-video-player")
        else
            $("#viewer .ui-content .active-mode").removeClass("ui-video-player")
    }
    console.log("creating viewer");
    $(".rotate-45").rotate(-45);
    viewer_resize();
    viewerResize();
    $('#viewer div[data-role=tabs]').tabs({
        beforeTabShow: function(event, ui){ prepare(ui.nextContent); },
        load: function(event, args){ prepare(args.currentContent);},
        selector: 'div[data-airi=mobile]'
    })
}

function setup_create(event){
    console.log("creating setup");
    $('#setup [data-role=tabs]').tabs({
            selector: 'form[id=setup-form]'
    })

    $("div[data-role=page][id=setup] #reload_button").addClass("hide")
}

function viewerResizeDesktop(width, height){
    var viewer = $("#viewer .active-mode #video-content");
    if (width != undefined && height != undefined ){
        console.log("viewerResize", width, height);
        viewer.data("width", width);
        viewer.data("height", height);
    }
    $("#viewer .active-mode").parent().removeClass("ui-content-marginless")
    $("#viewer div[data-role=header]").find("a[id!=home_button],h1,h4").removeClass("hide")
    $("#viewer #home_button").removeClass("top-front")
    $("object", viewer).css("width", viewer.data("width"));
    $("object", viewer).css("height", viewer.data("height"));
}

function makeFullScreen(selector){
    var $this = $(selector);
    $this.addClass('ui-page-fullscreen');
    $this.find( ".ui-header:jqmData(position='fixed')" ).addClass('ui-header-fixed ui-fixed-inline fade'); //should be slidedown
    $this.find( ".ui-footer:jqmData(position='fixed')" ).addClass('ui-footer-fixed ui-fixed-inline fade'); //should be slideup
}

function makePartialScreen(selector){
    var $this = $(selector);
    $this.removeClass('ui-page-fullscreen');
    $this.find( ".ui-header:jqmData(position='fixed')" ).removeClass('ui-header-fixed ui-fixed-inline fade'); //should be slidedown
    $this.find( ".ui-footer:jqmData(position='fixed')" ).removeClass('ui-footer-fixed ui-fixed-inline fade'); //should be slideup
}


function viewerResizeMobile(width, height){
    $("#viewer div[data-role=header]").
        find("a[id=back_button],a[id=reload_button],h1,h4").
        addClass("hide")
    $("#viewer #home_button").addClass("top-front")
    $("#viewer .active-mode").parent().addClass("ui-content-marginless")
    var height = $(window).height();
    var width = $(window).width()-50;
    $.each($("#viewer div[data-role=header]"), function(a, p){
        height -= $(p).outerHeight();
    })
    console.log("new size " + width + " , " + height);
    $("#viewer .active-mode #video-content").css("width", width);
    $("#viewer .active-mode #video-content").css("height", height);
    $("#viewer .active-mode #video-content").css("margin", 0);
}

function viewerResize(width, height){
    var current = $("#viewer .active-mode").attr("data-airi");
    if ( current == "mobile" )
        return viewerResizeMobile(width, height);
    else
        return viewerResizeDesktop(width, height);
}

function viewerReady(){
    console.log("viewerReady")
    connectViewer();
}

function hide_setup(){
}

function connectViewer(extra){
	console.log("connectViewer")
	var player = getPlayerApi();
	if ( player == null )
		return;
	var url = "/stream/"+$("#stream-address").val().replace(/:/g, "_");
	url+="?flash=true&uniqId="+new Date().getTime()
	if (extra != null){
		url+="&"+extra
	}
	player.xhrConnect(url)
}

function disconnectViewer(){
  console.log("disconnectViewer")
  var player = getPlayerApi();
  if ( player == null )
    return;

  try {
    player.xhrDisconnect()
  } catch (err) {}
}


function switchState(){
  $.post(
    "/api/switchstate/",
    {
      "address": $("#stream-address").val()
    },function(data){
      console.log("switchState result", data)
    }
  )
}

function resize(event){
    if ( $(window).width() < 768 ) {
      $(".ui-page-active #home_button,#back_button,#reload_button").
        jqmData("iconpos", "notext")
    } else {
      $(".ui-page-active #home_button,#reload_button").jqmData("iconpos", "right")
      $(".ui-page-active #back_button").jqmData("iconpos", "left")
    }
    refreshButton(".ui-page-active #home_button");
    refreshButton(".ui-page-active #back_button");
    refreshButton(".ui-page-active #reload_button");

    if ( currentId() == "viewer" )
    {
        var r = viewer_resize(event);
        viewerResize();
        if (r){
            update_viewer();
        }
    }
}

function pagebeforecreate(){
}

function index_init(){
    $('div').live("pageshow", pageshow);
    $('div').live("pagebeforehide", pagehide);
    $('#viewer').live("pagecreate", viewer_create);
    $('#setup').live("pagecreate", setup_create);
    $(window).bind('orientationchange', resize);
    $(window).bind('resize', resize);
}

$(document).bind("mobileinit", index_init);
