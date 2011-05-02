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
    
    private function trc(content: Object): void {
      var a: Date = new Date();
      trace(a.getTime()+" " + content);
    }

    public function connect(uri: String = null): void {
      if (stream != null)
        disconnect();

      if (uri == null){
        uri = this.uri;
      }
      this.uri = uri;

      stream = new URLStream();
      trc("connect " + uri)
      var request:URLRequest = new URLRequest(uri);
      request.method = URLRequestMethod.POST;
      request.contentType = "multipart/x-mixed-replace";
      configureListeners();
      try {
        trc("connecting");
        stream.load(request);
        trc("connected")
      } catch (error:Error){
	    trc("Unable to load requested resource");
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
      trc("XHRMultipart()");
      trc(ExternalInterface.available);
      var v : String = root.loaderInfo.parameters.browser;
      trc(v);
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

      trc(browser);

      ExternalInterface.addCallback("xhrConnect", connect);
      ExternalInterface.addCallback("xhrDisconnect", disconnect);
    }


    private function configureListeners(): void{
      stream.addEventListener(Event.COMPLETE, completeHandler, false, 0, true);
      stream.addEventListener(HTTPStatusEvent.HTTP_STATUS, httpStatusHandler, false, 0, true);
      stream.addEventListener(IOErrorEvent.IO_ERROR, ioErrorHandler, false, 0, true);
      stream.addEventListener(Event.OPEN, openHandler, false, 0, true);
      stream.addEventListener(ProgressEvent.PROGRESS, progressHandler, false, 0, true);
      stream.addEventListener(SecurityErrorEvent.SECURITY_ERROR, securityErrorHandler, false, 0, true);
    }
    
    private function removeListeners(): void{
      stream.removeEventListener(Event.COMPLETE, completeHandler);
      stream.removeEventListener(HTTPStatusEvent.HTTP_STATUS, httpStatusHandler);
      stream.removeEventListener(IOErrorEvent.IO_ERROR, ioErrorHandler);
      stream.removeEventListener(Event.OPEN, openHandler);
      stream.removeEventListener(ProgressEvent.PROGRESS, progressHandler);
      stream.removeEventListener(SecurityErrorEvent.SECURITY_ERROR, securityErrorHandler);
    }
    
    


    private function propagatePart(out: ByteArray, type: String): void{
	  trc("found " + out.length + " mime: " + type);
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
        trc(line);
        if ( stream.bytesAvailable == 0)
          return;
        if (line.indexOf('--') > -1)
	  	  continue;

  	    head = line.split(":");
        if (head.length==2)
          headers[head[0].toLowerCase()]=head[1];
	  }

      pending=int(headers["content-length"]);
      type = headers["content-type"];
      if ( pending > 0 && type != null)
        flag = true;
      trc("pending: " + pending + " type: " + type);
    }

    private function firefoxExtract(): void {
      trc("firefoxPrepareToExtract");
      if (stream.bytesAvailable == 0){
        trc("No more bytes, aborting")
        return;
      }

      while ( flag == false ) {
        if (stream.bytesAvailable == 0){
          trc("No more bytes, aborting - can't extract headers");
          return;
        }
        extractHeader();
      }

      trc("so far have: " + stream.bytesAvailable);
      trc("we need: " + pending);
      if (stream.bytesAvailable < pending)
        return;

      var output: ByteArray = new ByteArray();
      stream.readBytes(output, 0, pending);
      trc("pushing " + output.bytesAvailable);

      readLine();
      propagatePart(output, type);
      headers["content-length"] = "";
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

      trc("findImageInBuffer, start: " + start + " end: " + end);
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
      trc("safariExtract()");
      stream.readBytes(buffer, buffer.length);
      findImageInBuffer();
    }

    private function chromeExtract(): void {
      trc("chromeExtract()");
      stream.readBytes(buffer, buffer.length);
      findImageInBuffer();
    }

    private function extractImage(): void {
      trc("extractImage");

      if (browser == null) firefoxExtract();
      else if (browser == "safari") safariExtract();
      else if (browser == "chrome") chromeExtract();
    }

    private function completeHandler(event:Event):void {
      trc("completeHandler: " + event);
      stream = null;
      connect();
    }

    private function openHandler(event:Event):void {
      trc("openHandler: " + event);
      sbuffer = "";
    }

    public function disconnect(): void{
      trc("disconnect()");
      if ( stream != null){
        try {
          stream.close();
        } catch ( error : Error ){
          trc(error);
        }
        removeListeners();
        stream = null;
      }
    }

    private function progressHandler(event:ProgressEvent):void {
      trc("progressHandler: " + event)
      trc("available: " + stream.bytesAvailable);
      extractImage();
      if (event.type == ProgressEvent.PROGRESS)
        if (event.bytesLoaded > 1048576) { //1*1024*1024 bytes = 1MB
          trc("transfered " + event.bytesLoaded +" closing")
          disconnect();
          connect();
	    }
    }

    private function securityErrorHandler(event:SecurityErrorEvent):void {
      trc("securityErrorHandler: " + event);
      disconnect();
    }

    private function httpStatusHandler(event:HTTPStatusEvent):void {
      trc("httpStatusHandler: " + event);
      trc("available: " + stream.bytesAvailable);
      extractImage();
    }

    private function ioErrorHandler(event:IOErrorEvent):void {
      trc("ioErrorHandler: " + event);
      disconnect();
    }
  }
};

