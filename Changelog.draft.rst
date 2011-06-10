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

Changes
-------

Bug Fixes
---------

* A bug in the underlying imap library has been fixed that could
  potentially lead to data loss if the server interrupted responses with
  unexpected but legal server status responses. This would mainly occur
  in folders with many thousands of emails. Upgrading from the previous
  release is strongly recommended.

Peanding for the next major release
==================================

* UIs get shorter and nicer names. (API changing)
* Implement IDLE feature. (delayed until next major release)
