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

Download the tar.gz version of the package from the website.  Then run these
commands, making sure that you are the "root" user first::

  tar -zxvf offlineimap_x.y.z.tar.gz
  cd offlineimap-x.y.z
  python2.2 setup.py install

On some systems, you will need to use python instead of python2.6.  Next,
proceed to  below.  You will type offlineimap to invoke the program.

Single-Account Installation
===========================

Download the tar.gz version of the package from the website.  Then run these
commands::

  tar -zxvf offlineimap_x.y.z.tar.gz
  cd offlineimap-x.y.z

When you want to run `OfflineIMAP`_, you will issue the cd command as above and
then type `./offlineimap.py`; there is no installation step necessary.

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
