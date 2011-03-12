var address;
var address_;
var slider;

String.prototype.capitalize = function() {
  return this.charAt(0).toUpperCase() + this.slice(1);
}

function createIconText(text, icon, id){
  return $._div({
    'class': 'ui-state-highlight ui-corner-all',
    'id': id,
    })
    ._p()
      ._span_({
        "class": "ui-icon " + icon,
        "style":"float: left; margin-right: .3em;"
      })
      ._span_()
        .text(text)
    .p_()
  .div_()
}

function createDropDown(name, list){
  var output = $._select_({name:name});
  var item;
  $.each(list[name], function(index, val){
    item = $._option_({value: val, id:val}).text(val.capitalize());
    item.appendTo(output);
  })
  output.appendTo("#"+name);
  return output
}

function createSelectable(name, value, capable){
  //not used function, shame on me MN
  value = eval(value.toLowerCase())
  $._input_({ name: name, type: 'hidden', value: "false"}).appendTo("#"+name)
  $._input_({ name: name, type: 'checkbox', checked: value==true, disabled: capable==false, value: "true"}).appendTo("#"+name)
}

function updateExposure(event, ui){
  var seconds = (ui.value)*1/15.
  $("#exposure_text").text(seconds.toPrecision(4)+" secs");
  $("#exposure_form").attr("value", ui.value);
}

function createCheckBox(name, enable){
  $._input_({
    name: name,
    type: 'hidden',
    value: "false",
    id: name+"_disabled",
  }).appendTo("#"+name)

  $._input_({
      name: name,
      id: name+"_enabled",
      type: 'checkbox',
      disabled: enable==false,
      value: "true",
  }).appendTo("#"+name)
  return;
}

function updateConfiguration(){
  $.ajax({
    url: "/api/connected/"+address_,
    datatype: 'json',
    error: function(jqXHR, textStatus, errorThrown){
      $("#loading").hide()
      $("html").empty()
      $(jqXHR.response).appendTo("html")
    },
    success: function(data, textStatus){
      var item;
      $.each(data, function(name, value){
        if (name == "capabilities")
          return;

        if (data['capabilities'][name]==false)
          return;

        switch (name){
          case "capabilities":
            return;
          case "transport":
          case "size":
          case "pan":
            $("#"+name+" #"+value).attr("selected", "selected")
            return
          case "exposure":
            if (data['capabilities'][name])
              slider.slider('value', value)
            return;
          case "battery":
            if (data['capabilities'][name]){
              $("#"+name).addClass("disabled").text(value);
              return;
            }
          case "voice":
          case "flash":
          case "reconnect":
            $("#"+name+"_enabled").attr("checked", value)
            return;
          case "status":
            $("#"+name).text(value==true?"Online":"Offline");
            return;
          case "reconnect_timeout":
            $("#reconnect_timeout").attr("value", value);
            return
          default:
            $("#"+name).text(value);
          }
      })
    }
  })
}

function prepareConfiguration(holder, callback){
  address_= window.location.search.substr(1);
  address = address_.replace(/_/g, ":")

  $("#address_form").attr("value", address);

  slider=$("#exposure").slider({
    min: 0,
    max: 31,
    slide: updateExposure,
    change: updateExposure,
  })
  slider.slider('value',0)
  slider.css({width: "100px"})
  createCheckBox("reconnect", true)

  $.ajax({
    url: "/api/connected/"+address_+"?test=true",
    datatype: 'json',
    error: function(jqXHR, textStatus, errorThrown){
      $("html").empty()
      $(jqXHR.response).appendTo("html")
    },
    success: function(data, textStatus){
      var item;
      if ('error' in data){
        alert("Something went wrong, cause: " + data['error']);
        return
      }

      $.each(data['capabilities'], function(name, value){
        switch(name){
          case "transport":
          case "size":
          case "pan":
            createDropDown(name, data['capabilities'])
            return;
          case "exposure":
            if (value==false){
              slider.slider('disable', false)
              $("#exposure_text").addClass("disabled")
            }
            return;
          case "voice":
          case "flash":
            createCheckBox(name, value)
            return;
          case "battery":
            if (value==false){
              $("#"+name).addClass("disabled").text("Not Supported");
              return;
            }
        }
      })
      if (data['capabilities']['pan']=[]){
        $("#panholder").hide()
        $("#pan >select").addClass("disabled")
        $._option_().text("Not Supported").appendTo("#pan >select");
      }
      $("#loading").hide()
      $(holder).show()

      updateConfiguration();
      if (callback != null)
        callback();
    }
  })
}

function getBrowser(){
  	return navigator.appVersion+'-'+navigator.appName;
}

function prepareMjpeg(){
  $("#video").empty()

  createIconText("You're running Chrome you will not get Audio", "ui-icon-info", "chrome-warning").appendTo("#video")

  $._div_({'id': 'videoholder', 'class': 'ui-widget-content'}).appendTo("#video")

}

function prepareSWF(){
  $("#video").empty()

  $._div_({'id': 'videoholder'}).appendTo("#video");
}

function prepareStream(){
  if (getBrowser().toLowerCase().indexOf("chrome")>-1)
    prepareMjpeg();
  else
    prepareSWF();
}


function enableMjpeg(address){
  $._embed_({
    "id": "video-content",
    "class": "wrapper",
    "width": "100%",
    "height": "100%",
    "src": "/stream/"+address.replace(/:/g, "_")
  }).appendTo("#videoholder")
}

function enableSWF(address){
  $._p()
    ._a_({'href': 'http://www.adobe.com/go/getflashplayer'})
      ._img_({
        'src': 'http://www.adobe.com/images/shared/download_buttons/get_flash_player.gif',
        'alt': 'Get Adobe Flash player'
      })
  .p_().appendTo("#videoholder")

  $("#videoholder").flash({
    swf: "/media/airi.swf",
    style: "width: 100%; height: 100%",
    flashvars : {
      browser: getBrowser(),
      target: address.replace(/:/g, "_"),
    },
    play: "true",
    id: "video-content",
    class: "wrapper"
  })
}

function enableStream(address){
  if (getBrowser().toLowerCase().indexOf("chrome")>-1)
    enableMjpeg(address);
  else
    enableSWF(address);
}
