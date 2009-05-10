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
import sys
import os.path
import gtk
gtk.gdk.threads_init()

def run():
    sound = Sound()
    player = Player(sound)
    graph = Graph(sound)
    selection = Selection(graph)
    controller = Controller(sound, player, graph, selection)
    win = MainWindow(controller, graph, selection)
    win.resize(700, 500)
    win.show_all()
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        controller.open(filename)
        win.filedialog.curdir = os.path.dirname(filename)
    gtk.main()

if __name__ == "__main__":
    run()
