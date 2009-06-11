#!/usr/bin/env python

# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import app
import gtkui
import sys

def run():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = None

    # FIXME: problem when wrong filename passed from command-line
    app.open_(filename)
    gtkui.main_loop()

if __name__ == "__main__":
    run()
