package de.mjpegsample;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.TimerTask;

import org.json.JSONException;
import org.json.JSONObject;

import net.aircable.aircam.R;

import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.PowerManager;
import android.view.KeyEvent;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.Window;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import net.aircable.aircam.SL4A;
import de.mjpegsample.MjpegView.MjpegInputStream;
import de.mjpegsample.MjpegView.MjpegView;

public class MjpegSample extends Activity {
	public MjpegView mv;
	public static String URL = "http://127.0.0.1:10000";
	public SL4A API;
	public Handler mHandler = new Handler();
	private UpdateTimeTask mTimer = new UpdateTimeTask(this);
	public boolean prev_state = false;
	private long last_back_press = -1;
	public PowerManager pm;
	public PowerManager.WakeLock wl;
	static final int DIALOG_ABOUT = 1;
	
	private void forcedExit(){
		Context context = getApplicationContext();
		CharSequence text = "SL4A is down, can't go on";
		int duration = Toast.LENGTH_LONG;
		
		Toast toast = Toast.makeText(context, text, duration);
		toast.show();
		this.mTimer.cancel();
		this.mTimer.running=false;
		this.finish();
	}
	
	private void postEvent(String event){
		try {
			this.API.callMethod("postEvent", event);
		} catch (JSONException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			this.forcedExit();
		}
	}
	
	JSONObject doAPICallWithResult(String action, String key){
		JSONObject out = null;
		
		try {
			out = this.API.callMethod(action).getJSONObject(key);
		} catch (JSONException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (Exception e) {
			e.printStackTrace();
			this.forcedExit();
		}
		
		return out;
	}

	private Dialog createAboutDialog(){
		Dialog dialog = new Dialog(this);

		dialog.setContentView(R.layout.about);
		dialog.setTitle(getString(R.string.app_name) + ' ' + getString(R.string.about));

		TextView text = (TextView) dialog.findViewById(R.id.text);
		String out = getString(R.string.app_name) + " version " + getString(R.string.version_number)+"\n";
		out+=getString(R.string.copyright)+"\n";
		out+="Webpage: " + getString(R.string.webpage);
		text.setText(out);
		ImageView image = (ImageView) dialog.findViewById(R.id.image);
		image.setImageResource(R.drawable.logo);
		return dialog;
	}

	
	protected Dialog onCreateDialog(int id) {
	    Dialog dialog;
    	switch(id) {
    		case DIALOG_ABOUT:
    			// do the work to define the pause Dialog
    			dialog = createAboutDialog();
    			break;
    		default:
    			dialog = null;
    	}
	    return dialog;
	}
	
	@Override
	public boolean onCreateOptionsMenu(Menu menu) {
	    MenuInflater inflater = getMenuInflater();
	    inflater.inflate(R.menu.main, menu);
	    return true;
	}
	
	@Override
	public boolean onPrepareOptionsMenu (Menu menu){
		if (this.mv.getPlay()){
			menu.findItem(R.id.menu_play).setEnabled(false);
			menu.findItem(R.id.menu_pause).setEnabled(true);
		} else {
			menu.findItem(R.id.menu_play).setEnabled(true);
			menu.findItem(R.id.menu_pause).setEnabled(false);			
		}
		
		if (this.doAPICallWithResult("bluetoothActiveConnections", "result").length()>0){
			menu.findItem(R.id.menu_disconnect).setEnabled(true);
			menu.findItem(R.id.menu_connect).setEnabled(false);
			
			if (this.isRecording())
				menu.findItem(R.id.menu_record).setTitle(R.string.menu_record_stop);
			else 
				menu.findItem(R.id.menu_record).setTitle(R.string.menu_record_start);
			menu.findItem(R.id.menu_record).setEnabled(true);
		} else {
			menu.findItem(R.id.menu_disconnect).setEnabled(false);
			menu.findItem(R.id.menu_connect).setEnabled(true);
			menu.findItem(R.id.menu_record).setTitle(R.string.menu_record_start);
			menu.findItem(R.id.menu_record).setEnabled(false);
		}
		
		return super.onPrepareOptionsMenu(menu);
	}
	
	private void exit(){
		this.postEvent("aircam_client, exit");
		this.mTimer.cancel();
		this.mTimer.running=false;
		this.finish();
	}
	
	private void disconnect(){
		this.postEvent("aircam_client, disconnect");
	}
	
	private void connect(){
		this.postEvent("aircam_client, connect");
	}
	
	private boolean isRecording(){
		File f = new File("/tmp", "aircam_buffer.mjpeg");
		return f.exists();
	}
	
	private void switchRecord(){
		if (!isRecording())
			this.postEvent("aircam_client, record_start$10");
		else
			this.postEvent("aircam_client, record_stop");
	}
	
	private void about(){
		showDialog(DIALOG_ABOUT);
	}
	
	@Override
	public boolean onOptionsItemSelected(MenuItem item) {
	  switch (item.getItemId()) {
		  case R.id.menu_play:
			  this.mv.setPlay(true);
			  return true;
		  case R.id.menu_pause:
			  this.mv.setPlay(false);
			  return true;
		  case R.id.menu_exit:
			  exit();
			  return true;
		  case R.id.menu_disconnect:
			  this.disconnect();
			  return true;
		  case R.id.menu_connect:
			  this.connect();
			  return true;
		  case R.id.menu_about:
			  this.about();
			  return true;
		  case R.id.menu_record:
			  this.switchRecord();
			  return true;
		  default:
		    return super.onOptionsItemSelected(item);
	  }
	}
	
	public void onCreate(Bundle icicle){
	    super.onCreate(icicle);

	    pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
	    wl = pm.newWakeLock(PowerManager.SCREEN_BRIGHT_WAKE_LOCK
	    		| PowerManager.ON_AFTER_RELEASE, "AIRcam");
	    
	    requestWindowFeature(Window.FEATURE_NO_TITLE);
	    getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, 
                             WindowManager.LayoutParams.FLAG_FULLSCREEN);

	    mv = new MjpegView(this);
	    setContentView(mv);

	    //mv.setSource(MjpegInputStream.read(URL));
	    mv.setDisplayMode(MjpegView.SIZE_BEST_FIT);
	    mv.showFps(true);

	    try{
	    	SL4A sl4a = new SL4A();
	    	sl4a.connect();
	    	this.API = sl4a;
	    }catch(Exception e){}

	    this.mTimer.run();
	}
		
	@Override
	public boolean onKeyDown(int keyCode, KeyEvent event) {
	    if (keyCode == KeyEvent.KEYCODE_BACK){
	    	if (last_back_press==-1){
	    		last_back_press = System.currentTimeMillis();
	    		Context context = getApplicationContext();
	    		CharSequence text = "Keep BACK pressed for 3 seconds to exit";
	    		int duration = Toast.LENGTH_SHORT;
	    		Toast.makeText(context, text, duration).show();
	    	}
	    	return true;
	    }
	    return super.onKeyDown(keyCode, event);
	}
	
	@Override
	public boolean onKeyUp(int keyCode, KeyEvent event) {
	    if (keyCode == KeyEvent.KEYCODE_BACK){
	    	if ( last_back_press!=-1 && System.currentTimeMillis() - last_back_press > 3000 ){
	    		this.exit();
	    		return true;
	    	}
	    	last_back_press = -1;
	    	return true;
	    }
	    return super.onKeyDown(keyCode, event);
	}


	public void onPause() {
		super.onPause();
		mv.stopPlayback();
		this.postEvent("aircam_client, onpause");
		if (this.wl.isHeld())
			this.wl.release();
		this.mTimer.cancel();
		this.mTimer.running=false;
	}
	
	public void onResume() {
		super.onResume();
		this.mTimer.running=true;
		this.mTimer.run();
		this.postEvent("aircam_client, onresume");
	}
}

class UpdateTimeTask extends TimerTask {
	private MjpegSample father;
	public boolean running = true;
	
	public UpdateTimeTask(MjpegSample father){
		this.father = father;
	}
	
	public void run() {
		if (this.running==false)
			return;
		
		if (father.API==null)
			return;
		
		boolean state;
		JSONObject o = father.doAPICallWithResult("bluetoothActiveConnections", "result");
		if (o == null)
			state=false;
		else
			state = o.length()>0;
		father.mv.setRecordingState( state );
		if (state && father.mv.getSource()==null){
			father.mv.stopPlayback();
			father.mv.setSource(MjpegInputStream.read(MjpegSample.URL));
		}
		
		if (state && !father.wl.isHeld())
			father.wl.acquire();
		else 
			if (!state && father.wl.isHeld())
				father.wl.release();
		
		father.mHandler.postDelayed(this, 300);
	}
}
