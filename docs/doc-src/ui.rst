:mod:`offlineimap.ui` -- A flexible logging system
--------------------------------------------------------

.. currentmodule:: offlineimap.ui

OfflineImap has various ui systems, that can be selected. They offer various
functionalities. They must implement all functions that the
:class:`offlineimap.ui.UIBase` offers. Early on, the ui must be set using
:meth:`getglobalui`

.. automethod:: offlineimap.ui.setglobalui
.. automethod:: offlineimap.ui.getglobalui

Base UI plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: offlineimap.ui.UIBase.UIBase
   :members:
   :inherited-members:

..   .. note:: :meth:`foo`
..   .. attribute:: Database.MODE

     Defines constants that are used as the mode in which to open a database.

     MODE.READ_ONLY
       Open the database in read-only mode

     MODE.READ_WRITE
       Open the database in read-write mode
