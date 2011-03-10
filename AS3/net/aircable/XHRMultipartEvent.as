package net.aircable {
  import flash.events.Event;
  import flash.utils.ByteArray;

  public class XHRMultipartEvent extends Event{
    public static const GOT_DATA: String = "multipart-data";

    private var _data: ByteArray;
    private var _mime: String;

    public function XHRMultipartEvent(type: String,
					bubbles:Boolean,
					cancelable: Boolean,
					data: ByteArray=null,
					mime: String=null){
	super(type, bubbles, cancelable);
	  _data = data;
	  _mime = mime
    }
    
    public function getMime(): String {
      return _mime;
    }
    
    public function getData(): ByteArray{
      return _data;
    }

    override public function clone(): Event{
      return new XHRMultipartEvent(type, bubbles, cancelable, _data, _mime);
    }

  }
};
