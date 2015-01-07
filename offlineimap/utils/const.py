# Copyright (C) 2013-2014 Eygene A. Ryabinkin and contributors
#
# Collection of classes that implement const-like behaviour
# for various objects.

import copy

class ConstProxy(object):
    """Implements read-only access to a given object
    that can be attached to each instance only once."""

    def __init__(self):
        self.__dict__['__source'] = None


    def __getattr__(self, name):
        src = self.__dict__['__source']
        if src == None:
            raise ValueError("using non-initialized ConstProxy() object")
        return copy.deepcopy(getattr(src, name))


    def __setattr__(self, name, value):
        raise AttributeError("tried to set '%s' to '%s' for constant object"% \
            (name, value))


    def __delattr__(self, name):
        raise RuntimeError("tried to delete field '%s' from constant object"% \
            (name))


    def set_source(self, source):
        """ Sets source object for this instance. """
        if (self.__dict__['__source'] != None):
            raise ValueError("source object is already set")
        self.__dict__['__source'] = source
