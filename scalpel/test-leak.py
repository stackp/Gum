import gc
import sys
import run
import gtkui

def seek_objects(classes=[]):
    gc.set_debug(gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_INSTANCES
                 | gc.DEBUG_OBJECTS | gc.DEBUG_SAVEALL)
    gc.collect()
    oo = gc.get_objects()
    l = []
    for o in oo:
        if hasattr(o, '__class__') and o.__class__ in classes:
            l.append(o)
    return l


if __name__ == "__main__":
    sys.argv[1:] = ['../sounds/test1.wav']
    run.run()

    l = seek_objects([gtkui.EditorPage])
    assert len(l) == 0, "uncollected garbage found : " + str(l)
