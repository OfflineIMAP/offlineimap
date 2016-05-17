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

import re
from sys import exc_info

from offlineimap import imaputil, OfflineImapError
from offlineimap import imaplibutil
import offlineimap.accounts
from .IMAP import IMAPFolder

import six

"""Folder implementation to support features of the Gmail IMAP server."""

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
      https://developers.google.com/google-apps/gmail/imap_extensions
    """

    def __init__(self, imapserver, name, repository):
        super(GmailFolder, self).__init__(imapserver, name, repository)
        self.trash_folder = repository.gettrashfolder(name)
        # Gmail will really delete messages upon EXPUNGE in these folders
        self.real_delete_folders =  [ self.trash_folder, repository.getspamfolder() ]

        # The header under which labels are stored
        self.labelsheader = self.repository.account.getconf('labelsheader', 'X-Keywords')

        # enables / disables label sync
        self.synclabels = self.repository.account.getconfboolean('synclabels', False)

        # if synclabels is enabled, add a 4th pass to sync labels
        if self.synclabels:
            self.imap_query.insert(0, 'X-GM-LABELS')
            self.syncmessagesto_passes.append(('syncing labels', self.syncmessagesto_labels))

        # Labels to be left alone
        ignorelabels =  self.repository.account.getconf('ignorelabels', '')
        self.ignorelabels = set([l for l in re.split(r'\s*,\s*', ignorelabels) if len(l)])


    def getmessage(self, uid):
        """Retrieve message with UID from the IMAP server (incl body).  Also
           gets Gmail labels and embeds them into the message.

        :returns: the message body or throws and OfflineImapError
                  (probably severity MESSAGE) if e.g. no message with
                  this UID could be found.
        """
        data = self._fetch_from_imap(str(uid), 2)

        # data looks now e.g.
        #[('320 (X-GM-LABELS (...) UID 17061 BODY[] {2565}','msgbody....')]
        # we only asked for one message, and that msg is in data[0].
        # msbody is in [0][1].
        body = data[0][1].replace("\r\n", "\n")

        # Embed the labels into the message headers
        if self.synclabels:
            m = re.search('X-GM-LABELS\s*\(([^\)]*)\)', data[0][0])
            if m:
                labels = set([imaputil.dequote(lb) for lb in imaputil.imapsplit(m.group(1))])
            else:
                labels = set()
            labels = labels - self.ignorelabels
            labels_str = imaputil.format_labels_string(self.labelsheader, sorted(labels))

            # First remove old label headers that may be in the message content retrieved
            # from gmail Then add a labels header with current gmail labels.
            body = self.deletemessageheaders(body, self.labelsheader)
            body = self.addmessageheader(body, '\n', self.labelsheader, labels_str)

        if len(body)>200:
            dbg_output = "%s...%s"% (str(body)[:150], str(body)[-50:])
        else:
            dbg_output = body

        self.ui.debug('imap', "Returned object from fetching %d: '%s'"%
                      (uid, dbg_output))
        return body

    def getmessagelabels(self, uid):
        if 'labels' in self.messagelist[uid]:
            return self.messagelist[uid]['labels']
        else:
            return set()

    # Interface from BaseFolder
    def msglist_item_initializer(self, uid):
        return {'uid': uid, 'flags': set(), 'labels': set(), 'time': 0}


    # TODO: merge this code with the parent's cachemessagelist:
    # TODO: they have too much common logics.
    def cachemessagelist(self, min_date=None, min_uid=None):
        if not self.synclabels:
            return super(GmailFolder, self).cachemessagelist(
                min_date=min_date, min_uid=min_uid)

        self.dropmessagelistcache()

        self.ui.collectingdata(None, self)
        imapobj = self.imapserver.acquireconnection()
        try:
            msgsToFetch = self._msgs_to_fetch(
                imapobj, min_date=min_date, min_uid=min_uid)
            if not msgsToFetch:
                return # No messages to sync

            # Get the flags and UIDs for these. single-quotes prevent
            # imaplib2 from quoting the sequence.
            #
            # NB: msgsToFetch are sequential numbers, not UID's
            res_type, response = imapobj.fetch("'%s'"% msgsToFetch,
              '(FLAGS X-GM-LABELS UID)')
            if res_type != 'OK':
                six.reraise(OfflineImapError("FETCHING UIDs in folder [%s]%s failed. " % \
                  (self.getrepository(), self) + \
                  "Server responded '[%s] %s'" % \
                  (res_type, response), OfflineImapError.ERROR.FOLDER), None, exc_info()[2])
        finally:
            self.imapserver.releaseconnection(imapobj)

        for messagestr in response:
            # looks like: '1 (FLAGS (\\Seen Old) X-GM-LABELS (\\Inbox \\Favorites) UID 4807)' or None if no msg
            # Discard initial message number.
            if messagestr == None:
                continue
            messagestr = messagestr.split(' ', 1)[1]
            options = imaputil.flags2hash(messagestr)
            if not 'UID' in options:
                self.ui.warn('No UID in message with options %s' %\
                                          str(options),
                                          minor = 1)
            else:
                uid = int(options['UID'])
                self.messagelist[uid] = self.msglist_item_initializer(uid)
                flags = imaputil.flagsimap2maildir(options['FLAGS'])
                m = re.search('\(([^\)]*)\)', options['X-GM-LABELS'])
                if m:
                    labels = set([imaputil.dequote(lb) for lb in imaputil.imapsplit(m.group(1))])
                else:
                    labels = set()
                labels = labels - self.ignorelabels
                rtime = imaplibutil.Internaldate2epoch(messagestr)
                self.messagelist[uid] = {'uid': uid, 'flags': flags, 'labels': labels, 'time': rtime}

    def savemessage(self, uid, content, flags, rtime):
        """Save the message on the Server

        This backend always assigns a new uid, so the uid arg is ignored.

        This function will update the self.messagelist dict to contain
        the new message after sucessfully saving it, including labels.

        See folder/Base for details. Note that savemessage() does not
        check against dryrun settings, so you need to ensure that
        savemessage is never called in a dryrun mode.

        :param rtime: A timestamp to be used as the mail date
        :returns: the UID of the new message as assigned by the server. If the
                  message is saved, but it's UID can not be found, it will
                  return 0. If the message can't be written (folder is
                  read-only for example) it will return -1."""

        if not self.synclabels:
            return super(GmailFolder, self).savemessage(uid, content, flags, rtime)

        labels = set()
        for hstr in self.getmessageheaderlist(content, self.labelsheader):
            labels.update(imaputil.labels_from_header(self.labelsheader, hstr))

        ret = super(GmailFolder, self).savemessage(uid, content, flags, rtime)
        self.savemessagelabels(ret, labels)
        return ret

    def _messagelabels_aux(self, arg, uidlist, labels):
        """Common code to savemessagelabels and addmessagelabels"""
        labels = labels - self.ignorelabels
        uidlist = [uid for uid in uidlist if uid > 0]
        if len(uidlist) > 0:
            imapobj = self.imapserver.acquireconnection()
            try:
                labels_str = '(' + ' '.join([imaputil.quote(lb) for lb in labels]) + ')'
                # Coalesce uid's into ranges
                uid_str = imaputil.uid_sequence(uidlist)
                result = self._store_to_imap(imapobj, uid_str, arg, labels_str)

            except imapobj.readonly:
                self.ui.labelstoreadonly(self, uidlist, labels)
                return None

            finally:
                self.imapserver.releaseconnection(imapobj)

            if result:
                retlabels = imaputil.flags2hash(imaputil.imapsplit(result)[1])['X-GM-LABELS']
                retlabels = set([imaputil.dequote(lb) for lb in imaputil.imapsplit(retlabels)])
                return retlabels
        return None

    def savemessagelabels(self, uid, labels):
        """Change a message's labels to `labels`.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a dryrun mode."""
        if uid in self.messagelist and 'labels' in self.messagelist[uid]:
            oldlabels = self.messagelist[uid]['labels']
        else:
            oldlabels = set()
        labels = labels - self.ignorelabels
        newlabels = labels | (oldlabels & self.ignorelabels)
        if oldlabels != newlabels:
            result = self._messagelabels_aux('X-GM-LABELS', [uid], newlabels)
            if result:
                self.messagelist[uid]['labels'] = newlabels
            else:
                self.messagelist[uid]['labels'] = oldlabels

    def addmessageslabels(self, uidlist, labels):
        """Add `labels` to all messages in uidlist.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a dryrun mode."""

        labels = labels - self.ignorelabels
        result = self._messagelabels_aux('+X-GM-LABELS', uidlist, labels)
        if result:
            for uid in uidlist:
                self.messagelist[uid]['labels'] = self.messagelist[uid]['labels'] | labels

    def deletemessageslabels(self, uidlist, labels):
        """Delete `labels` from all messages in uidlist.

        Note that this function does not check against dryrun settings,
        so you need to ensure that it is never called in a dryrun mode."""

        labels = labels - self.ignorelabels
        result = self._messagelabels_aux('-X-GM-LABELS', uidlist, labels)
        if result:
            for uid in uidlist:
                self.messagelist[uid]['labels'] = self.messagelist[uid]['labels'] - labels

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
        super(GmailFolder, self).copymessageto(uid, dstfolder, statusfolder, register)

        # sync labels and mtime now when the message is new (the embedded labels are up to date)
        # otherwise we may be spending time for nothing, as they will get updated on a later pass.
        if realcopy and self.synclabels:
            try:
                mtime = dstfolder.getmessagemtime(uid)
                labels = dstfolder.getmessagelabels(uid)
                statusfolder.savemessagelabels(uid, labels, mtime=mtime)

            # dstfolder is not GmailMaildir.
            except NotImplementedError:
                return

    def syncmessagesto_labels(self, dstfolder, statusfolder):
        """Pass 4: Label Synchronization (Gmail only)

        Compare label mismatches in self with those in statusfolder. If
        msg has a valid UID and exists on dstfolder (has not e.g. been
        deleted there), sync the labels change to both dstfolder and
        statusfolder.

        This function checks and protects us from action in dryrun mode.
        """
        # This applies the labels message by message, as this makes more sense for a
        # Maildir target. If applied with an other Gmail IMAP target it would not be
        # the fastest thing in the world though...
        uidlist = []

        # filter the uids (fast)
        try:
            for uid in self.getmessageuidlist():
                # bail out on CTRL-C or SIGTERM
                if offlineimap.accounts.Account.abort_NOW_signal.is_set():
                    break

                # Ignore messages with negative UIDs missed by pass 1 and
                # don't do anything if the message has been deleted remotely
                if uid < 0 or not dstfolder.uidexists(uid):
                    continue

                selflabels = self.getmessagelabels(uid) - self.ignorelabels

                if statusfolder.uidexists(uid):
                    statuslabels = statusfolder.getmessagelabels(uid) - self.ignorelabels
                else:
                    statuslabels = set()

                if selflabels != statuslabels:
                    uidlist.append(uid)

            # now sync labels (slow)
            mtimes = {}
            labels = {}
            for i, uid in enumerate(uidlist):
                # bail out on CTRL-C or SIGTERM
                if offlineimap.accounts.Account.abort_NOW_signal.is_set():
                    break

                selflabels = self.getmessagelabels(uid) - self.ignorelabels

                if statusfolder.uidexists(uid):
                    statuslabels = statusfolder.getmessagelabels(uid) - self.ignorelabels
                else:
                    statuslabels = set()

                if selflabels != statuslabels:
                    self.ui.settinglabels(uid, i+1, len(uidlist), sorted(selflabels), dstfolder)
                    if self.repository.account.dryrun:
                        continue #don't actually add in a dryrun
                    dstfolder.savemessagelabels(uid, selflabels, ignorelabels = self.ignorelabels)
                    mtime = dstfolder.getmessagemtime(uid)
                    mtimes[uid] = mtime
                    labels[uid] = selflabels

            # Update statusfolder in a single DB transaction. It is safe, as if something fails,
            # statusfolder will be updated on the next run.
            statusfolder.savemessageslabelsbulk(labels)
            statusfolder.savemessagesmtimebulk(mtimes)

        except NotImplementedError:
            self.ui.warn("Can't sync labels. You need to configure a local repository of type GmailMaildir")
