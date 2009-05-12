# Scalpel sound editor (http://stackp.online.fr/?p=48)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Python Software Foundation License
# (http://www.python.org/psf/license/)

import alsaaudio
import threading
from array import array
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
        self._pcm = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK,
                                  mode=alsaaudio.PCM_NORMAL,
                                  card='default')
        self._pcm.setrate(44100)
        self._pcm.setchannels(2)
        self._pcm.setformat(alsaaudio.PCM_FORMAT_FLOAT64_LE)
        self._pcm.setperiodsize(self._periodsize)
        self._lock = threading.Lock()

    def set_sound(self, sound):
        self._sound = sound
        self.start = 0
        self.end = len(sound._data)

    def play(self):

        # Reentrancy: only one thread is allowed to play at the same
        # time. An attempt to play while a thread is already playing
        # will return immediatly.
        if not self._lock.acquire(False):
            return

        # FIXME: self.stop() might have been called before!
        self._playing = True

        position = self.start
        while self._playing:
            if position > self.end:
                self._playing = False
            else:
                start = position
                end = position + self._periodsize
                buf = self._sound._data[start:end]
                if self._sound.numchan == 1:
                    # converting mono to stereo
                    buf = numpy.reshape([buf, buf], -1, 2)
                self._pcm.write(buf)
                position = end

        self._playing = False # useless ?
        self._lock.release()

    def thread_play(self):
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
    player.play()

    import pysndfile
    f = pysndfile.sndfile('sounds/test1.wav')
    data = f.read_frames(f.get_nframes())
    sound._data = data
    player.set_sound(sound)
    player.play()
    player.play()

    # Testing position
    player.start = 40000
    player.play()
    player.start = 0

    # Test reentrancy
    print ("Two threads will try to play at the same time, you should "
          "hear only one.")
    
    from time import sleep
    t1 = player.thread_play()
    sleep(0.5)
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
    f = pysndfile.sndfile('sounds/test2.wav')
    data = f.read_frames(f.get_nframes())
    sound._data = data
    sound.numchan = 2
    player = Player(sound)
    player.play()

if __name__ == '__main__':
    testPlayer()
    print "done"
