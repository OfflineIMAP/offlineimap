OfflineImap
===========

Description
-----------

OfflineIMAP is a tool to simplify your e-mail reading. With OfflineIMAP, you can
read the same mailbox from multiple computers. You get a current copy of your
messages on each computer, and changes you make one place will be visible on all
other systems. For instance, you can delete a message on your home computer, and
it will appear deleted on your work computer as well. OfflineIMAP is also useful
if you want to use a mail reader that does not have IMAP support, has poor IMAP
support, or does not provide disconnected operation. It's homepage at
http://offlineimap.org contains more information, source code, and online
documentation.

OfflineIMAP does not require additional python dependencies beyond python >=2.6
(although python-sqlite is strongly recommended).

OfflineIMAP is a Free Software project licensed under the GNU General
Public License version 2 (or later) with a special exception that allows
the OpenSSL library to be used. You can download it for free, and you
can modify it. In fact, you are encouraged to contribute to OfflineIMAP.

Documentation
-------------

The documentation is included (in .rst format) in the `docs` directory.
Read it directly or generate nice html docs (python-sphinx needed) and/or
the man page (python-docutils needed) while being in the `docs` dir via:

    'make doc' (user docs), 'make man' (man page only) or 'make' (both)

    (`make html` will simply create html versions of all *.rst files in /docs)

The resulting user documentation will be in `docs/html`. The full user
docs are also at: http://docs.offlineimap.org. Please see there for
detailed information on how to install and configure OfflineImap.

Quick Start
===========

First, install OfflineIMAP. See `docs/INSTALL.rst` or read
<http://docs.offlineimap.org/en/latest/INSTALL.html>
(hint: `sudo python setup.py install`).

Second, set up your configuration file and run it! The distribution
includes offlineimap.conf.minimal (Debian users may find this at
`/usr/share/doc/offlineimap/examples/offlineimap.conf.minimal`) that
provides you with the bare minimum of setting up OfflineIMAP.  You can
simply copy this file into your home directory and name it
`.offlineimaprc`.  A command such as `cp offlineimap.conf.minimal
~/.offlineimaprc` will do it.  Or, if you prefer, you can just copy
this text to `~/.offlineimaprc`:

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


Now, edit the `~/.offlineimaprc` file with your favorite editor.  All you have
to do is specify a directory for your folders to be in (on the `localfolders`
line), the host name of your IMAP server (on the `remotehost` line), and your
login name on the remote (on the `remoteuser` line).  That's it!

If you prefer to be compatible with the [XDG Base Directory
spec](http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html),
then substitute the above `~/.offlineimaprc` with
`$XDG_CONFIG_HOME/offlineimap/config` and don't forget to set
`XDG_CONFIG_HOME` properly if you want it to be different from
the default `$HOME/.config` for any reason.

To run OfflineIMAP, you just have to say `offlineimap` ― it will fire
up, ask you for a login password if necessary, synchronize your folders,
and exit.  See?

You can just throw away the rest of the finely-crafted, perfectly-honed user
manual!  Of course, if you want to see how you can make OfflineIMAP
FIVE TIMES FASTER FOR JUST $19.95 (err, well, $0), you have to read on our
full user documentation and peruse the sample offlineimap.conf (which
includes all available options) for further tweaks!


Mailing list & bug reporting
----------------------------

The user discussion, development and all exciting stuff take place in the
OfflineImap mailing list at
<http://lists.alioth.debian.org/mailman/listinfo/offlineimap-project>. You do not
need to subscribe to send emails.

Bugs, issues and contributions should be reported to the mailing list. Bugs can
also be reported in the issue tracker at
<https://github.com/OfflineIMAP/offlineimap/issues>.

Configuration Examples
======================

Here are some example configurations for various situations.  Please e-mail any
other examples you have that may be useful to me.


Multiple Accounts with Mutt
---------------------------

This example shows you how to set up OfflineIMAP to synchronize multiple
accounts with the mutt mail reader.

Start by creating a directory to hold your folders by running `mkdir ~/Mail`.
Then, in your `~/.offlineimaprc`, specify:

    accounts = Personal, Work


Make sure that you have both an `[Account Personal]` and an `[Account Work]`
section.  The local repository for each account must have different `localfolder`
path names.  Also, make sure to enable `[mbnames]`.

In each local repository section, write something like this:

    localfolders = ~/Mail/Personal


Finally, add these lines to your `~/.muttrc`:

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
to get at their mailboxes, specifying a reference of `~/Mail` or `#mh/`
depending on the configuration.  The below configuration from (originally from
docwhat@gerf.org) shows using a reference of Mail, a `nametrans` that strips the
leading `Mail/` off incoming folder names, and a `folderfilter` that limits the
folders synced to just three:

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
-------------------------------------

You can have OfflineIMAP load up a Python file before evaluating the
configuration file options that are Python expressions.  This example is based
on one supplied by Tommi Virtanen for this feature.


In `~/.offlineimaprc`, he adds these options:

    [general]
    pythonfile=~/.offlineimap.py
    [Repository foo]
    foldersort=mycmp

Then, the `~/.offlineimap.py` file will contain:

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


This code snippet illustrates how the `foldersort` option can be customized with a
Python function from the `pythonfile` to always synchronize certain folders first.
