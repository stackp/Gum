"""Gum Audio Editor

Gum is a simple audio editor for Linux, with a GTK frontend and an
ALSA backend.

"""

from os.path import abspath, dirname, join
from constants import __version__, __url__

basedir = dirname(abspath(__file__))
datadir = join(basedir, 'data')
testdir = join(datadir, 'test')
logofile = join(datadir, 'gum-128.png')
