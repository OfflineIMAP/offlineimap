.. OfflineImap documentation master file

.. currentmodule:: offlineimap

Welcome to :mod:`offlineimaps`'s documentation
==============================================

The :mod:`offlineimap` module provides the user interface for synchronization between IMAP servers and MailDirs or between IMAP servers. The homepage containing the source code repository can be found at the `offlineimap homepage <http://offlineimap.org>`_.

Within :mod:`offlineimap`, the classes :class:`OfflineImap` provides the high-level functionality. The rest of the classes should usually not needed to be touched by the user. A folder is represented by a :class:`offlineimap.folder.Base.BaseFolder` or any derivative :mod:`offlineimap.folder`.

.. moduleauthor:: John Goerzen, and many others. See AUTHORS and the git history for a full list.

:License: This module is covered under the GNU GPL v2 (or later).

This page contains the main API overview of OfflineImap |release|. 

Notmuch can be imported as::

 from offlineimap import OfflineImap

More information on specific topics can be found on the following pages:

.. toctree::
   :maxdepth: 1

   repository
   ui
   offlineimap

:mod:`offlineimap` -- The OfflineImap module
=============================================

.. module:: offlineimap

.. autoclass:: offlineimap.OfflineImap(cmdline_opts = None)

   .. automethod:: lock

   .. automethod:: run

..  .. autoattribute:: ui

      :todo: Document

:class:`offlineimap.account`
============================

An :class:`accounts.Account` connects two email repositories that are to be synced. It comes in two flavors, normal and syncable.

.. autoclass:: offlineimap.accounts.Account

.. autoclass:: offlineimap.accounts.SyncableAccount
   :members:
   :inherited-members:

   .. autodata:: ui

      Contains the current :mod:`offlineimap.ui`, and can be used for logging etc.


:exc:`OfflineImapException` -- A Notmuch execution error
--------------------------------------------------------

.. autoexception:: offlineimap.OfflineImapException
   :members:

   This execption inherits directly from :exc:`Exception` and is raised on errors during the offlineimap execution.
