# Base folder support
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

class BaseFolder:
    def getname(self):
        """Returns name"""
        return self.name

    def getroot(self):
        """Returns the root of the folder, in a folder-specific fashion."""
        return self.root

    def getsep(self):
        """Returns the separator for this folder type."""
        return self.sep

    def getfullname(self):
        return self.getroot() + self.getsep() + self.getname()
    
    def isuidvalidityok(self, remotefolder):
        raise NotImplementedException

    def getuidvalidity(self):
        raise NotImplementedException

    def saveuidvalidity(self, newval):
        raise NotImplementedException

    def cachemessagelist(self):
        """Reads the message list from disk or network and stores it in
        memory for later use.  This list will not be re-read from disk or
        memory unless this function is called again."""
        raise NotImplementedException

    def getmessagelist(self):
        """Gets the current message list.
        You must call cachemessagelist() before calling this function!"""
        raise NotImplementedException

    def getmessage(self, uid):
        """Returns the content of the specified message."""
        raise NotImplementedException

    def savemessage(self, uid, content):
        """Writes a new message, with the specified uid."""
        raise NotImplementedException

    def getmessageflags(self, uid):
        """Returns the flags for the specified message."""
        raise NotImplementedException

    def savemessageflags(self, uid, flags):
        """Sets the specified message's flags to the given set."""
        raise NotImplementedException

    def deletemessage(self, uid):
        raise NotImplementedException

    def syncmessagesto(self, dest, applyto = None):
        """Syncs messages in this folder to the destination.
        If applyto is specified, it should be a list of folders (don't forget
        to include dest!) to which all write actions should be applied.
        It defaults to [dest] if not specified."""
        if applyto == None:
            applyto = [dest]

        # Pass 1 -- Look for messages present in self but not in dest.
        # If any, add them to dest.
        
        for uid in self.getmessagelist().keys():
            if not uid in dest.getmessagelist():
                message = self.getmessage(uid)
                flags = self.getmessageflags(uid)
                for object in applyto:
                    object.savemessage(uid, message)
                    object.savemessageflags(uid, flags)

        # Pass 2 -- Look for message present in dest but not in self.
        # If any, delete them.

        for uid in dest.getmessagelist().keys():
            if not uid in self.getmessagelist():
                for object in applyto:
                    object.deletemessage(uid)

        # Now, the message lists should be identical wrt the uids present.

        # Pass 3 -- Look for any flag identity issues.

        
