.. -*- coding: utf-8 -*-

.. _mailing list: http://lists.alioth.debian.org/mailman/listinfo/offlineimap-project

======
README
======

.. contents::
.. sectnum::


Description
===========

Welcome to the official OfflineIMAP project.

*NOTICE:* this software was written by John Goerzen, who retired from
maintaining. It is now maintained by Nicolas Sebrecht at
https://github.com/nicolas33/offlineimap. Thanks to John for his great job and
to have share this project with us.


OfflineIMAP is a tool to simplify your e-mail reading. With OfflineIMAP, you can
read the same mailbox from multiple computers. You get a current copy of your
messages on each computer, and changes you make one place will be visible on all
other systems. For instance, you can delete a message on your home computer, and
it will appear deleted on your work computer as well. OfflineIMAP is also useful
if you want to use a mail reader that does not have IMAP support, has poor IMAP
support, or does not provide disconnected operation.

OfflineIMAP works on pretty much any POSIX operating system, such as Linux, BSD
operating systems, MacOS X, Solaris, etc.

OfflineIMAP is a Free Software project licensed under the GNU General Public
License. You can download it for free, and you can modify it. In fact, you are
encouraged to contribute to OfflineIMAP, and doing so is fast and easy.


OfflineIMAP is FAST; it synchronizes my two accounts with over 50 folders in 3
seconds.  Other similar tools might take over a minute, and achieve a
less-reliable result.  Some mail readers can take over 10 minutes to do the same
thing, and some don't even support it at all.  Unlike other mail tools,
OfflineIMAP features a multi-threaded synchronization algorithm that can
dramatically speed up performance in many situations by synchronizing several
different things simultaneously.

OfflineIMAP is FLEXIBLE; you can customize which folders are synced via regular
expressions, lists, or Python expressions; a versatile and comprehensive
configuration file is used to control behavior; two user interfaces are
built-in; fine-tuning of synchronization performance is possible; internal or
external automation is supported; SSL and PREAUTH tunnels are both supported;
offline (or "unplugged") reading is supported; and esoteric IMAP features are
supported to ensure compatibility with the widest variety of IMAP servers.

OfflineIMAP is SAFE; it uses an algorithm designed to prevent mail loss at all
costs.  Because of the design of this algorithm, even programming errors should
not result in loss of mail.  I am so confident in the algorithm that I use my
own personal and work accounts for testing of OfflineIMAP pre-release,
development, and beta releases.  Of course, legally speaking, OfflineIMAP comes
with no warranty, so I am not responsible if this turns out to be wrong.


Method of Operation
===================

OfflineIMAP traditionally operates by maintaining a hierarchy of mail folders in
Maildir format locally.  Your own mail reader will read mail from this tree, and
need never know that the mail comes from IMAP.  OfflineIMAP will detect changes
to the mail folders on your IMAP server and your own computer and
bi-directionally synchronize them, copying, marking, and deleting messages as
necessary.

With OfflineIMAP 4.0, a powerful new ability has been introduced ― the program
can now synchronize two IMAP servers with each other, with no need to have a
Maildir layer in-between.  Many people use this if they use a mail reader on
their local machine that does not support Maildirs.  People may install an IMAP
server on their local machine, and point both OfflineIMAP and their mail reader
of choice at it.  This is often preferable to the mail reader's own IMAP support
since OfflineIMAP supports many features (offline reading, for one) that most
IMAP-aware readers don't.  However, this feature is not as time-tested as
traditional syncing, so my advice is to stick with normal methods of operation
for the time being.


Quick Start
===========

If you have already installed OfflineIMAP system-wide, or your system
administrator has done that for you, your task for setting up OfflineIMAP for
the first time is quite simple.  You just need to set up your configuration
file, make your folder directory, and run it!

You can quickly set up your configuration file.  The distribution includes a
file offlineimap.conf.minimal (Debian users may find this at
``/usr/share/doc/offlineimap/examples/offlineimap.conf.minimal``) that is a
basic example of setting of OfflineIMAP.  You can simply copy this file into
your home directory and name it ``.offlineimaprc`` (note the leading period).  A
command such as ``cp offlineimap.conf.minimal ~/.offlineimaprc`` will do it.
Or, if you prefer, you can just copy this text to ``~/.offlineimaprc``::

  [general]
  accounts = Test

  [Account Test]
  localrepository = Local
  remoterepository = Remote

  [Repository Local]
  type = Maildir
  localfolders = ~/Test

  [Repository Remote]
  type = IMAP
  remotehost = examplehost
  remoteuser = jgoerzen


Now, edit the ``~/.offlineimaprc`` file with your favorite editor.  All you have
to do is specify a directory for your folders to be in (on the localfolders
line), the host name of your IMAP server (on the remotehost line), and your
login name on the remote (on the remoteuser line).  That's it!

To run OfflineIMAP, you just have to say offlineimap ― it will fire up, ask you
for a login password if necessary, synchronize your folders, and exit.  See?

You can just throw away the rest of this finely-crafted, perfectly-honed manual!
Of course, if you want to see how you can make OfflineIMAP FIVE TIMES FASTER FOR
JUST $19.95 (err, well, $0), you have to read on!


Documentation
=============

If you are reading this file on github, you can find more documentations in the
`docs` directory.

Using your git repository, you can generate documentation with::

	$ make doc


Mailing list
============

The user discussion, development and all exciting stuff take place in the
`mailing list`_. You're *NOT* supposed to subscribe to send emails.


Reporting bugs
==============

Bugs
----

Reports of bugs should be reported online at the `mailing list`_.


========
Examples
========

Here are some example configurations for various situations.  Please e-mail any
other examples you have that may be useful to me.


Multiple Accounts with Mutt
---------------------------

This example shows you how to set up OfflineIMAP to synchronize multiple
accounts with the mutt mail reader.

Start by creating a directory to hold your folders by running ``mkdir ~/Mail``.
Then, in your ``~/.offlineimaprc``, specify::

  accounts = Personal, Work


Make sure that you have both an [Account Personal] and an [Account Work]
section.  The local repository for each account must have different localfolder
path names.  Also, make sure to enable [mbnames].

In each local repository section, write something like this::

	localfolders = ~/Mail/Personal


Finally, add these lines to your ``~/.muttrc``::

  source ~/path-to-mbnames-muttrc-mailboxes
  folder-hook Personal set from="youremail@personal.com"
  folder-hook Work set from="youremail@work.com"
  set mbox_type=Maildir
  set folder=$HOME/Mail
  spoolfile=+Personal/INBOX


That's it!


UW-IMAPD and References
-----------------------

Some users with a UW-IMAPD server need to use OfflineIMAP's "reference" feature
to get at their mailboxes, specifying a reference of ``~/Mail`` or ``#mh/``
depending on the configuration.  The below configuration from (originally from
docwhat@gerf.org) shows using a reference of Mail, a nametrans that strips the
leading Mail/ off incoming folder names, and a folderfilter that limits the
folders synced to just three::

  [Account Gerf]
  localrepository = GerfLocal
  remoterepository = GerfRemote

  [Repository GerfLocal]
  type = Maildir
  localfolders = ~/Mail

  [Repository GerfRemote]
  type = IMAP
  remotehost = gerf.org
  ssl = yes
  remoteuser = docwhat
  reference = Mail
  # Trims off the preceeding Mail on all the folder names.
  nametrans = lambda foldername: \
    re.sub('^Mail/', '', foldername)
  # Yeah, you have to mention the Mail dir, even though it
  # would seem intuitive that reference would trim it.
  folderfilter = lambda foldername: foldername in [
    'Mail/INBOX',
    'Mail/list/zaurus-general',
    'Mail/list/zaurus-dev',
  ]
  maxconnections = 1
  holdconnectionopen = no


pythonfile Configuration File Option
------------------------------------

You can have OfflineIMAP load up a Python file before evaluating the
configuration file options that are Python expressions.  This example is based
on one supplied by Tommi Virtanen for this feature.


In ~/.offlineimaprc, he adds these options::

  [general]
  pythonfile=~/.offlineimap.py
  [Repository foo]
  foldersort=mycmp

Then, the ~/.offlineimap.py file will contain::

  prioritized = ['INBOX', 'personal', 'announce', 'list']

  def mycmp(x, y):
    for prefix in prioritized:
      xsw = x.startswith(prefix)
      ysw = y.startswith(prefix)
      if xsw and ysw:
        return cmp(x, y)
      elif xsw:
        return -1
      elif ysw:
        return +1
    return cmp(x, y)

  def test_mycmp():
    import os, os.path
    folders=os.listdir(os.path.expanduser('~/data/mail/tv@hq.yok.utu.fi'))
    folders.sort(mycmp)
    print folders


This code snippet illustrates how the foldersort option can be customized with a
Python function from the pythonfile to always synchronize certain folders first.


Signals
-------

OfflineIMAP writes its current PID into ``~/.offlineimap/pid`` when it is
running.  It is not guaranteed that this file will not exist when OfflineIMAP is
not running.

<!-- not done yet

  You can send SIGINT to OfflineIMAP using this file to kill it.  SIGUSR1 will
  force an immediate resync of all accounts.  This will be ignored for all
  accounts for which a resync is already in progress.

-->
