.. -*- coding: utf-8 -*-

.. NOTE TO MAINTAINERS: Please add new questions to the end of their
   sections, so section/question numbers remain stable.


=============================================
 OfflineIMAP FAQ (Frequently Asked Questions)
=============================================

:Web site: https://github.com/nicolas33/offlineimap
:Copyright: This document is licensed under GPLv2.

.. contents::
.. sectnum::


This is a work in progress.

Please feel free to ask questions and/or provide answers; send email to the
`mailing list`_.

.. _mailing list: http://lists.alioth.debian.org/mailman/listinfo/offlineimap-project
.. _OfflineIMAP: https://github.com/nicolas33/offlineimap
.. _ssl.wrap_socket: http://docs.python.org/library/ssl.html#ssl.wrap_socket


OfflineIMAP
===========

Where do I get OfflineIMAP?
---------------------------

See the information on the Home page `OfflineIMAP`_.

How fast is it?
---------------

OfflineIMAP has a multithreaded sync, so it should have very nice performance.

OfflineIMAP versions 2.0 and above contain a multithreaded system. A good way
to experiment is by setting maxsyncaccounts to 3 and maxconnections to 3 in
each account clause.

This lets OfflineIMAP open up multiple connections simultaneously. That will
let it process multiple folders and messages at once. In most cases, this will
increase performance of the sync.

Don’t set the number too high. If you do that, things might actually slow down
as your link gets saturated. Also, too many connections can cause mail servers
to have excessive load. Administrators might take unkindly to this, and the
server might bog down. There are many variables in the optimal setting;
experimentation may help.

An informal benchmark yields these results for my setup::

    * 10 minutes with MacOS X Mail.app “manual cache”
    * 5 minutes with GNUS agent sync
    * 20 seconds with OfflineIMAP 1.x
    * 9 seconds with OfflineIMAP 2.x
    * 3 seconds with OfflineIMAP 3.x “cold start”
    * 2 seconds with OfflineIMAP 3.x “held connection”

What platforms does OfflineIMAP support?
----------------------------------------

It should run on most platforms supported by Python, which are quite a few. I
do not support Windows myself, but some have made it work there.  Use on
Windows

These answers have been reported by OfflineIMAP users. I do not run OfflineIMAP
on Windows myself, so I can’t directly address their accuracy.

The basic answer is that it’s possible and doesn’t require hacking OfflineIMAP
source code. However, it’s not necessarily trivial. The information below is
based in instructions submitted by Chris Walker.

First, you must run OfflineIMAP in the Cygwin environment. The Windows
filesystem is not powerful enough to accomodate Maildir by itself.

Next, you’ll need to mount your Maildir directory in a special way. There is
information for doing that at http://barnson.org/node/295. That site gives this
example::

  mount -f -s -b -o managed "d:/tmp/mail" "/home/of/mail"

That URL also has more details on making OfflineIMAP work with Windows.


Does OfflineIMAP support mbox, mh, or anything else other than Maildir?
-----------------------------------------------------------------------

Not directly. Maildir was the easiest to implement. I’m not planning to write
mbox code for OfflineIMAP, though if someone sent me well-written mbox support
and pledged to support it, I’d commit it to the tree.

However, OfflineIMAP can directly sync accounts on two different IMAP servers
together. So you could install an IMAP server on your local machine that
supports mbox, sync to it, and then instruct your mail readers to use the
mboxes.

Or you could install whatever IMAP server you like on the local machine, and
point your mail readers to that IMAP server on localhost.

What is the UID validity problem for folder?
--------------------------------------------

IMAP servers use a unique ID (UID) to refer to a specific message.  This number
is guaranteed to be unique to a particular message forever.  No other message in
the same folder will ever get the same UID.  UIDs are an integral part of
`OfflineIMAP`_'s synchronization scheme; they are used to match up messages on
your computer to messages on the server.

Sometimes, the UIDs on the server might get reset.  Usually this will happen if
you delete and then recreate a folder.  When you create a folder, the server
will often start the UID back from 1.  But `OfflineIMAP`_ might still have the
UIDs from the previous folder by the same name stored.  `OfflineIMAP`_ will
detect this condition and skip the folder.  This is GOOD, because it prevents
data loss.

You can fix it by removing your local folder and cache data.  For instance, if
your folders are under `~/Folders` and the folder with the problem is INBOX,
you'd type this::

  rm -r ~/Folders/INBOX
  rm -r ~/.offlineimap/Account-AccountName/LocalStatus/INBOX
  rm -r ~/.offlineimap/Repository-RemoteRepositoryName/FolderValidity/INBOX

(Of course, replace AccountName and RemoteRepositoryName with the names as
specified in `~/.offlineimaprc`).

Next time you run `OfflineIMAP`_, it will re-download the folder with the new
UIDs.  Note that the procedure specified above will lose any local changes made
to the folder.

Some IMAP servers are broken and do not support UIDs properly.  If you continue
to get this error for all your folders even after performing the above
procedure, it is likely that your IMAP server falls into this category.
`OfflineIMAP`_ is incompatible with such servers.  Using `OfflineIMAP`_ with
them will not destroy any mail, but at the same time, it will not actually
synchronize it either.  (`OfflineIMAP`_ will detect this condition and abort
prior to synchronization.)


This question comes up frequently on the `mailing list`_.  You can find a detailed
discussion of the problem there
http://lists.complete.org/offlineimap@complete.org/2003/04/msg00012.html.gz.

How do I add or delete a folder?
--------------------------------

OfflineIMAP does not currently provide this feature. However, if you create a
new folder on the remote server, OfflineIMAP will detect this and create the
corresponding folder locally automatically.

May I delete local folders?
---------------------------

`OfflineIMAP`_ does a two-way synchronization.  That is, if you make a change
to the mail on the server, it will be propagated to your local copy, and
vise-versa.  Some people might think that it would be wise to just delete all
their local mail folders periodically.  If you do this with `OfflineIMAP`_,
remember to also remove your local status cache (`~/.offlineimap` by default).
Otherwise, `OfflineIMAP`_ will take this as an intentional deletion of many
messages and will interpret your action as requesting them to be deleted from
the server as well.  (If you don't understand this, don't worry; you probably
won't encounter this situation.)

Can I run multiple instances?
-----------------------------

`OfflineIMAP`_ is not designed to have several instances (for instance, a cron
job and an interactive invocation) run over the same mailbox simultaneously.
It will perform a check on startup and abort if another `OfflineIMAP`_ is
already running.  If you need to schedule synchronizations, you'll probably
find autorefresh settings more convenient than cron.  Alternatively, you can
set a separate metadata directory for each instance.

Can I copy messages between folders?
---------------------------------------

Normally, when you copy a message between folders or add a new message to a
folder locally, `OfflineIMAP`_ will just do the right thing.  However,
sometimes this can be tricky ― if your IMAP server does not provide the SEARCH
command, or does not return something useful, `OfflineIMAP`_ cannot determine
the new UID of the message.  So, in these rare instances, OfflineIMAP will
upload the message to the IMAP server and delete it from your local folder.
Then, on your next sync, the message will be re-downloaded with the proper UID.
`OfflineIMAP`_ makes sure that the message was properly uploaded before
deleting it, so there should be no risk of data loss.

Does OfflineIMAP support POP?
-----------------------------

No. POP is not robust enough to do a completely reliable multi-machine sync
like OfflineIMAP can do.

OfflineIMAP will never support POP.

How is OfflineIMAP conformance?
-------------------------------

* Internet Message Access Protocol version 4rev1 (IMAP 4rev1) as specified in
  `2060`:RFC: and `3501`:RFC:
* CRAM-MD5 as specified in `2195`:RFC:
* Maildir as specified in the Maildir manpage and the qmail website
* Standard Python 2.6 as implemented on POSIX-compliant systems

Can I force OfflineIMAP to sync a folder right now?
---------------------------------------------------

Yes, if you use the `Blinkenlights` UI.  That UI shows the active accounts
as follows::

  4: [active]      *Control: .
  3: [  4:36]      personal:
  2: [  3:37]          work: .
  1: [  6:28]           uni:

Simply press the appropriate digit (`3` for `personal`, etc.) to resync that
account immediately.  This will be ignored if a resync is already in progress
for that account.

Configuration Questions
=======================

Can I synchronize multiple accounts with OfflineIMAP?
-----------------------------------------------------

Of course!

Just name them all in the accounts line in the general section of the
configuration file, and add a per-account section for each one.

You can also optionally use the -a option when you run OfflineIMAP to request
that it only operate upon a subset of the accounts for a particular run.

How do I specify the names of folders?
--------------------------------------

You do not need to. OfflineIMAP is smart enough to automatically figure out
what folders are present on the IMAP server and synchronize them. You can use
the folderfilter and nametrans configuration file options to request only
certain folders and rename them as they come in if you like.

How do I prevent certain folders from being synced?
---------------------------------------------------

Use the folderfilter option.

What is the mailbox name recorder (mbnames) for?
------------------------------------------------

Some mail readers, such as mutt, are not capable of automatically determining the names of your mailboxes. OfflineIMAP can help these programs by writing the names of the folders in a format you specify. See the example offlineimap.conf for details.

Does OfflineIMAP verify SSL certificates?
-----------------------------------------

By default, no.  However, as of version 6.3.2, it is possible to enforce verification
of SSL certificate on a per-repository basis by setting the `sslcacertfile` option in the
config file.  (See the example offlineimap.conf for details.)

How do I generate an `sslcacertfile` file?
------------------------------------------

The `sslcacertfile` file must contain an SSL certificate (or a concatenated
certificates chain) in PEM format.  (See the documentation of
`ssl.wrap_socket`_'s `certfile` parameter for the gory details.)  The following
command should generate a file in the proper format::

    openssl s_client -CApath /etc/ssl/certs -connect ${hostname}:imaps -showcerts \
       | perl -ne 'print if /BEGIN/../END/; print STDERR if /return/' > $sslcacertfile
    ^D

Before using the resulting file, ensure that openssl verified the certificate
successfully.

The path `/etc/ssl/certs` is not standardized; your system may store
SSL certificates elsewhere.  (On some systems it may be in
`/usr/local/share/certs/`.)


IMAP Server Notes
=================

In general, OfflineIMAP works with any IMAP server that provides compatibility
with the IMAP RFCs. Some servers provide imperfect compatibility that may be
good enough for general clients. OfflineIMAP needs more features, specifically
support for UIDs, in order to do its job accurately and completely.

Microsoft Exchange
------------------

Several users have reported problems with Microsoft Exchange servers in
conjunction with OfflineIMAP. This generally seems to be related to the
Exchange servers not properly following the IMAP standards.

Mark Biggers has posted some information to the OfflineIMAP `mailing list`_
about how he made it work.

Other users have indicated that older (5.5) releases of Exchange are so bad
that they will likely not work at all.

I do not have access to Exchange servers for testing, so any problems with it,
if they can even be solved at all, will require help from OfflineIMAP users to
find and fix.


Client Notes
============

What clients does OfflineIMAP work with?
----------------------------------------

Any client that supports Maildir. Popular ones include mutt, Evolution and
KMail. Thunderbird does not have maildir suppport.

With OfflineIMAP’s IMAP-to-IMAP syncing, this can be even wider; see the next
question.

Evolution
---------

OfflineIMAP can work with Evolution. To do so, first configure your OfflineIMAP
account to have sep = / in its configuration. Then, configure Evolution with
the “Maildir-format mail directories” server type. For the path, you will need
to specify the name of the top-level folder inside your OfflineIMAP storage
location. You’re now set!

KMail
-----

At this time, I believe that OfflineIMAP with Maildirs is not compatible with
KMail. KMail cannot work in any mode other than to move all messages out of all
folders immediately, which (besides being annoying and fundamentally broken) is
incompatible with OfflineIMAP.

However, I have made KMail version 3 work well with OfflineIMAP by installing
an IMAP server on my local machine, having OfflineIMAP sync to that, and
pointing KMail at the same server.

Another way to see mails downloaded with offlineimap in KMail (KDE4) is to
create a local folder (e.g. Backup) and then use ``ln -s
localfolders_in_offlineimaprc ~/.kde/share/apps/kmail/mail/.Backup.directory``.
Maybe you have to rebuild the index of the new folder. Works well with KMail
1.11.4 (KDE4.x), offlineimap 6.1.2 and ArchLinux and sep = / in .offlineimaprc.

Mutt
----

* Do I need to use set maildir_trash?

Other IMAP sync programs require you to do this. OfflineIMAP does not. You’ll
get the best results without it, in fact, though turning it on won’t hurt
anything.

* How do I set up mbnames with mutt?

The example offlineimap.conf file has this example. In your offlineimap.conf,
you’ll list this::

  [mbnames]
  enabled = yes
  filename = ~/Mutt/muttrc.mailboxes
  header = "mailboxes " 
  peritem = "+%(accountname)s/%(foldername)s" 
  sep = " " 
  footer = "\n"

Then in your ``.muttrc``::

  source ~/Mutt/muttrc.mailboxes


You might also want to set::

  set mbox_type=Maildir
  set folder=$HOME/Maildirpath

The OfflineIMAP manual has a more detailed example for doing this for multiple
accounts.

Miscellaneous Questions
=======================

Why are your Maildir message filenames so long?
-----------------------------------------------

OfflineIMAP has two relevant principles: 1) never modifying your messages in
any way and 2) ensuring 100% reliable synchronizations. In order to do a
reliable sync, OfflineIMAP must have a way to uniquely identify each e-mail.
Three pieces of information are required to do this: your account name, the
folder name, and the message UID. The account name can be calculated from the
path in which your messages are. The folder name can usually be as well, BUT
some mail clients move messages between folders by simply moving the file,
leaving the name intact.

So, OfflineIMAP must store both a message UID and a folder ID. The
folder ID is necessary so OfflineIMAP can detect a message being moved
to a different folder. OfflineIMAP stores the UID (U= number) and an
md5sum of the foldername (FMD5= number) to facilitate this.


What can I do to ensure OfflineIMAP is still running and hasn’t crashed?
------------------------------------------------------------------------

This shell script will restart OfflineIMAP if it has crashed. Sorry, its
written in Korn, so you’ll need ksh, pdksh, or mksh to run it::

  #!/bin/ksh
  # remove any old instances of this shell script or offlineimap
  for pid in $(pgrep offlineimap)
  do
    if  $pid -ne $$ 
    then
      kill $pid
    fi
  done

  # wait for compiz (or whatever) to start and setup wifi
  sleep 20
  # If offlineimap exits, restart it
  while true
  do
    ( exec /usr/bin/offlineimap -u Noninteractive.Quiet )
    sleep 60 # prevents extended failure condition
