# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import event
import edit
import player
import graphmodel
import selection
import cursor
import control
import effect
import os.path

# This signal is emitted when a new sound has been loaded. User
# interface should connect to it. Values passed are: Controller,
# Graph, Selection and Cursor instances.
new_sound_loaded = event.Signal()

def open_(filename=None):
    sound = edit.Sound(filename)
    p = player.Player(sound)
    graph = graphmodel.Graph(sound)
    curs = cursor.Cursor(graph, p)
    sel = selection.Selection(graph, curs)
    controller = control.Controller(sound, p, graph, sel)
    new_sound_loaded(controller, graph, sel, curs)

def list_effects():
    l = effect.effects.keys()
    l.sort()
    return l

def list_extensions():
    return edit.list_extensions()
