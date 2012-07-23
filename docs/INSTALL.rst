.. -*- coding: utf-8 -*-
.. _OfflineIMAP: https://github.com/spaetz/offlineimap
.. _OLI_git_repo: git://github.com/spaetz/offlineimap.git

============
Installation
============

.. contents::
.. .. sectnum::

-------------
Prerequisites
-------------

In order to use `OfflineIMAP`_, you need to have these conditions satisfied:

1. Your mail server must support IMAP. Mail access via POP is not
   supported. A special Gmail mailbox type is available to interface
   with Gmail's IMAP front-end, although Gmail has a very peculiar and
   non-standard implementation of its IMAP interface.

2. You must have Python version 2.6 or above installed.  If you are
   running on Debian GNU/Linux, this requirement will automatically be
   taken care of for you.  If you intend to use the SSL interface,
   your Python must have been built with SSL support.

3. If you use OfflineImap as an IMAP<->Maildir synchronizer, you will
   obviously need to have a mail reader that supports the Maildir
   mailbox format.  Most modern mail readers have this support built-in,
   so you can choose from a wide variety of mail servers.  This format
   is also known as the "qmail" format, so any mail reader compatible
   with it will work with `OfflineIMAP`_.


------------
Installation
------------

Installing OfflineImap should usually be quite easy, as you can simply unpack
and run OfflineImap in place if you wish to do so. There are a number of options
though:

#. system-wide :ref:`installation via your distribution package manager <inst_pkg_man>`
#. system-wide or single user :ref:`installation from the source package <inst_src_tar>`
#. system-wide or single user :ref:`installation from a git checkout <inst_git>`

Having installed OfflineImap, you will need to configure it, to be actually
useful. Please check the :ref:`Configuration` section in the :doc:`MANUAL` for
more information on the configuration step.

.. _inst_pkg_man:

System-Wide Installation via distribution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The easiest way to install OfflineIMAP is via your distribution's package
manager. OfflineImap is available under the name `offlineimap` in most Linux and
BSD distributions.


.. _inst_src_tar:

Installation from source package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Download the latest source archive from our `download page
<https://github.com/spaetz/offlineimap/downloads>`_. Simply click the "Download
as .zip" or "Download as .tar.gz" buttons to get the latest "stable" code from
the master branch. If you prefer command line, you will want to use: wget
https://github.com/spaetz/offlineimap/tarball/master

Unpack and continue with the :ref:`system-wide installation <system_wide_inst>`
or the :ref:`single-user installation <single_user_inst>` section.


.. _inst_git:

Installation from git checkout
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get your own copy of the `official git repository <OLI_git_repo>`_ at `OfflineIMAP`_::

  git clone git://github.com/spaetz/offlineimap.git

This will download the source with history. By default, git sets up the
`master` branch up, which is most likely what you want. If not, you can
checkout a particular release like this::

  cd offlineimap
  git checkout v6.5.2.1

You have now a source tree available and proceed with either the
:ref:`system-wide installation <system_wide_inst>` or the :ref:`single-user
installation <single_user_inst>`.


.. _system_wide_inst:

System-wide installation
++++++++++++++++++++++++

Then run these commands, to build the python package::

  make clean
  make

Finally, install the program (as root)::

  python setup.py install

Next, proceed to below.  You tofflineimap to invoke the program.


.. _single_user_inst:

Single-user installation
++++++++++++++++++++++++

Download the git repository as described above. Instead of installing the
program as root, you type `./offlineimap.py`; there is no installation step
necessary.

---------
Uninstall
---------

If you installed a system-wide installation via "python setup.py
install", there are a few files to purge to cleanly uninstall
`OfflineImap`_ again. Assuming that `/usr/local` is the standard prefix of
your system and that you use python 2.7, you need to:

#) Delete the OfflineImap installation itself::

   /usr/local/lib/python2.7/dist-packages/offlineimap-6.4.4.egg-info
   /usr/local/lib/python2.7/dist-packages/offlineimap

  In case, you did the single-user installation, simply delete your
  offlineimap directory.

#) Delete all files that OfflineImap creates during its operation.
   - The cache at (default location) ~/.offlineimap
   - Your manually created (default loc) ~/.offlineimaprc
   (It is possible that you created those in different spots)

That's it. Have fun without OfflineImap.
