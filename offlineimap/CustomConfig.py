# Copyright (C) 2003-2015 John Goerzen & contributors
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

import os
import re
from sys import exc_info

import six

try:
    from ConfigParser import SafeConfigParser, Error
except ImportError: #python3
    from configparser import SafeConfigParser, Error
from offlineimap.localeval import LocalEval

class CustomConfigParser(SafeConfigParser):
    def __init__(self):
        SafeConfigParser.__init__(self)
        self.localeval = None

    def getdefault(self, section, option, default, *args, **kwargs):
        """Same as config.get, but returns the value of `default`
        if there is no such option specified."""

        if self.has_option(section, option):
            return self.get(*(section, option) + args, **kwargs)
        else:
            return default


    def getdefaultint(self, section, option, default, *args, **kwargs):
        """Same as config.getint, but returns the value of `default`
        if there is no such option specified."""

        if self.has_option(section, option):
            return self.getint(*(section, option) + args, **kwargs)
        else:
            return default


    def getdefaultfloat(self, section, option, default, *args, **kwargs):
        """Same as config.getfloat, but returns the value of `default`
        if there is no such option specified."""

        if self.has_option(section, option):
            return self.getfloat(*(section, option) + args, **kwargs)
        else:
            return default

    def getdefaultboolean(self, section, option, default, *args, **kwargs):
        """Same as config.getboolean, but returns the value of `default`
        if there is no such option specified."""

        if self.has_option(section, option):
            return self.getboolean(*(section, option) + args, **kwargs)
        else:
            return default

    def getlist(self, section, option, separator_re):
        """Parses option as the list of values separated
        by the given regexp."""

        try:
            val = self.get(section, option).strip()
            return re.split(separator_re, val)
        except re.error as e:
            six.reraise(Error("Bad split regexp '%s': %s" % \
              (separator_re, e)), None, exc_info()[2])

    def getdefaultlist(self, section, option, default, separator_re):
        """Same as getlist, but returns the value of `default`
        if there is no such option specified."""

        if self.has_option(section, option):
            return self.getlist(*(section, option, separator_re))
        else:
            return default

    def getmetadatadir(self):
        xforms = [os.path.expanduser, os.path.expandvars]
        d = self.getdefault("general", "metadata", "~/.offlineimap")
        metadatadir = self.apply_xforms(d, xforms)
        if not os.path.exists(metadatadir):
            os.mkdir(metadatadir, 0o700)
        return metadatadir

    def getlocaleval(self):
        # We already loaded pythonfile, so return this copy.
        if self.localeval is not None:
            return self.localeval

        xforms = [os.path.expanduser, os.path.expandvars]
        if self.has_option("general", "pythonfile"):
            path = self.get("general", "pythonfile")
            path = self.apply_xforms(path, xforms)
        else:
            path = None

        self.localeval = LocalEval(path)
        return self.localeval

    def getsectionlist(self, key):
        """Returns a list of sections that start with (str) key + " ".
        
        That is, if key is "Account", returns all section names that
        start with "Account ", but strips off the "Account ".
        
        For instance, for "Account Test", returns "Test"."""

        key = key + ' '
        return [x[len(key):] for x in self.sections() \
             if x.startswith(key)]

    def set_if_not_exists(self, section, option, value):
        """Set a value if it does not exist yet.

        This allows to set default if the user has not explicitly
        configured anything."""

        if not self.has_option(section, option):
            self.set(section, option, value)


    def apply_xforms(self, string, transforms):
        """Applies set of transformations to a string.

        Arguments:
         - string: source string; if None, then no processing will
           take place.
         - transforms: iterable that returns transformation function
           on each turn.

        Returns transformed string."""

        if string == None:
            return None
        for f in transforms:
            string = f(string)
        return string



def CustomConfigDefault():
    """Just a constant that won't occur anywhere else.

    This allows us to differentiate if the user has passed in any
    default value to the getconf* functions in ConfigHelperMixin
    derived classes."""

    pass



class ConfigHelperMixin:
    """Allow comfortable retrieving of config values pertaining
    to a section.

    If a class inherits from cls:`ConfigHelperMixin`, it needs
    to provide 2 functions:
    - meth:`getconfig` (returning a CustomConfigParser object)
    - and meth:`getsection` (returning a string which represents
      the section to look up).
    All calls to getconf* will then return the configuration values
    for the CustomConfigParser object in the specific section.
    """

    def _confighelper_runner(self, option, default, defaultfunc, mainfunc, *args):
        """Returns configuration or default value for option
        that contains in section identified by getsection().

        Arguments:
        - option: name of the option to retrieve;
        - default: governs which function we will call.
          * When CustomConfigDefault is passed, we will call
          the mainfunc.
          * When any other value is passed, we will call
          the defaultfunc and the value of `default` will
          be passed as the third argument to this function.
        - defaultfunc and mainfunc: processing helpers.
        - args: additional trailing arguments that will be passed
          to all processing helpers.
        """

        lst = [self.getsection(), option]
        if default == CustomConfigDefault:
            return mainfunc(*(lst + list(args)))
        else:
            lst.append(default)
            return defaultfunc(*(lst + list(args)))

    def getconfig(self):
        """Returns CustomConfigParser object that we will use
        for all our actions.

        Must be overriden in all classes that use this mix-in."""

        raise NotImplementedError("ConfigHelperMixin.getconfig() "
          "is to be overriden")



    def getsection(self):
        """Returns name of configuration section in which our
        class keeps its configuration.

        Must be overriden in all classes that use this mix-in."""

        raise NotImplementedError("ConfigHelperMixin.getsection() "
          "is to be overriden")


    def getconf(self, option, default = CustomConfigDefault):
        """Retrieves string from the configuration.

        Arguments:
         - option: option name whose value is to be retrieved;
         - default: default return value if no such option
           exists.
        """

        return self._confighelper_runner(option, default,
                                         self.getconfig().getdefault,
                                         self.getconfig().get)


    def getconf_xform(self, option, xforms, default = CustomConfigDefault):
        """Retrieves string from the configuration transforming the result.

        Arguments:
         - option: option name whose value is to be retrieved;
         - xforms: iterable that returns transform functions
           to be applied to the value of the option,
           both retrieved and default one;
         - default: default value for string if no such option
           exists.
        """

        value = self.getconf(option, default)
        return self.getconfig().apply_xforms(value, xforms)


    def getconfboolean(self, option, default = CustomConfigDefault):
        """Retrieves boolean value from the configuration.

        Arguments:
         - option: option name whose value is to be retrieved;
         - default: default return value if no such option
           exists.
        """

        return self._confighelper_runner(option, default,
                                         self.getconfig().getdefaultboolean,
                                         self.getconfig().getboolean)


    def getconfint(self, option, default = CustomConfigDefault):
        """
        Retrieves integer value from the configuration.

        Arguments:
         - option: option name whose value is to be retrieved;
         - default: default return value if no such option
           exists.

        """

        return self._confighelper_runner(option, default,
                                         self.getconfig().getdefaultint,
                                         self.getconfig().getint)


    def getconffloat(self, option, default = CustomConfigDefault):
        """Retrieves floating-point value from the configuration.

        Arguments:
         - option: option name whose value is to be retrieved;
         - default: default return value if no such option
           exists.
        """

        return self._confighelper_runner(option, default,
                                         self.getconfig().getdefaultfloat,
                                         self.getconfig().getfloat)


    def getconflist(self, option, separator_re,
                    default = CustomConfigDefault):
        """Retrieves strings from the configuration and splits it
        into the list of strings.

        Arguments:
         - option: option name whose value is to be retrieved;
         - separator_re: regular expression for separator
           to be used for split operation;
         - default: default return value if no such option
           exists.
        """

        return self._confighelper_runner(option, default,
                                         self.getconfig().getdefaultlist,
                                         self.getconfig().getlist, separator_re)
