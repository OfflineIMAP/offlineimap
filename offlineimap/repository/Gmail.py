# Gmail IMAP repository support
# Copyright (C) 2008-2016 Riccardo Murri <riccardo.murri@gmail.com> &
# contributors
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

    This class just has default settings for GMail's IMAP service. So
    you can do 'type = Gmail' instead of 'type = IMAP' and skip
    specifying the hostname, port etc. See
    http://mail.google.com/support/bin/answer.py?answer=78799&topic=12814
    for the values we use."""
    def __init__(self, reposname, account):
        """Initialize a GmailRepository object."""
        IMAPRepository.__init__(self, reposname, account)

    def gethost(self):
        """Return the server name to connect to.

        We first check the usual IMAP settings, and then fall back to
        imap.gmail.com if nothing is specified."""
        try:
            return super(GmailRepository, self).gethost()
        except OfflineImapError:
            # Nothing was configured, cache and return hardcoded
            # one. See the parent class (IMAPRepository) for how this
            # cache is used.
            self._host = "imap.gmail.com"
            return self._host

    def getoauth2_request_url(self):
        """Return the OAuth URL to request tokens from.

        We first check the usual OAuth settings, and then fall back to
        https://accounts.google.com/o/oauth2/token if nothing is
        specified."""

        url = super(GmailRepository, self).getoauth2_request_url()
        if url is None:
            # Nothing was configured, cache and return hardcoded one.
            self.setoauth2_request_url("https://accounts.google.com/o/oauth2/token")
        else:
            self.setoauth2_request_url(url)
        return self.oauth2_request_url

    def getport(self):
        """Return the port number to connect to.

        This Gmail implementation first checks for the usual IMAP settings
        and falls back to 993 if nothing is specified."""

        port = super(GmailRepository, self).getport()

        if port is None:
            return 993
        else:
            return port

    def getssl(self):
        ssl = self.getconfboolean('ssl', None)

        if ssl is None:
            # Nothing was configured, return our default setting for
            # GMail. Maybe this should look more similar to gethost &
            # we could just rely on the global "ssl = yes" default.
            return True
        else:
            return ssl

    def getpreauthtunnel(self):
        return None

    def getfolder(self, foldername):
        return self.getfoldertype()(self.imapserver, foldername,
                                    self)

    def getfoldertype(self):
        return folder.Gmail.GmailFolder

    def gettrashfolder(self, foldername):
        # Where deleted mail should be moved
        return self.getconf('trashfolder', '[Gmail]/Trash')

    def getspamfolder(self):
        # Depending on the IMAP settings (Settings -> Forwarding and
        # POP/IMAP -> IMAP Access -> "When I mark a message in IMAP as
        # deleted") GMail might also deletes messages upon EXPUNGE in
        # the Spam folder.
        return self.getconf('spamfolder', '[Gmail]/Spam')
