package net.aircable{
	import flash.display.DisplayObject;
	import net.aircable.XHRMultipart;
	import net.aircable.XHRMultipartEvent;

	public class Media {
		public var mjpeg: MJPEG;
		public var sco: SCO;
		public var socket: XHRMultipart;

		private function onData(event:XHRMultipartEvent): void {
			trace("onData");
			if (event.getMime().indexOf("image")> -1)
				mjpeg.loadBytes(event.getData());
			if (event.getMime().indexOf("application/octet-stream")>-1)
				sco.handleFrame(event.getData());
		}

		public function Media(root:DisplayObject) {
			trace("new Media");
			super();
			socket = new XHRMultipart(root);
			socket.addEventListener(XHRMultipartEvent.GOT_DATA, onData); 
			mjpeg = new MJPEG(root);
			sco = new SCO();
		}
	}
}

