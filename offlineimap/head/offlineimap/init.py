# OfflineIMAP initialization code
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

from offlineimap import imaplib, imapserver, repository, folder, mbnames, threadutil, version, syncmaster
from offlineimap.localeval import LocalEval
from offlineimap.threadutil import InstanceLimitedThread, ExitNotifyThread
from offlineimap.ui import UIBase
import re, os, os.path, offlineimap, sys
from ConfigParser import ConfigParser
from threading import *
from getopt import getopt

def startup(revno):
    assert revno == version.revno, "Revision of main program (%d) does not match that of library (%d).  Please double-check your PYTHONPATH and installation locations." % (revno, version.revno)
    options = {}
    if '--help' in sys.argv[1:]:
        sys.stdout.write(version.cmdhelp + "\n")
        sys.exit(0)

    for optlist in getopt(sys.argv[1:], 'P:1oa:c:d:u:h')[0]:
        options[optlist[0]] = optlist[1]

    if '-h' in options:
        sys.stdout.write(version.cmdhelp)
        sys.stdout.write("\n")
        sys.exit(0)
    configfilename = os.path.expanduser("~/.offlineimaprc")
    if '-c' in options:
        configfilename = options['-c']
    if '-P' in options:
        if not '-1' in options:
            sys.stderr.write("FATAL: profile mode REQUIRES -1\n")
            sys.exit(100)
        profiledir = options['-P']
        os.mkdir(profiledir)
        threadutil.setprofiledir(profiledir)
        sys.stderr.write("WARNING: profile mode engaged;\nPotentially large data will be created in " + profiledir + "\n")

    config = ConfigParser()
    if not os.path.exists(configfilename):
        sys.stderr.write(" *** Config file %s does not exist; aborting!\n" % configfilename)
        sys.exit(1)

    config.read(configfilename)

    if config.has_option("general", "pythonfile"):
        path=os.path.expanduser(config.get("general", "pythonfile"))
    else:
        path=None
    localeval = LocalEval(path)

    ui = offlineimap.ui.detector.findUI(config, localeval, options.get('-u'))
    ui.init_banner()
    UIBase.setglobalui(ui)

    if '-d' in options:
        for debugtype in options['-d'].split(','):
            ui.add_debug(debugtype.strip())
            if debugtype == 'imap':
                imaplib.Debug = 5

    if '-o' in options and config.has_option("general", "autorefresh"):
        config.remove_option("general", "autorefresh")

    metadatadir = os.path.expanduser(config.get("general", "metadata"))
    if not os.path.exists(metadatadir):
        os.mkdir(metadatadir, 0700)

    accounts = config.get("general", "accounts")
    if '-a' in options:
        accounts = options['-a']
    accounts = accounts.replace(" ", "")
    accounts = accounts.split(",")

    server = None
    remoterepos = None
    localrepos = None
    passwords = {}
    tunnels = {}

    if '-1' in options:
        threadutil.initInstanceLimit("ACCOUNTLIMIT", 1)
    else:
        threadutil.initInstanceLimit("ACCOUNTLIMIT",
                                     config.getint("general", "maxsyncaccounts"))

    # We have to gather passwords here -- don't want to have two threads
    # asking for passwords simultaneously.

    for account in accounts:
        #if '.' in account:
        #    raise ValueError, "Account '%s' contains a dot; dots are not " \
        #        "allowed in account names." % account
        if config.has_option(account, "preauthtunnel"):
            tunnels[account] = config.get(account, "preauthtunnel")
        elif config.has_option(account, "remotepass"):
            passwords[account] = config.get(account, "remotepass")
        elif config.has_option(account, "remotepassfile"):
            passfile = open(os.path.expanduser(config.get(account, "remotepassfile")))
            passwords[account] = passfile.readline().strip()
            passfile.close()
        else:
            passwords[account] = ui.getpass(account, config)
        for instancename in ["FOLDER_" + account, "MSGCOPY_" + account]:
            if '-1' in options:
                threadutil.initInstanceLimit(instancename, 1)
            else:
                threadutil.initInstanceLimit(instancename,
                                             config.getint(account, "maxconnections"))

    mailboxes = []
    servers = {}

    threadutil.initexitnotify()
    t = ExitNotifyThread(target=syncmaster.sync_with_timer,
                         name='Sync Runner',
                         kwargs = {'accounts': accounts,
                                   'metadatadir': metadatadir,
                                   'servers': servers,
                                   'config': config,
                                   'passwords': passwords,
                                   'localeval': localeval})
    t.setDaemon(1)
    t.start()
    try:
        threadutil.exitnotifymonitorloop(threadutil.threadexited)
    except SystemExit:
        raise
    except:
        ui.mainException()                  # Also expected to terminate.

        
