.. OfflineImap documentation master file
.. _OfflineImap: http://offlineimap.org


Welcome to :mod:`offlineimaps`'s documentation
==============================================

`OfflineImap`_ synchronizes email between an IMAP server and a MailDir or between two IMAP servers. It offers very powerful and flexible configuration options, that allow things such as the filtering of folders, transposing of names via static configuration or python scripting. It plays well with mutt and other MailDir consuming email clients.

The documentation contains the end user documentation in a first part. It also contains use cases and example configurations.  It is followed by the internal :doc:`API documentation <API>` for those interested in modifying the source code or otherwise peek into the OfflineImap internals in a second part.


If you just want to get started with minimal fuzz, have a look at our `online quick start guide <http://offlineimap.org/#ref-quick-start>`_. Do note though, that our configuration options are many and powerful. Perusing our precious documentation does often pay off!

More information on specific topics can be found on the following pages:

**User documentation**
  * :doc:`installation/uninstall <INSTALL>`
  * :doc:`user manual/Configuration <MANUAL>`
  * :doc:`Folder filtering & name transformation guide <nametrans>`
  * :doc:`command line options <offlineimap>`
  * :doc:`Frequently Asked Questions <FAQ>`

**Developer documentation**
  * :doc:`API documentation <API>` for internal details on the
    :mod:`offlineimap` module

.. toctree::
   :hidden:

   INSTALL
   MANUAL
   nametrans
   offlineimap
   FAQ

   API
   repository
   ui


.. moduleauthor:: John Goerzen, and many others. See AUTHORS and the git history for a full list.

:License: This module is covered under the GNU GPL v2 (or later).
