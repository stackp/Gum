# Installation

There are (at least) 3 methods to install Gum. But first, you must install the following dependencies: *python*, *pygtk*, *numpy*, *libsndfile*, *setuptools*, the development files for *python*, *libasound*, *libsamplerate*, *libcairo*, and *gcc*. To install these packages on a Debian or Ubuntu box, type:

    apt-get install python python-gtk2 python-numpy python-setuptools \
            libsndfile1 python-dev libasound2-dev libcairo2-dev \
            libsamplerate0 libsamplerate0-dev gcc

## Method 1: System-wide install with pip

Install pip (on Debian/Ubuntu: `apt-get install python-pip`). Then, type in a terminal:

    sudo pip install gum-audio
    gum

To uninstall Gum:

    sudo pip uninstall gum-audio

## Method 2: Local install with pip and virtualenv

If you’d rather install Gum in your home directory, you should use pip with virtualenv (`apt-get install python-pip python-virtualenv`). Type (not as root):

    cd $HOME
    virtualenv gummy
    source gummy/bin/activate
    pip install gum-audio
    gum

You can uninstall Gum removing the $HOME/gummy directory.

## Method 3: Manual installation of the development version

You’ll need git, cython and make (`apt-get install git cython make`). Type in a terminal (not as root):

    git clone https://github.com/stackp/Gum.git
    cd Gum
    ./build.sh
    ./run

To uninstall Gum, just remove the $HOME/gummy directory.

