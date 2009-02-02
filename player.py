import alsaaudio
import threading
from array import array

class Player(object):

    def __init__(self):
        self._lock = threading.Lock()
        self._playing = False
        self._periodsize = 128
        self._pcm = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK,
                                  mode=alsaaudio.PCM_NORMAL,
                                  card='default')
        self._pcm.setrate(44100)
        self._pcm.setchannels(2)
        self._pcm.setformat(alsaaudio.PCM_FORMAT_FLOAT64_LE)
        self._pcm.setperiodsize(self._periodsize)

    def play(self, data):

        # Reentrancy: only one thread is allowed to play at the same
        # time. An attempt to play while a thread is already playing
        # will return immediatly.
        if not self._lock.acquire(False):
            return

        # FIXME: self.stop() might have been called before!
        self._playing = True

        # FIXME: remove or make an if statement
        data = array('d', data)

        position = 0
        while self._playing:
            if position > len(data):
                self._playing = False
                position = 0
            else:
                start = position
                end = position + self._periodsize
                buf = data[start:end]
                # converting mono to stereo
                a = []
                for frame in buf:
                    a.append(frame)
                    a.append(frame)
                buf = array('d', a)
                self._pcm.write(buf)
                position = end

        self._playing = False # useless ?
        self._lock.release()
        #gobject.timeout_add(ms, fn)

    def thread_play(self, data):
        self._playing = True
        t = threading.Thread(target=self.play, args=(data,))
        t.start()
        return t
            
        
    def pause(self):
        self._playing = False
        
# test
def testPlayer():

    from math import sin
    SR = 44100
    f0 = 440
    time = 1
    sine = [sin(2 * 3.14 * f0/SR * x) for x in range(time * SR)]
    player = Player()
    player.play(sine)

    import pysndfile
    f = pysndfile.sndfile('sounds/test1.wav')
    data = f.read_frames(f.get_nframes())
    player = Player()
    player.play(data)
    player.play(data)

    # Test reentrancy
    print ("Two threads will try to play at the same time, you should "
          "hear only one.")
    
    from time import sleep
    t1 = player.thread_play(data)
    sleep(0.5)
    t2 = player.thread_play(data)
    t1.join()
    t2.join()
    
    # Testing pause
    print 
    print "Testing pause(): the sound should stop after 0.3 seconds."
    player.thread_play(data)
    sleep(0.3)
    player.pause()
        
#    f = pysndfile.sndfile('sounds/test2.wav')
#    data = f.read_frames(f.get_nframes())
#    player = Player(data)
#    player.play()


if __name__ == '__main__':
    testPlayer()
    print "done"
