#!/usr/bin/env python

from gtkui import MainWindow
from control import UIController
from graphmodel import Graph
from selection import Selection
from player import Player
from edit import Sound
import gtk
gtk.gdk.threads_init()

if __name__ == "__main__":
    sound = Sound()
    player = Player(sound)
    graph = Graph(sound)
    selection = Selection(graph)
    controller = UIController(sound, player, graph, selection)
    win = MainWindow(controller, graph, selection)
    win.resize(700, 500)
    win.show_all()
    gtk.main()
