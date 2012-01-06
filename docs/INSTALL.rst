.. -*- coding: utf-8 -*-

.. _OfflineIMAP: https://github.com/nicolas33/offlineimap

.. contents::
.. sectnum::

=============
Prerequisites
=============

In order to use `OfflineIMAP`_, you need to have these conditions satisfied:

1. Your mail server must support IMAP.  Most Internet Service Providers and
   corporate networks do, and most operating systems have an IMAP implementation
   readily available.  A special Gmail mailbox type is available to interface with
   Gmail's IMAP front-end.

2. You must have Python version 2.6 or above installed.  If you are running on
   Debian GNU/Linux, this requirement will automatically be taken care of for you.
   If you do not have Python already, check with your system administrator or
   operating system vendor; or, download it from the Python website.  If you intend
   to use the SSL interface, your Python must have been built with SSL support.

3. Have a mail reader that supports the Maildir mailbox format.  Most modern
   mail readers have this support built-in, so you can choose from a wide variety
   of mail servers.  This format is also known as the "qmail" format, so any mail
   reader compatible with it will work with `OfflineIMAP`_.  If you do not have a
   mail reader that supports Maildir, you can often install a local IMAP server and
   point both `OfflineIMAP`_ and your mail reader at it.


============
Installation
============

You have three options:

1. a system-wide installation with Debian
2. a system-wide installation with other systems
3. a single-user installation.  You can checkout the latest version of
   `OfflineIMAP`_ from official `OfflineIMAP`_ repository.


System-Wide Installation, Debian
================================

If you are tracking Debian unstable, you may install `OfflineIMAP`_ by simply
running the following command as root::

	  apt-get install offlineimap

If you are not tracking Debian unstable, download the Debian `.deb` package from
the `OfflineIMAP`_ website and then run ``dpkg -i`` to install the downloaded
package.  Then, skip to  below.  You will type offlineimap to invoke the
program.

System-Wide Installation, Other
===============================

Check your distribution packaging tool, OfflineIMAP may already be packaged for
you.

System-Wide Installation, From source
=====================================

Get your own copy of the official git repository at `OfflineIMAP`_::

  git clone git://github.com/nicolas33/offlineimap.git

This will download all the sources with history. By default, git set up the
local master branch up which is most likely what you want. If not, you can
checkout a particular release::

  cd offlineimap
  git checkout -b local_version v6.3.3

The latter creates a local branch called "local_version" of the v6.3.3 release.

Then run these commands, to build the python package::

  make clean
  make

Finally, install the program (as root)::

  python setup.py install

Next, proceed to below.  You will type offlineimap to invoke the program.

Single-Account Installation
===========================

Download the git repository as described above. Instead of installing the
program as root, you type `./offlineimap.py`; there is no installation step
necessary.

=============
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


===============
Uninstall
===============

If you installed a system-wide installation via "python setup.py
install", there are a few files to purge to uninstall it again. I assume
that /usr/local is the standard prefix that your system and you use
python 2.7. Adapt to your system. In that case you need to:

1) Delete:
   /usr/local/lib/python2.7/dist-packages/offlineimap-6.4.4.egg-info
   /usr/local/lib/python2.7/dist-packages/offlineimap

2) Delete the cache at (default location) ~/.offlineimap
   Delete your manually created (default loc) ~/.offlineimaprc
   (It is possible that you created those in different spots)

That's it. Have fun without OfflineImap.
