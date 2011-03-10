package net.aircable {
  import flash.errors.*;
  import flash.events.*;
  import flash.net.URLRequest;
  import flash.net.URLRequestMethod;
  import flash.net.URLRequestHeader;
  import flash.net.URLStream;
  import flash.utils.ByteArray;
  import flash.utils.Dictionary;
  import flash.system.Security;
  import flash.display.DisplayObject;
  import mx.utils.Base64Encoder;
  import flash.external.ExternalInterface;
  import net.aircable.XHRMultipartEvent;

  public class XHRMultipart extends EventDispatcher{
    private var uri: String;
    private var username: String;
    private var password: String;
    private var stream: URLStream;
    private var buffer: ByteArray;
    private var sbuffer: String;
    private var pending: int;
    private var flag: Boolean;
    private var type: String;
    private var browser: String;
    private var headers: Object = {};

    private function connect(): void {
      stream = new URLStream();
      trace("connect")
      var request:URLRequest = new URLRequest(uri);
      request.method = URLRequestMethod.POST;
      request.contentType = "multipart/x-mixed-replace";
      configureListeners();
      try {
        trace("connecting");
        stream.load(request);
        trace("connected")
      } catch (error:Error){
	    trace("Unable to load requested resource");
      }
      this.pending = 0;
      this.flag = false;
      this.buffer = new ByteArray();
    }

    public function XHRMultipart(
          root: DisplayObject,
          uri: String = null, 
          username: String = null, 
          password: String = null){
      trace("XHRMultipart()");
      var v : String = root.loaderInfo.parameters.browser;
      trace(v);
      if (v){
        v=v.toLowerCase();
        if (v.indexOf("chrome") > -1){
    	    browser="chrome";
        } else if (v && v.indexOf("safari") > -1){
    	    browser="safari";
        }
        else {
    	    browser=null;
        }
      }

      trace(browser);

      if (uri == null){
        if (root.loaderInfo.parameters.target)
          uri = "/stream/"+root.loaderInfo.parameters.target;
        else if (root.loaderInfo.parameters.uri)
          uri = root.loaderInfo.parameters.uri
        else
          uri = "/stream/";
      }
      this.uri = uri;
      ExternalInterface.addCallback("xhrConnect", connect);
      ExternalInterface.addCallback("xhrDisconnect", disconnect);
      connect();
      
    }


    private function configureListeners(): void{
      stream.addEventListener(Event.COMPLETE, completeHandler, false, 0, true);
      stream.addEventListener(HTTPStatusEvent.HTTP_STATUS, httpStatusHandler, false, 0, true);
      stream.addEventListener(IOErrorEvent.IO_ERROR, ioErrorHandler, false, 0, true);
      stream.addEventListener(Event.OPEN, openHandler, false, 0, true);
      stream.addEventListener(ProgressEvent.PROGRESS, progressHandler, false, 0, true);
      stream.addEventListener(SecurityErrorEvent.SECURITY_ERROR, securityErrorHandler, false, 0, true);
    }

    private function propagatePart(out: ByteArray, type: String): void{
	  trace("found " + out.length + " mime: " + type);
	  dispatchEvent(new XHRMultipartEvent(XHRMultipartEvent.GOT_DATA, true, false, out, type));
    }

    private function readLine(): String {
      var temp: String;
      var flag: Boolean = false;
      var out: String;

      while (true){
        if (stream.bytesAvailable == 0)
    	  break;
	    
        temp = stream.readUTFBytes(1);
        if (temp == "\r")
          continue;
        if (temp == "\n"){
          flag = true;
          break;
        }
        sbuffer+=temp;
      }
      out = sbuffer;
      
      if (flag)
        sbuffer = "";
      return out;
    }

    private function extractHeader(): void {
      var line: String;
      var head: Array;
      
      while ( (line=readLine()) != "" ){
        trace(line);
        if ( stream.bytesAvailable == 0)
          return;
        if (line.indexOf('--') > -1)
	  	  continue;

  	    head = line.split(":");
        if (head.length==2)
          headers[head[0].toLowerCase()]=head[1];
	  }

      pending=int(headers["content-size"]);
      type = headers["content-type"];
      if ( pending > 0 && type != null)
        flag = true;
      trace("pending: " + pending + " type: " + type);
    }

    private function firefoxExtract(): void {
      trace("firefoxPrepareToExtract");
      if (stream.bytesAvailable == 0){
        trace("No more bytes, aborting")
        return;
      }
      
      while ( flag == false ) {
        if (stream.bytesAvailable == 0){
          trace("No more bytes, aborting - can't extract headers");
          return;
        }
        extractHeader();
      }

      trace("so far have: " + stream.bytesAvailable);
      trace("we need: " + pending);
      if (stream.bytesAvailable < pending)
        return;

      var output: ByteArray = new ByteArray();
      stream.readBytes(output, 0, pending);
      trace("pushing " + output.bytesAvailable);
      
      readLine();
      propagatePart(output, type);
      headers["content-size"] = "";
      headers["content-type"] = "";
      flag = false;
      pending = 0;
      return;
    }

    private function findImageInBuffer(): void{
  	  if (buffer.length == 0)
        return;

      var temp: ByteArray = new ByteArray();
      var x: int = -1;
      var start: int = -1;
      var end: int = -1;
      for (x=0; x<buffer.length-1; x++){
        buffer.position=x;
        buffer.readBytes(temp, 0, 2);

        // check if we found the start marker
        if (temp[0]==0xff && temp[1]==0xd8){
          start = x;
          break;
        }
      }

      for (x=buffer.length-2; x>=0; x-=1){
        buffer.position=x;
        buffer.readBytes(temp, 0, 2);

        // check if we found end marker
        if (temp[0]==0xff && temp[1]==0xd9){
          end=x;
          break;
        }
      }

      trace("findImageInBuffer, start: " + start + " end: " + end);
      if (start >-1 && end > -1){
        var output: ByteArray = new ByteArray();
        buffer.position=start;
        buffer.readBytes(output, 0 , end-start);
        propagatePart(output, type);
        buffer.position=0; // drop everything
        buffer.length=0;
      }
    }

    private function safariExtract(): void {
      trace("safariExtract()");
      stream.readBytes(buffer, buffer.length);
      findImageInBuffer();
    }

    private function chromeExtract(): void {
      trace("chromeExtract()");
      stream.readBytes(buffer, buffer.length);
      findImageInBuffer();
    }

    private function extractImage(): void {
      trace("extractImage");

      if (browser == null) firefoxExtract();
      else if (browser == "safari") safariExtract();
      else if (browser == "chrome") chromeExtract();
    }

    private function completeHandler(event:Event):void {
      trace("completeHandler: " + event);
    }

    private function openHandler(event:Event):void {
      trace("openHandler: " + event);
      sbuffer = "";
    }
    
    private function disconnect(): void{
      trace("disconnect()");
      stream.close();
    }

    private function progressHandler(event:ProgressEvent):void {
      trace("progressHandler: " + event)
      trace("available: " + stream.bytesAvailable);
      extractImage();
      if (event.type == ProgressEvent.PROGRESS)
        if (event.bytesLoaded > 1048576) { //1*1024*1024 bytes = 1MB
          trace("transfered " + event.bytesLoaded +" closing")
          disconnect();
          connect();
	    }
    }

    private function securityErrorHandler(event:SecurityErrorEvent):void {
      trace("securityErrorHandler: " + event);
    }

    private function httpStatusHandler(event:HTTPStatusEvent):void {
      trace("httpStatusHandler: " + event);
      trace("available: " + stream.bytesAvailable);
      extractImage();
    }

    private function ioErrorHandler(event:IOErrorEvent):void {
      trace("ioErrorHandler: " + event);
    }
  }
};

