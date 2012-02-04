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

class GmailFolder(IMAPFolder):
    """Folder implementation to support features of the Gmail IMAP server.

    Removing a message from a folder will only remove the "label" from
    the message and keep it in the "All mails" folder. To really delete
    a message it needs to be copied to the Trash folder. However, this
    is dangerous as our folder moves are implemented as a 1) delete in
    one folder and 2) append to the other. If 2 comes before 1, this
    will effectively delete the message from all folders. So we cannot
    do that until we have a smarter folder move mechanism.

    For more information on the Gmail IMAP server:
      http://mail.google.com/support/bin/answer.py?answer=77657&topic=12815
    """

    def __init__(self, imapserver, name, repository):
        super(GmailFolder, self).__init__(imapserver, name, repository)
        self.trash_folder = repository.gettrashfolder(name)
        # Gmail will really delete messages upon EXPUNGE in these folders
        self.real_delete_folders =  [ self.trash_folder, repository.getspamfolder() ]
