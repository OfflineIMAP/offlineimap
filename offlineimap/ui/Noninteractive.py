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

class Basic(UIBase):
    """'Basic' simply sets log level to INFO"""
    def __init__(self, config, loglevel = logging.INFO):
        return super(Basic, self).__init__(config, loglevel)

class Quiet(UIBase):
    """'Quiet' simply sets log level to WARNING"""
    def __init__(self, config, loglevel = logging.WARNING):
        return super(Quiet, self).__init__(config, loglevel)
