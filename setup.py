#!/usr/bin/env python

from setuptools import setup, Extension
import gum
import os

doclines = gum.__doc__.split("\n")
classifiers = """\
Development Status :: 4 - Beta
Environment :: X11 Applications :: GTK
Intended Audience :: End Users/Desktop
License :: OSI Approved :: BSD License
Natural Language :: English
Operating System :: POSIX :: Linux
Programming Language :: Python
Topic :: Multimedia :: Sound/Audio :: Editors
"""

c_files = ['gum/fast/fast.c', 'gum/fx/_svf.c']

for path in c_files:
    if not os.path.exists(path):
        import Cython.Compiler.Main
        Cython.Compiler.Main.compile(path[:-2] + '.pyx')


setup(name = 'gum-audio',
      version = gum.__version__,
      description = doclines[0],
      author = 'Pierre',
      author_email = 'stackp@online.fr',
      url = gum.__url__,
      license = "BSD License",
      long_description = "\n".join(doclines[2:]),
      classifiers = filter(None, classifiers.split("\n")),
      packages = ['gum', 'gum.lib',
                  'gum.models', 'gum.controllers', 'gum.views', 
                  'gum.fx'],
      ext_modules = [Extension('gum.fast', ['gum/fast/fast.c'],
                               libraries=['cairo']),
                     Extension('gum.fx._svf', ['gum/fx/_svf.c'])],
      scripts = ['gum/scripts/gum'],
      requires = ['PyGTK', 'numpy', 'pyalsaaudio (>=0.6)',
                  'scikits.samplerate'],
      install_requires = ['pyalsaaudio>=0.6', 'scikits.samplerate']
      )
