# Mailbox name generator
# Copyright (C) 2002 John Goerzen
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

import os.path
import re                               # for folderfilter

def genmbnames(config, localeval, boxlist):
    """Takes a configparser object and a boxlist, which is a list of hashes
    containing 'accountname' and 'foldername' keys."""
    if not config.getboolean("mbnames", "enabled"):
        return
    file = open(os.path.expanduser(config.get("mbnames", "filename")), "wt")
    file.write(localeval.eval(config.get("mbnames", "header")))
    folderfilter = lambda accountname, foldername: 1
    if config.has_option("mbnames", "folderfilter"):
        folderfilter = localeval.eval(config.get("mbnames", "folderfilter"),
                                      {'re': re})
    itemlist = [localeval.eval(config.get("mbnames", "peritem", raw=1)) % item\
                for item in boxlist \
                if folderfilter(item['accountname'], item['foldername'])]
    file.write(localeval.eval(config.get("mbnames", "sep")).join(itemlist))
    file.write(localeval.eval(config.get("mbnames", "footer")))
    file.close()
    
    
    
