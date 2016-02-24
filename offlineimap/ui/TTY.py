# TTY UI
# Copyright (C) 2002-2015 John Goerzen & contributors
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

import logging
import sys
import time
from getpass import getpass
from offlineimap import banner
from offlineimap.ui.UIBase import UIBase

class TTYFormatter(logging.Formatter):
    """Specific Formatter that adds thread information to the log output."""

    def __init__(self, *args, **kwargs):
        #super() doesn't work in py2.6 as 'logging' uses old-style class
        logging.Formatter.__init__(self, *args, **kwargs)
        self._last_log_thread = None

    def format(self, record):
        """Override format to add thread information."""

        #super() doesn't work in py2.6 as 'logging' uses old-style class
        log_str = logging.Formatter.format(self, record)
        # If msg comes from a different thread than our last, prepend
        # thread info.  Most look like 'Account sync foo' or 'Folder
        # sync foo'.
        t_name = record.threadName
        if t_name == 'MainThread':
            return log_str # main thread doesn't get things prepended
        if t_name != self._last_log_thread:
            self._last_log_thread = t_name
            log_str = "%s:\n %s" % (t_name, log_str)
        else:
            log_str = " %s"% log_str
        return log_str


class TTYUI(UIBase):
    def setup_consolehandler(self):
        """Backend specific console handler

        Sets up things and adds them to self.logger.
        :returns: The logging.Handler() for console output"""

        # create console handler with a higher log level
        ch = logging.StreamHandler()
        #ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        self.formatter = TTYFormatter("%(message)s")
        ch.setFormatter(self.formatter)
        # add the handlers to the logger
        self.logger.addHandler(ch)
        self.logger.info(banner)
        # init lock for console output
        ch.createLock()
        return ch

    def isusable(self):
        """TTYUI is reported as usable when invoked on a terminal."""

        return sys.stdout.isatty() and sys.stdin.isatty()

    def getpass(self, accountname, config, errmsg=None):
        """TTYUI backend is capable of querying the password."""

        if errmsg:
            self.warn("%s: %s"% (accountname, errmsg))
        self._log_con_handler.acquire() # lock the console output
        try:
            return getpass("Enter password for account '%s': " % accountname)
        finally:
            self._log_con_handler.release()

    def mainException(self):
        if isinstance(sys.exc_info()[1], KeyboardInterrupt):
            self.logger.warn("Timer interrupted at user request; program "
                "terminating.\n")
            self.terminate()
        else:
            UIBase.mainException(self)

    def sleeping(self, sleepsecs, remainingsecs):
        """Sleep for sleepsecs, display remainingsecs to go.

        Does nothing if sleepsecs <= 0.
        Display a message on the screen if we pass a full minute.

        This implementation in UIBase does not support this, but some
        implementations return 0 for successful sleep and 1 for an
        'abort', ie a request to sync immediately."""

        if sleepsecs > 0:
            if remainingsecs//60 != (remainingsecs-sleepsecs)//60:
                self.logger.info("Next refresh in %.1f minutes" % (
                    remainingsecs/60.0))
            time.sleep(sleepsecs)
        return 0
