__all__ = ['OfflineImap']

__productname__ = 'OfflineIMAP'
__version__     = "6.5.2.1"
__copyright__   = "Copyright 2002-2012 John Goerzen & contributors"
__author__      = "John Goerzen"
__author_email__= "john@complete.org"
__description__ = "Disconnected Universal IMAP Mail Synchronization/Reader Support"
__license__  = "Licensed under the GNU GPL v2+ (v2 or any later version)"
__bigcopyright__ = """%(__productname__)s %(__version__)s
  %(__license__)s""" % locals()
__homepage__ = "http://offlineimap.org"

banner = __bigcopyright__

from offlineimap.error import OfflineImapError
# put this last, so we don't run into circular dependencies using 
# e.g. offlineimap.__version__.
from offlineimap.init import OfflineImap
