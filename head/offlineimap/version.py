productname = 'OfflineIMAP'
versionstr = "2.0.2"

versionlist = versionstr.split(".")
major = versionlist[0]
minor = versionlist[1]
patch = versionlist[2]
copyright = "Copyright (C) 2002 John Goerzen"
author = "John Goerzen"
author_email = "jgoerzen@complete.org"
description = "Disconnected Universal IMAP Mail Synchronization/Reader Support"

banner = """%(productname)s %(versionstr)s, %(copyright)s <%(author_email)s>
This software comes with ABSOLUTELY NO WARRANTY; see the file
COPYING for details.  This is free software, and you are welcome
to distribute it under the conditions laid out in COPYING.""" % locals()

homepage = "http://www.quux.org/devel/offlineimap"
homegopher = "gopher://quux.org/1/devel/offlineimap"
license = """Copyright (C) 2002 John Goerzen <jgoerzen@complete.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA"""
