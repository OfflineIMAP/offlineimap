# Gmail IMAP folder support
# Copyright (C) 2008 Riccardo Murri <riccardo.murri@gmail.com>
# Copyright (C) 2002-2007 John Goerzen <jgoerzen@complete.org>
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

"""Folder implementation to support features of the Gmail IMAP server.
"""

from IMAP import IMAPFolder
from offlineimap import imaplib2, imaputil, imaplibutil
from offlineimap.ui import UIBase
from copy import copy


class GmailFolder(IMAPFolder):
    """Folder implementation to support features of the Gmail IMAP server.
    Specifically, deleted messages are moved to folder `Gmail.TRASH_FOLDER`
    (by default: ``[Gmail]/Trash``) prior to expunging them, since
    Gmail maps to IMAP ``EXPUNGE`` command to "remove label".

    For more information on the Gmail IMAP server:
      http://mail.google.com/support/bin/answer.py?answer=77657&topic=12815
    """

    def __init__(self, imapserver, name, visiblename, accountname, repository):
        self.realdelete = repository.getrealdelete(name)
        self.trash_folder = repository.gettrashfolder(name)
        #: Gmail will really delete messages upon EXPUNGE in these folders
        self.real_delete_folders =  [ self.trash_folder, repository.getspamfolder() ]
        IMAPFolder.__init__(self, imapserver, name, visiblename, \
                            accountname, repository)

    def deletemessages_noconvert(self, uidlist):
        uidlist = [uid for uid in uidlist if uid in self.messagelist]
        if not len(uidlist):
            return        

        if self.realdelete and not (self.getname() in self.real_delete_folders):
            # IMAP expunge is just "remove label" in this folder,
            # so map the request into a "move into Trash"

            imapobj = self.imapserver.acquireconnection()
            try:
                imapobj.select(self.getfullname())
                result = imapobj.uid('copy',
                                     imaputil.listjoin(uidlist),
                                     self.trash_folder)
                assert result[0] == 'OK', \
                       "Bad IMAPlib result: %s" % result[0]
            finally:
                self.imapserver.releaseconnection(imapobj)
            for uid in uidlist:
                del self.messagelist[uid]
        else:
            IMAPFolder.deletemessages_noconvert(self, uidlist)
            
    def processmessagesflags(self, operation, uidlist, flags):
        # XXX: the imapobj.myrights(...) calls dies with an error
        # report from Gmail server stating that IMAP command
        # 'MYRIGHTS' is not implemented.  So, this
        # `processmessagesflags` is just a copy from `IMAPFolder`,
        # with the references to `imapobj.myrights()` deleted This
        # shouldn't hurt, however, Gmail users always have full
        # control over all their mailboxes (apparently).
        if len(uidlist) > 101:
            # Hack for those IMAP ervers with a limited line length
            self.processmessagesflags(operation, uidlist[:100], flags)
            self.processmessagesflags(operation, uidlist[100:], flags)
            return
        
        imapobj = self.imapserver.acquireconnection()
        try:
            imapobj.select(self.getfullname())
            r = imapobj.uid('store',
                            imaputil.listjoin(uidlist),
                            operation + 'FLAGS',
                            imaputil.flagsmaildir2imap(flags))
            assert r[0] == 'OK', 'Error with store: ' + '. '.join(r[1])
            r = r[1]
        finally:
            self.imapserver.releaseconnection(imapobj)

        needupdate = copy(uidlist)
        for result in r:
            if result == None:
                # Compensate for servers that don't return anything from
                # STORE.
                continue
            attributehash = imaputil.flags2hash(imaputil.imapsplit(result)[1])
            if not ('UID' in attributehash and 'FLAGS' in attributehash):
                # Compensate for servers that don't return a UID attribute.
                continue
            flags = attributehash['FLAGS']
            uid = long(attributehash['UID'])
            self.messagelist[uid]['flags'] = imaputil.flagsimap2maildir(flags)
            try:
                needupdate.remove(uid)
            except ValueError:          # Let it slide if it's not in the list
                pass
        for uid in needupdate:
            if operation == '+':
                for flag in flags:
                    if not flag in self.messagelist[uid]['flags']:
                        self.messagelist[uid]['flags'].append(flag)
                    self.messagelist[uid]['flags'].sort()
            elif operation == '-':
                for flag in flags:
                    if flag in self.messagelist[uid]['flags']:
                        self.messagelist[uid]['flags'].remove(flag)
