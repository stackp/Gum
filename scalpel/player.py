# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import alsaaudio
import threading
from array import array
from  event import Signal
import numpy

class Player(object):
    """Play sound using alsa.

    Public attributes:
       * start
       * end
       * position

    """
    def __init__(self, sound):
        self.set_sound(sound)
        self._playing = False
        self._periodsize = 128
        self._lock = threading.Lock()
        self.start_playing = Signal()
        self.stop_playing = Signal()
        self.position = 0

    def set_sound(self, sound):
        self._sound = sound
        self.start = 0
        self.end = len(sound._data)

    def play(self):
        pcm = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK,
                            mode=alsaaudio.PCM_NORMAL,
                            card='default')
        pcm.setrate(44100)
        pcm.setchannels(2)
        pcm.setformat(alsaaudio.PCM_FORMAT_FLOAT64_LE)
        pcm.setperiodsize(self._periodsize)
        self.position = self.start

        self.start_playing()
        while self._playing:
            if self.position >= self.end:
                self._playing = False
            else:
                start = self.position
                end = min(self.position + self._periodsize, self.end)
                buf = self._sound._data[start:end]
                if self._sound.numchan == 1:
                    # converting mono to stereo
                    buf = numpy.reshape([buf, buf], -1, 2)
                pcm.write(buf)
                self.position = end

        # Closing the device flushes buffered frames.
        pcm.close()
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

    def pause(self):
        self._playing = False


# test
def testPlayer():
    class FakeSound: pass
    
    from math import sin
    SR = 44100
    f0 = 440
    time = 1
    sine = [sin(2 * 3.14 * f0/SR * x) for x in range(time * SR)]
    sound = FakeSound()
    sound._data = sine
    sound.numchan = 1
    
    player = Player(sound)
    player.thread_play().join()

    import pysndfile
    f = pysndfile.sndfile('../sounds/test1.wav')
    data = f.read_frames(f.get_nframes())
    sound._data = data
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

    print ("Two threads will attempt to play simulatneously, you should "
           "hear only one.")
    
    from time import sleep
    t1 = player.thread_play()
    t2 = player.thread_play()
    t1.join()
    t2.join()

    # Testing pause
    print 
    print "Testing pause(): the sound should stop after 0.3 seconds."
    player.thread_play()
    sleep(0.3)
    player.pause()

    # Testing stereo
    f = pysndfile.sndfile('../sounds/test2.wav')
    data = f.read_frames(f.get_nframes())
    sound._data = data
    sound.numchan = 2
    player = Player(sound)
    player.thread_play().join()

if __name__ == '__main__':
    testPlayer()
    print "done"
