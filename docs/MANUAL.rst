====================
 OfflineIMAP Manual
====================

--------------------------------------------------------
Powerful IMAP/Maildir synchronization and reader support
--------------------------------------------------------

:Author: John Goerzen <jgoerzen@complete.org> & contributors
:Date: 2011-01-15
:Copyright: GPL v2
:Manual section: 1

.. TODO: :Manual group:


DESCRIPTION
===========

OfflineImap operates on a REMOTE and a LOCAL repository and synchronizes
emails between them, so that you can read the same mailbox from multiple
computers. The REMOTE repository is some IMAP server, while LOCAL can be
either a local Maildir or another IMAP server.

Missing folders will be automatically created on both sides if
needed. No folders will be deleted at the moment.

Configuring OfflineImap in basic mode is quite easy, however it provides
an amazing amount of flexibility for those with special needs.  You can
specify the number of connections to your IMAP server, use arbitrary
python functions (including regular expressions) to limit the number of
folders being synchronized. You can transpose folder names between
repositories using any python function, to mangle and modify folder
names on the LOCAL repository. There are six different ways to hand the
IMAP password to OfflineImap from console input, specifying in the
configuration file, .netrc support, specifying in a separate file, to
using arbitrary python functions that somehow return the
password. Finally, you can use IMAPs IDLE infrastructure to always keep
a connection to your IMAP server open and immediately be notified (and
synchronized) when a new mail arrives (aka Push mail).

Most configuration is done via the configuration file.  However, any setting can also be overriden by command line options handed to OfflineIMAP.

OfflineImap is well suited to be frequently invoked by cron jobs, or can run in daemon mode to periodically check your email (however, it will exit in some error situations).

Check out the `Use Cases`_ section for some example configurations.


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
informative of the overall picture of what OfflineIMAP is doing.

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
------

TTYUI interface is for people running in terminals.  It prints out basic
status messages and is generally friendly to use on a console or xterm.


Basic
------

Basic is designed for situations in which OfflineIMAP will be run
non-attended and the status of its execution will be logged.  This user
interface is not capable of reading a password from the keyboard;
account passwords must be specified using one of the configuration file
options. For example, it will not print periodic sleep announcements and tends to be a tad less verbose, in general.


Quiet
-----

It will output nothing except errors and serious warnings.  Like Basic,
this user interface is not capable of reading a password from the
keyboard; account passwords must be specified using one of the
configuration file options.

MachineUI
---------

MachineUI generates output in a machine-parsable format.  It is designed
for other programs that will interface to OfflineIMAP.


Synchronization Performance
===========================

By default, we use fairly conservative settings that are safe for
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
    sync once a day, and does quick syncs (-q) only synchronizing the
    "-f INBOX" in between.

 5) Turn off fsync. In the [general] section you can set fsync to True
    or False. If you want to play 110% safe and wait for all operations
    to hit the disk before continueing, you can set this to True. If you
    set it to False, you lose some of that safety, trading it for speed.


Upgrading from plain text cache to SQLITE based cache
=====================================================

OfflineImap uses a cache to store the last know status of mails (flags etc). Historically that has meant plain text files, but recently we introduced sqlite-based cache, which helps with performance and CPU usage on large folders. Here is how to upgrade existing plain text cache installations to sqlite based one:

 1) Sync to make sure things are reasonably similar
 3) Change the account section to status_backend = sqlite
 4) A new sync will convert your plain text cache to an sqlite cache (but
 leave the old plain text cache around for easy reverting)
    This should be quick and not involve any mail up/downloading.
 5) See if it works :-)
 6a) If it does not work, go back to the old version or set
     status_backend=plain
 6b) Or once you are sure it works, you can delete the
 .offlineimap/Account-foo/LocalStatus folder (the new cache will be in
 the LocalStatus-sqlite folder)


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
--------------------

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
--------

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

UNIX Signals
============

OfflineImap listens to the unix signals SIGUSR1 and SIGUSR2.

If sent a SIGUSR1 it will abort any current (or next future) sleep of all
accounts that are configured to "autorefresh". In effect, this will trigger a
full sync of all accounts to be performed as soon as possible.

If sent a SIGUSR2, it will stop "autorefresh mode" for all accounts. That is,
accounts will abort any current sleep and will exit after a currently running
synchronization has finished. This signal can be used to gracefully exit out of
a running offlineimap "daemon".

Folder filtering and Name translation
=====================================

OfflineImap provides advanced and potentially complex possibilities for
filtering and translating folder names. If you don't need this, you can
safely skip this section.

folderfilter
------------

If you do not want to synchronize all your filters, you can specify a folderfilter function that determines which folders to include in a sync and which to exclude. Typically, you would set a folderfilter option on the remote repository only, and it would be a lambda or any other python function.

If the filter function returns True, the folder will be synced, if it
returns False, it. The folderfilter operates on the *UNTRANSLATED* name
(before any nametrans translation takes place).

Example 1: synchronizing only INBOX and Sent::

   folderfilter = lambda foldername: foldername in ['INBOX', 'Sent']

Example 2: synchronizing everything except Trash::

   folderfilter = lambda foldername: foldername not in ['Trash']

Example 3: Using a regular expression to exclude Trash and all folders
containing the characters "Del"::

    folderfilter = lambda foldername: not re.search('(^Trash$|Del)', foldername)

If folderfilter is not specified, ALL remote folders will be
synchronized.

You can span multiple lines by indenting the others.  (Use backslashes
at the end when required by Python syntax)  For instance::

 folderfilter = lambda foldername: foldername in
        ['INBOX', 'Sent Mail', 'Deleted Items',
         'Received']

You only need a folderfilter option on the local repository if you want to prevent some folders on the local repository to be created on the remote one.

Even if you filtered out folders, You can specify folderincludes to
include additional folders.  It should return a Python list.  This might
be used to include a folder that was excluded by your folderfilter rule,
to include a folder that your server does not specify with its LIST
option, or to include a folder that is outside your basic reference. The
'reference' value will not be prefixed to this folder name, even if you
have specified one.  For example::

   folderincludes = ['debian.user', 'debian.personal']

nametrans
----------

Sometimes, folders need to have different names on the remote and the
local repositories. To achieve this you can specify a folder name
translator.  This must be a eval-able Python expression that takes a
foldername arg and returns the new value.  I suggest a lambda.  This
example below will remove "INBOX." from the leading edge of folders
(great for Courier IMAP users)::

   nametrans = lambda foldername: re.sub('^INBOX\.', '', foldername)

Using Courier remotely and want to duplicate its mailbox naming
locally?  Try this::

   nametrans = lambda foldername: re.sub('^INBOX\.*', '.', foldername)


WARNING: you MUST construct nametrans rules such that it NEVER returns
the same value for two folders, UNLESS the second values are
filtered out by folderfilter below. That is, two filters on one side may never point to the same folder on the other side. Failure to follow this rule
will result in undefined behavior. See also *Sharing a maildir with multiple IMAP servers* in the `PITFALLS & ISSUES`_ section.

Where to put nametrans rules, on the remote and/or local repository?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

If you never intend to create new folders on the LOCAL repository that
need to be synced to the REMOTE repository, it is sufficient to create a
nametrans rule on the remote Repository section. This will be used to
determine the names of new folder names on the LOCAL repository, and to
match existing folders that correspond.

*IF* you create folders on the local repository, that are supposed to be
 automatically created on the remote repository, you will need to create
 a nametrans rule that provides the reverse name translation.

(A nametrans rule provides only a one-way translation of names and in
order to know which names folders on the LOCAL side would have on the
REMOTE side, you need to specify the reverse nametrans rule on the local
repository)

OfflineImap will complain if it needs to create a new folder on the
remote side and a back-and-forth nametrans-lation does not yield the
original foldername (as that could potentially lead to infinite folder
creation cycles).

What folder separators do I need to use in nametrans rules?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

**Q:** If I sync from an IMAP server with folder separator '/' to a
  Maildir using the default folder separator '.' which do I need to use
  in nametrans rules?::

  nametrans = lambda f: "INBOX/" + f
or::
  nametrans = lambda f: "INBOX." + f

**A:** Generally use the folder separator as defined in the repository
  you write the nametrans rule for. That is, use '/' in the above
  case. We will pass in the untranslated name of the IMAP folder as
  parameter (here `f`). The translated name will ultimately have all
  folder separators be replaced with the destination repositories'
  folder separator.

So if 'f' was "Sent", the first nametrans yields the translated name
"INBOX/Sent" to be used on the other side. As that repository uses the
folder separator '.' rather than '/', the ultimate name to be used will
be "INBOX.Sent".

(As a final note, the smart will see that both variants of the above
nametrans rule would have worked identically in this case)

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
      - Exclamation mark was chosen because of the note in
        http://docs.python.org/library/mailbox.html
      - If you have some messages already stored without this option, you will
        have to re-sync them again

   * Enable file name character translation in windows registry (not tested)
      - http://support.microsoft.com/kb/289627

   * Use cygwin managed mount (not tested)
      - not available anymore since cygwin 1.7


PITFALLS & ISSUES
=================

Sharing a maildir with multiple IMAP servers
--------------------------------------------

 Generally a word of caution mixing IMAP repositories on the same
 Maildir root. You have to be careful that you *never* use the same
 maildir folder for 2 IMAP servers. In the best case, the folder MD5
 will be different, and you will get a loop where it will upload your
 mails to both servers in turn (infinitely!) as it thinks you have
 placed new mails in the local Maildir. In the worst case, the MD5 is
 the same (likely) and mail UIDs overlap (likely too!) and it will fail to
 sync some mails as it thinks they are already existent.

 I would create a new local Maildir Repository for the Personal Gmail and
 use a different root to be on the safe side here. You could e.g. use
 `~/mail/Pro` as Maildir root for the ProGmail and
 `~/mail/Personal` as root for the personal one.

 If you then point your local mutt, or whatever MUA you use to `~/mail/`
 as root, it should still recognize all folders. (see the 2 IMAP setup
 in the `Use Cases`_ section.

USE CASES
=========

Sync from GMail to another IMAP server
--------------------------------------

This is an example of a setup where "TheOtherImap" requires all folders to be under INBOX::

    [Repository Gmailserver-foo]
    #This is the remote repository
    type = Gmail
    remotepass = XXX
    remoteuser = XXX
    # The below will put all GMAIL folders as sub-folders of the 'local' INBOX,
    # assuming that your path separator on 'local' is a dot.
    nametrans = lambda x: 'INBOX.' + x
    
    [Repository TheOtherImap]
    #This is the 'local' repository
    type = IMAP
    remotehost = XXX
    remotepass = XXX
    remoteuser = XXX
    #Do not use nametrans here.

Selecting only a few folders to sync
------------------------------------
Add this to the remote gmail repository section to only sync mails which are in a certain folder::

    folderfilter = lambda folder: folder.startswith('MyLabel')

To only get the All Mail folder from a Gmail account, you would e.g. do::

    folderfilter = lambda folder: folder.startswith('[Gmail]/All Mail') 


Another nametrans transpose example
-----------------------------------

Put everything in a GMX. subfolder except for the boxes INBOX, Draft,
and Sent which should keep the same name::

     nametrans: lambda folder: folder if folder in ['INBOX', 'Drafts', 'Sent'] \
                               else re.sub(r'^', r'GMX.', folder)

2 IMAP using name translations
------------------------------

Synchronizing 2 IMAP accounts to local Maildirs that are "next to each
other", so that mutt can work on both. Full email setup described by
Thomas Kahle at `http://dev.gentoo.org/~tomka/mail.html`_

offlineimap.conf::

    [general]
    accounts = acc1, acc2
    maxsyncaccounts = 2
    ui = ttyui
    pythonfile=~/bin/offlineimap-helpers.py
    socktimeout = 90
    
    [Account acc1]
    localrepository = acc1local
    remoterepository = acc1remote
    autorefresh = 2
    
    [Account acc2]
    localrepository = acc2local
    remoterepository = acc2remote
    autorefresh = 4
    
    [Repository acc1local]
    type = Maildir
    localfolders = ~/Mail/acc1
    
    [Repository acc2local]
    type = Maildir
    localfolders = ~/Mail/acc2
    
    [Repository acc1remote]
    type = IMAP
    remotehost = imap.acc1.com
    remoteusereval = get_username("imap.acc1.net")
    remotepasseval = get_password("imap.acc1.net")
    nametrans = oimaptransfolder_acc1
    ssl = yes
    maxconnections = 2
    # Folders to get:
    folderfilter = lambda foldername: foldername in [
                 'INBOX', 'Drafts', 'Sent', 'archiv']
    
    [Repository acc2remote]
    type = IMAP
    remotehost = imap.acc2.net
    remoteusereval = get_username("imap.acc2.net")
    remotepasseval = get_password("imap.acc2.net")
    nametrans = oimaptransfolder_acc2
    ssl = yes
    maxconnections = 2

One of the coolest things about offlineimap is that you can call
arbitrary python code from your configuration.  To do this, specify a
pythonfile with::

    pythonfile=~/bin/offlineimap-helpers.py

Your pythonfile needs to contain implementations for the functions
that you want to use in offflineimaprc.  The example uses it for two
purposes: Fetching passwords from the gnome-keyring and translating
folder names on the server to local foldernames.  An example
implementation of get_username and get_password showing how to query
gnome-keyring is contained in
`http://dev.gentoo.org/~tomka/mail-setup.tar.bz2`_ The folderfilter is
a lambda term that, well, filters which folders to get. The function
`oimaptransfolder_acc2` translates remote folders into local folders
with a very simple logic. The `INBOX` folder will have the same name
as the account while any other folder will have the account name and a
dot as a prefix. This is useful for hierarchichal display in mutt.
Offlineimap handles the renaming correctly in both directions::

    import re
    def oimaptransfolder_acc1(foldername):
        if(foldername == "INBOX"):
            retval = "acc1"
        else:
            retval = "acc1." + foldername
        retval = re.sub("/", ".", retval)
        return retval
    
    def oimaptransfolder_acc2(foldername):
        if(foldername == "INBOX"):
            retval = "acc2"
        else:
            retval = "acc2." + foldername
        retval = re.sub("/", ".", retval)
        return retval
