#!/usr/bin/env python

from gtkui import MainWindow
from control import UIController
from graphdata import GraphData, Selection
from player import Player
import gtk
gtk.gdk.threads_init()

if __name__ == "__main__":
    player = Player()
    graphdata = GraphData()
    selection = Selection(graphdata)
    ui_ctrl = UIController(player, graphdata)
    win = MainWindow(ui_ctrl, graphdata, selection)
    win.resize(700, 500)
    win.show_all()
    gtk.main()

