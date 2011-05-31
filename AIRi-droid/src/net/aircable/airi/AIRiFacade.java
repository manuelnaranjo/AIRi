package net.aircable.airi;

import android.app.Service;
import android.content.SharedPreferences;
import android.content.SharedPreferences.Editor;
import android.preference.PreferenceManager;

import com.googlecode.android_scripting.MainThread;
import com.googlecode.android_scripting.jsonrpc.RpcReceiver;
import com.googlecode.android_scripting.rpc.Rpc;
import com.googlecode.android_scripting.rpc.RpcOptional;
import com.googlecode.android_scripting.rpc.RpcParameter;
import com.googlecode.android_scripting.facade.FacadeManager;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;

import java.io.IOException;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.Callable;

/**
 * This are a few extra methods needed for AIRi to work facade.
 *
 * @author Naranjo Manuel Francisco <manuel@aircable.net>
 */

public class AIRiFacade extends RpcReceiver {
    private Service mService;
    private BluetoothAdapter mBluetoothAdapter;
    
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
    }

    @Rpc(description = "Tells if a given address is bonded")
    public boolean bluetoothIsBonded(
            @RpcParameter(name="address") String address
    ){
        address = address.toLowerCase();
        Set<BluetoothDevice> devices =
            mBluetoothAdapter.getBondedDevices();
        for (BluetoothDevice e: devices){
            if (e.getAddress().toLowerCase().equals(address))
                    return true;
        }
        return false;
    }

    @Override
    public void shutdown() {
    }
}

