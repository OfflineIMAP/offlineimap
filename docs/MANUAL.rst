====================
 OfflineIMAP Manual
====================

--------------------------------------------------------
Powerful IMAP/Maildir synchronization and reader support
--------------------------------------------------------

:Author: John Goerzen <jgoerzen@complete.org>
:Date: 2011-01-15
:Copyright: GPL v2
:Manual section: 1

.. TODO: :Manual group:


SYNOPSIS
========

	offlineimap [-h|--help]

	offlineimap [OPTIONS]

|    -1
|    -P profiledir
|    -a accountlist
|    -c configfile
|    -d debugtype[,...]
|      -f foldername[,...]
|      -k [section:]option=value
|    -l filename
|    -o
|    -u interface


DESCRIPTION
===========

Most configuration is done via the configuration file.  Nevertheless, there are
a few command-line options that you may set for OfflineIMAP.


OPTIONS
=======





-1                Disable most multithreading operations

  Use solely a single-connection sync.  This effectively sets the
  maxsyncaccounts and all maxconnections configuration file variables to 1.


-P                profiledir

  Sets OfflineIMAP into profile mode.  The program will create profiledir (it
  must not already exist).  As it runs, Python profiling information about each
  thread is logged into profiledir.  Please note: This option is present for
  debugging and optimization only, and should NOT be used unless you have a
  specific reason to do so.  It will significantly slow program performance, may
  reduce reliability, and can generate huge amounts of data.  You must use the
  -1 option when you use -P.


-a                accountlist

  Overrides the accounts option in the general section of the configuration
  file.  You might use this to exclude certain accounts, or to sync some
  accounts that you normally prefer not to.  Separate the accounts by commas,
  and use no embedded spaces.


-c                configfile

  Specifies a configuration file to use in lieu of the default,
  ``~/.offlineimaprc``.


-d                debugtype[,...]

  Enables debugging for OfflineIMAP.  This is useful if you are trying to track
  down a malfunction or figure out what is going on under the hood.  I suggest
  that you use this with -1 to make the results more sensible.

  -d requires one or more debugtypes, separated by commas.  These define what
  exactly will be debugged, and include three options: imap, maildir, and
  thread.  The imap option will enable IMAP protocol stream and parsing
  debugging.  Note that the output may contain passwords, so take care to remove
  that from the debugging output before sending it to anyone else.  The maildir
  option will enable debugging for certain Maildir operations.  And thread will
  debug the threading model.


-f                foldername[,foldername]

  Only sync the specified folders.  The foldernames are the untranslated
  foldernames.  This command-line option overrides any folderfilter and
  folderincludes options in the configuration file.


-k                [section:]option=value

  Override configuration file option.  If "section" is omitted, it defaults to
  general.  Any underscores "_" in the section name are replaced with spaces:
  for instance, to override option autorefresh in the "[Account Personal]"
  section in the config file one would use "-k Account_Personal:autorefresh=30".
  You may give more than one -k on the command line if you wish.


-l                filename

  Enables logging to filename.  This will log everything that goes to the screen
  to the specified file.  Additionally, if any debugging is specified with -d,
  then debug messages will not go to the screen, but instead to the logfile
  only.


-o                Run only once,

  ignoring all autorefresh settings in the configuration file.


-q                Run only quick synchronizations.

  Ignore any flag updates on IMAP servers.


-h|--help         Show summary of options.


-u                interface

  Specifies an alternative user interface module to use.  This overrides the
  default specified in the configuration file.  The pre-defined options are
  listed in the User Interfaces section.


User Interfaces
===============

OfflineIMAP has a pluggable user interface system that lets you choose how the
program communicates information to you.  There are two graphical interfaces,
two terminal interfaces, and two noninteractive interfaces suitable for
scripting or logging purposes.  The ui option in the configuration file
specifies user interface preferences.  The -u command-line option can override
the configuration file setting.  The available values for the configuration file
or command-line are described in this section.


Curses.Blinkenlights
--------------------

Curses.Blinkenlights is an interface designed to be sleek, fun to watch, and
informative of the overall picture of what OfflineIMAP is doing.  I consider it
to be the best general-purpose interface in OfflineIMAP.


Curses.Blinkenlights contains a row of "LEDs" with command buttons and a log.
The  log shows more detail about what is happening and is color-coded to match
the color of the lights.


Each light in the Blinkenlights interface represents a thread of execution --
that is, a particular task that OfflineIMAP is performing right now.  The colors
indicate what task the particular thread is performing, and are as follows:

* Black:
    indicates that this light's thread has terminated; it will light up again
    later when new threads start up.  So, black indicates no activity.

* Red (Meaning 1):
    is the color of the main program's thread, which basically does nothing but
    monitor the others.  It might remind you of HAL 9000 in 2001.

* Gray:
    indicates that the thread is establishing a new connection to the IMAP
    server.

* Purple:
    is the color of an account synchronization thread that is monitoring the
    progress of the folders in that account (not generating any I/O).

* Cyan:
    indicates that the thread is syncing a folder.

* Green:
    means that a folder's message list is being loaded.

* Blue:
    is the color of a message synchronization controller thread.

* Orange:
    indicates that an actual message is being copied.  (We use fuchsia for fake
    messages.)

* Red (meaning 2):
    indicates that a message is being deleted.

* Yellow / bright orange:
    indicates that message flags are being added.

* Pink / bright red:
    indicates that message flags are being removed.

* Red / Black Flashing:
    corresponds to the countdown timer that runs between synchronizations.


The name of this interfaces derives from a bit of computer history.  Eric
Raymond's Jargon File defines blinkenlights, in part, as:

  Front-panel diagnostic lights on a computer, esp. a dinosaur. Now that
  dinosaurs are rare, this term usually refers to status lights on a modem,
  network hub, or the like.

This term derives from the last word of the famous blackletter-Gothic sign in
mangled pseudo-German that once graced about half the computer rooms in the
English-speaking world. One version ran in its entirety as follows:

| ACHTUNG!  ALLES LOOKENSPEEPERS!
|
| Das computermachine ist nicht fuer gefingerpoken und mittengrabben.
| Ist easy schnappen der springenwerk, blowenfusen und poppencorken
| mit spitzensparken.  Ist nicht fuer gewerken bei das dumpkopfen.
| Das rubbernecken sichtseeren keepen das cotten-pickenen hans in das
| pockets muss; relaxen und watchen das blinkenlichten.


TTY.TTYUI
---------

TTY.TTYUI interface is for people running in basic, non-color terminals.  It
prints out basic status messages and is generally friendly to use on a console
or xterm.


Noninteractive.Basic
--------------------

Noninteractive.Basic is designed for situations in which OfflineIMAP will be run
non-attended and the status of its execution will be logged.  You might use it,
for instance, to have the system run automatically and e-mail you the results of
the synchronization.  This user interface is not capable of reading a password
from the keyboard; account passwords must be specified using one of the
configuration file options.


Noninteractive.Quiet
--------------------

Noninteractive.Quiet is designed for non-attended running in situations where
normal status messages are not desired.  It will output nothing except errors
and serious warnings.  Like Noninteractive.Basic, this user interface is not
capable of reading a password from the keyboard; account passwords must be
specified using one of the configuration file options.


Machine.MachineUI
-----------------

Machine.MachineUI generates output in a machine-parsable format.  It is designed
for other programs that will interface to OfflineIMAP.


KNOWN BUGS
==========

SEE ALSO
========
