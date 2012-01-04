=========
ChangeLog
=========

:website: http://offlineimap.org


**NOTE FROM THE MAINTAINER:**
  Contributors should use the `WIP` section in Changelog.draft.rst in order to
  add changes they are working on. I will use it to make the new changelog entry
  on releases. And because I'm lazy, it will also be used as a draft for the
  releases announces.

OfflineIMAP v6.4.3 (2012-01-04)
===============================

New Features
------------

* add a --info command line switch that outputs useful information about
  the server and the configuration for all enabled accounts.

Changes
-------

* Reworked logging which was reported to e.g. not flush output to files
  often enough. User-visible changes:
  a) console output goes to stderr (for now).
  b) file output has timestamps and looks identical in the basic and
  ttyui UIs.
  c) File output should be flushed after logging by default (do
  report if not).

* Bumped bundled imaplib2 to release 2.29

* Make ctrl-c exit cleanly rather aborting brutally (which could leave
  around temporary files, half-written cache files, etc). Exiting on
  SIGTERM and CTRL-C can take a little longer, but will be clean.


OfflineIMAP v6.4.2 (2011-12-01)
===============================

* IMAP<->IMAP sync with a readonly local IMAP repository failed with a
  rather mysterious "TypeError: expected a character buffer object"
  error. Fix this my retrieving the list of folders early enough even
  for readonly repositories.

* Fix regression from 6.4.0. When using local Maildirs with "/" as a
  folder separator, all folder names would get a trailing slash
  appended, which is plain wrong.

OfflineIMAP v6.4.1 (2011-11-17)
===============================

Changes
-------

* Indicate progress when copying many messages (slightly change log format)

* Output how long an account sync took (min:sec).

Bug Fixes
---------

* Syncing multiple accounts in single-threaded mode would fail as we try
  to "register" a thread as belonging to two accounts which was
  fatal. Make it non-fatal (it can be legitimate).

* New folders on the remote would be skipped on the very sync run they
  are created and only by synced in subsequent runs. Fixed.

* a readonly parameter to select() was not always treated correctly,
  which could result in some folders being opened read-only when we
  really needed read-write.

OfflineIMAP v6.4.0 (2011-09-29)
===============================

This is the first stable release to support the forward-compatible per-account locks and remote folder creation that has been introduced in the 6.3.5 series.

* Various regression and bug fixes from the last couple of RCs

OfflineIMAP v6.3.5-rc3 (2011-09-21)
===================================

Changes
-------

* Refresh server capabilities after login, so we know that Gmail
  supports UIDPLUS (it only announces that after login, not
  before). This prevents us from adding custom headers to Gmail uploads.
  
Bug Fixes
---------

* Fix the creation of folders on remote repositories, which was still
  botched on rc2.

OfflineIMAP v6.3.5-rc2 (2011-09-19)
===================================

New Features
------------

* Implement per-account locking, so that it will possible to sync
  different accounts at the same time. The old global lock is still in
  place for backward compatibility reasons (to be able to run old and
  new versions of OfflineImap concurrently) and will be removed in the
  future. Starting with this version, OfflineImap will be
  forward-compatible with the per-account locking style.

* Implement RFC 2595 LOGINDISABLED. Warn the user and abort when we
  attempt a plaintext login but the server has explicitly disabled
  plaintext logins rather than crashing.

* Folders will now also be automatically created on the REMOTE side of
  an account if they exist on the local side. Use the folderfilters
  setting on the local side to prevent some folders from migrating to
  the remote side.  Also, if you have a nametrans setting on the remote
  repository, you might need a nametrans setting on the local repository
  that leads to the original name (reverse nametrans).

Changes
-------

* Documentation improvements concerning 'restoreatime' and some code cleanup

* Maildir repositories now also respond to folderfilter= configurations.

Bug Fixes
---------

* New emails are not created with "-rwxr-xr-x" but as "-rw-r--r--"
  anymore, fixing a regression in 6.3.4.

OfflineIMAP v6.3.5-rc1 (2011-09-12)
===================================

Notes
-----

Idle feature and SQLite backend leave the experimental stage! ,-)

New Features
------------

* When a message upload/download fails, we do not abort the whole folder
  synchronization, but only skip that message, informing the user at the
  end of the sync run.
 
* If you connect via ssl and 'cert_fingerprint' is configured, we check
  that the server certificate is actually known and identical by
  comparing the stored sha1 fingerprint with the current one.

Changes
-------

* Refactor our IMAPServer class. Background work without user-visible
  changes.
* Remove the configurability of the Blinkenlights statuschar. It
  cluttered the main configuration file for little gain.
* Updated bundled imaplib2 to version 2.28.

Bug Fixes
---------

* We protect more robustly against asking for inexistent messages from the
  IMAP server, when someone else deletes or moves messages while we sync.
* Selecting inexistent folders specified in folderincludes now throws
  nice errors and continues to sync with all other folders rather than
  exiting offlineimap with a traceback.



OfflineIMAP v6.3.4 (2011-08-10)
===============================

Notes
-----

Here we are. A nice release since v6.3.3, I think.

Changes
-------

* Handle when UID can't be found on saved messages.



OfflineIMAP v6.3.4-rc4 (2011-07-27)
===================================

Notes
-----

There is nothing exciting in this release. This is somewhat expected due to the
late merge on -rc3.

New Features
------------

* Support maildir for Windows.

Changes
-------

* Manual improved.


OfflineIMAP v6.3.4-rc3 (2011-07-07)
===================================

Notes
-----

Here is a surprising release. :-)

As expected we have a lot bug fixes in this round (see git log for details),
including a fix for a bug we had for ages (details below) which is a very good
news.

What makes this cycle so unusual is that I merged a feature to support StartTLS
automatically (thanks Sebastian!). Another very good news.

We usually don't do much changes so late in a cycle. Now, things are highly
calming down and I hope a lot of people will test this release. Next one could
be the stable!

New Features
------------

* Added StartTLS support, it will automatically be used if the server
  supports it.

Bug Fixes
---------

* We protect more robustly against asking for inexistent messages from the
  IMAP server, when someone else deletes or moves messages while we sync.


OfflineIMAP v6.3.4-rc2 (2011-06-15)
===================================

Notes
-----

This was a very active rc1 and we could expect a lot of new fixes for the next
release. 

The most important fix is about a bug that could lead to data loss. Find more
information about his bug here:

  http://permalink.gmane.org/gmane.mail.imap.offlineimap.general/3803

The IDLE support is merged as experimental feature.

New Features
------------

* Implement experimental IDLE feature.

Changes
-------

* Maildirs use less memory while syncing.

Bug Fixes
---------

* Saving to Maildirs now checks for file existence without race conditions.
* A bug in the underlying imap library has been fixed that could
  potentially lead to data loss if the server interrupted responses with
  unexpected but legal server status responses. This would mainly occur
  in folders with many thousands of emails. Upgrading from the previous
  release is strongly recommended.


OfflineIMAP v6.3.4-rc1 (2011-05-16)
===================================

Notes
-----

Welcome to the v6.3.4 pre-release cycle. Your favorite IMAP tool wins 2 new
features which were asked for a long time:
* an experimental SQL-based backend for the local cache;
* one-way synchronization cabability.

Logic synchronization is reviewed and simplified (from 4 to 3 passes) giving
improved performance.

Lot of work was done to give OfflineIMAP a better code base. Raised errors can
now rely on a new error system and should become the default in the coming
releases.

As usual, we ask our users to test this release as much as possible, especially
the SQL backend. Have fun!

New Features
------------

* Begin sphinx-based documentation for the code.
* Enable 1-way synchronization by settting a [Repository ...] to
  readonly = True. When e.g. using offlineimap for backup purposes you
  can thus make sure that no changes in your backup trickle back into
  the main IMAP server.
* Optional: experimental SQLite-based backend for the LocalStatus
  cache. Plain text remains the default.

Changes
-------

* Start a enhanced error handling background system. This is designed to not
  stop a whole sync process on all errors (not much used, yet).
* Documentation improvements: the FAQ wins new entries and add a new HACKING
  file for developers.
* Lot of code cleanups.
* Reduced our sync logic from 4 passes to 3 passes (integrating upload of
  "new" and "existing" messages into one function). This should result in a
  slight speedup.
* No whitespace is stripped from comma-separated arguments passed via
  the -f option.
* Give more detailed error when encountering a corrupt UID mapping file.

Bug Fixes
---------

* Drop connection if synchronization failed. This is needed if resuming the
  system from suspend mode gives a wrong connection.
* Fix the offlineimap crash when invoking debug option 'thread'.
* Make 'thread' command line option work.


OfflineIMAP v6.3.3 (2011-04-24)
===============================

Notes
-----

Make this last candidate cycle short. It looks like we don't need more tests as
most issues were raised and solved in the second round. Also, we have huge work
to merge big and expected features into OfflineIMAP.

Thanks to all contributors, again. With such a contribution rate, we can release
stable faster. I hope it will be confirmed in the longer run!

Changes
-------

* Improved documentation for querying password.


OfflineIMAP v6.3.3-rc3 (2011-04-19)
===================================

Notes
-----

It's more than a week since the previous release. Most of the issues raised were
discussed and fixed since last release. I think we can be glad and confident for
the future while the project live his merry life.

Changes
-------

* The -f option did not work with Folder names with spaces. It works
  now, use with quoting e.g. -f "INBOX, Deleted Mails".
* Improved documentation.
* Bump from imaplib2 v2.20 to v2.22.
* Code refactoring.

Bug Fixes
---------

* Fix IMAP4 tunnel with imaplib2.


OfflineIMAP v6.3.3-rc2 (2011-04-07)
===================================

Notes
-----

We are now at the third week of the -rc1 cycle. I think it's welcome to begin
the -rc2 cycle.  Things are highly calming down in the code even if we had
much more feedbacks than usual. Keep going your effort!

I'd like to thank reporters who involved in this cycle:
  - Баталов Григорий
  - Alexander Skwar
  - Christoph Höger
  - dtk
  - Greg Grossmeier
  - h2oz7v
  - Iain Dalton
  - Pan Tsu
  - Vincent Beffara
  - Will Styler
  (my apologies if I forget somebody)

...and all active developers, of course!

The imaplib2 migration looks to go the right way to be definetly released but
still needs more tests.  So, here we go...

Changes
-------

* Increase compatability with Gmail servers which claim to not support
  the UIDPLUS extension but in reality do.

Bug Fixes
---------

* Fix hang when using Ctrl+C in some cases.


OfflineIMAP v6.3.3-rc1 (2011-03-16)
===================================

Notes
-----

Here is time to begin the tests cycle. If feature topics are sent, I may merge
or delay them until the next stable release.

Main change comes from the migration from imaplib to imaplib2. It's internal
code changes and doesn't impact users. UIDPLUS and subjectAltName for SSL are
also great improvements.

This release includes a hang fix due to infinite loop. Users seeing OfflineIMAP
hang and consuming a lot of CPU are asked to update.

That beeing said, this is still an early release candidate you should use for
non-critical data only!

New Features
------------

* Implement UIDPLUS extension support. OfflineIMAP will now not insert
  an X-OfflineIMAP header if the mail server supports the UIDPLUS
  extension.
* SSL: support subjectAltName.

Changes
-------

* Use imaplib2 instead of imaplib.
* Makefile use magic to find the version number.
* Rework the repository module
* Change UI names to Blinkenlights,TTYUI,Basic,Quiet,MachineUI.
  Old names will still work, but are deprecated.
  Document that we don't accept a list of UIs anymore.
* Reworked the syncing strategy. The only user-visible change is that
  blowing away LocalStatus will not require you to redownload ALL of
  your mails if you still have the local Maildir. It will simply
  recreate LocalStatus.
* TTYUI ouput improved.
* Code cleanups.

Bug Fixes
---------

* Fix ignoring output while determining the rst2xxx command name to build
  documentation.
* Fix hang because of infinite loop reading EOF.
* Allow SSL connections to send keep-alive messages.
* Fix regression (UIBase is no more).
* Make profiling mode really enforce single-threading
* Do not send localized date strings to the IMAP server as it will
  either ignore or refuse them.


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
