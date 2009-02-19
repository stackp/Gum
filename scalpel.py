#!/usr/bin/env python

from gtkui import MainWindow
from control import UIController
from graphmodel import Graph, Selection
from player import Player
import gtk
gtk.gdk.threads_init()

if __name__ == "__main__":
    player = Player()
    graph = Graph()
    selection = Selection(graph)
    ui_ctrl = UIController(player, graph, selection)
    win = MainWindow(ui_ctrl, graph, selection)
    win.resize(700, 500)
    win.show_all()
    gtk.main()

