# Gmail IMAP repository support
# Copyright (C) 2008 Riccardo Murri <riccardo.murri@gmail.com>
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

from offlineimap.repository.IMAP import IMAPRepository
from offlineimap import folder, OfflineImapError

class GmailRepository(IMAPRepository):
    """Gmail IMAP repository.

    Falls back to hard-coded gmail host name and port, if none were specified:
    http://mail.google.com/support/bin/answer.py?answer=78799&topic=12814
    """
    # Gmail IMAP server hostname
    HOSTNAME = "imap.gmail.com"
    # Gmail IMAP server port
    PORT = 993

    OAUTH2_URL = 'https://accounts.google.com/o/oauth2/token'

    def __init__(self, reposname, account):
        """Initialize a GmailRepository object."""
        # Enforce SSL usage
        account.getconfig().set('Repository ' + reposname,
                                'ssl', 'yes')
        IMAPRepository.__init__(self, reposname, account)


    def gethost(self):
        """Return the server name to connect to.

        Gmail implementation first checks for the usual IMAP settings
        and falls back to imap.gmail.com if not specified."""
        try:
            return super(GmailRepository, self).gethost()
        except OfflineImapError:
            # nothing was configured, cache and return hardcoded one
            self._host = GmailRepository.HOSTNAME
            return self._host

    def getoauth2_request_url(self):
        """Return the server name to connect to.

        Gmail implementation first checks for the usual IMAP settings
        and falls back to imap.gmail.com if not specified."""

        url = super(GmailRepository, self).getoauth2_request_url()
        if url is None:
            # Nothing was configured, cache and return hardcoded one.
            self._oauth2_request_url = GmailRepository.OAUTH2_URL
        else:
            self._oauth2_request_url = url
        return self._oauth2_request_url

    def getport(self):
        return GmailRepository.PORT

    def getssl(self):
        return 1

    def getpreauthtunnel(self):
        return None

    def getfolder(self, foldername):
        return self.getfoldertype()(self.imapserver, foldername,
                                    self)

    def getfoldertype(self):
        return folder.Gmail.GmailFolder

    def gettrashfolder(self, foldername):
        #: Where deleted mail should be moved
        return  self.getconf('trashfolder','[Gmail]/Trash')

    def getspamfolder(self):
        #: Gmail also deletes messages upon EXPUNGE in the Spam folder
        return  self.getconf('spamfolder','[Gmail]/Spam')
