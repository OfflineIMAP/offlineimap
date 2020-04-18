__all__ = ['OfflineImap']

from offlineimap.version import (
        __productname__,
        __version__,
        __copyright__,
        __author__,
        __author_email__,
        __description__,
        __license__,
        __bigcopyright__,
        __homepage__,
        banner
        )

from offlineimap.error import OfflineImapError
# put this last, so we don't run into circular dependencies using
# e.g. offlineimap.__version__.
from offlineimap.init import OfflineImap
