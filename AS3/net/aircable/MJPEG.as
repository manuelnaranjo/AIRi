package net.aircable{
    import flash.display.Loader;
    import flash.display.DisplayObject;
    import flash.display.StageScaleMode;
    import flash.display.StageAlign;
    import net.aircable.XHRMultipart;
    import net.aircable.XHRMultipartEvent;
    import flash.external.ExternalInterface;
    import flash.events.Event;

    public class MJPEG extends Loader {
      public var socket: XHRMultipart;
      private var flag: Boolean = true;

      private function onComplete(e: Event): void{
        trace("onComplete", this.content.height, this.content.width, this.height, this.width, stage.stageHeight, stage.stageWidth);
        this.content.x=0;
        this.content.y=0;
        if (stage.stageHeight > 0)
          this.content.height=stage.stageHeight;
        else
          this.height=this.content.height;

        if (this.height == 0)
          this.height = stage.stageHeight;

        if (stage.stageWidth > 0)
          this.content.width=stage.stageWidth;
        else
          this.width=this.content.width;

        if (this.width == 0)
          this.width = stage.stageWidth;
	  }

      private function onImage(event:XHRMultipartEvent): void {
        trace("onImage");
	    if (event.getMime().indexOf("image")> -1)
	      loadBytes(event.getData());
      }

  	  public function MJPEG(root:DisplayObject, uri: String=null) {
	    super();
	    socket = new XHRMultipart(root, uri);
	    socket.addEventListener(XHRMultipartEvent.GOT_DATA, onImage);
        contentLoaderInfo.addEventListener(Event.COMPLETE, onComplete, false, 0, true);
	  }
    }
}
