# Maildir folder support
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

from Base import BaseFolder
from imapsync import imaputil
import os.path, os, re

class MaildirFolder(BaseFolder):
    def __init__(self, root, name):
        self.name = name
        self.root = root
        self.sep = '.'
        self.uidfilename = os.path.join(self.getfullname(), "imapsync.uidvalidity")
        self.messagelist = None

    def getuidvalidity(self):
        if not os.path.exists(self.uidfilename):
            return None
        file = open(self.uidfilename, "rt")
        retval = int(file.readline().strip())
        file.close()
        return retval

    def saveuidvalidity(self, newval):
        file = open(self.uidfilename, "wt")
        file.write("%d\n", newval)
        file.close()

    def isuidvalidityok(self, remotefolder):
        myval = self.getuidvalidity()
        if myval != None:
            return myval == remotefolder.getuidvalidity()
        else:
            self.saveuidvalidity(remotefolder.getuidvalidity())
            
    def cachemessagelist(self):
        """Cache the message list.  Maildir flags are:
        R (replied)
        S (seen)
        T (trashed)
        D (draft)
        F (flagged)
        and must occur in ASCII order."""
        self.messagelist = {}
        files = []
        for dirannex in ['new', 'cur']:
            fulldirname = os.path.join(self.getfullname(), dirannex)
            files.append([os.path.join(fulldirname, filename) for
                          filename in os.listdir(fulldirname)])
        for file in files:
            messagename = os.path.basename(file)
            uid = int(re.search(',U=(\d+)', messagename).group(1))
            flagmatch = re.search(':.*2,([A-Z]+)')
            flags = []
            if flagmatch:
                flags = [f for x in flagmatch.group(1)]
            self.messagelist[uid] = {'uid': uid,
                                     'flags': flags,
                                     'filename': messagename}
            
    def getmessagelist(self):
        if self.messagelist == None:
            self.cachemessagelist()
        return self.messagelist

    
