all:
	cython2 _svf.pyx
	gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing \
            -I/usr/include/python2.5 -I/usr/include/python2.6 \
            -I/usr/include/python2.7 \
            -o _svf.so _svf.c

clean:
	rm -f _svf.so _svf.c
