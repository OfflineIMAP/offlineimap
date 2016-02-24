#Constants, that don't rely on anything else in the module
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
try:
    from cStringIO import StringIO
except ImportError: #python3
    from io import StringIO

default_conf=StringIO("""[general]
#will be set automatically
metadata = 
accounts = test
ui = quiet

[Account test]
localrepository = Maildir
remoterepository = IMAP

[Repository Maildir]
Type = Maildir
# will be set automatically during tests
localfolders = 

[Repository IMAP]
type=IMAP
# Don't hammer the server with too many connection attempts:
maxconnections=1
folderfilter= lambda f: f.startswith('INBOX.OLItest') or f.startswith('INBOX/OLItest')
""")
