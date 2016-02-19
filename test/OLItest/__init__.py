# OfflineImap test library
# Copyright (C) 2012- Sebastian Spaeth & contributors
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

__all__ = ['OLITestLib', 'TextTestRunner','TestLoader']

__productname__ = 'OfflineIMAP Test suite'
__version__     = '0'
__copyright__   = "Copyright 2012- Sebastian Spaeth & contributors"
__author__      = 'Sebastian Spaeth'
__author_email__= 'Sebastian@SSpaeth.de'
__description__ = 'Moo'
__license__  = "Licensed under the GNU GPL v2+ (v2 or any later version)"
__homepage__ = "http://www.offlineimap.org"
banner = """%(__productname__)s %(__version__)s
  %(__license__)s""" % locals()

import unittest
from unittest import TestLoader, TextTestRunner
from .globals import default_conf
from .TestRunner import OLITestLib
