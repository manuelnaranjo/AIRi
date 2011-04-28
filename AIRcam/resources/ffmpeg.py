# -*- coding: utf-8 -*-
import sys, os, time
from fcntl import fcntl, F_GETFL, F_SETFL
from subprocess import Popen, PIPE
from multiprocessing import Process, Pipe, Value
import android
droid = android.Android()

def ffmpeg_push_thread(fps, pipe, running, buffer_file):
    droid = android.Android()
    last_frame = None
    droid.log("Starting pushing thread at %s fps" % fps)
    try:
	while not running.poll():
    	    time.sleep(1.0/(fps*2))
    	    time.sleep(1.0/(fps*2))
    	    droid.log("%s ffmpeg_push_thread tick" % time.time())
    	    if pipe.poll():
    		last_frame=pipe.recv_bytes()
    	    if last_frame:
    		buffer_file.write(last_frame)
	droid.log("Stopping pushing thread")
    except Exception, err:
	droid.log(str(err))

class ffmpeg(object):
    output_path = None
    ffmpeg_path = None
    droid = None
    FILES_PATH = '/data/data/net.aircable.aircam/files'
    BUFFER_PATH= '/tmp/aircam_buffer.jpg'
    ffmpeg_process = None
    buffer_file = None
    last_frame = None
    push_thread = None
    _running = False
    _running_p = None

    def __init__(self, output_path='/storage/Video/aircam/', ffmpeg_path='/tmp'):
	self.output_path=output_path or '%s/Video/aircam/' % os.environ['EXTERNAL_STORAGE']
	self.ffmpeg_path=ffmpeg_path or '/tmp'
	droid.log("sanitizing ffmpeg")
	os.system('cp %s/ffmpeg.amr %s/ffmpeg' % (self.FILES_PATH, self.ffmpeg_path))
	os.system('chmod 777 %s/ffmpeg' % self.ffmpeg_path)
	os.system('rm -rf %s' % self.BUFFER_PATH)
	os.system('mknod %s p' % self.BUFFER_PATH)
	os.system('mkdir -p %s' % self.output_path)
	droid.log(self.output_path)
	droid.log(self.ffmpeg_path)
	droid.log("sanitizing done")

    def start_recording(self, fps=25, path=None, name=None):
	if self._running:
	    raise RuntimeException("I can't record more than one video at the same time!")

	fps = float(fps)
	if not fps or fps <= 0:
	    raise RuntimeException("not valid FPS")

	self.last_frame = None
	path = path or self.output_path
	name = name or '%s.mp4' % time.strftime('%m%d%Y-%H%M%S')
	self.name = '%s/%s' % (path, name)
	args = [ '%s/ffmpeg' % self.ffmpeg_path,
	    '-v', '9',
	    '-r', str(fps),
	    #'-isync', '-re',
	    '-vsync', '0',
	    '-f', 'image2pipe',
	    '-i', self.BUFFER_PATH,
	    #'-sameq', '-an',
	    '-r', str(fps),
	    '-y', self.name]
	droid.log("%s" % args)
	self.ffmpeg_process=Popen(args,  stdout=PIPE, stderr=PIPE)
	droid.log("process started")
	time.sleep(1./10)
	self.ffmpeg_process.poll()
	if self.ffmpeg_process.returncode:
	    droid.log("ffmpeg stopped: %s" % self.ffmpeg_process.returncode)
	    droid.log(self.ffmpeg_process.stdout.read())
	    droid.log(self.ffmpeg_process.stderr.read())
	    self.ffmpeg_process = None

	droid.log("opening buffer")
	self.buffer_file = open(self.BUFFER_PATH, 'wb')
	droid.log("buffer opened")
#	flags = fcntl(self.buffer_file.fileno(), F_GETFL)
#	fcntl(self.buffer_file.fileno(), F_SETFL, flags | os.O_NONBLOCK)

	droid.log("starting thread")
	self._running=True
	self.push_pipe1, self.push_pipe = Pipe(False)
	self._running_p = Pipe(False)
	self.push_thread = Process(target=ffmpeg_push_thread, 
		args=(fps, self.push_pipe1, self._running_p[0], self.buffer_file))
	self.push_thread.daemon = True
	self.push_thread.start()
	droid.log("thread started: %s" % self.push_thread.is_alive())

    def stop_recording(self):
	if not self._running:
	    return

	self._running=False
	self._running_p[1].send_bytes("False")
	self.push_thread.join()
	self.push_thread = None
	self.buffer_file.flush()
	self.buffer_file.close()
	self.buffer_file = None
	self.ffmpeg_process.wait()
	self.push_pipe.close()
	self.push_pipe1.close()
	for p in self._running_p: p.close()
	droid.log("encoding completed: %s" % self.ffmpeg_process.returncode)
	droid.log(str(self.ffmpeg_process.stdout.read()))
	droid.log(str(self.ffmpeg_process.stderr.read()))
	droid.makeToast("%s created" % self.name)
	self.ffmpeg_process = None

    def push_frame(self, new_frame):
	if not self._running:
	    return
	droid.log("ffmpeg push_frame")
	self.push_pipe.send_bytes(new_frame)

