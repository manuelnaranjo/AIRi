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
	import flash.system.LoaderContext;

    public class MJPEG extends Loader {
		private var flag: Boolean = true;
		private var last_height: int = 0;
		private var last_width: int = 0;
		private static const AIRCABLE: String = "AIRcable";
		private var last_date: String = "";

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
			trace("onComplete", this.content.height, this.content.width, 
				this.height, this.width, stage.stageHeight, 
				stage.stageWidth);
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
				if ( last_width != contentLoaderInfo.width || 
						last_height != contentLoaderInfo.height ){
					ExternalInterface.call("viewerResize", 
						this.contentLoaderInfo.width,
						this.contentLoaderInfo.height);
					last_width = this.contentLoaderInfo.width;
					last_height = this.contentLoaderInfo.height;
					flag = false;
				}
		}
		
		private function isAIRcablePicture(data: ByteArray): Boolean {
			if (data[0x14] != 0xff || data[0x15] != 0xe1){
				return false;
			}
			data.position = 0x50;
			var maker: String = data.readUTFBytes(8);
			if (maker!=AIRCABLE)
				return false;
			var address: String = data.readUTFBytes(12);
			data.position+=2;
			var date: String = data.readUTFBytes(20);
			var ffe9: uint = data.readUnsignedShort();
			var length: int = data.readShort();
			var magic: int = data.readShort();
			var temperature: int = data.readShort();
			var grav_x: int = data.readShort();
			var grav_y: int = data.readShort();
			var grav_z: int = data.readShort();
			var compass_x: int = data.readShort();
			var compass_y: int = data.readShort();
			var compass_z: int = data.readShort();
			var ambient: int = data.readShort();
			var batt: int = data.readShort();
			var extra: String = data.readUTFBytes(32);
			if (ffe9 != 0xffe9){
//				trace(ffe9.toString(16));
				return false;
			}
			if (last_date == date) // updates each 5 seconds
				return true;
			last_date = date;
//			trace(maker);
//			trace(address);
//			trace(date);
//			trace(ffe9.toString(16));
//			trace(length);
//			trace(magic.toString(16));
//			trace(temperature);
//			trace(grav_x+","+grav_y+","+grav_z);
//			trace(compass_x+","+compass_y+","+compass_z);
//			trace(ambient);
//			trace(batt);
//			trace(extra);

			if (ExternalInterface == null){
				trace("no external interface");
				return true;
			}

			var sensor: Object = {
				maker: maker,
				address: address,
				date: date,
				magic: magic,
				temperature: temperature,
				gravitation: {
					x: grav_x,
					y: grav_y,
					z: grav_z
				},
				compass: {
					x: compass_x,
					y: compass_y,
					z: compass_z
				},
				ambient: ambient,
				battery: batt,
				extra: extra
			}
			ExternalInterface.call("updateSensorData", sensor);
			return true;
		}

		override public function loadBytes(bytes:ByteArray, 
			context:LoaderContext = null): void {
			trace("isAIRcablePicture " + isAIRcablePicture(bytes));
			bytes.position = 0;
			return super.loadBytes(bytes, context);
		}
		
		private function externalImage(data:ByteArray): void {
			trace("onExternalImage");
			loadBytes(data);
	    }

		public function MJPEG(root:DisplayObject) {
			super();
			contentLoaderInfo.addEventListener(Event.COMPLETE, 
					onComplete, false, 0, true);
			if (ExternalInterface.available){
				trace("ExternalInterface is available");
				ExternalInterface.addCallback("resetSize", reset);
				ExternalInterface.addCallback("showImage", externalImage);
				ExternalInterface.call("viewerReady");
			}
		}
    }
}

