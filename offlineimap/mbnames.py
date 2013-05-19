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
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import os.path
import re                               # for folderfilter
from threading import Lock

boxes = {}
config = None
accounts = None
mblock = Lock()

def init(conf, accts):
    global config, accounts
    config = conf
    accounts = accts

def add(accountname, foldername):
    if not accountname in boxes:
        boxes[accountname] = []
    if not foldername in boxes[accountname]:
        boxes[accountname].append(foldername)

def write():
    # See if we're ready to write it out.
    for account in accounts:
        if account not in boxes:
            return

    genmbnames()

def genmbnames():
    """Takes a configparser object and a boxlist, which is a list of hashes
    containing 'accountname' and 'foldername' keys."""
    mblock.acquire()
    try:
        localeval = config.getlocaleval()
        if not config.getdefaultboolean("mbnames", "enabled", 0):
            return
        file = open(os.path.expanduser(config.get("mbnames", "filename")), "wt")
        file.write(localeval.eval(config.get("mbnames", "header")))
        folderfilter = lambda accountname, foldername: 1
        if config.has_option("mbnames", "folderfilter"):
            folderfilter = localeval.eval(config.get("mbnames", "folderfilter"),
                                          {'re': re})
        mb_sort_key = lambda d: (d['accountname'], d['foldername'])
        if config.has_option("mbnames", "sortkey"):
            mb_sort_key = localeval.eval(config.get("mbnames", "sortkey"),
                                         {'re': re})
        itemlist = []
        for accountname in boxes.keys():
            for foldername in boxes[accountname]:
                if folderfilter(accountname, foldername):
                    itemlist.append({'accountname': accountname,
                                     'foldername': foldername})
        itemlist.sort(key = mb_sort_key)
        format_string = config.get("mbnames", "peritem", raw=1)
        itemlist = [format_string % d for d in itemlist]
        file.write(localeval.eval(config.get("mbnames", "sep")).join(itemlist))
        file.write(localeval.eval(config.get("mbnames", "footer")))
        file.close()
    finally:
        mblock.release()
