# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import edit
import player
import graphmodel
import selection
import cursor
import control
import gtkui
import os.path

def open_(filename=None):
    # FIXME: problem when wrong filename passed from command-line
    sound = edit.Sound(filename)
    p = player.Player(sound)
    graph = graphmodel.Graph(sound)
    sel = selection.Selection(graph)
    curs = cursor.Cursor(graph, p, sel)
    controller = control.Controller(sound, p, graph, sel)
    win = gtkui.MainWindow(controller, graph, sel, curs)
    if filename:
        win.filedialog.filename = os.path.abspath(filename)
