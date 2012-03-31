# Installation

There are (at least) 3 methods to install Gum. But first, you must install the following dependencies: *python*, *pygtk*, *numpy*, *libsndfile*, *setuptools*, the development files for *python*, *libasound*, *libsamplerate*, *libcairo*, and *gcc*. To install these packages on a Debian or Ubuntu box, type:

    apt-get install python python-gtk2 python-numpy python-setuptools \
            libsndfile1 python-dev libasound2-dev libcairo2-dev \
            libsamplerate0 libsamplerate0-dev gcc

## Method 1: System-wide install with pip

Install pip (on Debian/Ubuntu: `apt-get install python-pip`). Then, type in a terminal:

    su -c "pip install gum-audio"
    gum

To uninstall Gum:

    su -c "pip uninstall gum-audio"

## Method 2: Local install with pip and virtualenv

If you’d rather install Gum in your home directory, you should use pip with virtualenv (`apt-get install python-pip python-virtualenv`). Type (not as root):

    cd $HOME
    virtualenv gummy
    source gummy/bin/activate
    pip install gum
    gum

You can uninstall Gum removing the $HOME/gummy directory.

## Method 3: Manual installation of the development version

You’ll need git, cython and make (`apt-get install git cython make`). Type in a terminal (not as root):

    cd $HOME
    mkdir gummy
    cd gummy
    git clone https://github.com/stackp/Gum.git
    wget http://downloads.sourceforge.net/pyalsaaudio/pyalsaaudio-0.6.tar.gz
    tar xvzf pyalsaaudio-0.6.tar.gz
    cd pyalsaaudio-0.6/
    python setup.py build
    cp build/lib.linux-i686-2.*/alsaaudio.so ../Gum/gum/
    cd ../
    wget http://pypi.python.org/packages/source/s/scikits.samplerate/scikits.samplerate-0.3.3.tar.gz
    tar xvzf scikits.samplerate-0.3.3.tar.gz
    cd scikits.samplerate-0.3.3/scikits/samplerate/
    cython _samplerate.pyx
    gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing             -I/usr/include/python2.5 -I/usr/include/python2.6 -I /usr/include/samplerate            -lsamplerate -o _samplerate.so _samplerate.c
    cd ../../..
    mv scikits.samplerate-0.3.3/scikits/ Gum/gum
    rm -rf scikits.samplerate-0.3.3*
    cd Gum/gum/fast
    make
    cd ../fx
    make
    cd ../..
    ./run

To uninstall Gum, just remove the $HOME/gummy directory.

