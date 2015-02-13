====================
 OfflineIMAP Manual
====================

.. _OfflineIMAP: http://offlineimap.org

--------------------------------------------------------
Powerful IMAP/Maildir synchronization and reader support
--------------------------------------------------------

:Author: John Goerzen <jgoerzen@complete.org> & contributors
:Date: 2012-02-23

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

Most configuration is done via the configuration file.  However, any setting can
also be overriden by command line options handed to OfflineIMAP.

OfflineImap is well suited to be frequently invoked by cron jobs, or can run in
daemon mode to periodically check your email (however, it will exit in some
error situations).

The documentation is included in the git repository and can be created by
issueing `make doc` in the `doc` folder (python-sphinx required), or it can
be viewed online at http://docs.offlineimap.org.

.. _configuration:

Configuration
=============

`OfflineIMAP`_ is regulated by a configuration file that is normally stored in
`~/.offlineimaprc`.  `OfflineIMAP`_ ships with a file named `offlineimap.conf`
that you should copy to that location and then edit.  This file is vital to
proper operation of the system; it sets everything you need to run
`OfflineIMAP`_.  Full documentation for the configuration file is included
within the sample file.


`OfflineIMAP`_ also ships a file named `offlineimap.conf.minimal` that you can
also try.  It's useful if you want to get started with the most basic feature
set, and you can read about other features later with `offlineimap.conf`.

Check out the `Use Cases`_ section for some example configurations.

If you want to be XDG-compatible, you can put your configuration file into
`$XDG_CONFIG_HOME/offlineimap/config`.


OPTIONS
=======

The command line options are described by issueing `offlineimap --help`.
Details on their use can be found either in the sample offlineimap.conf file or
in the user docs at http://docs.offlineimap.org.

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

Basic is designed for situations in which OfflineIMAP will be run non-attended
and the status of its execution will be logged.  This user interface is not
capable of reading a password from the keyboard; account passwords must be
specified using one of the configuration file options. For example, it will not
print periodic sleep announcements and tends to be a tad less verbose, in
general.


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
    cache should not be a tragedy as that file can be rebuilt
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

OfflineImap uses a cache to store the last know status of mails (flags etc).
Historically that has meant plain text files, but recently we introduced
sqlite-based cache, which helps with performance and CPU usage on large folders.
Here is how to upgrade existing plain text cache installations to sqlite based
one:

1) Sync to make sure things are reasonably similar

2) Change the account section to status_backend = sqlite

3) A new sync will convert your plain text cache to an sqlite cache
   (but leave the old plain text cache around for easy reverting) This
   should be quick and not involve any mail up/downloading.

4) See if it works :-)

5) If it does not work, go back to the old version or set
   status_backend=plain

6) Or, once you are sure it works, you can delete the
   .offlineimap/Account-foo/LocalStatus folder (the new cache will be
   in the LocalStatus-sqlite folder)

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

.. _UNIX signals:

UNIX Signals
============

OfflineImap listens to the unix signals SIGUSR1, SIGUSR2, SIGTERM,
SIGINT, SIGHUP, SIGQUIT:

If sent a SIGUSR1 it will abort any current (or next future) sleep of all
accounts that are configured to "autorefresh". In effect, this will trigger a
full sync of all accounts to be performed as soon as possible.

If sent a SIGUSR2, it will stop "autorefresh mode" for all accounts. That is,
accounts will abort any current sleep and will exit after a currently running
synchronization has finished. This signal can be used to gracefully exit out of
a running offlineimap "daemon".

SIGTERM, SIGINT, SIGHUP are all treated to gracefully terminate as
soon as possible. This means it will finish syncing the current folder
in each account, close keep alive connections, remove locks on the
accounts and exit. It may take up to 10 seconds, if autorefresh option
is used.

SIGQUIT dumps stack traces for all threads and tries to dump process
core.

Folder filtering and nametrans
==============================

OfflineImap offers flexible (and complex) ways of filtering and transforming
folder names. Please see the docs/doc-src/nametrans.rst document about details
how to use folder filters and name transformations. The documentation will be
autogenerated by a "make doc" in the docs directory. It is also viewable at
:ref:`folder_filtering_and_name_translation`.

KNOWN ISSUES
============

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

* OfflineIMAP confused after system suspend.
    When resuming a suspended session, OfflineIMAP does not cleanly handles the
    broken socket(s) if socktimeout option is not set.
    You should enable this option with a value like 10.

.. _pitfalls:

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


Sync from Gmail to a local Maildir with labels
----------------------------------------------

This is an example of a setup where GMail gets synced with a local Maildir.
It also keeps track of GMail labels, that get embedded into the messages
under the header configured in the labelsheader setting, and syncs them back
and forth the same way as flags. This is particularly useful with an email
client that indexes your email and recognizes the labels header, so that you
can sync a single "All Mail" folder, and navigate your email via searches.

The header used to store the labels depends on the email client you plan to use.
Some choices that may be recognized by email clients are X-Keywords
(the default) or X-Labels. Note that if you need to change the label header
after the labels have already been synced, you will have to change the header
manually on all messages, otherwise offlineimap will not pick up the labels under
the old header.

The first time OfflineIMAP runs with synclabels enabled on a large repository it
may take some time as the labels are read / embedded on every message.
Afterwards local label changes are detected using modification times, which is
much faster::

    [Account Gmail-mine]
    localrepository = Gmaillocal-mine
    remoterepository = Gmailserver-mine
    synclabels = yes
    # This header is where labels go.  Usually you will be fine
    # with default value (X-Keywords), but in case you want it
    # different, here we go:
    labelsheader = X-Keywords

    [Repository Gmailserver-mine]
    #This is the remote repository
    type = Gmail
    remotepass = XXX
    remoteuser = XXX

    [Repository Gmaillocal-mine]
    #This is the 'local' repository
    type = GmailMaildir

There are some labels, that gmail treats in a special way. All internal gmail
labels start with "\\". Those labels include: \\Drafts, \\Important, \\Inbox,
\\Sent, \\Junk, \\Flagged, \\Trash. You can add and remove those labels
locally, and when synced, will have special actions on the gmail side. For instance,
adding the label \Trash to an email will move it to the trash, and be permanantly
deleted after some time. This is relevant, since gmail's IMAP prevents from removing
messages from the "All Mail" folder the usual way.


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
Thomas Kahle at `<http://dev.gentoo.org/~tomka/mail.html>`_

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

Here is a basic content sample::

    import commands

    def get_password(account_name):
      cmd = "security find-internet-password -w -a '%s'"% account_name
      (status, output) = commands.getstatusoutput(cmd)
      return output

From this sample, replace the cmd line with whatever can retrieve your password.
Your pythonfile needs to contain implementations for the functions
that you want to use in offflineimaprc.  The example uses it for two
purposes: Fetching passwords from the gnome-keyring and translating
folder names on the server to local foldernames.  An example
implementation of get_username and get_password showing how to query
gnome-keyring is contained in
`<http://dev.gentoo.org/~tomka/mail-setup.tar.bz2>`_ The folderfilter is
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
