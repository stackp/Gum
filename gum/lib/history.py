class Action(object):
    """Describes an action, and a way to revert that action"""
     
    def __init__(self, do, undo):
        """do and undo are tuples in the form (fun, args) where fun is a
        function and args contains the arguments"""
        self._do = do
        self._undo = undo

    def do(self):
        fun, args = self._do
        return fun(*args)

    def undo(self):
        fun, args = self._undo
        return fun(*args)


class History(object):
    "A list of actions, that can be undone and redone."

    def __init__(self):
        self._actions = []
        self._last = -1
        self._counter = 0

    def _push(self, action):
        if self._last < len(self._actions) - 1:
            # erase previously undone actions
            del self._actions[self._last + 1:]
        self._actions.append(action)
        self._last = self._last + 1
        self._counter += 1
        action.number = self._counter
        
    def undo(self):
        if self._last < 0:
            return None
        else:
            action = self._actions[self._last]
            self._last = self._last - 1
            return action.undo()
            
    def redo(self):
        if self._last == len(self._actions) - 1:
            return None
        else:
            self._last = self._last + 1
            action = self._actions[self._last]
            return action.do()

    def add(self, do, undo):
        "Does an action and adds it to history."
        action = Action(do, undo)
        self._push(action)
        return action.do()

    def revision(self):
        if self._last < 0:
            return 0
        else:
            action = self._actions[self._last]
            return action.number

    def is_empty(self):
        return len(self._actions) == 0

    
if __name__ == '__main__':
    def testAction():
        f = lambda x: x
        do = (f, (1,))
        undo = (f, (2,))
        a = Action(do, undo)
        assert a.do() == 1
        assert a.undo() == 2
    
        g = lambda : 1
        do = (g, ())
        undo = (g, ())
        a = Action(do, undo)
        assert a.do() == 1
        assert a.undo() == 1
    
    def testHistory():    
        history = History()
        f = lambda x: x
        do = (f, (1,))
        undo = (f, (2,))
        assert history.add(do, undo) == 1
        assert history.undo() == 2
        assert history.undo() == None
        assert history.redo() == 1
        assert history.redo() == None
        assert history.undo() == 2
        assert history.add(do, undo) ==  1
        assert history.add(do, undo) == 1
        assert history.undo() == 2
        assert history.undo() == 2
        assert history.redo() == 1
        assert history.redo() == 1
        assert history.redo() == None
    
        # Test Revisions
        history = History()
        assert history.revision() == 0
        history.add(do, undo)
        assert history.revision() == 1
        history.add(do, undo)
        assert history.revision() == 2
        history.undo()
        assert history.revision() == 1
        history.redo()
        assert history.revision() == 2
        history.add(do, undo)
        assert history.revision() == 3
        history.undo()
        assert history.revision() == 2
        history.add(do, undo)
        assert history.revision() == 4
        history.undo()
        assert history.revision() == 2
        history.redo()
        assert history.revision() == 4

    testAction()
    testHistory()
