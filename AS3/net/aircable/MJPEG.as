package net.aircable{
    import flash.display.Loader;
    import flash.display.DisplayObject;
    import flash.display.StageScaleMode;
    import flash.display.StageAlign;
    import net.aircable.XHRMultipart;
    import net.aircable.XHRMultipartEvent;
    import flash.external.ExternalInterface;
    import flash.events.Event;
    import flash.utils.ByteArray;

    public class MJPEG extends Loader {
		private var flag: Boolean = true;
		private var last_height: int = 0;
		private var last_width: int = 0;

		public function reset(): void {
			flag = true;
			this.height = 0;
			this.width = 0;
			if (stage){
				stage.stageHeight = 0;
				stage.stageWidth = 0;
			}
		}

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

			if (ExternalInterface.available)
				if ( last_width != contentLoaderInfo.width || last_height != contentLoaderInfo.height ){
					ExternalInterface.call("viewerResize", 
						this.contentLoaderInfo.width,
						this.contentLoaderInfo.height);
					last_width = this.contentLoaderInfo.width;
					last_height = this.contentLoaderInfo.height;
					flag = false;
				}
		}
		
		private function externalImage(data:ByteArray): void {
			trace("onExternalImage");
			loadBytes(data);
	    }

		public function MJPEG(root:DisplayObject) {
			super();
			contentLoaderInfo.addEventListener(Event.COMPLETE, onComplete, false, 0, true);
			if (ExternalInterface.available){
				trace("ExternalInterface is available");
				ExternalInterface.addCallback("resetSize", reset);
				ExternalInterface.addCallback("showImage", externalImage); 
				ExternalInterface.call("viewerReady");
			}
		}
    }
}

