# Noninteractive UI
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

import sys, time
from UIBase import UIBase

class Basic(UIBase):
    def getpass(s, accountname, config):
        raise NotImplementedError, "Prompting for a password is not supported in noninteractive mode."

    def _msg(s, msg):
        print msg

    def warn(s, msg):
        sys.stderr.write("WARNING: " + str(msg) + "\n")

    def sleep(s, sleepsecs):
        if s.verbose >= 0:
            s._msg("Sleeping for %d:%02d" % (sleepsecs / 60, sleepsecs % 60))
        UIBase.sleep(s, sleepsecs)

    def sleeping(s, sleepsecs, remainingsecs):
        if sleepsecs > 0:
            time.sleep(sleepsecs)
        return 0

class Quiet(Basic):
    def __init__(s, config, verbose = -1):
        Basic.__init__(s, config, verbose)
