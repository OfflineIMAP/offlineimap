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

from threading import *
from offlineimap import threadutil
from offlineimap.threadutil import InstanceLimitedThread
from offlineimap.ui import UIBase

class BaseFolder:
    def getname(self):
        """Returns name"""
        return self.name

    def suggeststhreads(self):
        """Returns true if this folder suggests using threads for actions;
        false otherwise.  Probably only IMAP will return true."""
        return 0

    def waitforthread(self):
        """For threading folders, waits until there is a resource available
        before firing off a thread.  For all others, returns immediately."""
        pass

    def getcopyinstancelimit(self):
        """For threading folders, returns the instancelimitname for
        InstanceLimitedThreads."""
        raise NotImplementedException

    def storesmessages(self):
        """Should be true for any backend that actually saves message bodies.
        (Almost all of them).  False for the LocalStatus backend.  Saves
        us from having to slurp up messages just for localstatus purposes."""
        return 1

    def getvisiblename(self):
        return self.name

    def getrepository(self):
        """Returns the repository object that this folder is within."""
        return self.repository

    def getroot(self):
        """Returns the root of the folder, in a folder-specific fashion."""
        return self.root

    def getsep(self):
        """Returns the separator for this folder type."""
        return self.sep

    def getfullname(self):
        if self.getroot():
            return self.getroot() + self.getsep() + self.getname()
        else:
            return self.getname()
    
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

    def savemessage(self, uid, content, flags):
        """Writes a new message, with the specified uid.
        If the uid is < 0, the backend should assign a new uid and return it.

        If the backend cannot assign a new uid, it returns the uid passed in
        WITHOUT saving the message.

        If the backend CAN assign a new uid, but cannot find out what this UID
        is (as is the case with many IMAP servers), it returns 0 but DOES save
        the message.
        
        IMAP backend should be the only one that can assign a new uid.

        If the uid is > 0, the backend should set the uid to this, if it can.
        If it cannot set the uid to that, it will save it anyway.
        It will return the uid assigned in any case.
        """
        raise NotImplementedException

    def getmessageflags(self, uid):
        """Returns the flags for the specified message."""
        raise NotImplementedException

    def savemessageflags(self, uid, flags):
        """Sets the specified message's flags to the given set."""
        raise NotImplementedException

    def addmessageflags(self, uid, flags):
        """Adds the specified flags to the message's flag set.  If a given
        flag is already present, it will not be duplicated."""
        newflags = self.getmessageflags(uid)
        for flag in flags:
            if not flag in newflags:
                newflags.append(flag)
        newflags.sort()
        self.savemessageflags(uid, newflags)

    def addmessagesflags(self, uidlist, flags):
        for uid in uidlist:
            self.addmessageflags(uid, flags)

    def deletemessageflags(self, uid, flags):
        """Removes each flag given from the message's flag set.  If a given
        flag is already removed, no action will be taken for that flag."""
        newflags = self.getmessageflags(uid)
        for flag in flags:
            if flag in newflags:
                newflags.remove(flag)
        newflags.sort()
        self.savemessageflags(uid, newflags)

    def deletemessagesflags(self, uidlist, flags):
        for uid in uidlist:
            self.deletemessageflags(uid, flags)

    def deletemessage(self, uid):
        raise NotImplementedException

    def deletemessages(self, uidlist):
        for uid in uidlist:
            self.deletemessage(uid)

    def syncmessagesto_neguid_msg(self, uid, dest, applyto, register = 1):
        if register:
            UIBase.getglobalui().registerthread(self.getaccountname())
        UIBase.getglobalui().copyingmessage(uid, self, applyto)
        successobject = None
        successuid = None
        message = self.getmessage(uid)
        flags = self.getmessageflags(uid)
        for tryappend in applyto:
            successuid = tryappend.savemessage(uid, message, flags)
            if successuid >= 0:
                successobject = tryappend
                break
        # Did we succeed?
        if successobject != None:
            if successuid:       # Only if IMAP actually assigned a UID
                # Copy the message to the other remote servers.
                for appendserver in \
                        [x for x in applyto if x != successobject]:
                    appendserver.savemessage(successuid, message, flags)
                    # Copy to its new name on the local server and delete
                    # the one without a UID.
                    self.savemessage(successuid, message, flags)
            self.deletemessage(uid) # It'll be re-downloaded.
        else:
            # Did not find any server to take this message.  Ignore.
            pass
        

    def syncmessagesto_neguid(self, dest, applyto):
        """Pass 1 of folder synchronization.

        Look for messages in self with a negative uid.  These are messages in
        Maildirs that were not added by us.  Try to add them to the dests,
        and once that succeeds, get the UID, add it to the others for real,
        add it to local for real, and delete the fake one."""

        uidlist = [uid for uid in self.getmessagelist().keys() if uid < 0]
        threads = []

        usethread = None
        if applyto != None:
            usethread = applyto[0]
        
        for uid in uidlist:
            if usethread and usethread.suggeststhreads():
                usethread.waitforthread()
                thread = InstanceLimitedThread(\
                    usethread.getcopyinstancelimit(),
                    target = self.syncmessagesto_neguid_msg,
                    name = "New msg sync from %s" % self.getvisiblename(),
                    args = (uid, dest, applyto))
                thread.setDaemon(1)
                thread.start()
                threads.append(thread)
            else:
                self.syncmessagesto_neguid_msg(uid, dest, applyto, register = 0)
        for thread in threads:
            thread.join()

    def copymessageto(self, uid, applyto, register = 1):
        # Sometimes, it could be the case that if a sync takes awhile,
        # a message might be deleted from the maildir before it can be
        # synced to the status cache.  This is only a problem with
        # self.getmessage().  So, don't call self.getmessage unless
        # really needed.
        if register:
            UIBase.getglobalui().registerthread(self.getaccountname())
        UIBase.getglobalui().copyingmessage(uid, self, applyto)
        message = ''
        # If any of the destinations actually stores the message body,
        # load it up.
        for object in applyto:
            if object.storesmessages():
                message = self.getmessage(uid)
                break
        flags = self.getmessageflags(uid)
        for object in applyto:
            newuid = object.savemessage(uid, message, flags)
            if newuid > 0 and newuid != uid:
                # Change the local uid.
                self.savemessage(newuid, message, flags)
                self.deletemessage(uid)
                uid = newuid
        

    def syncmessagesto_copy(self, dest, applyto):
        """Pass 2 of folder synchronization.

        Look for messages present in self but not in dest.  If any, add
        them to dest."""
        threads = []
        
        for uid in self.getmessagelist().keys():
            if uid < 0:                 # Ignore messages that pass 1 missed.
                continue
            if not uid in dest.getmessagelist():
                if self.suggeststhreads():
                    self.waitforthread()
                    thread = InstanceLimitedThread(\
                        self.getcopyinstancelimit(),
                        target = self.copymessageto,
                        name = "Copy message %d from %s" % (uid,
                                                            self.getvisiblename()),
                        args = (uid, applyto))
                    thread.setDaemon(1)
                    thread.start()
                    threads.append(thread)
                else:
                    self.copymessageto(uid, applyto, register = 0)
        for thread in threads:
            thread.join()

    def syncmessagesto_delete(self, dest, applyto):
        """Pass 3 of folder synchronization.

        Look for message present in dest but not in self.
        If any, delete them."""
        deletelist = []
        for uid in dest.getmessagelist().keys():
            if uid < 0:
                continue
            if not uid in self.getmessagelist():
                deletelist.append(uid)
        if len(deletelist):
            UIBase.getglobalui().deletingmessages(deletelist, applyto)
            for object in applyto:
                object.deletemessages(deletelist)

    def syncmessagesto_flags(self, dest, applyto):
        """Pass 4 of folder synchronization.

        Look for any flag matching issues -- set dest message to have the
        same flags that we have."""

        # As an optimization over previous versions, we store up which flags
        # are being used for an add or a delete.  For each flag, we store
        # a list of uids to which it should be added.  Then, we can call
        # addmessagesflags() to apply them in bulk, rather than one
        # call per message as before.  This should result in some significant
        # performance improvements.

        addflaglist = {}
        delflaglist = {}
        
        for uid in self.getmessagelist().keys():
            if uid < 0:                 # Ignore messages missed by pass 1
                continue
            selfflags = self.getmessageflags(uid)
            destflags = dest.getmessageflags(uid)

            addflags = [x for x in selfflags if x not in destflags]

            for flag in addflags:
                if not flag in addflaglist:
                    addflaglist[flag] = []
                addflaglist[flag].append(uid)

            delflags = [x for x in destflags if x not in selfflags]
            for flag in delflags:
                if not flag in delflaglist:
                    delflaglist[flag] = []
                delflaglist[flag].append(uid)

        for object in applyto:
            for flag in addflaglist.keys():
                UIBase.getglobalui().addingflags(addflaglist[flag], flag, [object])
                object.addmessagesflags(addflaglist[flag], [flag])
            for flag in delflaglist.keys():
                UIBase.getglobalui().deletingflags(delflaglist[flag], flag, [object])
                object.deletemessagesflags(delflaglist[flag], [flag])
                
    def syncmessagesto(self, dest, applyto = None):
        """Syncs messages in this folder to the destination.
        If applyto is specified, it should be a list of folders (don't forget
        to include dest!) to which all write actions should be applied.
        It defaults to [dest] if not specified.  It is important that
        the UID generator be listed first in applyto; that is, the other
        applyto ones should be the ones that "copy" the main action."""
        if applyto == None:
            applyto = [dest]
            
        self.syncmessagesto_neguid(dest, applyto)
        self.syncmessagesto_copy(dest, applyto)
        self.syncmessagesto_delete(dest, applyto)
        
        # Now, the message lists should be identical wrt the uids present.
        # (except for potential negative uids that couldn't be placed
        # anywhere)

        self.syncmessagesto_flags(dest, applyto)
        
            
