=========
ChangeLog
=========

:website: http://offlineimap.org


**NOTE FROM THE MAINTAINER:**
  Contributors should use the `WIP` section in Changelog.draft.rst in order to
  add changes they are working on. I will use it to make the new changelog entry
  on releases. And because I'm lazy, it will also be used as a draft for the
  releases announces.


OfflineIMAP v6.3.2 (2010-02-21)
===============================

Notes
-----

First of all I'm really happy to announce our new official `website`_.  Most of
the work started from the impulse of Philippe LeCavalier with the help of
Sebastian Spaeth and other contributors. Thanks to everybody.

In this release, we are still touched by the "SSL3 write pending" but I think
time was long enough to try to fix it. We have our first entry in the "KNOWN
BUG" section of the manual about that. I'm afraid it could impact a lot of users
if some distribution package any SSL library not having underlying (still
obscure) requirements. Distribution maintainers should be care of it. I hope
this release will help us to have more reports.

This release will also be the root of our long maintenance support.

Other bugs were fixed.

Bug Fixes
---------

* Fix craches for getglobalui().
* Fix documentation build.
* Restore compatibiliy with python 2.5.


OfflineIMAP v6.3.2-rc3 (2010-02-06)
===================================

Notes
-----

We are still touched by the "SSL3 write pending" bug it would be really nice to
fix before releasing the coming stable. In the worse case, we'll have to add the
first entry in the "KNOWN BUG" section of the manual. I'm afraid it could impact
a lot of users if some distribution package any SSL library not having
underlying (still obscure) requirements.

The best news with this release are the Curse UI fixed and the better reports
on errors.

In this release I won't merge any patch not fixing a bug or a security issue.

More feedbacks on the main issue would be appreciated.

Changes
-------

* Sample offlineimap.conf states it expects a PEM formatted certificat.
* Give better trace information if an error occurs.
* Have --version ONLY print the version number.
* Code cleanups.

Bug Fixes
---------

* Fix Curses UI (simplified by moving from MultiLock to Rlock implementation).
* Makefile: docutils build work whether python extension command is stripped or not.
* Makefile: clean now removes HTML documentation files.


OfflineIMAP v6.3.2-rc2 (2010-12-21)
===================================

Notes
-----

We are beginning a new tests cycle. At this stage, I expect most people will try
to intensively stuck OfflineIMAP. :-)

New Features
------------

* Makefile learn to build the package and make it the default.
* Introduce a Changelog to involve community in the releasing process.
* Migrate documentation to restructuredtext.

Changes
-------

* Improve CustomConfig documentation.
* Imply single threading mode in debug mode exept for "-d thread".
* Code and import cleanups.
* Allow UI to have arbitrary names.
* Code refactoring around UI and UIBase.
* Improve version managment and make it easier.
* Introduce a true single threading mode.

Bug Fixes
---------

* Understand multiple EXISTS replies from servers like Zimbra.
* Only verify hostname if we actually use CA cert.
* Fix ssl ca-cert in the sample configuration file.
* Fix 'Ctrl+C' interruptions in threads.
* Fix makefile clean for files having whitespaces.
* Fix makefile to not remove unrelated files.
* Fixes in README.
* Remove uneeded files.


OfflineIMAP v6.3.2-rc1 (2010-12-19)
===================================

Notes
-----

We are beginning a tests cycle. If feature topics are sent, I may merge or
delay them until the next stable release.

New Features
------------

* Primitive implementation of SSL certificates check.

Changes
-------

* Use OptionParser instead of getopts.
* Code cleanups.

Bug Fixes
---------

* Fix reading password from UI.


OfflineIMAP v6.3.1 (2010-12-11)
===============================

Notes
-----

Yes, I know I've just annouced the v6.3.0 in the same week. As said, it
was not really a true release for the software. This last release
includes fixes and improvements it might be nice to update to.

Thanks to every body who helped to make this release with patches and
tips through the mailing list. This is clearly a release they own.

Changes
-------

* cProfile becomes the default profiler. Sebastian Spaeth did refactoring to
  prepare to the coming unit test suites.
* UI output formating enhanced.
* Some code cleanups.

Bug Fixes
---------

* Fix possible overflow while working with Exchange.
* Fix time sleep while exiting threads.


OfflineIMAP v6.3.0 (2010-12-09)
===============================

Notes
-----

This release is more "administrative" than anything else and mainly marks the
change of the maintainer. New workflow and policy for developers come in.  BTW,
I don't think I'll maintain debian/changelog. At least, not in the debian way.

Most users and maintainers may rather want to skip this release.

Bug Fixes
---------

* Fix terminal display on exit.
* netrc password authentication.
* User name querying from netrc.
