# Copyright (C) 2003-2015 John Goerzen & contributors
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

from subprocess import Popen, PIPE
from threading import Event
import os
from sys import exc_info
import traceback

from offlineimap import mbnames, CustomConfig, OfflineImapError
from offlineimap import globals
from offlineimap.repository import Repository
from offlineimap.ui import getglobalui
from offlineimap.threadutil import InstanceLimitedThread

try:
    import fcntl
except:
    pass # ok if this fails, we can do without

# FIXME: spaghetti code alert!
def getaccountlist(customconfig):
    return customconfig.getsectionlist('Account')

# FIXME: spaghetti code alert!
def AccountListGenerator(customconfig):
    return [Account(customconfig, accountname)
            for accountname in getaccountlist(customconfig)]

# FIXME: spaghetti code alert!
def AccountHashGenerator(customconfig):
    retval = {}
    for item in AccountListGenerator(customconfig):
        retval[item.getname()] = item
    return retval


class Account(CustomConfig.ConfigHelperMixin):
    """Represents an account (ie. 2 repositories) to sync

    Most of the time you will actually want to use the derived
    :class:`accounts.SyncableAccount` which contains all functions used
    for syncing an account."""
    #signal gets set when we should stop looping
    abort_soon_signal = Event()
    #signal gets set on CTRL-C/SIGTERM
    abort_NOW_signal = Event()

    def __init__(self, config, name):
        """
        :param config: Representing the offlineimap configuration file.
        :type config: :class:`offlineimap.CustomConfig.CustomConfigParser`

        :param name: A string denoting the name of the Account
                     as configured"""
        self.config = config
        self.name = name
        self.metadatadir = config.getmetadatadir()
        self.localeval = config.getlocaleval()
        # current :mod:`offlineimap.ui`, can be used for logging:
        self.ui = getglobalui()
        self.refreshperiod = self.getconffloat('autorefresh', 0.0)
        # should we run in "dry-run" mode?
        self.dryrun = self.config.getboolean('general', 'dry-run')
        self.quicknum = 0
        if self.refreshperiod == 0.0:
            self.refreshperiod = None

    def getlocaleval(self):
        return self.localeval

    # Interface from CustomConfig.ConfigHelperMixin
    def getconfig(self):
        return self.config

    def getname(self):
        return self.name

    def __str__(self):
        return self.name

    def getaccountmeta(self):
        return os.path.join(self.metadatadir, 'Account-' + self.name)

    # Interface from CustomConfig.ConfigHelperMixin
    def getsection(self):
        return 'Account ' + self.getname()

    @classmethod
    def set_abort_event(cls, config, signum):
        """Set skip sleep/abort event for all accounts

        If we want to skip a current (or the next) sleep, or if we want
        to abort an autorefresh loop, the main thread can use
        set_abort_event() to send the corresponding signal. Signum = 1
        implies that we want all accounts to abort or skip the current
        or next sleep phase. Signum = 2 will end the autorefresh loop,
        ie all accounts will return after they finished a sync. signum=3
        means, abort NOW, e.g. on SIGINT or SIGTERM.

        This is a class method, it will send the signal to all accounts.
        """
        if signum == 1:
            # resync signal, set config option for all accounts
            for acctsection in getaccountlist(config):
                config.set('Account ' + acctsection, "skipsleep", '1')
        elif signum == 2:
            # don't autorefresh anymore
            cls.abort_soon_signal.set()
        elif signum == 3:
            # abort ASAP
            cls.abort_NOW_signal.set()

    def get_abort_event(self):
        """Checks if an abort signal had been sent

        If the 'skipsleep' config option for this account had been set,
        with `set_abort_event(config, 1)` it will get cleared in this
        function. Ie, we will only skip one sleep and not all.

        :returns: True, if the main thread had called
            :meth:`set_abort_event` earlier, otherwise 'False'.
        """
        skipsleep = self.getconfboolean("skipsleep", 0)
        if skipsleep:
            self.config.set(self.getsection(), "skipsleep", '0')
        return skipsleep or Account.abort_soon_signal.is_set() or \
            Account.abort_NOW_signal.is_set()

    def _sleeper(self):
        """Sleep if the account is set to autorefresh

        :returns: 0:timeout expired, 1: canceled the timer,
                  2:request to abort the program,
                  100: if configured to not sleep at all.
        """
        if not self.refreshperiod:
            return 100

        kaobjs = []

        if hasattr(self, 'localrepos'):
            kaobjs.append(self.localrepos)
        if hasattr(self, 'remoterepos'):
            kaobjs.append(self.remoterepos)

        for item in kaobjs:
            item.startkeepalive()

        refreshperiod = int(self.refreshperiod * 60)
        sleepresult = self.ui.sleep(refreshperiod, self)

        # Cancel keepalive
        for item in kaobjs:
            item.stopkeepalive()

        if sleepresult:
            if Account.abort_soon_signal.is_set() or \
                    Account.abort_NOW_signal.is_set():
                return 2
            self.quicknum = 0
            return 1
        return 0

    def serverdiagnostics(self):
        """Output diagnostics for all involved repositories"""
        remote_repo = Repository(self, 'remote')
        local_repo  = Repository(self, 'local')
        #status_repo = Repository(self, 'status')
        self.ui.serverdiagnostics(remote_repo, 'Remote')
        self.ui.serverdiagnostics(local_repo, 'Local')
        #self.ui.serverdiagnostics(statusrepos, 'Status')


class SyncableAccount(Account):
    """A syncable email account connecting 2 repositories

    Derives from :class:`accounts.Account` but contains the additional
    functions :meth:`syncrunner`, :meth:`sync`, :meth:`syncfolders`,
    used for syncing."""

    def __init__(self, *args, **kwargs):
        Account.__init__(self, *args, **kwargs)
        self._lockfd = None
        self._lockfilepath = os.path.join(self.config.getmetadatadir(),
                                          "%s.lock" % self)

    def __lock(self):
        """Lock the account, throwing an exception if it is locked already"""
        self._lockfd = open(self._lockfilepath, 'w')
        try:
            fcntl.lockf(self._lockfd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except NameError:
            #fcntl not available (Windows), disable file locking... :(
            pass
        except IOError:
            self._lockfd.close()
            raise OfflineImapError("Could not lock account %s. Is another "
                                   "instance using this account?" % self,
                                   OfflineImapError.ERROR.REPO)

    def _unlock(self):
        """Unlock the account, deleting the lock file"""
        #If we own the lock file, delete it
        if self._lockfd and not self._lockfd.closed:
            self._lockfd.close()
            try:
                os.unlink(self._lockfilepath)
            except OSError:
                pass #Failed to delete for some reason.

    def syncrunner(self):
        self.ui.registerthread(self)
        try:
            accountmetadata = self.getaccountmeta()
            if not os.path.exists(accountmetadata):
                os.mkdir(accountmetadata, 0o700)

            self.remoterepos = Repository(self, 'remote')
            self.localrepos  = Repository(self, 'local')
            self.statusrepos = Repository(self, 'status')
        except OfflineImapError as e:
            self.ui.error(e, exc_info()[2])
            if e.severity >= OfflineImapError.ERROR.CRITICAL:
                raise
            return

        # Loop account sync if needed (bail out after 3 failures)
        looping = 3
        while looping:
            self.ui.acct(self)
            try:
                self.__lock()
                self.__sync()
            except (KeyboardInterrupt, SystemExit):
                raise
            except OfflineImapError as e:
                # Stop looping and bubble up Exception if needed.
                if e.severity >= OfflineImapError.ERROR.REPO:
                    if looping:
                        looping -= 1
                    if e.severity >= OfflineImapError.ERROR.CRITICAL:
                        raise
                self.ui.error(e, exc_info()[2])
            except Exception as e:
                self.ui.error(e, exc_info()[2], msg = "While attempting to sync"
                    " account '%s'" % self)
            else:
                # after success sync, reset the looping counter to 3
                if self.refreshperiod:
                    looping = 3
            finally:
                self.ui.acctdone(self)
                self._unlock()
                if looping and self._sleeper() >= 2:
                    looping = 0

    def get_local_folder(self, remotefolder):
        """Return the corresponding local folder for a given remotefolder"""
        return self.localrepos.getfolder(
            remotefolder.getvisiblename().
            replace(self.remoterepos.getsep(), self.localrepos.getsep()))

    def __sync(self):
        """Synchronize the account once, then return

        Assumes that `self.remoterepos`, `self.localrepos`, and
        `self.statusrepos` has already been populated, so it should only
        be called from the :meth:`syncrunner` function.
        """
        folderthreads = []

        hook = self.getconf('presynchook', '')
        self.callhook(hook)

        quickconfig = self.getconfint('quick', 0)
        if quickconfig < 0:
            quick = True
        elif quickconfig > 0:
            if self.quicknum == 0 or self.quicknum > quickconfig:
                self.quicknum = 1
                quick = False
            else:
                self.quicknum = self.quicknum + 1
                quick = True
        else:
            quick = False

        try:
            remoterepos = self.remoterepos
            localrepos = self.localrepos
            statusrepos = self.statusrepos

            # init repos with list of folders, so we have them (and the
            # folder delimiter etc)
            remoterepos.getfolders()
            localrepos.getfolders()

            remoterepos.sync_folder_structure(localrepos, statusrepos)
            # replicate the folderstructure between REMOTE to LOCAL
            if not localrepos.getconfboolean('readonly', False):
                self.ui.syncfolders(remoterepos, localrepos)

            # iterate through all folders on the remote repo and sync
            for remotefolder in remoterepos.getfolders():
                # check for CTRL-C or SIGTERM
                if Account.abort_NOW_signal.is_set(): break

                if not remotefolder.sync_this:
                    self.ui.debug('', "Not syncing filtered folder '%s'"
                                  "[%s]" % (remotefolder, remoterepos))
                    continue # Ignore filtered folder
                localfolder = self.get_local_folder(remotefolder)
                if not localfolder.sync_this:
                    self.ui.debug('', "Not syncing filtered folder '%s'"
                                 "[%s]" % (localfolder, localfolder.repository))
                    continue # Ignore filtered folder
                if not globals.options.singlethreading:
                    thread = InstanceLimitedThread(\
                        instancename = 'FOLDER_' + self.remoterepos.getname(),
                        target = syncfolder,
                        name = "Folder %s [acc: %s]" % (remotefolder.getexplainedname(), self),
                        args = (self, remotefolder, quick))
                    thread.start()
                    folderthreads.append(thread)
                else:
                    syncfolder(self, remotefolder, quick)
            # wait for all threads to finish
            for thr in folderthreads:
                thr.join()
            # Write out mailbox names if required and not in dry-run mode
            if not self.dryrun:
                mbnames.write()
            localrepos.forgetfolders()
            remoterepos.forgetfolders()
        except:
            #error while syncing. Drop all connections that we have, they
            #might be bogus by now (e.g. after suspend)
            localrepos.dropconnections()
            remoterepos.dropconnections()
            raise
        else:
            # sync went fine. Hold or drop depending on config
            localrepos.holdordropconnections()
            remoterepos.holdordropconnections()

        hook = self.getconf('postsynchook', '')
        self.callhook(hook)

    def callhook(self, cmd):
        # check for CTRL-C or SIGTERM and run postsynchook
        if Account.abort_NOW_signal.is_set():
            return
        if not cmd:
            return
        try:
            self.ui.callhook("Calling hook: " + cmd)
            if self.dryrun: # don't if we are in dry-run mode
                return
            p = Popen(cmd, shell=True,
                      stdin=PIPE, stdout=PIPE, stderr=PIPE,
                      close_fds=True)
            r = p.communicate()
            self.ui.callhook("Hook stdout: %s\nHook stderr:%s\n" % r)
            self.ui.callhook("Hook return code: %d" % p.returncode)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.ui.error(e, exc_info()[2], msg = "Calling hook")

def syncfolder(account, remotefolder, quick):
    """Synchronizes given remote folder for the specified account.

    Filtered folders on the remote side will not invoke this function."""
    remoterepos = account.remoterepos
    localrepos = account.localrepos
    statusrepos = account.statusrepos

    ui = getglobalui()
    ui.registerthread(account)
    try:
        # Load local folder.
        localfolder = account.get_local_folder(remotefolder)

        # Write the mailboxes
        mbnames.add(account.name, localfolder.getname(),
          localrepos.getlocalroot())

        # Load status folder.
        statusfolder = statusrepos.getfolder(remotefolder.getvisiblename().\
                                             replace(remoterepos.getsep(),
                                                     statusrepos.getsep()))
        if localfolder.get_uidvalidity() == None:
            # This is a new folder, so delete the status cache to be
            # sure we don't have a conflict.
            # TODO: This does not work. We always return a value, need
            # to rework this...
            statusfolder.deletemessagelist()

        statusfolder.cachemessagelist()

        if quick:
            if not localfolder.quickchanged(statusfolder) \
                   and not remotefolder.quickchanged(statusfolder):
                ui.skippingfolder(remotefolder)
                localrepos.restore_atime()
                return

        # Load local folder
        ui.syncingfolder(remoterepos, remotefolder, localrepos, localfolder)
        ui.loadmessagelist(localrepos, localfolder)
        localfolder.cachemessagelist()
        ui.messagelistloaded(localrepos, localfolder, localfolder.getmessagecount())

        # If either the local or the status folder has messages and
        # there is a UID validity problem, warn and abort.  If there are
        # no messages, UW IMAPd loses UIDVALIDITY.  But we don't really
        # need it if both local folders are empty.  So, in that case,
        # just save it off.
        if localfolder.getmessagecount() or statusfolder.getmessagecount():
            if not localfolder.check_uidvalidity():
                ui.validityproblem(localfolder)
                localrepos.restore_atime()
                return
            if not remotefolder.check_uidvalidity():
                ui.validityproblem(remotefolder)
                localrepos.restore_atime()
                return
        else:
            # Both folders empty, just save new UIDVALIDITY
            localfolder.save_uidvalidity()
            remotefolder.save_uidvalidity()

        # Load remote folder.
        ui.loadmessagelist(remoterepos, remotefolder)
        remotefolder.cachemessagelist()
        ui.messagelistloaded(remoterepos, remotefolder,
                             remotefolder.getmessagecount())

        # Synchronize remote changes.
        if not localrepos.getconfboolean('readonly', False):
            ui.syncingmessages(remoterepos, remotefolder, localrepos, localfolder)
            remotefolder.syncmessagesto(localfolder, statusfolder)
        else:
            ui.debug('imap', "Not syncing to read-only repository '%s'" \
                         % localrepos.getname())

        # Synchronize local changes
        if not remoterepos.getconfboolean('readonly', False):
            ui.syncingmessages(localrepos, localfolder, remoterepos, remotefolder)
            localfolder.syncmessagesto(remotefolder, statusfolder)
        else:
            ui.debug('', "Not syncing to read-only repository '%s'" \
                         % remoterepos.getname())

        statusfolder.save()
        localrepos.restore_atime()
    except (KeyboardInterrupt, SystemExit):
        raise
    except OfflineImapError as e:
        # bubble up severe Errors, skip folder otherwise
        if e.severity > OfflineImapError.ERROR.FOLDER:
            raise
        else:
            ui.error(e, exc_info()[2], msg = "Aborting sync, folder '%s' "
                     "[acc: '%s']" % (localfolder, account))
    except Exception as e:
        ui.error(e, msg = "ERROR in syncfolder for %s folder %s: %s" % \
                (account, remotefolder.getvisiblename(),
                 traceback.format_exc()))
