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
                  help="Do not actually modify any store but check and print "
              "what synchronization actions would be taken if a sync would be"
              " performed. It will not precisely give the exact information w"
              "hat will happen. If e.g. we need to create a folder, it merely"
              " outputs 'Would create folder X', but not how many and which m"
              "ails it would transfer.")

        parser.add_option("--info",
                  action="store_true", dest="diagnostics",
                  default=False,
                  help="Output information on the configured email repositories"
              ". Useful for debugging and bug reporting. Use in conjunction wit"
              "h the -a option to limit the output to a single account. This mo"
              "de will prevent any actual sync to occur and exits after it outp"
              "ut the debug information.")

        parser.add_option("-1",
                  action="store_true", dest="singlethreading",
                  default=False,
                  help="Disable all multithreading operations and use "
              "solely a single-thread sync. This effectively sets the "
              "maxsyncaccounts and all maxconnections configuration file "
              "variables to 1.")

        parser.add_option("-P", dest="profiledir", metavar="DIR",
                  help="Sets OfflineIMAP into profile mode. The program "
              "will create DIR (it must not already exist). "
              "As it runs, Python profiling information about each "
              "thread is logged into profiledir. Please note: "
              "This option is present for debugging and optimization "
              "only, and should NOT be used unless you have a "
              "specific reason to do so. It will significantly "
              "decrease program performance, may reduce reliability, "
              "and can generate huge amounts of data. This option "
              "implies the -1 option.")

        parser.add_option("-a", dest="accounts", metavar="ACCOUNTS",
                  help="Overrides the accounts section in the config file. "
              "Lets you specify a particular account or set of "
              "accounts to sync without having to edit the config "
              "file. You might use this to exclude certain accounts, "
              "or to sync some accounts that you normally prefer not to.")

        parser.add_option("-c", dest="configfile", metavar="FILE",
                  default=None,
                  help="Specifies a configuration file to use")

        parser.add_option("-d", dest="debugtype", metavar="type1,[type2...]",
                  help="Enables debugging for OfflineIMAP. This is useful "
              "if you are to track down a malfunction or figure out what is "
              "going on under the hood. This option requires one or more "
              "debugtypes, separated by commas. These define what exactly "
              "will be debugged, and so far include two options: imap, thread, "
              "maildir or ALL. The imap option will enable IMAP protocol "
              "stream and parsing debugging. Note that the output may contain "
              "passwords, so take care to remove that from the debugging "
              "output before sending it to anyone else. The maildir option "
              "will enable debugging for certain Maildir operations. "
              "The use of any debug option (unless 'thread' is included), "
              "implies the single-thread option -1.")

        parser.add_option("-l", dest="logfile", metavar="FILE",
                  help="Log to FILE")

        parser.add_option("-f", dest="folders", metavar="folder1,[folder2...]",
                  help="Only sync the specified folders. The folder names "
              "are the *untranslated* foldernames of the remote repository. "
              "This command-line option overrides any 'folderfilter' "
              "and 'folderincludes' options in the configuration file.")

        parser.add_option("-k", dest="configoverride",
                  action="append",
                  metavar="[section:]option=value",
                  help=
              """Override configuration file option. If"section" is
              omitted, it defaults to "general". Any underscores
              in the section name are replaced with spaces:
              for instance, to override option "autorefresh" in
              the "[Account Personal]" section in the config file
              one would use "-k Account_Personal:autorefresh=30".""")

        parser.add_option("-o",
                  action="store_true", dest="runonce",
                  default=False,
                  help="Run only once, ignoring any autorefresh setting "
                       "in the configuration file.")

        parser.add_option("-q",
                  action="store_true", dest="quick",
                  default=False,
                  help="Run only quick synchronizations. Ignore any "
              "flag updates on IMAP servers (if a flag on the remote IMAP "
              "changes, and we have the message locally, it will be left "
              "untouched in a quick run.")

        parser.add_option("-u", dest="interface",
                  help="Specifies an alternative user interface to "
              "use. This overrides the default specified in the "
              "configuration file. The UI specified with -u will "
              "be forced to be used, even if checks determine that it is "
              "not usable. Possible interface choices are: %s " %
              ", ".join(UI_LIST.keys()))

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

        #dry-run? Set [general]dry-run=True
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
