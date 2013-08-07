# Copyright (C) 2003-2012 John Goerzen & contributors
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
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

try:
    from ConfigParser import SafeConfigParser, Error, NoOptionError
except ImportError: #python3
    from configparser import SafeConfigParser, Error, NoOptionError
from offlineimap.localeval import LocalEval
import os
import re

class CustomConfigParser(SafeConfigParser):
    def getdefault(self, section, option, default, *args, **kwargs):
        """Same as config.get, but returns the "default" option if there
        is no such option specified."""
        if self.has_option(section, option):
            return self.get(*(section, option) + args, **kwargs)
        else:
            return default

    def getdefaultint(self, section, option, default, *args, **kwargs):
        if self.has_option(section, option):
            return self.getint (*(section, option) + args, **kwargs)
        else:
            return default

    def getdefaultfloat(self, section, option, default, *args, **kwargs):
        if self.has_option(section, option):
            return self.getfloat(*(section, option) + args, **kwargs)
        else:
            return default

    def getdefaultboolean(self, section, option, default, *args, **kwargs):
        if self.has_option(section, option):
            return self.getboolean(*(section, option) + args, **kwargs)
        else:
            return default

    def getlist(self, section, option, separator_re):
    	"""
    	Parses option as the list of values separated
    	by the given regexp.

    	"""
        try:
            val = self.get(section, option).strip()
            return re.split(separator_re, val)
        except re.error as e:
            raise Error("Bad split regexp '%s': %s" % \
              (separator_re, e))

    def getdefaultlist(self, section, option, default, separator_re):
        if self.has_option(section, option):
            return self.getlist(*(section, option, separator_re))
        else:
            return default

    def getmetadatadir(self):
        metadatadir = os.path.expanduser(self.getdefault("general", "metadata", "~/.offlineimap"))
        if not os.path.exists(metadatadir):
            os.mkdir(metadatadir, 0o700)
        return metadatadir

    def getlocaleval(self):
        if self.has_option("general", "pythonfile"):
            path = os.path.expanduser(self.get("general", "pythonfile"))
        else:
            path = None
        return LocalEval(path)

    def getsectionlist(self, key):
        """Returns a list of sections that start with key + " ".  That is,
        if key is "Account", returns all section names that start with
        "Account ", but strips off the "Account ".  For instance, for
        "Account Test", returns "Test"."""

        key = key + ' '
        return [x[len(key):] for x in self.sections() \
                if x.startswith(key)]

    def set_if_not_exists(self, section, option, value):
        """Set a value if it does not exist yet

        This allows to set default if the user has not explicitly
        configured anything."""
        if not self.has_option(section, option):
            self.set(section, option, value)

def CustomConfigDefault():
    """Just a constant that won't occur anywhere else.

    This allows us to differentiate if the user has passed in any
    default value to the getconf* functions in ConfigHelperMixin
    derived classes."""
    pass

class ConfigHelperMixin:
    """Allow comfortable retrieving of config values pertaining to a section.

    If a class inherits from this cls:`ConfigHelperMixin`, it needs
    to provide 2 functions: meth:`getconfig` (returning a
    ConfigParser object) and meth:`getsection` (returning a string
    which represents the section to look up). All calls to getconf*
    will then return the configuration values for the ConfigParser
    object in the specific section."""

    def _confighelper_runner(self, option, default, defaultfunc, mainfunc, *args):
        """Return config value for getsection()"""
        lst = [self.getsection(), option]
        if default == CustomConfigDefault:
            return mainfunc(*(lst + list(args)))
        else:
            lst.append(default)
            return defaultfunc(*(lst + list(args)))


    def getconf(self, option,
                default = CustomConfigDefault):
        return self._confighelper_runner(option, default,
                                         self.getconfig().getdefault,
                                         self.getconfig().get)

    def getconfboolean(self, option, default = CustomConfigDefault):
        return self._confighelper_runner(option, default,
                                         self.getconfig().getdefaultboolean,
                                         self.getconfig().getboolean)

    def getconfint(self, option, default = CustomConfigDefault):
        return self._confighelper_runner(option, default,
                                         self.getconfig().getdefaultint,
                                         self.getconfig().getint)

    def getconffloat(self, option, default = CustomConfigDefault):
        return self._confighelper_runner(option, default,
                                         self.getconfig().getdefaultfloat,
                                         self.getconfig().getfloat)

    def getconflist(self, option, separator_re,
                default = CustomConfigDefault):
        return self._confighelper_runner(option, default,
                                         self.getconfig().getdefaultlist,
                                         self.getconfig().getlist, separator_re)
