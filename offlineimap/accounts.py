# Copyright (C) 2003 John Goerzen
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
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from offlineimap import mbnames, CustomConfig, OfflineImapError
from offlineimap.repository import Repository
from offlineimap.ui import getglobalui
from offlineimap.threadutil import InstanceLimitedThread
from subprocess import Popen, PIPE
from threading import Event
import os
from sys import exc_info
import traceback

try:
    import fcntl
except:
    pass # ok if this fails, we can do without

def getaccountlist(customconfig):
    return customconfig.getsectionlist('Account')

def AccountListGenerator(customconfig):
    return [Account(customconfig, accountname)
            for accountname in getaccountlist(customconfig)]

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
    abort_signal = Event()

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
        #Contains the current :mod:`offlineimap.ui`, and can be used for logging etc.
        self.ui = getglobalui()
        self.refreshperiod = self.getconffloat('autorefresh', 0.0)
        self.quicknum = 0
        if self.refreshperiod == 0.0:
            self.refreshperiod = None

    def getlocaleval(self):
        return self.localeval

    def getconfig(self):
        return self.config

    def getname(self):
        return self.name

    def __str__(self):
        return self.name

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
        ie all accounts will return after they finished a sync.

        This is a class method, it will send the signal to all accounts.
        """
        if signum == 1:
            # resync signal, set config option for all accounts
            for acctsection in getaccountlist(config):
                config.set('Account ' + acctsection, "skipsleep", '1')
        elif signum == 2:
            # don't autorefresh anymore
            cls.abort_signal.set()

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
        return skipsleep or Account.abort_signal.is_set()

    def sleeper(self):
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
            if Account.abort_signal.is_set():
                return 2
            self.quicknum = 0
            return 1
        return 0
            
    
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

    def lock(self):
        """Lock the account, throwing an exception if it is locked already"""
        # Take a new-style per-account lock
        self._lockfd = open(self._lockfilepath, 'w')
        try:
            fcntl.lockf(self._lockfd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except NameError:
            #fcntl not available (Windows), disable file locking... :(
            pass
        except IOError:
            self._lockfd.close()
            raise OfflineImapError("Could not lock account %s." % self,
                                   OfflineImapError.ERROR.REPO)

    def unlock(self):
        """Unlock the account, deleting the lock file"""
        #If we own the lock file, delete it
        if self._lockfd and not self._lockfd.closed:
            self._lockfd.close()
            try:
                os.unlink(self._lockfilepath)
            except OSError:
                pass #Failed to delete for some reason.

    def syncrunner(self):
        self.ui.registerthread(self.name)
        self.ui.acct(self.name)
        accountmetadata = self.getaccountmeta()
        if not os.path.exists(accountmetadata):
            os.mkdir(accountmetadata, 0700)            

        self.remoterepos = Repository(self, 'remote')
        self.localrepos  = Repository(self, 'local')
        self.statusrepos = Repository(self, 'status')

        # Loop account sync if needed (bail out after 3 failures)
        looping = 3
        while looping:
            try:
                try:
                    self.lock()
                    self.sync()
                except (KeyboardInterrupt, SystemExit):
                    raise
                except OfflineImapError, e:                    
                    # Stop looping and bubble up Exception if needed.
                    if e.severity >= OfflineImapError.ERROR.REPO:
                        if looping:
                            looping -= 1
                        if e.severity >= OfflineImapError.ERROR.CRITICAL:
                            raise
                    self.ui.error(e, exc_info()[2])
                except Exception, e:
                    self.ui.error(e, msg = "While attempting to sync "
                        "account %s:\n  %s"% (self, traceback.format_exc()))
                else:
                    # after success sync, reset the looping counter to 3
                    if self.refreshperiod:
                        looping = 3
            finally:
                self.unlock()
                if looping and self.sleeper() >= 2:
                    looping = 0                    
                self.ui.acctdone(self.name)

    def getaccountmeta(self):
        return os.path.join(self.metadatadir, 'Account-' + self.name)

    def sync(self):
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
            # replicate the folderstructure from REMOTE to LOCAL
            if not localrepos.getconfboolean('readonly', False):
                self.ui.syncfolders(remoterepos, localrepos)
                remoterepos.syncfoldersto(localrepos, statusrepos)

            # iterate through all folders on the remote repo and sync
            for remotefolder in remoterepos.getfolders():
                if not remotefolder.sync_this:
                    self.ui.debug('', "Not syncing filtered remote folder '%s'"
                                  "[%s]" % (remotefolder, remoterepos))
                    continue # Filtered out remote folder
                thread = InstanceLimitedThread(\
                    instancename = 'FOLDER_' + self.remoterepos.getname(),
                    target = syncfolder,
                    name = "Folder sync [%s]" % self,
                    args = (self.name, remoterepos, remotefolder, localrepos,
                            statusrepos, quick))
                thread.setDaemon(1)
                thread.start()
                folderthreads.append(thread)
            # wait for all threads to finish
            for thr in folderthreads:
                thr.join()
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
        if not cmd:
            return
        try:
            self.ui.callhook("Calling hook: " + cmd)
            p = Popen(cmd, shell=True,
                      stdin=PIPE, stdout=PIPE, stderr=PIPE,
                      close_fds=True)
            r = p.communicate()
            self.ui.callhook("Hook stdout: %s\nHook stderr:%s\n" % r)
            self.ui.callhook("Hook return code: %d" % p.returncode)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            self.ui.error(e, exc_info()[2], msg = "Calling hook")


def syncfolder(accountname, remoterepos, remotefolder, localrepos,
               statusrepos, quick):
    """This function is called as target for the
    InstanceLimitedThread invokation in SyncableAccount.

    Filtered folders on the remote side will not invoke this function."""
    ui = getglobalui()
    ui.registerthread(accountname)
    try:
        # Load local folder.
        localfolder = localrepos.\
                      getfolder(remotefolder.getvisiblename().\
                                replace(remoterepos.getsep(), localrepos.getsep()))

        #Filtered folders on the remote side will not invoke this
        #function, but we need to NOOP if the local folder is filtered
        #out too:
        if not localfolder.sync_this:
            ui.debug('', "Not syncing filtered local folder '%s'" \
                         % localfolder)
            return
        # Write the mailboxes
        mbnames.add(accountname, localfolder.getvisiblename())

        # Load status folder.
        statusfolder = statusrepos.getfolder(remotefolder.getvisiblename().\
                                             replace(remoterepos.getsep(),
                                                     statusrepos.getsep()))
        if localfolder.getuidvalidity() == None:
            # This is a new folder, so delete the status cache to be sure
            # we don't have a conflict.
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

        # If either the local or the status folder has messages and there is a UID
        # validity problem, warn and abort.  If there are no messages, UW IMAPd
        # loses UIDVALIDITY.  But we don't really need it if both local folders are
        # empty.  So, in that case, just save it off.
        if localfolder.getmessagecount() or statusfolder.getmessagecount():
            if not localfolder.isuidvalidityok():
                ui.validityproblem(localfolder)
                localrepos.restore_atime()
                return
            if not remotefolder.isuidvalidityok():
                ui.validityproblem(remotefolder)
                localrepos.restore_atime()
                return
        else:
            localfolder.saveuidvalidity()
            remotefolder.saveuidvalidity()

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
    except OfflineImapError, e:
        # bubble up severe Errors, skip folder otherwise
        if e.severity > OfflineImapError.ERROR.FOLDER:
            raise
        else:
            #if the initial localfolder assignement bailed out, the localfolder var will not be available, so we need
            ui.error(e, exc_info()[2], msg = "Aborting sync, folder '%s' "
                     "[acc: '%s']" % (
                    remotefolder.getvisiblename().\
                        replace(remoterepos.getsep(), localrepos.getsep()),
                    accountname))
                    # we reconstruct foldername above rather than using
                    # localfolder, as the localfolder var is not
                    # available if assignment fails.
    except Exception, e:
        ui.error(e, msg = "ERROR in syncfolder for %s folder %s: %s" % \
                (accountname,remotefolder.getvisiblename(),
                 traceback.format_exc()))
