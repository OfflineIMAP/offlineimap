# Copyright (C) 2003 John Goerzen
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

from ConfigParser import ConfigParser
from offlineimap.localeval import LocalEval
import os

class CustomConfigParser(ConfigParser):
    def getdefault(self, section, option, default, *args, **kwargs):
        """Same as config.get, but returns the "default" option if there
        is no such option specified."""
        if self.has_option(section, option):
            return apply(self.get, [section, option] + list(args), kwargs)
        else:
            return default
    
    def getdefaultint(self, section, option, default, *args, **kwargs):
        if self.has_option(section, option):
            return apply(self.getint, [section, option] + list(args), kwargs)
        else:
            return default

    def getdefaultboolean(self, section, option, default, *args, **kwargs):
        if self.has_option(section, option):
            return apply(self.getboolean, [section, option] + list(args),
                         kwargs)
        else:
            return default

    def getmetadatadir(self):
        metadatadir = os.path.expanduser(self.getdefault("general", "metadata", "~/.offlineimap"))
        if not os.path.exists(metadatadir):
            os.mkdir(metadatadir, 0700)
        return metadatadir

    def getlocaleval(self):
        if self.has_option("general", "pythonfile"):
            path = os.path.expanduser(self.get("general", "pythonfile"))
        else:
            path = None
        return LocalEval(path)

    def getaccountlist(self):
        return [x for x in self.sections() if x != 'general']
    
