# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import alsaaudio
import threading
from  event import Signal
import numpy

class AlsaBackend(object):
    def __init__(self, rate=44100):
        self._pcm = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK,
                            mode=alsaaudio.PCM_NORMAL,
                            card='default')
        self._pcm.setchannels(2)
        self._pcm.setformat(alsaaudio.PCM_FORMAT_FLOAT64_LE)
        self.set_samplerate(rate)
        # alsaaudio.PCM.setperiodsize() does not work but it
        # returns the actual period size.
        self.periodsize = self._pcm.setperiodsize(128)

    def set_samplerate(self, rate):
        self._pcm.setrate(rate)

    def write(self, buf):
        if buf.ndim == 1:
            # converting mono to stereo
            buf = numpy.array([buf, buf]).transpose()
        if 0 < len(buf) < self.periodsize: # FIXME: wrong
            # zero padding to flush the ALSA buffer
            padlen = self.periodsize - len(buf)
            padding = numpy.zeros((padlen, buf.ndim))
            buf = numpy.concatenate((buf, padding))
        buf = buf.tostring()
        self._pcm.write(buf)
        

class Player(object):
    """Play sound using alsa.

    """
    def __init__(self, sound):
        self._playing = False
        self._lock = threading.Lock()
        self.start_playing = Signal()
        self.stop_playing = Signal()
        self.position = 0
        self._backend = AlsaBackend()
        self.set_sound(sound)

    def set_sound(self, sound):
        self._sound = sound
        self.start = 0
        self.end = len(sound.frames)
        self._backend.set_samplerate(self._sound.samplerate)

    def play(self):
        self.position = self.start
        self.start_playing()
        try:
            while self._playing:
                if self.position >= self.end:
                    self._playing = False
                else:
                    start = self.position
                    end = min(self.position + self._backend.periodsize, 
                              self.end)
                    buf = self._sound.frames[start:end]
                    self.position = end
                    self._backend.write(buf)
        finally:
            self.stop_playing()
            self._lock.release()

    def thread_play(self):
        # Only one thread at a time can play. If a thread is already
        # playing, stop it before creating a new thread.
        self._playing = False
        self._lock.acquire()
        self._playing = True
        t = threading.Thread(target=self.play, args=())
        t.start()
        return t

    def stop(self):
        self._playing = False


# test
def testPlayer():
    from mock import Mock
    from math import sin
    SR = 44100
    f0 = 440
    time = 1
    sine = numpy.array([sin(2 * 3.14 * f0/SR * x) for x in range(time * SR)])
    sound = Mock({"numchan": 1})
    sound.samplerate = 44100
    sound.frames = sine
    
    player = Player(sound)
    player.thread_play().join()

    import pysndfile
    f = pysndfile.sndfile('../sounds/test1.wav')
    data = f.read_frames(f.get_nframes())
    sound.frames = data
    player.set_sound(sound)
    player.thread_play().join()
    player.thread_play().join()

    # Testing position
    player.start = 40000
    player.thread_play().join()
    player.start = 0

    # Test reentrancy
    print ("Two threads will attempt to play at a small interval, you should "
           "hear the first one being interrupted by the second one.")
    
    from time import sleep
    t1 = player.thread_play()
    sleep(0.5)
    t2 = player.thread_play()
    t1.join()
    t2.join()

    print ("Two threads will attempt to play simultaneously, you should "
           "hear only one.")
    
    from time import sleep
    t1 = player.thread_play()
    t2 = player.thread_play()
    t1.join()
    t2.join()

    # Testing stop
    print 
    print "Testing stop(): the sound should stop after 0.3 seconds."
    player.thread_play()
    sleep(0.3)
    player.stop()

    # Testing stereo
    f = pysndfile.sndfile('../sounds/test2.wav')
    data = f.read_frames(f.get_nframes())
    sound = Mock({"numchan": 2})
    sound.samplerate = 44100
    sound.frames = data
    player = Player(sound)
    player.thread_play().join()

if __name__ == '__main__':
    testPlayer()
    print "done"
