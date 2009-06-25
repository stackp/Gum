#!/usr/bin/env python

# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import app
import gtkui
import sys

def run():

    # Open files passed on the command line.
    opened = False
    for filename in sys.argv[1:]:
        try:
            app.open_(filename)
            opened = True
        except Exception, e:
            gtkui.display_error("Error", str(e))

    # Load an empty sound if no file was open.
    if not opened:
        app.open_()

    gtkui.main_loop()

if __name__ == "__main__":
    run()
