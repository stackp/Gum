all: _samplerate.so

_samplerate.so: _samplerate.c
	gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing \
            -I/usr/include/python2.5 -I/usr/include/python2.6 \
            -I/usr/include/python2.7 \
            -lsamplerate -o _samplerate.so _samplerate.c

_samplerate.c: _samplerate.pyx
	cython2 _samplerate.pyx

clean:
	rm -f _samplerate.so _samplerate.c
