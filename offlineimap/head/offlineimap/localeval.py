"""Eval python code with global namespace of a python source file."""
import imp, errno

class LocalEval:
    def __init__(self, path=None):
        self.namespace={}

        if path is not None:
            file=open(path, 'r')
            module=imp.load_module(
                '<none>',
                file,
                path,
                ('', 'r', imp.PY_SOURCE))
            for attr in dir(module):
                self.namespace[attr]=getattr(module, attr)

    def eval(self, text, namespace=None):
        names = {}
        names.update(self.namespace)
        if namespace is not None:
            names.update(namespace)
        return eval(text, names)
