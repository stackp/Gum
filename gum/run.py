#!/usr/bin/env python

# Gum sound editor (https://github.com/stackp/Gum)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from gum import app
from gum.views import ui
import sys

def run():

    # Open files passed on the command line.
    opened = False
    for filename in sys.argv[1:]:
        try:
            app.open_(filename)
            opened = True
        except Exception, e:
            ui.display_error("Error", str(e))

    # Load an empty sound if no file was open.
    if not opened:
        app.open_()

    ui.main_loop()

if __name__ == "__main__":
    run()
