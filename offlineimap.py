#!/usr/bin/env python
# Startup from single-user installation
# Copyright (C) 2002 - 2008 John Goerzen
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

import os
import sys

if not 'DEVELOPING_OFFLINEIMAP_PYTHON3_SUPPORT' in os.environ:
	if sys.version_info[0] > 2:
		sys.stderr.write("""IIMAPS!

Sorry, OfflineIMAP currently doesn't support Python higher than 2.x.
We're doing our best to bring in support for 3.x really soon.  You can
also join us at https://github.com/OfflineIMAP/offlineimap/ and help.
""")
		sys.exit(1)

from offlineimap import OfflineImap

oi = OfflineImap()
oi.run()
