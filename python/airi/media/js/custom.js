// a few needed constants
False = false;
True = true;

// shared variables
previous_post = null;
player = null;

function goBack(){
  if ($.mobile.urlHistory.stack.length == 1)
    return;

  if ($.mobile.urlHistory.activeIndex == 0)
    window.history.forward()
  else
    window.history.back()
}

function goHome(){
  if ($.mobile.activePage != $.mobile.firstPage)
    $.mobile.path.set($.mobile.firstPage.attr("data-url"));
}

function doReload(){
  $.mobile.changePage(
    {
      url: $.mobile.activePage.attr("data-url")
    }, 
    "slide ", false, false
  )
  $.mobile.urlHistory.stack = $.mobile.urlHistory.stack.slice(0, $.mobile.urlHistory.activeIndex)
}

function update_home(){
  console.log("home")
  if ( $.mobile.firstPage.attr("data-url") == "home" ){
    $.mobile.firstPage.attr("data-url", window.location.pathname);
    $("#back_button").live("vclick", goBack);
    $("#home_button").live("vclick", goHome);
  }
}

function update_setup(){
  console.log("setup");
  create_exposure_slider("exposure-display", "exposure-slider", "exposure");
}

function getPlayerApi(){
  var a = $("#video-content").data("flashembed");
  if ( a == null){
    console.log("no player found");
    return null
  }
  return a.getApi()
}

function doConfigure(option, value){
  $.post("/api/doconfigure/",
    {
      "address": $("#stream-address").val(),
      "option": option,
      "value": value
    }
  )
}

function select_changed(){
  var option = this.id.split("-", 2)[1];
  var value = $("option:selected", this).attr("value");
  doConfigure(option, value)
  $("#"+this.id).selectmenu("refresh");
}

function switchGeneric(option){
  doConfigure(option, ! eval($("#stream-"+option).attr("data-state")));
}

function switchFlash(){
  switchGeneric("flash");
}

function switchVoice(){
  switchGeneric("voice");
}

function updateGeneric(option){
  if ( eval($("#stream-"+option).attr("data-notsupported")) == true)
    return;

  if ( eval($("#stream-"+option).attr("data-state"))==true )
    $("#stream-"+option).attr("data-theme", "e")
  else
    $("#stream-"+option).attr("data-theme", "a")
  $("#stream-"+option).button()
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
            $("#stream-"+index+" option:selected").removeAttr("selected");
            $("#stream-"+index+" > option[value="+element+"]").attr("selected", "selected");
            $("#stream-"+index).selectmenu("refresh");
            break;
          case "status":
            if (element==true){
              $("#stream-disconnect").css("display", "")
              $("#stream-connect").css("display", "none")
              connectViewer();
            } else if (element==false) {
              $("#stream-connect").css("display", "")
              $("#stream-disconnect").css("display", "none")
              disconnectViewer();
            }
            break;
          case "flash":
          case "voice":
            $("#stream-"+index).attr("data-state", element);
            updateGeneric(index)
            break;
          default:
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
  create_exposure_slider("stream-exposure-display", "stream-exposure-slider", "exposure");

  $("#stream-exposure-slider", $(".ui-page-active")).unbind("slidechange")
  $("#stream-exposure-slider", $(".ui-page-active")).bind("slidechange", function(event, ui){
    doConfigure("exposure", ui.value);
  })

  $("#stream-size", $(".ui-page-active")).unbind("change")
  $("#stream-size", $(".ui-page-active")).change(select_changed, {"origin": "stream-size"})
  $("#stream-pan", $(".ui-page-active")).unbind("change")
  $("#stream-pan", $(".ui-page-active")).change(select_changed, {"origin": "stream-pan"})
  watch_device();
  if ( $("#flash_container").length == 0 )
    return;

  player = $("#video-content").flashembed(
      {
        src: "/media/airi.swf",
        quality: "low"
      }
  )
  updateGeneric("flash")
  updateGeneric("voice")
}

function currentId(){
  return $(".ui-page-active").attr("id");
}

function pageshow(event, ui){
  var id = currentId();
  console.log("show " + id);
  $("[data-rel=back]").remove()

  switch (id){
    case "home":
      return update_home();
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
  holder=$("#"+holder, $(".ui-page-active"));
  label=$("#"+label, $(".ui-page-active"));
  real=$("#"+real, $(".ui-page-active"));
  var slide=holder.slider({
    min: 1,
    max: 30,
    value: real.val(),
    slide: function(event, ui) {
      label.val(""+ui.value*1000/15);
      real.val(ui.value);
    }
  })
  label.val(""+slide.slider("value")*1000/15);
  var a = slide.children()
  var h = a.height();
  holder.css("height", h+"px");
  a.css("top","0px");
  a.css("margin-top","0px");
}

function viewer_create(event){
  console.log("creating viewer");
}

function setup_create(event){
  console.log("creating setup");
}

function viewerResize(width, height){
  console.log("viewerResize", width, height);
  $("#video-content").css("width", width);
  $("#video-content").css("height", height);
}

function viewerReady(){
  console.log("viewerReady")
  connectViewer();
}

function hide_setup(){
}

function connectViewer(){
  console.log("connectViewer")
  var player = getPlayerApi();
  if ( player == null )
    return;
  
  var url = "/stream/"+$("#stream-address").val().replace(/:/g, "_");
  url+="?flash=true&uniqId="+new Date().getTime()
  player.xhrConnect(url)
}

function disconnectViewer(){
  console.log("disconnectViewer")
  var player = getPlayerApi();
  if ( player == null )
    return;

  player.xhrDisconnect()
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

function index_init(){
  $('div').live("pageshow", pageshow);
  $('div').live("pagebeforehide", pagehide);
  $('#viewer').live("pagecreate", viewer_create);
  $('#setup').live("pagecreate", setup_create);
}

$(document).bind("mobileinit", index_init);
