#!/usr/bin/env python2.2

# $Id: setup.py,v 1.1 2002/06/21 18:10:49 jgoerzen Exp $

# IMAP synchronization
# Module: installer
# COPYRIGHT #
# Copyright (C) 2002 John Goerzen
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; version 2 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# END OF COPYRIGHT #


from distutils.core import setup
import offlineimap.version

setup(name = "offlineimap",
      version = offlineimap.version.versionstr,
      description = offlineimap.version.description,
      author = offlineimap.version.author,
      author_email = offlineimap.version.author_email,
      url = offlineimap.version.homepage,
      packages = ['offlineimap', 'offlineimap.folder',
                  'offlineimap.repository', 'offlineimap.ui'],
      scripts = ['bin/offlineimap'],
      license = offlineimap.version.copyright + \
                ", Licensed under the GPL version 2"
)

