"""Scalpel Audio Editor

Scalpel is an audio editor for Linux written in Python_. It aims at
providing a simple-to-use and easy-to-extend audio editor. Sound
hackers, get started translating your Matlab routines into
Python/Numpy functions!

Scalpel uses PyGTK_ for the user interface, Numpy_ for the internal
processing, ALSA_ for the audio playing and libsndfile_ for reading
and writing files. A minimal part of the code is written in Cython_
for better performance.

Scalpel still has some rough edges but is quite usable. Try it now and
be sure to send your feedback. Installing is as easy as (see
http://scalpelsound.online.fr/?page_id=457 for more details)::

    pip install scalpel

Scalpel is released under the BSD License.

Links:

* Homepage: http://scalpelsound.online.fr
* Source: http://gitorious.org/scalpel
* Pypi: http://pypi.python.org/pypi/scalpel

.. _Python: http://www.python.org
.. _PyGTK: http://www.pygtk.org
.. _Numpy: http://numpy.scipy.org
.. _ALSA: http://www.alsa-project.org
.. _libsndfile: http://www.mega-nerd.com/libsndfile
.. _Cython: http://www.cython.org

"""

from constants import __version__

__docformat__ = 'restructuredtext'
