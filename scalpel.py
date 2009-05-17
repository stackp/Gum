#!/usr/bin/env python

# Scalpel sound editor (http://stackp.online.fr/?p=48)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Python Software Foundation License
# (http://www.python.org/psf/license/)

from gtkui import MainWindow
from control import Controller
from graphmodel import Graph
from selection import Selection
from player import Player
from edit import Sound
from cursor import Cursor
import sys
import gtk
gtk.gdk.threads_init()

def run():
    sound = Sound()
    player = Player(sound)
    graph = Graph(sound)
    selection = Selection(graph)
    cursor = Cursor(graph, player, selection)
    controller = Controller(sound, player, graph, selection)
    win = MainWindow(controller, graph, selection, cursor)
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        win.display_exception(controller.open)(filename)
        win.filedialog.filename = filename
    gtk.main()

if __name__ == "__main__":
    run()
