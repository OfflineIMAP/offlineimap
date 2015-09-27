# OfflineIMAP initialization code
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

import os
import sys
import threading
import offlineimap.imaplib2 as imaplib
import signal
import socket
import logging
from optparse import OptionParser

import offlineimap
from offlineimap import accounts, threadutil, syncmaster
from offlineimap import globals
from offlineimap.ui import UI_LIST, setglobalui, getglobalui
from offlineimap.CustomConfig import CustomConfigParser
from offlineimap.utils import stacktrace


class OfflineImap:
    """The main class that encapsulates the high level use of OfflineImap.

    To invoke OfflineImap you would call it with::

      oi = OfflineImap()
      oi.run()
    """

    def run(self):
        """Parse the commandline and invoke everything"""
        # next line also sets self.config and self.ui
        options, args = self.__parse_cmd_options()
        if options.diagnostics:
            self.__serverdiagnostics(options)
        else:
            self.__sync(options)

    def __parse_cmd_options(self):
        parser = OptionParser(version=offlineimap.__bigversion__,
                              description="%s.\n\n%s" %
                              (offlineimap.__copyright__,
                               offlineimap.__license__))
        parser.add_option("--dry-run",
                  action="store_true", dest="dryrun",
                  default=False,
                  help="dry run mode")

        parser.add_option("--info",
                  action="store_true", dest="diagnostics",
                  default=False,
                  help="output information on the configured email repositories")

        parser.add_option("-1",
                  action="store_true", dest="singlethreading",
                  default=False,
                  help="(the number one) disable all multithreading operations")

        parser.add_option("-P", dest="profiledir", metavar="DIR",
                  help="sets OfflineIMAP into profile mode.")

        parser.add_option("-a", dest="accounts",
                  metavar="account1[,account2[,...]]",
                  help="list of accounts to sync")

        parser.add_option("-c", dest="configfile", metavar="FILE",
                  default=None,
                  help="specifies a configuration file to use")

        parser.add_option("-d", dest="debugtype",
                  metavar="type1[,type2[,...]]",
                  help="enables debugging for OfflineIMAP "
                  " (types: imap, maildir, thread)")

        parser.add_option("-l", dest="logfile", metavar="FILE",
                  help="log to FILE")

        parser.add_option("-s",
                  action="store_true", dest="syslog",
                  default=False,
                  help="log to syslog")

        parser.add_option("-f", dest="folders",
                  metavar="folder1[,folder2[,...]]",
                  help="only sync the specified folders")

        parser.add_option("-k", dest="configoverride",
                  action="append",
                  metavar="[section:]option=value",
                  help="override configuration file option")

        parser.add_option("-o",
                  action="store_true", dest="runonce",
                  default=False,
                  help="run only once (ignore autorefresh)")

        parser.add_option("-q",
                  action="store_true", dest="quick",
                  default=False,
                  help="run only quick synchronizations (don't update flags)")

        parser.add_option("-u", dest="interface",
                  help="specifies an alternative user interface"
                  " (quiet, basic, ttyui, blinkenlights, machineui)")

        (options, args) = parser.parse_args()
        globals.set_options (options)

        #read in configuration file
        if not options.configfile:
            # Try XDG location, then fall back to ~/.offlineimaprc
            xdg_var = 'XDG_CONFIG_HOME'
            if not xdg_var in os.environ or not os.environ[xdg_var]:
                xdg_home = os.path.expanduser('~/.config')
            else:
                xdg_home = os.environ[xdg_var]
            options.configfile = os.path.join(xdg_home, "offlineimap", "config")
            if not os.path.exists(options.configfile):
                options.configfile = os.path.expanduser('~/.offlineimaprc')
            configfilename = options.configfile
        else:
            configfilename = os.path.expanduser(options.configfile)

        config = CustomConfigParser()
        if not os.path.exists(configfilename):
            # TODO, initialize and make use of chosen ui for logging
            logging.error(" *** Config file '%s' does not exist; aborting!"%
                          configfilename)
            sys.exit(1)
        config.read(configfilename)

        #profile mode chosen?
        if options.profiledir:
            if not options.singlethreading:
                # TODO, make use of chosen ui for logging
                logging.warn("Profile mode: Forcing to singlethreaded.")
                options.singlethreading = True
            if os.path.exists(options.profiledir):
                # TODO, make use of chosen ui for logging
                logging.warn("Profile mode: Directory '%s' already exists!"%
                             options.profiledir)
            else:
                os.mkdir(options.profiledir)
            threadutil.ExitNotifyThread.set_profiledir(options.profiledir)
            # TODO, make use of chosen ui for logging
            logging.warn("Profile mode: Potentially large data will be "
                         "created in '%s'"% options.profiledir)

        #override a config value
        if options.configoverride:
            for option in options.configoverride:
                (key, value) = option.split('=', 1)
                if ':' in key:
                    (secname, key) = key.split(':', 1)
                    section = secname.replace("_", " ")
                else:
                    section = "general"
                config.set(section, key, value)

        #which ui to use? cmd line option overrides config file
        ui_type = config.getdefault('general', 'ui', 'ttyui')
        if options.interface != None:
            ui_type = options.interface
        if '.' in ui_type:
            #transform Curses.Blinkenlights -> Blinkenlights
            ui_type = ui_type.split('.')[-1]
            # TODO, make use of chosen ui for logging
            logging.warning('Using old interface name, consider using one '
                            'of %s'% ', '.join(UI_LIST.keys()))
        if options.diagnostics: ui_type = 'basic' # enforce basic UI for --info

        # dry-run? Set [general]dry-run=True
        if options.dryrun:
            dryrun = config.set('general', 'dry-run', 'True')
        config.set_if_not_exists('general', 'dry-run', 'False')

        try:
            # create the ui class
            self.ui = UI_LIST[ui_type.lower()](config)
        except KeyError:
            logging.error("UI '%s' does not exist, choose one of: %s"% \
                              (ui_type, ', '.join(UI_LIST.keys())))
            sys.exit(1)
        setglobalui(self.ui)

        #set up additional log files
        if options.logfile:
            self.ui.setlogfile(options.logfile)

        #set up syslog
        if options.syslog:
            self.ui.setup_sysloghandler()

        #welcome blurb
        self.ui.init_banner()

        if options.debugtype:
            self.ui.logger.setLevel(logging.DEBUG)
            if options.debugtype.lower() == 'all':
                options.debugtype = 'imap,maildir,thread'
            #force single threading?
            if not ('thread' in options.debugtype.split(',') \
                    and not options.singlethreading):
                self.ui._msg("Debug mode: Forcing to singlethreaded.")
                options.singlethreading = True

            debugtypes = options.debugtype.split(',') + ['']
            for dtype in debugtypes:
                dtype = dtype.strip()
                self.ui.add_debug(dtype)
                if dtype.lower() == u'imap':
                    imaplib.Debug = 5

        if options.runonce:
            # FIXME: spaghetti code alert!
            for section in accounts.getaccountlist(config):
                config.remove_option('Account ' + section, "autorefresh")

        if options.quick:
            for section in accounts.getaccountlist(config):
                config.set('Account ' + section, "quick", '-1')

        #custom folder list specified?
        if options.folders:
            foldernames = options.folders.split(",")
            folderfilter = "lambda f: f in %s"% foldernames
            folderincludes = "[]"
            for accountname in accounts.getaccountlist(config):
                account_section = 'Account ' + accountname
                remote_repo_section = 'Repository ' + \
                    config.get(account_section, 'remoterepository')
                config.set(remote_repo_section, "folderfilter", folderfilter)
                config.set(remote_repo_section, "folderincludes",
                           folderincludes)

        if options.logfile:
            sys.stderr = self.ui.logfile

        socktimeout = config.getdefaultint("general", "socktimeout", 0)
        if socktimeout > 0:
            socket.setdefaulttimeout(socktimeout)

        threadutil.initInstanceLimit('ACCOUNTLIMIT',
            config.getdefaultint('general', 'maxsyncaccounts', 1))

        for reposname in config.getsectionlist('Repository'):
            for instancename in ["FOLDER_" + reposname,
                                 "MSGCOPY_" + reposname]:
                if options.singlethreading:
                    threadutil.initInstanceLimit(instancename, 1)
                else:
                    threadutil.initInstanceLimit(instancename,
                        config.getdefaultint('Repository ' + reposname,
                                                  'maxconnections', 2))
        self.config = config
        return (options, args)

    def __sync(self, options):
        """Invoke the correct single/multithread syncing

        self.config is supposed to have been correctly initialized
        already."""
        try:
            pidfd = open(self.config.getmetadatadir() + "/pid", "w")
            pidfd.write(str(os.getpid()) + "\n")
            pidfd.close()
        except:
            pass

        try:
            # Honor CLI --account option, only.
            # Accounts to sync are put into syncaccounts variable.
            activeaccounts = self.config.get("general", "accounts")
            if options.accounts:
                activeaccounts = options.accounts
            activeaccounts = activeaccounts.replace(" ", "")
            activeaccounts = activeaccounts.split(",")
            allaccounts = accounts.AccountHashGenerator(self.config)

            syncaccounts = []
            for account in activeaccounts:
                if account not in allaccounts:
                    if len(allaccounts) == 0:
                        errormsg = "The account '%s' does not exist because no" \
                            " accounts are defined!"% account
                    else:
                        errormsg = "The account '%s' does not exist.  Valid ac" \
                            "counts are: %s"% \
                            (account, ", ".join(allaccounts.keys()))
                    self.ui.terminate(1, errormsg=errormsg)
                if account not in syncaccounts:
                    syncaccounts.append(account)

            def sig_handler(sig, frame):
                if sig == signal.SIGUSR1:
                    # tell each account to stop sleeping
                    accounts.Account.set_abort_event(self.config, 1)
                elif sig == signal.SIGUSR2:
                    # tell each account to stop looping
                    getglobalui().warn("Terminating after this sync...")
                    accounts.Account.set_abort_event(self.config, 2)
                elif sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                    # tell each account to ABORT ASAP (ctrl-c)
                    getglobalui().warn("Terminating NOW (this may "\
                                       "take a few seconds)...")
                    accounts.Account.set_abort_event(self.config, 3)
                elif sig == signal.SIGQUIT:
                    stacktrace.dump(sys.stderr)
                    os.abort()

            signal.signal(signal.SIGHUP, sig_handler)
            signal.signal(signal.SIGUSR1, sig_handler)
            signal.signal(signal.SIGUSR2, sig_handler)
            signal.signal(signal.SIGTERM, sig_handler)
            signal.signal(signal.SIGINT, sig_handler)
            signal.signal(signal.SIGQUIT, sig_handler)

            #various initializations that need to be performed:
            offlineimap.mbnames.init(self.config, syncaccounts)

            if options.singlethreading:
                #singlethreaded
                self.__sync_singlethreaded(syncaccounts)
            else:
                # multithreaded
                t = threadutil.ExitNotifyThread(target=syncmaster.syncitall,
                                 name='Sync Runner',
                                 kwargs = {'accounts': syncaccounts,
                                           'config': self.config})
                t.start()
                threadutil.exitnotifymonitorloop(threadutil.threadexited)

            if not options.dryrun:
                offlineimap.mbnames.write(True)

            self.ui.terminate()
        except (SystemExit):
            raise
        except Exception as e:
            self.ui.error(e)
            self.ui.terminate()

    def __sync_singlethreaded(self, accs):
        """Executed if we do not want a separate syncmaster thread

        :param accs: A list of accounts that should be synced
        """
        for accountname in accs:
            account = offlineimap.accounts.SyncableAccount(self.config,
                                                           accountname)
            threading.currentThread().name = "Account sync %s"% accountname
            account.syncrunner()

    def __serverdiagnostics(self, options):
        activeaccounts = self.config.get("general", "accounts")
        if options.accounts:
            activeaccounts = options.accounts
        activeaccounts = activeaccounts.split(",")
        allaccounts = accounts.AccountListGenerator(self.config)
        for account in allaccounts:
            if account.name not in activeaccounts: continue
            account.serverdiagnostics()
