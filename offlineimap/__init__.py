__all__ = ['OfflineImap']

__productname__ = 'OfflineIMAP'
__version__     = "6.3.2.1"
__copyright__   = "Copyright (C) 2002 - 2010 John Goerzen"
__author__      = "John Goerzen"
__author_email__= "john@complete.org"
__description__ = "Disconnected Universal IMAP Mail Synchronization/Reader Support"
__bigcopyright__ = """%(__productname__)s %(__version__)s
%(__copyright__)s <%(__author_email__)s>""" % locals()

banner = __bigcopyright__ + """

This software comes with ABSOLUTELY NO WARRANTY; see the file
COPYING for details.  This is free software, and you are welcome
to distribute it under the conditions laid out in COPYING."""

__homepage__ = "http://github.com/nicolas33/offlineimap"
__license__  = "Licensed under the GNU GPL v2+ (v2 or any later version)."

# put this last, so we don't run into circular dependencies using 
# e.g. offlineimap.__version__.
from offlineimap.init import OfflineImap
