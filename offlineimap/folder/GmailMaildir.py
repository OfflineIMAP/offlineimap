# Maildir folder support with labels
# Copyright (C) 2002 - 2011 John Goerzen & contributors
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


import os
from .Maildir import MaildirFolder
from offlineimap import OfflineImapError
import offlineimap.accounts

class GmailMaildirFolder(MaildirFolder):
    """Folder implementation to support adding labels to messages in a Maildir.
    """
    def __init__(self, root, name, sep, repository):
        super(GmailMaildirFolder, self).__init__(root, name, sep, repository)

        # The header under which labels are stored
        self.labelsheader = self.repository.account.getconf('labelsheader', 'X-Keywords')

        # enables / disables label sync
        self.synclabels = self.repository.account.getconfboolean('synclabels', 0)

        # if synclabels is enabled, add a 4th pass to sync labels
        if self.synclabels:
            self.syncmessagesto_passes.append(('syncing labels', self.syncmessagesto_labels))

    def quickchanged(self, statusfolder):
        """Returns True if the Maildir has changed. Checks uids, flags and mtimes"""

        self.cachemessagelist()
        # Folder has different uids than statusfolder => TRUE
        if sorted(self.getmessageuidlist()) != \
                sorted(statusfolder.getmessageuidlist()):
            return True
        # check for flag changes, it's quick on a Maildir
        for (uid, message) in self.getmessagelist().iteritems():
            if message['flags'] != statusfolder.getmessageflags(uid):
                return True
        # check for newer mtimes. it is also fast
        for (uid, message) in self.getmessagelist().iteritems():
            if message['mtime'] > statusfolder.getmessagemtime(uid):
                return True
        return False  #Nope, nothing changed

    def cachemessagelist(self):
        if self.messagelist is None:
            self.messagelist = self._scanfolder()

        # Get mtimes
        if self.synclabels:
            for uid, msg in self.messagelist.items():
                filepath = os.path.join(self.getfullname(), msg['filename'])
                msg['mtime'] = long(os.stat(filepath).st_mtime)

    def getmessagelabels(self, uid):
        # Labels are not cached in cachemessagelist because it is too slow.
        if not 'labels' in self.messagelist[uid]:
            filename = self.messagelist[uid]['filename']
            filepath = os.path.join(self.getfullname(), filename)

            if not os.path.exists(filepath):
                return set()

            file = open(filepath, 'rt')
            content = file.read()
            file.close()

            labels = self.message_getheader(content, self.labelsheader)
            if labels:
                labels = set([lb.strip() for lb in labels.split(',') if len(lb.strip()) > 0])
            else:
                labels = set()
            self.messagelist[uid]['labels'] = labels

        return self.messagelist[uid]['labels']

    def getmessagemtime(self, uid):
        if not 'mtime' in self.messagelist[uid]:
            return 0
        else:
            return self.messagelist[uid]['mtime']

    def savemessage(self, uid, content, flags, rtime):
        """Writes a new message, with the specified uid.

        See folder/Base for detail. Note that savemessage() does not
        check against dryrun settings, so you need to ensure that
        savemessage is never called in a dryrun mode."""

        if not self.synclabels:
            return super(GmailMaildirFolder, self).savemessage(uid, content, flags, rtime)

        labels = self.message_getheader(content, self.labelsheader)
        if labels:
            labels = set([lb.strip() for lb in labels.split(',') if len(lb.strip()) > 0])
        else:
            labels = set()
        ret = super(GmailMaildirFolder, self).savemessage(uid, content, flags, rtime)

        # Update the mtime and labels
        filename = self.messagelist[uid]['filename']
        filepath = os.path.join(self.getfullname(), filename)
        self.messagelist[uid]['mtime'] = long(os.stat(filepath).st_mtime)
        self.messagelist[uid]['labels'] = labels
        return ret

    def savemessagelabels(self, uid, labels, ignorelabels=set()):
        """Change a message's labels to `labels`.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a dryrun mode."""

        filename = self.messagelist[uid]['filename']
        filepath = os.path.join(self.getfullname(), filename)

        file = open(filepath, 'rt')
        content = file.read()
        file.close()

        oldlabels = self.message_getheader(content, self.labelsheader)

        if oldlabels:
            oldlabels = set([lb.strip() for lb in oldlabels.split(',') if len(lb.strip()) > 0])
        else:
            oldlabels = set()

        labels = labels - ignorelabels
        ignoredlabels = oldlabels & ignorelabels
        oldlabels = oldlabels - ignorelabels

        # Nothing to change
        if labels == oldlabels:
            return

        # Change labels into content
        labels_str = ', '.join(sorted(labels | ignoredlabels))
        content = self.message_addheader(content, self.labelsheader, labels_str)
        rtime = self.messagelist[uid].get('rtime', None)

        # Write file to tmp
        tmppath = os.path.join(self.getfullname(), 'tmp', os.path.basename(self.messagelist[uid]['filename']))
        file = open(tmppath, 'wt')
        file.write(content)
        file.close()

        # move to actual location
        os.rename(tmppath, filepath)
        if rtime != None:
            os.utime(filepath, (rtime, rtime))

        # save the new mtime and labels
        self.messagelist[uid]['mtime'] = long(os.stat(filepath).st_mtime)
        self.messagelist[uid]['labels'] = labels

    def copymessageto(self, uid, dstfolder, statusfolder, register = 1):
        """Copies a message from self to dst if needed, updating the status

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a
        dryrun mode.

        :param uid: uid of the message to be copied.
        :param dstfolder: A BaseFolder-derived instance
        :param statusfolder: A LocalStatusFolder instance
        :param register: whether we should register a new thread."
        :returns: Nothing on success, or raises an Exception."""

        # Check if we are really copying
        realcopy = uid > 0 and not dstfolder.uidexists(uid)

        # first copy the message
        super(GmailMaildirFolder, self).copymessageto(uid, dstfolder, statusfolder, register)

        # sync labels and mtime now when the message is new (the embedded labels are up to date,
        # and have already propagated to the remote server.
        # for message which already existed on the remote, this is useless, as later the labels may
        # get updated.
        if realcopy and self.synclabels:
            try:
                labels = dstfolder.getmessagelabels(uid)
                statusfolder.savemessagelabels(uid, labels, mtime=self.getmessagemtime(uid))

            # either statusfolder is not sqlite or dstfolder is not GmailMaildir.
            except NotImplementedError:
                return

    def syncmessagesto_labels(self, dstfolder, statusfolder):
        """Pass 4: Label Synchronization (Gmail only)

        Compare label mismatches in self with those in statusfolder. If
        msg has a valid UID and exists on dstfolder (has not e.g. been
        deleted there), sync the labels change to both dstfolder and
        statusfolder.

        Also skips messages whose mtime remains the same as statusfolder, as the
        contents have not changed.

        This function checks and protects us from action in ryrun mode.
        """
        # For each label, we store a list of uids to which it should be
        # added.  Then, we can call addmessageslabels() to apply them in
        # bulk, rather than one call per message.

        addlabellist = {}
        dellabellist = {}
        try:
            # filter out negative uid's missed by pass 1,
            # also skip if message deleted mtime has not changed.
            uidlist = [uid for uid in self.getmessageuidlist()
                       if uid >= 0 and dstfolder.uidexists(uid) and
                       self.getmessagemtime(uid) > statusfolder.getmessagemtime(uid)]

            self.ui.collectingdata(uidlist, self)
            # This can be slow if there is a lot of modified files
            for uid in uidlist:
                # bail out on CTRL-C or SIGTERM
                if offlineimap.accounts.Account.abort_NOW_signal.is_set():
                    break

                selflabels = self.getmessagelabels(uid)
                statuslabels = statusfolder.getmessagelabels(uid)

                addlabels = selflabels - statuslabels
                dellabels = statuslabels - selflabels

                for lb in addlabels:
                    if not lb in addlabellist:
                        addlabellist[lb] = []
                    addlabellist[lb].append(uid)

                for lb in dellabels:
                    if not lb in dellabellist:
                        dellabellist[lb] = []
                    dellabellist[lb].append(uid)

            for lb, uids in addlabellist.items():
                # bail out on CTRL-C or SIGTERM
                if offlineimap.accounts.Account.abort_NOW_signal.is_set():
                    break

                self.ui.addinglabels(uids, lb, dstfolder)
                if self.repository.account.dryrun:
                    continue #don't actually add in a dryrun
                dstfolder.addmessageslabels(uids, set([lb]))
                statusfolder.addmessageslabels(uids, set([lb]))

            for lb, uids in dellabellist.items():
                # bail out on CTRL-C or SIGTERM
                if offlineimap.accounts.Account.abort_NOW_signal.is_set():
                    break

                self.ui.deletinglabels(uids, lb, dstfolder)
                if self.repository.account.dryrun:
                    continue #don't actually remove in a dryrun
                dstfolder.deletemessageslabels(uids, set([lb]))
                statusfolder.deletemessageslabels(uids, set([lb]))

            # Update mtimes on StatusFolder. It is done last to be safe. If something els fails
            # and the mtime is not updated, the labels will still be synced next time.
            mtimes = {}
            for uid in uidlist:
                # bail out on CTRL-C or SIGTERM
                if offlineimap.accounts.Account.abort_NOW_signal.is_set():
                    break

                if self.repository.account.dryrun:
                    continue #don't actually update statusfolder

                filename = self.messagelist[uid]['filename']
                filepath = os.path.join(self.getfullname(), filename)
                mtimes[uid] = long(os.stat(filepath).st_mtime)

            # finally update statusfolder in a single DB transaction
            statusfolder.savemessagesmtimebulk(mtimes)

        except NotImplementedError:
            self.ui.warn("Can't sync labels. You need to configure a remote repository of type Gmail.")
