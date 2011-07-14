package net.aircable.airi;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;

import com.googlecode.android_scripting.MainThread;
import com.googlecode.android_scripting.jsonrpc.RpcReceiver;
import com.googlecode.android_scripting.rpc.Rpc;
import com.googlecode.android_scripting.rpc.RpcParameter;
import com.googlecode.android_scripting.facade.FacadeManager;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;

import java.util.Set;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

import android.util.Log;

import com.hexad.bluezime.ImprovedBluetoothDevice;

/**
 * This are a few extra methods needed for AIRi to work facade.
 *
 * @author Naranjo Manuel Francisco <manuel@aircable.net>
 */

public class AIRiFacade extends RpcReceiver {
    private final Service mService;
    private final BluetoothAdapter mBluetoothAdapter;
    private static final String TAG="AIRiFacade";
	private final NotificationManager mNotificationManager;

    public AIRiFacade(FacadeManager manager) {
        super(manager);
        mService = manager.getService();
        mBluetoothAdapter = MainThread.run(manager.getService(), new
            Callable<BluetoothAdapter>() {
                @Override
                public BluetoothAdapter call() throws Exception {
                    return BluetoothAdapter.getDefaultAdapter();    
                }
        });
        String ns = Context.NOTIFICATION_SERVICE;
        mNotificationManager = (NotificationManager) 
				this.mService.getSystemService(ns);
    }

    @Rpc(description = "Tells if a given address is bonded")
    public boolean bluetoothIsBonded(
            @RpcParameter(name="address") String address
    ){
    	int bondstate;
        address = address.toUpperCase();
        BluetoothDevice mDevice = mBluetoothAdapter.getRemoteDevice(address);
        bondstate = mDevice.getBondState();
        Log.v(TAG, "Internal bluetoothIsBondend " + address + " -> " + bondstate);
        return bondstate == BluetoothDevice.BOND_BONDED;
    }

    @Rpc(description = "Try to pair with the given PIN code")
    public boolean bluetoothPair(
        @RpcParameter(name="address") String address,
        @RpcParameter(name="pincode") String pincode
    ) throws IllegalArgumentException, Exception{
        boolean out = false;
        BluetoothDevice mDevice;
        ImprovedBluetoothDevice mImproved;
        PairingListener mListener;
        IntentFilter mIFilter;
        CountDownLatch mLatch;
        int i = 0;
        
        address = address.toUpperCase();
        Log.v(TAG, "Bonding to " + address);
        mDevice = mBluetoothAdapter.getRemoteDevice(address);
        mImproved = new ImprovedBluetoothDevice(mDevice);
        if (mDevice.getBondState() == BluetoothDevice.BOND_NONE){
        	Log.v(TAG, "Not bonded at all bonding");
        	mLatch = new CountDownLatch(1);
        	mListener = new PairingListener( address, mLatch );
            
        	//wait until the pairing request is generated
        	mIFilter = new IntentFilter();
        	mIFilter.addAction(BluetoothDevice.ACTION_BOND_STATE_CHANGED);
        	mService.registerReceiver(mListener, mIFilter);
        	Log.v(TAG, "CreatingBond " + mImproved.createBond());
        	mLatch.await(4, TimeUnit.SECONDS);
        	mService.unregisterReceiver(mListener);
        	Log.v(TAG, "PairingDialog back");
        	Thread.sleep(500);
        	Log.v(TAG, "Sleep done");
        }

        // seems timing is crucial, some logs show that on the first call to
        // setPin BlueZ wasn't ready, so we try over and over until we're done
        // with the bond, just in case we only do this no more than 20 times
        // if the pin code is wrong it seems the OS still lets the user know
        // and sometimes it even pop ups a window to put in the correct code.
        while (mDevice.getBondState() == BluetoothDevice.BOND_BONDING && i < 20){
        	Log.v(TAG, "Bonding state " + mDevice.getBondState());
        	out = mImproved.setPin(pincode);
        	Log.v(TAG, "setPin( " + pincode + " ) -> " + out);
        	if (out)
        		break;
        	Thread.sleep(500);
        	Log.v(TAG, "Sleep");
        	i++;
        }
        return out;
    }
    
    @Rpc(description = "Remove AIRi notification")
    public void airiRemoveNotification() {
    	this.mNotificationManager.cancel(ScriptService.getNotificationID());
    }

    @Rpc(description = "Update AIRi notification")
    public void airiUpdateNotification(
        @RpcParameter(name="text") String text
    ) throws IllegalArgumentException, Exception{
    	Notification notification = ScriptService.
    			createNotification(text, this.mService);
    	int id = ScriptService.getNotificationID();
    	this.mNotificationManager.notify(id, notification);
    	
    }
    
    @Rpc(description = "Call this method when AIRi is ready to hide the splash screen")
    public void airiHideSplashScreen(){
    	Log.v(TAG, "Broadcasting " + ScriptActivity.HIDE_SPLASHSCREEN);
    	Intent intent = new Intent();
    	intent.setAction(ScriptActivity.HIDE_SPLASHSCREEN);
    	this.mService.sendBroadcast(intent);
    }
    
    @Override
    public void shutdown() {
    	airiRemoveNotification();
    }
}

