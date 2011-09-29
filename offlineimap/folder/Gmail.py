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
from offlineimap import imaputil


class GmailFolder(IMAPFolder):
    """Folder implementation to support features of the Gmail IMAP server.
    Specifically, deleted messages are moved to folder `Gmail.TRASH_FOLDER`
    (by default: ``[Gmail]/Trash``) prior to expunging them, since
    Gmail maps to IMAP ``EXPUNGE`` command to "remove label".

    For more information on the Gmail IMAP server:
      http://mail.google.com/support/bin/answer.py?answer=77657&topic=12815
    """

    def __init__(self, imapserver, name, repository):
        super(GmailFolder, self).__init__(imapserver, name, repository)
        self.realdelete = repository.getrealdelete(name)
        self.trash_folder = repository.gettrashfolder(name)
        #: Gmail will really delete messages upon EXPUNGE in these folders
        self.real_delete_folders =  [ self.trash_folder, repository.getspamfolder() ]

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
                                     imaputil.uid_sequence(uidlist),
                                     self.trash_folder)
                assert result[0] == 'OK', \
                       "Bad IMAPlib result: %s" % result[0]
            finally:
                self.imapserver.releaseconnection(imapobj)
            for uid in uidlist:
                del self.messagelist[uid]
        else:
            IMAPFolder.deletemessages_noconvert(self, uidlist)
