.. OfflineImap documentation master file

.. currentmodule:: offlineimap

Welcome to :mod:`offlineimaps`'s documentation
===========================================

The :mod:`offlineimap` module provides the user interface for synchronization between IMAP servers and MailDirs or between IMAP servers. The homepage containing the source code repository can be found at the `offlineimap wiki <https://github.com/spaetz/offlineimap/wiki>`_.

Within :mod:`offlineimap`, the classes :class:`OfflineImap` provides the high-level functionality. The rest of the classes should usually not needed to be touched by the user. A folder is represented by a :class:`offlineimap.folder.Base.BaseFolder` or any derivative :mod:`offlineimap.folder`.

.. moduleauthor:: John Goerzen, Sebastian Spaeth <Sebastian@SSpaeth.de>

:License: This module is covered under the GNU GPL v2 (or later).

This page contains the main API overview of OfflineImap |release|. 

Notmuch can be imported as::

 from offlineimap import OfflineImap

More information on specific topics can be found on the following pages:

.. toctree::
   :maxdepth: 1

   offlineimap   

:mod:`offlineimap` -- The OfflineImap module
=================================================

.. automodule:: offlineimap

.. autoclass:: offlineimap.OfflineImap(cmdline_opts = None)

   .. automethod:: parse_commandline

   .. automethod:: write_pidfile

   .. automethod:: delete_pidfile

   .. automethod:: lock

   .. automethod:: unlock

   .. autoattribute:: ui

      :todo: Document

:mod:`offlineimap.folder` -- Basic representation of a local or remote Mail folder
---------------------------------------------------------------------------------------------------------

.. autoclass:: offlineimap.folder.Base.BaseFolder
   :members:
   :inherited-members:

..   .. note:: :meth:`foo`
..   .. attribute:: Database.MODE

     Defines constants that are used as the mode in which to open a database.

     MODE.READ_ONLY
       Open the database in read-only mode

     MODE.READ_WRITE
       Open the database in read-write mode


:exc:`OfflineImapException` -- A Notmuch execution error
------------------------------------------------
.. autoexception:: offlineimap.OfflineImapException
   :members:

   This execption inherits directly from :exc:`Exception` and is raised on errors during the notmuch execution.


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

