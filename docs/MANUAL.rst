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
  listed in the User Interfaces section. The interface name is case insensitive.


User Interfaces
===============

OfflineIMAP has various user interfaces that let you choose how the
program communicates information to you. The 'ui' option in the
configuration file specifies the user interface.  The -u command-line
option overrides the configuration file setting.  The available values
for the configuration file or command-line are described in this
section.


Blinkenlights
---------------

Blinkenlights is an interface designed to be sleek, fun to watch, and
informative of the overall picture of what OfflineIMAP is doing.  I consider it
to be the best general-purpose interface in OfflineIMAP.


Blinkenlights contains a row of "LEDs" with command buttons and a log.
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


TTYUI
---------

TTYUI interface is for people running in basic, non-color terminals.  It
prints out basic status messages and is generally friendly to use on a console
or xterm.


Basic
--------------------

Basic is designed for situations in which OfflineIMAP will be run
non-attended and the status of its execution will be logged.  You might use it,
for instance, to have the system run automatically and e-mail you the results of
the synchronization.  This user interface is not capable of reading a password
from the keyboard; account passwords must be specified using one of the
configuration file options.


Quiet
-----

Quiet is designed for non-attended running in situations where normal
status messages are not desired.  It will output nothing except errors
and serious warnings.  Like Noninteractive.Basic, this user interface is
not capable of reading a password from the keyboard; account passwords
must be specified using one of the configuration file options.

MachineUI
---------

MachineUI generates output in a machine-parsable format.  It is designed
for other programs that will interface to OfflineIMAP.


Signals
=======

OfflineImap listens to the unix signals SIGUSR1 and SIGUSR2.

If sent a SIGUSR1 it will abort any current (or next future) sleep of all
accounts that are configured to "autorefresh". In effect, this will trigger a
full sync of all accounts to be performed as soon as possible.

If sent a SIGUSR2, it will stop "autorefresh mode" for all accounts. That is,
accounts will abort any current sleep and will exit after a currently running
synchronization has finished. This signal can be used to gracefully exit out of
a running offlineimap "daemon".


KNOWN BUGS
==========

* SSL3 write pending:
    users enabling SSL may hit a bug about "SSL3 write pending". If so, the
    account(s) will stay unsynchronised from the time the bug appeared. Running
    OfflineIMAP again can help. We are still working on this bug.  Patches or
    detailed bug reports would be appreciated. Please check you're running the
    last stable version and send us a report to the mailing list including the
    full log.

* IDLE support is incomplete and experimental.  Bugs may be encountered.

  * No hook exists for "run after an IDLE response".  Email will
    show up, but may not be processed until the next refresh cycle.

  * nametrans may not be supported correctly.

  * IMAP IDLE <-> IMAP IDLE doesn't work yet.

  * IDLE may only work "once" per refresh.  If you encounter this bug,
    please send a report to the list!

* Maildir support in Windows drive
    Maildir uses colon caracter (:) in message file names. Colon is however
    forbidden character in windows drives. There are several workarounds for
    that situation:

   * Use "maildir-windows-compatible = yes" account OfflineIMAP configuration.
      - That makes OfflineIMAP to use exclamation mark (!) instead of colon for
        storing messages. Such files can be written to windows partitions. But
        you will probably loose compatibility with other programs trying to
        read the same Maildir.
      - Exclamation mark was choosed because of the note in
        http://docs.python.org/library/mailbox.html
      - If you have some messages already stored without this option, you will
        have to re-sync them again

   * Enable file name character translation in windows registry (not tested)
      - http://support.microsoft.com/kb/289627

   * Use cygwin managed mount (not tested)
      - not available anymore since cygwin 1.7


Synchronization Performance
===========================

By default, we use fairly conservative settings that are good for
syncing but that might not be the best performing one. Once you got
everything set up and running, you might want to look into speeding up
your synchronization. Here are a couple of hints and tips on how to
achieve this.

 1) Use maxconnections > 1. By default we only use one connection to an
    IMAP server. Using 2 or even 3 speeds things up considerably in most
    cases. This setting goes into the [Repository XXX] section.

 2) Use folderfilters. The quickest sync is a sync that can ignore some
    folders. I sort my inbox into monthly folders, and ignore every
    folder that is more than 2-3 months old, this lets me only inspect a
    fraction of my Mails on every sync. If you haven't done this yet, do
    it :). See the folderfilter section the example offlineimap.conf.

 3) The default status cache is a plain text file that will write out
    the complete file for each single new message (or even changed flag)
    to a temporary file. If you have plenty of files in a folder, this
    is a few hundred kilo to megabytes for each mail and is bound to
    make things slower. I recommend to use the sqlite backend for
    that. See the status_backend = sqlite setting in the example
    offlineimap.conf. You will need to have python-sqlite installed in
    order to use this. This will save you plenty of disk activity. Do
    note that the sqlite backend is still considered experimental as it
    has only been included recently (although a loss of your status
    cache should not be a tragedy as that file can be rebuild
    automatically)

 4) Use quick sync. A regular sync will request all flags and all UIDs
    of all mails in each folder which takes quite some time. A 'quick'
    sync only compares the number of messages in a folder on the IMAP
    side (it will detect flag changes on the Maildir side of things
    though). A quick sync on my smallish account will take 7 seconds
    rather than 40 seconds. Eg, I run a cron script that does a regular
    sync once a day, and does quick syncs inbetween.

 5) Turn off fsync. In the [general] section you can set fsync to True
    or False. If you want to play 110% safe and wait for all operations
    to hit the disk before continueing, you can set this to True. If you
    set it to False, you lose some of that safety trading it for speed.

Security and SSL
================

Some words on OfflineImap and its use of SSL/TLS. By default, we will
connect using any method that openssl supports, that is SSLv2, SSLv3, or
TLSv1. Do note that SSLv2 is notoriously insecure and deprecated.
Unfortunately, python2 does not offer easy ways to disable SSLv2. It is
recommended you test your setup and make sure that the mail server does
not use an SSLv2 connection. Use e.g. "openssl s_client -host
mail.server -port 443" to find out the connection that is used by
default.

Certificate checking
^^^^^^^^^^^^^^^^^^^^

Unfortunately, by default we will not verify the certificate of an IMAP
TLS/SSL server we connect to, so connecting by SSL is no guarantee
against man-in-the-middle attacks. While verifying a server certificate
fingerprint is being planned, it is not implemented yet. There is
currently only one safe way to ensure that you connect to the correct
server in an encrypted manner: You can specify a 'sslcacertfile' setting
in your repository section of offlineimap.conf pointing to a file that
contains (among others) a CA Certificate in PEM format which validating
your server certificate. In this case, we will check that: 1) The server
SSL certificate is validated by the CA Certificate 2) The server host
name matches the SSL certificate 3) The server certificate is not past
its expiration date. The FAQ contains an entry on how to create your own
certificate and CA certificate.

StartTLS
^^^^^^^^

If you have not configured your account to connect via SSL anyway,
OfflineImap will still attempt to set up an SSL connection via the
STARTTLS function, in case the imap server supports it. Do note, that
there is no certificate or fingerprint checking involved at all, when
using STARTTLS (the underlying imaplib library does not support this
yet). This means that you will be protected against passively listening
eavesdroppers and they will not be able to see your password or email
contents. However, this will not protect you from active attacks, such
as Man-In-The-Middle attacks which cause you to connect to the wrong
server and pretend to be your mail server. DO NOT RELY ON STARTTLS AS A
SAFE CONNECTION GUARANTEEING THE AUTHENTICITY OF YOUR IMAP SERVER!
=======
