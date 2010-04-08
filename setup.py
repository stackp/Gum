#!/usr/bin/env python

from setuptools import setup, Extension
import scalpel
import os

doclines = scalpel.__doc__.split("\n")
classifiers = """\
Development Status :: 3 - Alpha
Environment :: X11 Applications :: GTK
Intended Audience :: End Users/Desktop
License :: OSI Approved :: BSD License
Natural Language :: English
Operating System :: POSIX :: Linux
Programming Language :: Python
Topic :: Multimedia :: Sound/Audio :: Editors
"""


if not os.path.exists('scalpel/fast/fast.c'):
    import Cython.Compiler.Main
    Cython.Compiler.Main.compile('scalpel/fast/fast.pyx')


setup(name = 'scalpel',
      version = scalpel.__version__,
      description = doclines[0],
      author = 'Pierre',
      author_email = 'stackp@online.fr',
      url = 'http://scalpelsound.online.fr',
      license = "BSD License",
      long_description = "\n".join(doclines[2:]),
      classifiers = filter(None, classifiers.split("\n")),
      packages = ['scalpel'],
      ext_modules = [Extension('scalpel.fast',
                               ['scalpel/fast/fast.c'],
                               libraries=['cairo'])],
      scripts = ['scripts/scalpel'],
      requires = ['PyGTK', 'numpy', 'pyalsaaudio (==0.4)'],
      install_requires = ['pyalsaaudio==0.4']
      )
