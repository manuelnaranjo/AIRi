package net.aircable.airi;

import android.bluetooth.BluetoothDevice;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

import android.util.Log;

import java.util.concurrent.CountDownLatch;

/**
 * A BroadcastReceiver that will let AIRiFacade.bluetoothPair when
 * the bonding process is ready for the pin code to be set.
 *
 * @author Naranjo Manuel Francisco <manuel@aircable.net>
 */

public class PairingListener extends BroadcastReceiver{
    private static final String TAG = "AIRI-ParingDialog";
    private String mAddress;
    private CountDownLatch mLatch;

    public PairingListener(String address, CountDownLatch latch){
        super();
        this.mAddress = address;
        this.mLatch = latch;
    }

    public void onReceive(Context context, Intent intent){
        if (!intent.getAction().equals(
                BluetoothDevice.ACTION_BOND_STATE_CHANGED)) {
            return;
        }

        int bondState = intent.getIntExtra(BluetoothDevice.EXTRA_BOND_STATE,
            BluetoothDevice.ERROR);
        Log.v(TAG, "BOND_STATE_CHANGED " + bondState);
        if (bondState != BluetoothDevice.BOND_BONDING) {
            return;
        }

        BluetoothDevice target = intent.getParcelableExtra(
            BluetoothDevice.EXTRA_DEVICE);
        Log.v(TAG, "BONDING " + target.getAddress());
        if ( target.getAddress().compareToIgnoreCase(mAddress) != 0 ) {
            return;
        }

        this.mLatch.countDown();
    }
}
