package net.aircable{
	import flash.errors.EOFError; 
	import flash.events.SampleDataEvent; 
	import flash.media.Sound; 
	import flash.media.SoundChannel; 
	import flash.utils.ByteArray; 
	import flash.utils.Endian; 
	import flash.utils.getTimer;
	import flash.external.ExternalInterface;

	public class SCO {
		/**
		 * This class will is in charge of passing SCO audio into the 
		 * flash component. SCO audio comes coded as 16 bits Big Endian.
		 * Based on: http://goo.gl/depYW
		 */
		private var buffer:ByteArray; 
		private var sound:Sound;
		private var maxAmplitude:int;
		private var sound_channel:SoundChannel;
		private var lastPosition: int;

		public function SCO() {
			trace("new SCO");
			buffer = new ByteArray();
			//buffer.endian = Endian.BIG_ENDIAN;
			lastPosition = 0;
			maxAmplitude = 1 << 15;
			if (ExternalInterface==null)
				return;
			ExternalInterface.addCallback("scoConnect", createSound);
			ExternalInterface.addCallback("scoDisconnect", destroySound);
		}

		private function createSound(): void {
			trace("createSound");
			if (sound!=null)
				destroySound();
			buffer.clear()
			lastPosition=0;
			sound = new Sound();
			sound.addEventListener(SampleDataEvent.SAMPLE_DATA, 
				onSampleData);
			sound_channel = sound.play(); 
		}
		
		public function destroySound(): void {
			trace("destroySound");
			if (sound == null)
				return;
			sound.removeEventListener(SampleDataEvent.SAMPLE_DATA, 
				onSampleData);
			sound_channel.stop();
			sound = null;
		}

		public function handleFrame(data:ByteArray): void{
			/**
			 * Function called when ever there's more data that 
			 * needs to be pushed into our buffer
			 */
			//data.endian = Endian.BIG_ENDIAN;
			if (sound == null)
				return;
			
			data.readBytes(buffer, buffer.length);
			trace("SCO::handleFrame " + lastPosition + " " + 
				buffer.length + " " + buffer.position);
		}

		private function onSampleData(evt:SampleDataEvent):void {
			//trace('SCO::onSample ' + lastPosition+ " " + buffer.length); 
			evt.data.endian = Endian.BIG_ENDIAN;
			var samples: int = 0;
			var amplitude:int = 0;
			var sample: Number;
			if (buffer.length - lastPosition >= 2000) { 
				// drop some frames
				trace("SCO:: dropping");
				buffer.position = buffer.length-1000;
			} else 
				buffer.position = lastPosition
			trace('SCO::onSample ' + buffer.bytesAvailable);
			while(buffer.bytesAvailable>0 && samples < 4096) {
				amplitude = buffer.readShort();
				sample = amplitude / maxAmplitude;
				//trace("" + amplitude+ " " +sample);
				// SCO is 8000 Hz Mono
				// Flash is 44100 Hz Stereo
				// Conversion needs 5 samples of SCO to match frequency
				// And *2 samples to match stereo
				evt.data.writeFloat(sample);
				evt.data.writeFloat(sample);
				evt.data.writeFloat(sample);
				evt.data.writeFloat(sample);
				evt.data.writeFloat(sample);
				evt.data.writeFloat(sample);
				evt.data.writeFloat(sample);
				evt.data.writeFloat(sample);
				evt.data.writeFloat(sample);
				evt.data.writeFloat(sample);
				samples+=10;
			}
			while (samples < 4096) {
				evt.data.writeFloat(sample);
				evt.data.writeFloat(sample);
				samples+=2;
			}
			trace("Sent " + samples+" pending " + buffer.bytesAvailable);
			lastPosition=buffer.position;
			buffer.position = buffer.length;
			
		}
    }
}

