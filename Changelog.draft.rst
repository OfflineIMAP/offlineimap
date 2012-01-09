=========
ChangeLog
=========

Users should ignore this content: **it is draft**.

Contributors should add entries here in the following section, on top of the
others.

`WIP (coming releases)`
=======================

* Gmail "realdelete" is considered harmful and has the potential for data loss. Analysis at http://article.gmane.org/gmane.mail.imap.offlineimap.general/5265
Warnings were added to offlineimap.conf

New Features
------------

Changes
-------

* Rather than to write out the nametrans'lated folder names for mbnames,
  we now write out the local untransformed box names. This is generally
  what we want. This became relevant since we support nametrans rules on
  the local side since only a short time. Reported by Paul Collignan.

* Some sanity checks and improved error messages.

* Revert 6.5.1.1 change to use public imaplib2 function, it was reported to 
  not always work.

Bug Fixes
---------
