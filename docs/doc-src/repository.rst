.. currentmodule:: offlineimap.repository

:mod:`offlineimap.repository` -- Email repositories
------------------------------------------------------------

A derivative of class
:class:`Base.BaseRepository` represents an email
repository depending on the type of storage, possible options are:

 * :class:`IMAPRepository`,
 * :class:`MappedIMAPRepository`
 * :class:`GmailRepository`,
 * :class:`MaildirRepository`, or
 * :class:`LocalStatusRepository`.

Which class you need depends on your account
configuration. The helper class :class:`offlineimap.repository.Repository` is
an *autoloader*, that returns the correct class depending
on your configuration. So when you want to instanciate a new
:mod:`offlineimap.repository`, you will mostly do it through this class.

.. autoclass:: offlineimap.repository.Repository
   :members:
   :inherited-members:



:mod:`offlineimap.repository.Base.BaseRepository` -- Representation of a mail repository
------------------------------------------------------------------------------------------
.. autoclass:: offlineimap.repository.Base.BaseRepository
   :members:
   :inherited-members:
   :undoc-members:

..   .. note:: :meth:`foo`
..   .. attribute:: Database.MODE

     Defines constants that are used as the mode in which to open a database.

     MODE.READ_ONLY
       Open the database in read-only mode

     MODE.READ_WRITE
       Open the database in read-write mode

.. autoclass:: offlineimap.repository.IMAPRepository
.. autoclass:: offlineimap.repository.MappedIMAPRepository
.. autoclass:: offlineimap.repository.GmailRepository
.. autoclass:: offlineimap.repository.MaildirRepository
.. autoclass:: offlineimap.repository.LocalStatusRepository

:mod:`offlineimap.folder` -- Basic representation of a local or remote Mail folder
---------------------------------------------------------------------------------------------------------

.. autoclass:: offlineimap.folder.Base.BaseFolder
   :members:
   :inherited-members:
   :undoc-members:

..   .. attribute:: Database.MODE

     Defines constants that are used as the mode in which to open a database.

     MODE.READ_ONLY
       Open the database in read-only mode

     MODE.READ_WRITE
       Open the database in read-write mode
