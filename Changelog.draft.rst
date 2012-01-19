=========
ChangeLog
=========

Users should ignore this content: **it is draft**.

Contributors should add entries here in the following section, on top of the
others.

`WIP (coming releases)`
=======================

New Features
------------

* Beginning of a test suite. So far there is only one test. Configure
  test/credentials.conf and invoke with "python setup.py test"

Changes
-------

* Improve delete msg performance with SQLITE backend

Bug Fixes
---------

* Fix python2.6 compatibility with the TTYUI backend (crash)
* Fix TTYUI regression from 6.5.2 in refresh loop (crash)
* Fix crashes related to UIDVALIDITY returning "None"
