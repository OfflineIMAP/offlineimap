# UI base class
# Copyright (C) 2002-2015 John Goerzen & contributors
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

import logging
import logging.handlers
import re
import time
import sys
import traceback
import threading
try:
    from Queue import Queue
except ImportError: #python3
    from queue import Queue
from collections import deque
from offlineimap.error import OfflineImapError
import offlineimap

debugtypes = {'':'Other offlineimap related sync messages',
              'imap': 'IMAP protocol debugging',
              'maildir': 'Maildir repository debugging',
              'thread': 'Threading debugging'}

globalui = None
def setglobalui(newui):
    """Set the global ui object to be used for logging."""

    global globalui
    globalui = newui

def getglobalui():
    """Return the current ui object."""

    global globalui
    return globalui


class UIBase(object):
    def __init__(self, config, loglevel=logging.INFO):
        self.config = config
        # Is this a 'dryrun'?
        self.dryrun = config.getdefaultboolean('general', 'dry-run', False)
        self.debuglist = []
        # list of debugtypes we are supposed to log
        self.debugmessages = {}
        # debugmessages in a deque(v) per thread(k)
        self.debugmsglen = 15
        self.threadaccounts = {}
        # dict linking active threads (k) to account names (v)
        self.acct_startimes = {}
        # linking active accounts with the time.time() when sync started
        self.logfile = None
        self.exc_queue = Queue()
        # saves all occuring exceptions, so we can output them at the end
        self.uidval_problem = False
        # at least one folder skipped due to UID validity problem
        # create logger with 'OfflineImap' app
        self.logger = logging.getLogger('OfflineImap')
        self.logger.setLevel(loglevel)
        self._log_con_handler = self.setup_consolehandler()
        """The console handler (we need access to be able to lock it)."""

    ################################################## UTILS
    def setup_consolehandler(self):
        """Backend specific console handler.

        Sets up things and adds them to self.logger.
        :returns: The logging.Handler() for console output"""

        # create console handler with a higher log level
        ch = logging.StreamHandler(sys.stdout)
        #ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        self.formatter = logging.Formatter("%(message)s")
        ch.setFormatter(self.formatter)
        # add the handlers to the logger
        self.logger.addHandler(ch)
        self.logger.info(offlineimap.banner)
        return ch

    def setup_sysloghandler(self):
        """Backend specific syslog handler."""

        # create syslog handler
        ch = logging.handlers.SysLogHandler('/dev/log')
        # create formatter and add it to the handlers
        self.formatter = logging.Formatter("%(message)s")
        ch.setFormatter(self.formatter)
        # add the handlers to the logger
        self.logger.addHandler(ch)

    def setlogfile(self, logfile):
        """Create file handler which logs to file."""

        fh = logging.FileHandler(logfile, 'at')
        #fh.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s %(levelname)s: "
            "%(message)s", '%Y-%m-%d %H:%M:%S')
        fh.setFormatter(file_formatter)
        self.logger.addHandler(fh)
        # write out more verbose initial info blurb on the log file
        p_ver = ".".join([str(x) for x in sys.version_info[0:3]])
        msg = "OfflineImap %s starting...\n  Python: %s Platform: %s\n  "\
              "Args: %s"% (offlineimap.__version__, p_ver, sys.platform,
                            " ".join(sys.argv))
        record = logging.LogRecord('OfflineImap', logging.INFO, __file__,
                                   None, msg, None, None)
        fh.emit(record)

    def _msg(self, msg):
        """Display a message."""

        # TODO: legacy function, rip out.
        self.info(msg)

    def info(self, msg):
        """Display a message."""

        self.logger.info(msg)

    def warn(self, msg, minor=0):
        self.logger.warning(msg)

    def error(self, exc, exc_traceback=None, msg=None):
        """Log a message at severity level ERROR.

        Log Exception 'exc' to error log, possibly prepended by a preceding
        error "msg", detailing at what point the error occurred.

        In debug mode, we also output the full traceback that occurred
        if one has been passed in via sys.info()[2].

        Also save the Exception to a stack that can be output at the end
        of the sync run when offlineiamp exits. It is recommended to
        always pass in exceptions if possible, so we can give the user
        the best debugging info.
        
        We are always pushing tracebacks to the exception queue to
        make them to be output at the end of the run to allow users
        pass sensible diagnostics to the developers or to solve
        problems by themselves.

        One example of such a call might be:

           ui.error(exc, sys.exc_info()[2], msg="While syncing Folder %s in "
               "repo %s")
        """
        if msg:
            self.logger.error("ERROR: %s\n  %s" % (msg, exc))
        else:
            self.logger.error("ERROR: %s" % (exc))

        instant_traceback = exc_traceback
        if not self.debuglist:
            # only output tracebacks in debug mode
            instant_traceback = None
        # push exc on the queue for later output
        self.exc_queue.put((msg, exc, exc_traceback))
        if instant_traceback:
            self.logger.error(traceback.format_tb(instant_traceback))

    def registerthread(self, account):
        """Register current thread as being associated with an account name."""

        cur_thread = threading.currentThread()
        if cur_thread in self.threadaccounts:
            # was already associated with an old account, update info
            self.debug('thread', "Register thread '%s' (previously '%s', now "
                    "'%s')" % (cur_thread.getName(),
                               self.getthreadaccount(cur_thread), account))
        else:
            self.debug('thread', "Register new thread '%s' (account '%s')"%
                (cur_thread.getName(), account))
        self.threadaccounts[cur_thread] = account

    def unregisterthread(self, thr):
        """Unregister a thread as being associated with an account name."""

        if thr in self.threadaccounts:
            del self.threadaccounts[thr]
        self.debug('thread', "Unregister thread '%s'" % thr.getName())

    def getthreadaccount(self, thr=None):
        """Get Account() for a thread (current if None)

        If no account has been registered with this thread, return 'None'."""

        if thr == None:
            thr = threading.currentThread()
        if thr in self.threadaccounts:
            return self.threadaccounts[thr]
        return None

    def debug(self, debugtype, msg):
        cur_thread = threading.currentThread()
        if not cur_thread in self.debugmessages:
            # deque(..., self.debugmsglen) would be handy but was
            # introduced in p2.6 only, so we'll need to work around and
            # shorten our debugmsg list manually :-(
            self.debugmessages[cur_thread] = deque()
        self.debugmessages[cur_thread].append("%s: %s" % (debugtype, msg))

        # Shorten queue if needed
        if len(self.debugmessages[cur_thread]) > self.debugmsglen:
            self.debugmessages[cur_thread].popleft()

        if debugtype in self.debuglist: # log if we are supposed to do so
            self.logger.debug("[%s]: %s" % (debugtype, msg))

    def add_debug(self, debugtype):
        global debugtypes
        if debugtype in debugtypes:
            if not debugtype in self.debuglist:
                self.debuglist.append(debugtype)
                self.debugging(debugtype)
        else:
            self.invaliddebug(debugtype)

    def debugging(self, debugtype):
        global debugtypes
        self.logger.debug("Now debugging for %s: %s" % (debugtype,
                                                        debugtypes[debugtype]))

    def invaliddebug(self, debugtype):
        self.warn("Invalid debug type: %s" % debugtype)

    def getnicename(self, object):
        """Return the type of a repository or Folder as string.

        (IMAP, Gmail, Maildir, etc...)"""

        prelimname = object.__class__.__name__.split('.')[-1]
        # Strip off extra stuff.
        return re.sub('(Folder|Repository)', '', prelimname)

    def isusable(self):
        """Returns true if this UI object is usable in the current
        environment.  For instance, an X GUI would return true if it's
        being run in X with a valid DISPLAY setting, and false otherwise."""

        return True

    ################################################## INPUT

    def getpass(self, accountname, config, errmsg = None):
        raise NotImplementedError("Prompting for a password is not supported"
            " in this UI backend.")

    def folderlist(self, folder_list):
        return ', '.join(["%s[%s]"% \
            (self.getnicename(x), x.getname()) for x in folder_list])

    ################################################## WARNINGS
    def msgtoreadonly(self, destfolder, uid, content, flags):
        if self.config.has_option('general', 'ignore-readonly') and \
            self.config.getboolean('general', 'ignore-readonly'):
            return
        self.warn("Attempted to synchronize message %d to folder %s[%s], "
            "but that folder is read-only.  The message will not be "
            "copied to that folder."% (
            uid, self.getnicename(destfolder), destfolder))

    def flagstoreadonly(self, destfolder, uidlist, flags):
        if self.config.has_option('general', 'ignore-readonly') and \
                self.config.getboolean('general', 'ignore-readonly'):
            return
        self.warn("Attempted to modify flags for messages %s in folder %s[%s], "
            "but that folder is read-only.  No flags have been modified "
            "for that message."% (
            str(uidlist), self.getnicename(destfolder), destfolder))

    def labelstoreadonly(self, destfolder, uidlist, labels):
        if self.config.has_option('general', 'ignore-readonly') and \
                self.config.getboolean('general', 'ignore-readonly'):
            return
        self.warn("Attempted to modify labels for messages %s in folder %s[%s], "
            "but that folder is read-only.  No labels have been modified "
            "for that message."% (
            str(uidlist), self.getnicename(destfolder), destfolder))

    def deletereadonly(self, destfolder, uidlist):
        if self.config.has_option('general', 'ignore-readonly') and \
                self.config.getboolean('general', 'ignore-readonly'):
            return
        self.warn("Attempted to delete messages %s in folder %s[%s], but that "
            "folder is read-only.  No messages have been deleted in that "
            "folder."% (str(uidlist), self.getnicename(destfolder),
            destfolder))

    ################################################## MESSAGES

    def init_banner(self):
        """Called when the UI starts.  Must be called before any other UI
        call except isusable().  Displays the copyright banner.  This is
        where the UI should do its setup -- TK, for instance, would
        create the application window here."""
        pass

    def connecting(self, hostname, port):
        """Log 'Establishing connection to'."""

        if not self.logger.isEnabledFor(logging.INFO): return
        displaystr = ''
        hostname = hostname if hostname else ''
        port = "%s"% port if port else ''
        if hostname:
            displaystr = ' to %s:%s' % (hostname, port)
        self.logger.info("Establishing connection%s" % displaystr)

    def acct(self, account):
        """Output that we start syncing an account (and start counting)."""

        self.acct_startimes[account] = time.time()
        self.logger.info("*** Processing account %s" % account)

    def acctdone(self, account):
        """Output that we finished syncing an account (in which time)."""

        sec = time.time() - self.acct_startimes[account]
        del self.acct_startimes[account]
        self.logger.info("*** Finished account '%s' in %d:%02d"%
            (account, sec // 60, sec % 60))

    def syncfolders(self, src_repo, dst_repo):
        """Log 'Copying folder structure...'."""

        if self.logger.isEnabledFor(logging.DEBUG):
            self.debug('', "Copying folder structure from %s to %s" %\
                           (src_repo, dst_repo))

    ############################## Folder syncing
    def makefolder(self, repo, foldername):
        """Called when a folder is created."""

        prefix = "[DRYRUN] " if self.dryrun else ""
        self.info(("{0}Creating folder {1}[{2}]".format(
            prefix, foldername, repo)))

    def syncingfolder(self, srcrepos, srcfolder, destrepos, destfolder):
        """Called when a folder sync operation is started."""

        self.logger.info("Syncing %s: %s -> %s"% (srcfolder,
            self.getnicename(srcrepos),
            self.getnicename(destrepos)))

    def skippingfolder(self, folder):
        """Called when a folder sync operation is started."""
        self.logger.info("Skipping %s (not changed)" % folder)

    def validityproblem(self, folder):
        self.uidval_problem = True
        self.logger.warning("UID validity problem for folder %s (repo %s) "
                            "(saved %d; got %d); skipping it. Please see FAQ "
                            "and manual on how to handle this."% \
               (folder, folder.getrepository(),
                folder.get_saveduidvalidity(), folder.get_uidvalidity()))

    def loadmessagelist(self, repos, folder):
        self.logger.debug("Loading message list for %s[%s]"% (
                self.getnicename(repos),
                folder))

    def messagelistloaded(self, repos, folder, count):
        self.logger.debug("Message list for %s[%s] loaded: %d messages" % (
                self.getnicename(repos), folder, count))

    ############################## Message syncing

    def syncingmessages(self, sr, srcfolder, dr, dstfolder):
        self.logger.debug("Syncing messages %s[%s] -> %s[%s]" % (
                self.getnicename(sr), srcfolder,
                self.getnicename(dr), dstfolder))

    def copyingmessage(self, uid, num, num_to_copy, src, destfolder):
        """Output a log line stating which message we copy"""
        self.logger.info("Copy message %s (%d of %d) %s:%s -> %s" % (
                uid, num, num_to_copy, src.repository, src,
                destfolder.repository))

    def deletingmessages(self, uidlist, destlist):
        ds = self.folderlist(destlist)
        prefix = "[DRYRUN] " if self.dryrun else ""
        self.info("{0}Deleting {1} messages ({2}) in {3}".format(
            prefix, len(uidlist),
            offlineimap.imaputil.uid_sequence(uidlist), ds))

    def addingflags(self, uidlist, flags, dest):
        self.logger.info("Adding flag %s to %d messages on %s" % (
                ", ".join(flags), len(uidlist), dest))

    def deletingflags(self, uidlist, flags, dest):
        self.logger.info("Deleting flag %s from %d messages on %s" % (
                ", ".join(flags), len(uidlist), dest))

    def addinglabels(self, uidlist, label, dest):
        self.logger.info("Adding label %s to %d messages on %s" % (
                label, len(uidlist), dest))

    def deletinglabels(self, uidlist, label, dest):
        self.logger.info("Deleting label %s from %d messages on %s" % (
                label, len(uidlist), dest))

    def settinglabels(self, uid, num, num_to_set, labels, dest):
        self.logger.info("Setting labels to message %d on %s (%d of %d): %s" % (
                uid, dest, num, num_to_set, ", ".join(labels)))

    def collectingdata(self, uidlist, source):
        if uidlist:
            self.logger.info("Collecting data from %d messages on %s"% (
                len(uidlist), source))
        else:
            self.logger.info("Collecting data from messages on %s"% source)

    def serverdiagnostics(self, repository, type):
        """Connect to repository and output useful information for debugging."""

        conn = None
        self._msg("%s repository '%s': type '%s'" % (type, repository.name,
                  self.getnicename(repository)))
        try:
            if hasattr(repository, 'gethost'): # IMAP
                self._msg("Host: %s Port: %s SSL: %s"% (repository.gethost(),
                    repository.getport(), repository.getssl()))
                try:
                    conn = repository.imapserver.acquireconnection()
                except OfflineImapError as e:
                    self._msg("Failed to connect. Reason %s" % e)
                else:
                    if 'ID' in conn.capabilities:
                        self._msg("Server supports ID extension.")
                        #TODO: Debug and make below working, it hangs Gmail
                        #res_type, response = conn.id((
                        #    'name', offlineimap.__productname__,
                        #    'version', offlineimap.__version__))
                        #self._msg("Server ID: %s %s" % (res_type, response[0]))
                    self._msg("Server welcome string: %s" % str(conn.welcome))
                    self._msg("Server capabilities: %s\n" % str(conn.capabilities))
                    repository.imapserver.releaseconnection(conn)
            if type != 'Status':
                folderfilter = repository.getconf('folderfilter', None)
                if folderfilter:
                    self._msg("folderfilter= %s\n" % folderfilter)
                folderincludes = repository.getconf('folderincludes', None)
                if folderincludes:
                    self._msg("folderincludes= %s\n" % folderincludes)
                nametrans = repository.getconf('nametrans', None)
                if nametrans:
                    self._msg("nametrans= %s\n" % nametrans)

                folders = repository.getfolders()
                foldernames = [(f.name, f.getvisiblename(), f.sync_this)
                    for f in folders]
                folders = []
                for name, visiblename, sync_this in foldernames:
                    syncstr = "" if sync_this else " (disabled)"
                    if name == visiblename: folders.append("%s%s" % (name,
                                                                     syncstr))
                    else: folders.append("%s -> %s%s" % (name,
                                                       visiblename, syncstr))
                self._msg("Folderlist:\n %s\n" % "\n ".join(folders))
        finally:
            if conn: #release any existing IMAP connection
                repository.imapserver.close()

    def savemessage(self, debugtype, uid, flags, folder):
        """Output a log line stating that we save a msg."""

        self.debug(debugtype, "Write mail '%s:%d' with flags %s"%
            (folder, uid, repr(flags)))

    ################################################## Threads

    def getThreadDebugLog(self, thread):
        if thread in self.debugmessages:
            message = "\nLast %d debug messages logged for %s prior to exception:\n"\
                       % (len(self.debugmessages[thread]), thread.getName())
            message += "\n".join(self.debugmessages[thread])
        else:
            message = "\nNo debug messages were logged for %s."% \
                thread.getName()
        return message

    def delThreadDebugLog(self, thread):
        if thread in self.debugmessages:
            del self.debugmessages[thread]

    def getThreadExceptionString(self, thread):
        message = "Thread '%s' terminated with exception:\n%s"% \
            (thread.getName(), thread.exit_stacktrace)
        message += "\n" + self.getThreadDebugLog(thread)
        return message

    def threadException(self, thread):
        """Called when a thread has terminated with an exception.
        The argument is the ExitNotifyThread that has so terminated."""

        self.warn(self.getThreadExceptionString(thread))
        self.delThreadDebugLog(thread)
        self.terminate(100)

    def terminate(self, exitstatus = 0, errortitle = None, errormsg = None):
        """Called to terminate the application."""

        #print any exceptions that have occurred over the run
        if not self.exc_queue.empty():
           self.warn("ERROR: Exceptions occurred during the run!")
           if exitstatus == 0:
               exitstatus = 1
        while not self.exc_queue.empty():
            msg, exc, exc_traceback = self.exc_queue.get()
            if msg:
                self.warn("ERROR: %s\n  %s"% (msg, exc))
            else:
                self.warn("ERROR: %s"% (exc))
            if exc_traceback:
                self.warn("\nTraceback:\n%s"% "".join(
                        traceback.format_tb(exc_traceback)))

        if errormsg and errortitle:
            self.warn('ERROR: %s\n\n%s\n'% (errortitle, errormsg))
        elif errormsg:
                self.warn('%s\n'% errormsg)
        if self.uidval_problem:
            self.warn('At least one folder skipped due to UID validity problem')
            if exitstatus == 0:
                exitstatus = 2
        sys.exit(exitstatus)

    def threadExited(self, thread):
        """Called when a thread has exited normally.

        Many UIs will just ignore this."""

        self.delThreadDebugLog(thread)
        self.unregisterthread(thread)

    ################################################## Hooks

    def callhook(self, msg):
        if self.dryrun:
            self.info("[DRYRUN] {0}".format(msg))
        else:
            self.info(msg)

    ################################################## Other

    def sleep(self, sleepsecs, account):
        """This function does not actually output anything, but handles
        the overall sleep, dealing with updates as necessary.  It will,
        however, call sleeping() which DOES output something.

        :returns: 0/False if timeout expired, 1/2/True if there is a
                  request to cancel the timer.
        """

        abortsleep = False
        while sleepsecs > 0 and not abortsleep:
            if account.get_abort_event():
                abortsleep = True
            else:
                abortsleep = self.sleeping(10, sleepsecs)
                sleepsecs -= 10
        self.sleeping(0, 0)  # Done sleeping.
        return abortsleep

    def sleeping(self, sleepsecs, remainingsecs):
        """Sleep for sleepsecs, display remainingsecs to go.

        Does nothing if sleepsecs <= 0.
        Display a message on the screen if we pass a full minute.

        This implementation in UIBase does not support this, but some
        implementations return 0 for successful sleep and 1 for an
        'abort', ie a request to sync immediately.
        """

        if sleepsecs > 0:
            if remainingsecs//60 != (remainingsecs-sleepsecs)//60:
                self.logger.debug("Next refresh in %.1f minutes" % (
                        remainingsecs/60.0))
            time.sleep(sleepsecs)
        return 0
