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
from offlineimap import folder

class GmailRepository(IMAPRepository):
    """Gmail IMAP repository.

    Uses hard-coded host name and port, see:
      http://mail.google.com/support/bin/answer.py?answer=78799&topic=12814
    """

    #: Gmail IMAP server hostname
    HOSTNAME = "imap.gmail.com"

    #: Gmail IMAP server port
    PORT = 993
    
    def __init__(self, reposname, account):
        """Initialize a GmailRepository object."""
        account.getconfig().set('Repository ' + reposname,
                                'remotehost', GmailRepository.HOSTNAME)
        account.getconfig().set('Repository ' + reposname,
                                'remoteport', GmailRepository.PORT)
        account.getconfig().set('Repository ' + reposname,
                                'ssl', 'yes')
        IMAPRepository.__init__(self, reposname, account)

    def gethost(self):
        return GmailRepository.HOSTNAME

    def getport(self):
        return GmailRepository.PORT

    def getssl(self):
        return 1

    def getpreauthtunnel(self):
        return None

    def getfolder(self, foldername):
        return self.getfoldertype()(self.imapserver, foldername,
                                    self.nametrans(foldername),
                                    self.accountname, self)

    def getfoldertype(self):
        return folder.Gmail.GmailFolder

    def getrealdelete(self, foldername):
        # XXX: `foldername` is currently ignored - the `realdelete`
        # setting is repository-wide
        return self.getconfboolean('realdelete', 0)

    def gettrashfolder(self, foldername):
        #: Where deleted mail should be moved
        return  self.getconf('trashfolder','[Gmail]/Trash')
	
    def getspamfolder(self):
        #: Gmail also deletes messages upon EXPUNGE in the Spam folder
        return  self.getconf('spamfolder','[Gmail]/Spam')

