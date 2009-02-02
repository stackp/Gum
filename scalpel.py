#!/usr/bin/env python

from gtkui import MainWindow
from control import UIController
from graphdata import GraphData
from player import Player
import gtk
gtk.gdk.threads_init()

if __name__ == "__main__":
    player = Player()
    graphdata = GraphData()
    ui_ctrl = UIController(player, graphdata)
    win = MainWindow(ui_ctrl, graphdata)
    win.resize(700, 500)
    win.show_all()
    gtk.main()

