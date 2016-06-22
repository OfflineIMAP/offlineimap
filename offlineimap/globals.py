# Copyright 2013-2016 Eygene A. Ryabinkin & contributors.
#
# Module that holds various global objects.

from offlineimap.utils import const

# Holds command-line options for OfflineIMAP.
options = const.ConstProxy()

def set_options(source):
    """Sets the source for options variable."""

    options.set_source(source)
