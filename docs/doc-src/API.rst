.. OfflineImap API documentation

.. currentmodule:: offlineimap

.. _API docs:

:mod:`offlineimap's` API documentation
======================================

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


:class:`offlineimap.repository.BaseRepository`
==============================================

Each repository that will take part of a synchronization implement this interface.
Depending on the repository type, either Maildir, IMAP or GmailImap provide a common interface for listing and syncing the folders.
Any mapping (with the `nametrans` option) is done here.
This class is not in charge of synchronizing the content of the folders.

:class:`offlineimap.folder.BaseFolder`
======================================

A repository uses folders to synchronize. A repository will use a specialized folder implementation.
All folders implements this interface, which allow listing the messages, fetching them, and saving them.


:exc:`OfflineImapError` -- A Notmuch execution error
--------------------------------------------------------

.. autoexception:: offlineimap.error.OfflineImapError
   :members:

   This execption inherits directly from :exc:`Exception` and is raised
   on errors during the offlineimap execution. It has an attribute
   `severity` that denotes the severity level of the error.


:mod:`offlineimap.globals` -- module with global variables
==========================================================

.. module:: offlineimap.globals

Module :mod:`offlineimap.globals` provides the read-only storage
for the global variables.

All exported module attributes can be set manually, but this practice
is highly discouraged and shouldn't be used.
However, attributes of all stored variables can only be read, write
access to them is denied.

Currently, we have only :attr:`options` attribute that holds
command-line options as returned by OptionParser.
The value of :attr:`options` must be set by :func:`set_options`
prior to its first use.

.. automodule:: offlineimap.globals
   :members:

   .. data:: options

      You can access the values of stored options using the usual
      syntax, offlineimap.globals.options.<option-name>
