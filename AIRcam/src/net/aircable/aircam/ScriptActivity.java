/*
 * Copyright (C) 2010-2011 Naranjo Manuel Francisco <manuel@aircable.net>
 * Copyright (C) 2010 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

package net.aircable.aircam;

import net.aircable.aircam.R;
import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.res.Resources;
import android.os.Bundle;
import android.os.IBinder;

import com.googlecode.android_scripting.Constants;
import com.googlecode.android_scripting.FileUtils;
import com.googlecode.android_scripting.Log;
import com.googlecode.android_scripting.facade.ActivityResultFacade;
import com.googlecode.android_scripting.interpreter.InterpreterUtils;
import com.googlecode.android_scripting.jsonrpc.RpcReceiverManager;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;

/**
 * @author Alexey Reznichenko (alexey.reznichenko@gmail.com)
 */
public class ScriptActivity extends Activity {
	public boolean isSame( InputStream input1, InputStream input2 ) throws IOException {
		try {
			byte[] buffer1 = new byte[4096];
			byte[] buffer2 = new byte[4096];
			int numRead1 = 0;
			int numRead2 = 0;
			while (true) {
				numRead1 = input1.read(buffer1);
				numRead2 = input2.read(buffer2);
				if (numRead1 > -1) {
					if (numRead2 != numRead1) return false;
					// Otherwise same number of bytes read
					if (!Arrays.equals(buffer1, buffer2)) return false;
					// Otherwise same bytes read, so continue ...
				} else {
					// Nothing more in stream 1 ...
					return numRead2 < 0;
				}
			}
		} catch (IOException e) {
			throw e;
		} catch (RuntimeException e) {
			throw e;
		}
	}
	
	private boolean needsToBeUpdated(String filename, InputStream content){
		File script = new File(filename);
		FileInputStream fin;
		Log.d("Checking if " + filename + " exists");

		if (!script.exists()){
			Log.d("not found");
			return true;
		}

		Log.d("Comparing file with content");
		try {
			fin = new FileInputStream (filename);
			
			if ( ! isSame(fin, content) ){
				Log.d("There's a difference, updating");
				return true;
			}
		} catch (Exception e) {
			Log.d("Something failed during comparing");
			e.printStackTrace();
			return true;
		}
		
		Log.d("No changes, not updating");
		return false;
	}

	public void copyResourcesToLocal(){
		String name, sFileName;
		InputStream content;
		R.raw a = new R.raw();
		java.lang.reflect.Field[] t = R.raw.class.getFields();
		Resources resources = getResources();
		for (int i = 0; i < t.length; i++){
			try {
				name = resources.getText(t[i].getInt(a)).toString();
				sFileName = name.substring(name.lastIndexOf('/') + 1, name.length());
				content = getResources().openRawResource(t[i].getInt(a));

				// Copies script to internal memory only if changes were made
				sFileName = InterpreterUtils.getInterpreterRoot(this).getAbsolutePath() + "/" + sFileName;
				if (needsToBeUpdated(sFileName, content)){
					Log.d("Copying from stream " + sFileName);
					content.reset();
					Log.d(content.available() + " bytes available");
					FileUtils.copyFromStream(sFileName, content );
				}
			} catch (Exception e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
	}


	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);

		copyResourcesToLocal();

		if (Constants.ACTION_LAUNCH_SCRIPT_FOR_RESULT.equals(getIntent().getAction())) {
			setTheme(android.R.style.Theme_Dialog);
			setContentView(R.layout.dialog);
			ServiceConnection connection = new ServiceConnection() {
				@Override
				public void onServiceConnected(ComponentName name, IBinder service) {
					ScriptService scriptService = ((ScriptService.LocalBinder) service).getService();
					try {
						RpcReceiverManager manager = scriptService.getRpcReceiverManager();
						ActivityResultFacade resultFacade = manager.getReceiver(ActivityResultFacade.class);
						resultFacade.setActivity(ScriptActivity.this);
					} catch (InterruptedException e) {
						throw new RuntimeException(e);
					}
				}

				@Override
				public void onServiceDisconnected(ComponentName name) {
					// Ignore.
				}
			};
			bindService(new Intent(this, ScriptService.class), connection, Context.BIND_AUTO_CREATE);
			startService(new Intent(this, ScriptService.class));
		} else {
			ScriptApplication application = (ScriptApplication) getApplication();
			if (application.readyToStart()) {
				startService(new Intent(this, ScriptService.class));
			}
			finish();
		}
	}

	public void onPause(){

	}

	public void onResume(){

	}
}
