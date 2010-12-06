all:
	cython fast.pyx
	gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing \
            -I/usr/include/python2.5 \
            -lcairo -o fast.so fast.c
	if [ ! -e ../fast.so ]; then ln -s fast/fast.so ../; fi

clean:
	rm -f fast.so fast.c
