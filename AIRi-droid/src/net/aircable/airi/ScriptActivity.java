/*
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

package net.aircable.airi;

import android.app.Activity;
import android.app.ProgressDialog;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.IBinder;
import android.util.Log;

import com.googlecode.android_scripting.Constants;
import com.googlecode.android_scripting.facade.ActivityResultFacade;
import com.googlecode.android_scripting.jsonrpc.RpcReceiverManager;

/**
 * @author Alexey Reznichenko (alexey.reznichenko@gmail.com)
 */
public class ScriptActivity extends Activity {
    private static final String TAG = "AIRiActivity";
    public static final String HIDE_SPLASHSCREEN = "net.aircable.airi.ScriptActivity.HIDE_SPLASHSCREEN";
    
    private ProgressDialog mDialog;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (Constants.ACTION_LAUNCH_SCRIPT_FOR_RESULT.equals(getIntent().getAction())) {
            setTheme(android.R.style.Theme_Dialog);
            setContentView(R.layout.dialog);
            Log.v(TAG, "LAUNCH_SCRIPT_FOR_RESULT");
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
            Log.v(TAG, "NO LAUNCH_SCRIPT_FOR_RESULT");
            boolean from_notification = this.getIntent().getBooleanExtra(ScriptService.FROM_NOTIFICATION, false); 		
            ScriptApplication application = (ScriptApplication) getApplication();
            if (application.readyToStart()) {
                startService(new Intent(this, ScriptService.class));
            }
            if (!from_notification){
                IntentFilter filter = new IntentFilter();
                filter.addAction(HIDE_SPLASHSCREEN);
                this.registerReceiver(new BroadcastReceiver(){
    				@Override
    				public void onReceive(Context context, Intent intent) {
    					if (intent.getAction().equals(HIDE_SPLASHSCREEN)){
    						Log.v(TAG, "Received " + HIDE_SPLASHSCREEN);
    						ScriptActivity.this.unregisterReceiver(this);
    						ScriptActivity.this.mDialog.dismiss();
    						ScriptActivity.this.finish();
    					}
    				}
                	
                }, filter);
            	mDialog = ProgressDialog.show(this, "AIRi", 
                        "AIRi is Loading. Please wait...", true);
            } else
            	this.finish();
        }
    }
}

