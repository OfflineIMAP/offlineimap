# Mailbox name generator
#
# Copyright (C) 2002-2015 John Goerzen & contributors
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

import os.path
import re                               # for folderfilter
from threading import Lock

boxes = {}
localroots = {}
config = None
accounts = None
mblock = Lock()

def init(conf, accts):
    global config, accounts
    config = conf
    accounts = accts

def add(accountname, foldername, localfolders):
    if not accountname in boxes:
        boxes[accountname] = []
        localroots[accountname] = localfolders
    if not foldername in boxes[accountname]:
        boxes[accountname].append(foldername)

def write(allcomplete):
    incremental = config.getdefaultboolean("mbnames", "incremental", False)

    # Skip writing if we don't want incremental writing and we're not done.
    if not incremental and not allcomplete:
        return

    # Skip writing if we want incremental writing and we're done.
    if incremental and allcomplete:
        return

    # See if we're ready to write it out.
    for account in accounts:
        if account not in boxes:
            return

    __genmbnames()

def __genmbnames():
    """Takes a configparser object and a boxlist, which is a list of hashes
    containing 'accountname' and 'foldername' keys."""

    xforms = [os.path.expanduser, os.path.expandvars]
    mblock.acquire()
    try:
        localeval = config.getlocaleval()
        if not config.getdefaultboolean("mbnames", "enabled", 0):
            return
        path = config.apply_xforms(config.get("mbnames", "filename"), xforms)
        file = open(path, "wt")
        file.write(localeval.eval(config.get("mbnames", "header")))
        folderfilter = lambda accountname, foldername: 1
        if config.has_option("mbnames", "folderfilter"):
            folderfilter = localeval.eval(config.get("mbnames", "folderfilter"),
                                          {'re': re})
        mb_sort_keyfunc = lambda d: (d['accountname'], d['foldername'])
        if config.has_option("mbnames", "sort_keyfunc"):
            mb_sort_keyfunc = localeval.eval(config.get("mbnames", "sort_keyfunc"),
                                         {'re': re})
        itemlist = []
        for accountname in boxes.keys():
            localroot = localroots[accountname]
            for foldername in boxes[accountname]:
                if folderfilter(accountname, foldername):
                    itemlist.append({'accountname': accountname,
                                     'foldername': foldername,
                                     'localfolders': localroot})
        itemlist.sort(key = mb_sort_keyfunc)
        format_string = config.get("mbnames", "peritem", raw=1)
        itemlist = [format_string % d for d in itemlist]
        file.write(localeval.eval(config.get("mbnames", "sep")).join(itemlist))
        file.write(localeval.eval(config.get("mbnames", "footer")))
        file.close()
    finally:
        mblock.release()
