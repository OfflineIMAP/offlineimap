"""Eval python code with global namespace of a python source file."""

# Copyright (C) 2002 John Goerzen
# <jgoerzen@complete.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import imp
try:
    import errno
except:
    pass

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
