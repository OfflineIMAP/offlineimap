.. OfflineImap API documentation

.. currentmodule:: offlineimap

Welcome to :mod:`offlineimaps`'s documentation
==============================================

Within :mod:`offlineimap`, the classes :class:`OfflineImap` provides the high-level functionality. The rest of the classes should usually not needed to be touched by the user. Email repositories are represented by a :class:`offlineimap.repository.Base.BaseRepository` or derivatives (see :mod:`offlineimap.repository` for details). A folder within a repository is represented by a :class:`offlineimap.folder.Base.BaseFolder` or any derivative from :mod:`offlineimap.folder`.

This page contains the main API overview of OfflineImap |release|. 

OfflineImap can be imported as::

 from offlineimap import OfflineImap

The file ``SubmittingPatches.rst`` in the source distribution documents a
number of resources and conventions you may find useful.  It will eventually
be merged into the main documentation.
.. TODO: merge SubmittingPatches.rst to the main documentation

:mod:`offlineimap` -- The OfflineImap module
=============================================
 
.. module:: offlineimap

.. autoclass:: offlineimap.OfflineImap(cmdline_opts = None)


   .. automethod:: run

   .. automethod:: parse_cmd_options

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
