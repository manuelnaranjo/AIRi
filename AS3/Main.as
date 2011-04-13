package{
    import flash.display.Sprite;
    import flash.display.StageScaleMode;
    import flash.display.StageAlign;
    import flash.system.Security;
    import net.aircable.MJPEG;
    import com.flashdynamix.utils.SWFProfiler;
    import flash.events.Event;

    public class Main extends Sprite {
	  private var buffer:MJPEG;

	  public function Main() {
	    super();
	    trace("Version 13 Abr 16:40");
	    Security.allowDomain("*");
	    Security.allowInsecureDomain("*");
	    buffer = new MJPEG(this.root);
	    SWFProfiler.init(stage, this, buffer.socket);
	    addChild(buffer);
      }
    }
}
