# Gum sound editor (https://github.com/stackp/Gum)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from gum.lib import event
from gum.models import Graph, Cursor, Sound, Selection
from gum.controllers import control, player, effect
import os.path
import glob
import imp
import sys

PLUGINS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fx')

# This signal is emitted when a new sound has been loaded. User
# interface should connect to it. Values passed are: Controller,
# Graph, Selection and Cursor instances.
new_sound_loaded = event.Signal()

def open_(filename=None):
    sound = Sound(filename)
    p = player.Player(sound)
    graph = Graph(sound)
    curs = Cursor(graph, p)
    sel = Selection(graph, curs)
    controller = control.Controller(sound, p, graph, sel)
    new_sound_loaded(controller, graph, sel, curs)

def list_effects():
    l = effect.effects.keys()
    l.sort()
    return l

def list_extensions():
    return edit.list_extensions()

def load_all_plugins():
    plugins = glob.glob(os.path.join(PLUGINS_DIR, '*.py'))

    # The plugin may do a relative import
    sys.path.append(PLUGINS_DIR)

    for filename in plugins:
        try:
            execfile(filename, globals())
        except Exception, e:
            print "Error while loading plugin: '%s'" % filename
            print e

    sys.path.remove(PLUGINS_DIR)

load_all_plugins()
