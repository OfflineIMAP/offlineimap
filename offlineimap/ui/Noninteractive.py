# Noninteractive UI
# Copyright (C) 2002-2012 John Goerzen & contributors
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
from offlineimap.ui.UIBase import UIBase
import offlineimap

class Basic(UIBase):
    """'Basic' simply sets log level to INFO"""
    def __init__(self, config, loglevel = logging.INFO):
        return super(Basic, self).__init__(config, loglevel)

class Quiet(UIBase):
    """'Quiet' simply sets log level to WARNING"""
    def __init__(self, config, loglevel = logging.WARNING):
        return super(Quiet, self).__init__(config, loglevel)

class Syslog(UIBase):
    """'Syslog' sets log level to INFO and outputs to syslog instead of stdout"""
    def __init__(self, config, loglevel = logging.INFO):
        return super(Syslog, self).__init__(config, loglevel)

    def setup_consolehandler(self):
        # create syslog handler
        ch = logging.handlers.SysLogHandler('/dev/log')
        # create formatter and add it to the handlers
        self.formatter = logging.Formatter("%(message)s")
        ch.setFormatter(self.formatter)
        # add the handlers to the logger
        self.logger.addHandler(ch)
        self.logger.info(offlineimap.banner)
        return ch

    def setup_sysloghandler(self):
        pass # Do not honor -s (log to syslog) CLI option.
