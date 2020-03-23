# Copyright (C) 2003-2016 John Goerzen & contributors
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
from threading import Event, Lock
import os
import time
from sys import exc_info
import traceback
import six

from offlineimap import mbnames, CustomConfig, OfflineImapError
from offlineimap import globals
from offlineimap.repository import Repository
from offlineimap.ui import getglobalui
from offlineimap.threadutil import InstanceLimitedThread

FOLDER_NAMESPACE = 'LIMITED_FOLDER_'
# Key: account name, Value: Dict of Key: remotefolder name, Value: lock.
SYNC_MUTEXES = {}
SYNC_MUTEXES_LOCK = Lock()

try:
    import portalocker
except:
    try:
        import fcntl
    except:
        pass # Ok if this fails, we can do without.

# FIXME: spaghetti code alert!
def getaccountlist(customconfig):
    # Account names in a list.
    return [name.lstrip() for name in customconfig.getsectionlist('Account')]


class Account(CustomConfig.ConfigHelperMixin):
    """Represents an account (ie. 2 repositories) to sync.

    Most of the time you will actually want to use the derived
    :class:`accounts.SyncableAccount` which contains all functions used
    for syncing an account."""

    # Signal gets set when we should stop looping.
    abort_soon_signal = Event()
    # Signal gets set on CTRL-C/SIGTERM.
    abort_NOW_signal = Event()

    def __init__(self, config, name):
        """
        :param config: Representing the offlineimap configuration file.
        :type config: :class:`offlineimap.CustomConfig.CustomConfigParser`

        :param name: A (str) string denoting the name of the Account
                     as configured.
        """

        self.config = config
        self.name = name
        self.metadatadir = config.getmetadatadir()
        self.localeval = config.getlocaleval()
        # Store utf-8 support as a property of Account object
        self.utf_8_support = self.getconfboolean('utf8foldernames', False)
        # Current :mod:`offlineimap.ui`, can be used for logging:
        self.ui = getglobalui()
        self.refreshperiod = self.getconffloat('autorefresh', 0.0)
        self.dryrun = self.config.getboolean('general', 'dry-run')
        self.quicknum = 0
        if self.refreshperiod < 0:
            self.ui.warn("autorefresh for %s is negative, fixing it to 0."%
                    name)
            self.refreshperiod = 0.0
        if self.refreshperiod == 0.0:
            self.refreshperiod = None
        self.remoterepos = None
        self.localrepos = None
        self.statusrepos = None

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
        """Set skip sleep/abort event for all accounts.

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
        """Checks if an abort signal had been sent.

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
        """Sleep if the account is set to autorefresh.

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
        """Output diagnostics for all involved repositories."""

        remote_repo = Repository(self, 'remote')
        local_repo  = Repository(self, 'local')
        #status_repo = Repository(self, 'status')
        self.ui.serverdiagnostics(remote_repo, 'Remote')
        self.ui.serverdiagnostics(local_repo, 'Local')
        #self.ui.serverdiagnostics(statusrepos, 'Status')

    def deletefolder(self, foldername):
        remote_repo = Repository(self, 'remote')

        try:
            if self.dryrun:
                self.ui.info("would try to remove '%s' on remote of '%s' "
                    "account"% (foldername, self))
            else:
                remote_repo.deletefolder(foldername)
                self.ui.info("Folder '%s' deleted."% foldername)
            return 0
        except Exception as e:
            self.ui.error(e)
            return 1


class SyncableAccount(Account):
    """A syncable email account connecting 2 repositories.

    Derives from :class:`accounts.Account` but contains the additional
    functions :meth:`syncrunner`, :meth:`sync`, :meth:`syncfolders`,
    used for syncing.

    In multi-threaded mode, one instance of this object is run per "account"
    thread."""

    def __init__(self, *args, **kwargs):
        Account.__init__(self, *args, **kwargs)
        self._lockfd = None
        self._lockfilepath = os.path.join(
            self.config.getmetadatadir(), "%s.lock"% self)

    def __lock(self):
        """Lock the account, throwing an exception if it is locked already."""

        self._lockfd = open(self._lockfilepath, 'w')
        try:
            portalocker.lock(self._lockfd, portalocker.LOCK_EX)
        except NameError:
            # portalocker not available for Windows.
            try:
                fcntl.lockf(self._lockfd, fcntl.LOCK_EX|fcntl.LOCK_NB)
            except NameError:
                pass # fnctl not available, disable file locking... :(
        except IOError:
            self._lockfd.close()
            six.reraise(OfflineImapError,
                        OfflineImapError(
                            "Could not lock account %s. Is another "
                            "instance using this account?"% self,
                            OfflineImapError.ERROR.REPO),
                        exc_info()[2])

    def _unlock(self):
        """Unlock the account, deleting the lock file"""

        #If we own the lock file, delete it
        if self._lockfd and not self._lockfd.closed:
            try:
                portalocker.unlock(self._lockfd)
            except NameError:
                pass
            self._lockfd.close()
            try:
                os.unlink(self._lockfilepath)
            except OSError:
                pass    # Failed to delete for some reason.

    def syncrunner(self):
        """The target for both single and multi-threaded modes."""

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

        # Loop account sync if needed (bail out after 3 failures).
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
                self.ui.error(e, exc_info()[2], msg=
                    "While attempting to sync account '%s'"% self)
            else:
                # After success sync, reset the looping counter to 3.
                if self.refreshperiod:
                    looping = 3
            finally:
                self.ui.acctdone(self)
                self._unlock()
                if looping and self._sleeper() >= 2:
                    looping = 0

    def get_local_folder(self, remotefolder):
        """Return the corresponding local folder for a given remotefolder."""

        return self.localrepos.getfolder(
            remotefolder.getvisiblename().
            replace(self.remoterepos.getsep(), self.localrepos.getsep()))


    # The syncrunner will loop on this method. This means it is called more than
    # once during the run.
    def __sync(self):
        """Synchronize the account once, then return.

        Assumes that `self.remoterepos`, `self.localrepos`, and
        `self.statusrepos` has already been populated, so it should only
        be called from the :meth:`syncrunner` function."""

        folderthreads = []

        hook_env = {
            'OIMAP_ACCOUNT_NAME': self.getname(),
        }

        self.callhook('presynchook', hook_env)

        if self.utf_8_support and self.remoterepos.getdecodefoldernames():
            raise OfflineImapError("Configuration mismatch in account " +
                        "'%s'. "% self.getname() +
                        "\nAccount setting 'utf8foldernames' and repository " +
                        "setting 'decodefoldernames'\nmay not be used at the " +
                        "same time. This account has not been synchronized.\n" +
                        "Please check the configuration and documentation.",
                    OfflineImapError.ERROR.REPO)

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
            startedThread = False
            remoterepos = self.remoterepos
            localrepos = self.localrepos
            statusrepos = self.statusrepos

            # Init repos with list of folders, so we have them (and the
            # folder delimiter etc).
            remoterepos.getfolders()
            localrepos.getfolders()

            remoterepos.sync_folder_structure(localrepos, statusrepos)
            # Replicate the folderstructure between REMOTE to LOCAL.
            if not localrepos.getconfboolean('readonly', False):
                self.ui.syncfolders(remoterepos, localrepos)

            # Iterate through all folders on the remote repo and sync.
            for remotefolder in remoterepos.getfolders():
                # Check for CTRL-C or SIGTERM.
                if Account.abort_NOW_signal.is_set():
                    break

                if not remotefolder.sync_this:
                    self.ui.debug('', "Not syncing filtered folder '%s'"
                                  "[%s]"% (remotefolder.getname(), remoterepos))
                    continue # Ignore filtered folder.

                # The remote folder names must not have the local sep char in
                # their names since this would cause troubles while converting
                # the name back (from local to remote).
                sep = localrepos.getsep()
                if (sep != os.path.sep and
                    sep != remoterepos.getsep() and
                    sep in remotefolder.getname()):
                    self.ui.warn('', "Ignoring folder '%s' due to unsupported "
                        "'%s' character serving as local separator."%
                        (remotefolder.getname(), localrepos.getsep()))
                    continue # Ignore unsupported folder name.

                localfolder = self.get_local_folder(remotefolder)
                if not localfolder.sync_this:
                    self.ui.debug('', "Not syncing filtered folder '%s'"
                                 "[%s]"% (localfolder.getname(), localfolder.repository))
                    continue # Ignore filtered folder.

                if not globals.options.singlethreading:
                    thread = InstanceLimitedThread(
                        limitNamespace="%s%s"% (
                            FOLDER_NAMESPACE, self.remoterepos.getname()),
                        target=syncfolder,
                        name="Folder %s [acc: %s]"% (
                            remotefolder.getexplainedname(), self),
                        args=(self, remotefolder, quick)
                    )
                    thread.start()
                    folderthreads.append(thread)
                else:
                    syncfolder(self, remotefolder, quick)
                startedThread = True
            # Wait for all threads to finish.
            for thr in folderthreads:
                thr.join()
            if startedThread is True:
                mbnames.writeIntermediateFile(self.name) # Write out mailbox names.
            else:
                msg = "Account {}: no folder to sync (folderfilter issue?)".format(self)
                raise OfflineImapError(msg, OfflineImapError.ERROR.REPO)
            localrepos.forgetfolders()
            remoterepos.forgetfolders()
        except:
            # Error while syncing. Drop all connections that we have, they
            # might be bogus by now (e.g. after suspend).
            localrepos.dropconnections()
            remoterepos.dropconnections()
            raise
        else:
            # Sync went fine. Hold or drop depending on config.
            localrepos.holdordropconnections()
            remoterepos.holdordropconnections()

        self.callhook('postsynchook', hook_env)

    def callhook(self, name, env={}):
        # Check for CTRL-C or SIGTERM and run postsynchook.
        if Account.abort_NOW_signal.is_set():
            return
        cmd = self.getconf(name, '')
        if not cmd:
            return
        try:
            self.ui.callhook("Calling hook: " + cmd)
            if self.dryrun:
                return
            env = env.copy()
            env.update(os.environ)
            env['OIMAP_HOOK_NAME'] = name
            p = Popen(cmd, shell=True, env=env,
                      stdin=PIPE, stdout=PIPE, stderr=PIPE,
                      close_fds=True)
            r = p.communicate()
            self.ui.callhook("Hook stdout: %s\nHook stderr:%s\n"% r)
            self.ui.callhook("Hook return code: %d"% p.returncode)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.ui.error(e, exc_info()[2], msg="Calling hook")


#XXX: This function should likely be refactored. This should not be passed the
# account instance.
def syncfolder(account, remotefolder, quick):
    """Synchronizes given remote folder for the specified account.

    Filtered folders on the remote side will not invoke this function.

    When called in concurrently for the same localfolder, syncs are
    serialized."""

    def acquire_mutex():
        account_name = account.getname()
        localfolder_name = localfolder.getfullname()

        with SYNC_MUTEXES_LOCK:
            if SYNC_MUTEXES.get(account_name) is None:
                SYNC_MUTEXES[account_name] = {}
            # The localfolder full name is good to uniquely identify the sync
            # transaction.
            if SYNC_MUTEXES[account_name].get(localfolder_name) is None:
                #XXX: This lock could be an external file lock so we can remove
                # the lock at the account level.
                SYNC_MUTEXES[account_name][localfolder_name] = Lock()

        # Acquire the lock.
        SYNC_MUTEXES[account_name][localfolder_name].acquire()

    def release_mutex():
        SYNC_MUTEXES[account.getname()][localfolder.getfullname()].release()

    def check_uid_validity():
        # If either the local or the status folder has messages and
        # there is a UID validity problem, warn and abort.  If there are
        # no messages, UW IMAPd loses UIDVALIDITY.  But we don't really
        # need it if both local folders are empty.  So, in that case,
        # just save it off.
        if localfolder.getmessagecount() > 0 or statusfolder.getmessagecount() > 0:
            if not localfolder.check_uidvalidity():
                ui.validityproblem(localfolder)
                localfolder.repository.restore_atime()
                return
            if not remotefolder.check_uidvalidity():
                ui.validityproblem(remotefolder)
                localrepos.restore_atime()
                return
        else:
            # Both folders empty, just save new UIDVALIDITY.
            localfolder.save_uidvalidity()
            remotefolder.save_uidvalidity()

    def cachemessagelists_upto_date(date):
        """Returns messages with uid > min(uids of messages newer than date)."""

        remotefolder.cachemessagelist(
            min_date=time.gmtime(time.mktime(date) + 24*60*60))
        uids = remotefolder.getmessageuidlist()
        localfolder.dropmessagelistcache()
        if len(uids) > 0:
            # Reload the remote message list from min_uid. This avoid issues for
            # old messages, which has been added from local on any previous run
            # (IOW, message is older than maxage _and_ has high enough UID).
            remotefolder.dropmessagelistcache()
            remotefolder.cachemessagelist(min_uid=min(uids))
            localfolder.cachemessagelist(min_uid=min(uids))
        else:
            # Remote folder UIDs list is empty for the given range. We still
            # might have valid local UIDs for this range (e.g.: new local
            # emails).
            localfolder.cachemessagelist(min_date=date)
            uids = localfolder.getmessageuidlist()
            # Take care to only consider positive uids. Negative UIDs might be
            # present due to new emails.
            uids = [uid for uid in uids if uid > 0]
            if len(uids) > 0:
                # Update the remote cache list for this new min(uids).
                remotefolder.dropmessagelistcache()
                remotefolder.cachemessagelist(min_uid=min(uids))

    def cachemessagelists_startdate(new, partial, date):
        """Retrieve messagelists when startdate has been set for
        the folder 'partial'.

        Idea: suppose you want to clone the messages after date in one
        account (partial) to a new one (new). If new is empty, then copy
        messages in partial newer than date to new, and keep track of the
        min uid. On subsequent syncs, sync all the messages in new against
        those after that min uid in partial. This is a partial replacement
        for maxage in the IMAP-IMAP sync case, where maxage doesn't work:
        the UIDs of the messages in localfolder might not be in the same
        order as those of corresponding messages in remotefolder, so if L in
        local corresponds to R in remote, the ranges [L, ...] and [R, ...]
        might not correspond. But, if we're cloning a folder into a new one,
        [min_uid, ...] does correspond to [1, ...].

        This is just for IMAP-IMAP. For Maildir-IMAP, use maxage instead."""

        new.cachemessagelist()
        min_uid = partial.retrieve_min_uid()
        if min_uid == None: # min_uid file didn't exist
            if len(new.getmessageuidlist()) > 0:
                raise OfflineImapError("To use startdate on Repository %s, "
                    "Repository %s must be empty"%
                    (partial.repository.name, new.repository.name),
                    OfflineImapError.ERROR.MESSAGE)
            else:
                partial.cachemessagelist(min_date=date)
                # messagelist.keys() instead of getuidmessagelist() because in
                # the UID mapped case we want the actual local UIDs, not their
                # remote counterparts.
                positive_uids = [uid for uid in list(partial.messagelist.keys()) if uid > 0]
                if len(positive_uids) > 0:
                    min_uid = min(positive_uids)
                else:
                    min_uid = 1
                partial.save_min_uid(min_uid)
        else:
            partial.cachemessagelist(min_uid=min_uid)


    remoterepos = account.remoterepos
    localrepos = account.localrepos
    statusrepos = account.statusrepos

    ui = getglobalui()
    ui.registerthread(account)
    try:
        # Load local folder.
        localfolder = account.get_local_folder(remotefolder)

        # Acquire the mutex to start syncing.
        acquire_mutex()

        # Add the folder to the mbnames mailboxes.
        mbnames.add(account.name, localrepos.getlocalroot(),
            localfolder.getname())

        # Load status folder.
        statusfolder = statusrepos.getfolder(remotefolder.getvisiblename().
            replace(remoterepos.getsep(), statusrepos.getsep()))
        statusfolder.openfiles()
        statusfolder.cachemessagelist()

        # Load local folder.
        ui.syncingfolder(remoterepos, remotefolder, localrepos, localfolder)

        # Retrieve messagelists, taking into account age-restriction
        # options.
        maxage = localfolder.getmaxage()
        localstart = localfolder.getstartdate()
        remotestart = remotefolder.getstartdate()
        if (maxage != None) + (localstart != None) + (remotestart != None) > 1:
            six.reraise(OfflineImapError,
                        OfflineImapError("You can set at most one of the "
                            "following: maxage, startdate (for the local "
                            "folder), startdate (for the remote folder)",
                            OfflineImapError.ERROR.REPO),
                        exc_info()[2])
        if (maxage != None or localstart or remotestart) and quick:
            # IMAP quickchanged isn't compatible with options that
            # involve restricting the messagelist, since the "quick"
            # check can only retrieve a full list of UIDs in the folder.
            ui.warn("Quick syncs (-q) not supported in conjunction "
                "with maxage or startdate; ignoring -q.")
        if maxage != None:
            cachemessagelists_upto_date(maxage)
            check_uid_validity()
        elif localstart != None:
            cachemessagelists_startdate(remotefolder, localfolder,
                localstart)
            check_uid_validity()
        elif remotestart != None:
            cachemessagelists_startdate(localfolder, remotefolder,
                remotestart)
            check_uid_validity()
        else:
            localfolder.cachemessagelist()
            if quick:
                if (not localfolder.quickchanged(statusfolder) and
                    not remotefolder.quickchanged(statusfolder)):
                    ui.skippingfolder(remotefolder)
                    localrepos.restore_atime()
                    return
            check_uid_validity()
            remotefolder.cachemessagelist()

        # Synchronize remote changes.
        if not localrepos.getconfboolean('readonly', False):
            ui.syncingmessages(remoterepos, remotefolder, localrepos, localfolder)
            remotefolder.syncmessagesto(localfolder, statusfolder)
        else:
            ui.debug('', "Not syncing to read-only repository '%s'"%
                    localrepos.getname())

        # Synchronize local changes.
        if not remoterepos.getconfboolean('readonly', False):
            ui.syncingmessages(localrepos, localfolder, remoterepos, remotefolder)
            localfolder.syncmessagesto(remotefolder, statusfolder)
        else:
            ui.debug('', "Not syncing to read-only repository '%s'"%
                    remoterepos.getname())

        statusfolder.save()
        localrepos.restore_atime()
    except (KeyboardInterrupt, SystemExit):
        raise
    except OfflineImapError as e:
        # Bubble up severe Errors, skip folder otherwise.
        if e.severity > OfflineImapError.ERROR.FOLDER:
            raise
        else:
            ui.error(e, exc_info()[2], msg="Aborting sync, folder '%s' "
                     "[acc: '%s']"% (localfolder, account))
    except Exception as e:
        ui.error(e, msg="ERROR in syncfolder for %s folder %s: %s"%
            (account, remotefolder.getvisiblename(), traceback.format_exc()))
    finally:
        for folder in ["statusfolder", "localfolder", "remotefolder"]:
            if folder in locals():
                locals()[folder].dropmessagelistcache()
        statusfolder.closefiles()
        # Release the mutex of this sync transaction.
        release_mutex()
