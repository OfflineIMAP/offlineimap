productname = 'OfflineIMAP'
versionstr = "4.0.7"
revno = long('$Rev: 592 $'[6:-2])
revstr = "Rev %d" % revno
datestr = '$Date: 2004-08-01 16:50:23 -0500 (Sun, 01 Aug 2004) $'

versionlist = versionstr.split(".")
major = versionlist[0]
minor = versionlist[1]
patch = versionlist[2]
copyright = "Copyright (C) 2002 - 2004 John Goerzen"
author = "John Goerzen"
author_email = "jgoerzen@complete.org"
description = "Disconnected Universal IMAP Mail Synchronization/Reader Support"
bigcopyright = """%(productname)s %(versionstr)s (%(revstr)s)
%(copyright)s <%(author_email)s>""" % locals()

banner = bigcopyright + """
This software comes with ABSOLUTELY NO WARRANTY; see the file
COPYING for details.  This is free software, and you are welcome
to distribute it under the conditions laid out in COPYING."""

homepage = "http://www.quux.org/devel/offlineimap"
homegopher = "gopher://quux.org/1/devel/offlineimap"
license = """Copyright (C) 2002 - 2004 John Goerzen <jgoerzen@complete.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA"""

cmdhelp = """
       offlineimap [ -1 ] [ -P profiledir ] [ -a accountlist ]  [
       -c configfile  ] [ -d debugtype[,debugtype...]  ] [ -o ] [
       -u interface ]

       offlineimap -h | --help

       -1     Disable   all  multithreading  operations  and  use
              solely a single-thread sync.  This effectively sets
              the maxsyncaccounts and all maxconnections configu-
              ration file variables to 1.

       -P profiledir
              Sets OfflineIMAP into profile  mode.   The  program
              will create profiledir (it must not already exist).
              As it runs, Python profiling information about each
              thread  is  logged  into  profiledir.  Please note:
              This option is present for debugging and  optimiza-
              tion only, and should NOT be used unless you have a
              specific reason to do so.   It  will  significantly
              slow  program  performance, may reduce reliability,
              and can generate huge amounts of  data.   You  must
              use the -1 option when you use -P.


       -a accountlist
              Overrides  the accounts section in the config file.
              Lets you specify a particular  account  or  set  of
              accounts  to sync without having to edit the config
              file.   You  might  use  this  to  exclude  certain
              accounts,  or  to  sync some accounts that you nor-
              mally prefer not to.

       -c configfile
              Specifies a configuration file to use  in  lieu  of
              the default, ~/.offlineimaprc.

       -d debugtype[,debugtype...]
              Enables  debugging for OfflineIMAP.  This is useful
              if you are trying to track down  a  malfunction  or
              figure out what is going on under the hood.  I sug-
              gest that you use this with -1 in order to make the
              results more sensible.

              -d  now  requires one or more debugtypes, separated
              by commas.   These  define  what  exactly  will  be
              debugged,  and so far include two options: imap and
              maildir.  The imap option will enable IMAP protocol
              stream and parsing debugging.  Note that the output
              may contain passwords, so take care to remove  that
              from the debugging output before sending it to any-
              one else.  The maildir option will enable debugging
              for certain Maildir operations.

       -o     Run  only once, ignoring any autorefresh setting in
              the config file.

       -h, --help
              Show summary of options.

       -u interface
              Specifies an alternative user interface  module  to
              use.   This  overrides the default specified in the
              configuration file.  The UI specified with -u  will
              be  forced to be used, even if its isuable() method
              states that it cannot be.   Use  this  option  with
              care.   The  pre-defined  options are listed in the
              USER INTERFACES section.

"""
