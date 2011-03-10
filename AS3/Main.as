package{
    import flash.display.Sprite;
    import flash.display.StageScaleMode;
    import flash.display.StageAlign;
    import net.aircable.MJPEG;
    import com.flashdynamix.utils.SWFProfiler;
    import flash.events.Event;

    public class Main extends Sprite {
	  private var buffer:MJPEG;

	  public function Main() {
	    super();
	    trace("Version 3 Mar 11:00");
	    buffer = new MJPEG(this.root);
	    SWFProfiler.init(stage, this, buffer.socket);
	    addChild(buffer);
      }
    }
}
