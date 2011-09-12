.. OfflineImap documentation master file

.. currentmodule:: offlineimap

Welcome to :mod:`offlineimaps`'s documentation
==============================================

The :mod:`offlineimap` module provides the user interface for synchronization between IMAP servers and MailDirs or between IMAP servers. The homepage containing the source code repository can be found at the `offlineimap homepage <http://offlineimap.org>`_. The following provides the developer documentation for those who are interested in modifying the source code or otherwise peek into the OfflineImap internals. End users might want to check the MANUAL, our INSTALLation instructions, and the FAQ.

Within :mod:`offlineimap`, the classes :class:`OfflineImap` provides the high-level functionality. The rest of the classes should usually not needed to be touched by the user. Email repositories are represented by a :class:`offlineimap.repository.Base.BaseRepository` or derivatives (see :mod:`offlineimap.repository` for details). A folder within a repository is represented by a :class:`offlineimap.folder.Base.BaseFolder` or any derivative from :mod:`offlineimap.folder`.

.. moduleauthor:: John Goerzen, and many others. See AUTHORS and the git history for a full list.

:License: This module is covered under the GNU GPL v2 (or later).

This page contains the main API overview of OfflineImap |release|. 

OfflineImap can be imported as::

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

:exc:`OfflineImapError` -- A Notmuch execution error
--------------------------------------------------------

.. autoexception:: offlineimap.error.OfflineImapError
   :members:

   This execption inherits directly from :exc:`Exception` and is raised
   on errors during the offlineimap execution. It has an attribute
   `severity` that denotes the severity level of the error.
