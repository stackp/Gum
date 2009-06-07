#!/usr/bin/env python

# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import app
import sys
import gobject
import gtk
gtk.gdk.threads_init()

def run():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = None
    gobject.idle_add(app.open_, filename)
    gtk.main()

if __name__ == "__main__":
    run()
