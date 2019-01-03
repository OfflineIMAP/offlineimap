---
layout: page
title: Changelog of mainline
---

<!--
Note to mainainers:
* You should not edit this file manually; prefer the ./contrib/release.sh script.
* If you really want to do manual edition, keep in mind that it's exported as-is
  to the website which expect the current structure (title levels, title syntax,
  sub-sections, front matter, etc).
-->


* The following excerpt is only usefull when rendered in the website.
{:toc}

### OfflineIMAP v7.2.2 (2018-12-22)

#### Notes

With this release offlineimap can renew the token for OAUTH2. There is better
integration for ArchLinux and OSX. SSL configuration options are more
consistent.

There are bug fixes about maxage and GSSAPI.

The imaplib2 library looks discontinued. I wonder we'll have no other choice
than maintaining our own fork.

This release was tested by:

- Nicolas Sebrecht


#### Authors

- Nicolas Sebrecht (5)
- Philippe Loctaux (4)
- Benedikt Heine (2)
- Carnë Draug (2)
- Frode Aannevik (1)
- Robbie Harwood (1)


#### Features

- 2890dec Added ssl certfile on osx for openssl pacakge on homebrew. [Philippe Loctaux]
- 761e10e Add Archlinux to list of supported distros. [Philippe Loctaux]

#### Fixes

- 8692799 Fix expired oauth2_access_token. [Frode Aannevik]
- 096aa07 Handle empty token with complete GSSAPI context. [Robbie Harwood]
- a51064e maxage: always compute the remote cache list for min_uid. [Nicolas Sebrecht]
- 698ec64 offlineimap.conf: minor fixes. [Nicolas Sebrecht]
- af3a35a offlineimap/utilis/distro.py: indentation fix. [Philippe Loctaux]
- d3ba837 Fix typo in exception message. [Benedikt Heine]
- c9005cd Check if username is provided before trying plain authentication.. [Carnë Draug]

#### Changes

- 5f9474e Print username instead of accountname when asking for password. [Carnë Draug]
- ce9a198 Chain tls_level and ssl_version only if ssl is enabled. [Benedikt Heine]
- 6ef5937 docs/website-doc.sh: minor improvements in comments of versions.yml. [Nicolas Sebrecht]
- 4544bb1 contrib/release.py: minor UI improvement. [Nicolas Sebrecht]
- d930125 fix dates in copyright lines. [Nicolas Sebrecht]


### OfflineIMAP v7.2.1 (2018-06-16)

#### Notes

This new version introduces interesting features. The fingerprints now accepts
hashes in sha224, sha256, sha384 and sha512 to improve the compatibility with
IMAP servers.

There's a new script in ./contrib to store passwords with GPG.

The new GSSAPI library for kerberos gets a fix about authentication. Gmail
labels can now have parenthesis and the hostname can have path separators in
theirs names.

There's a lot of other minors improvements to make offlineimap better
(in the documentation, UI, configuration file and the code).

This release was tested by:

- Nicolas Sebrecht

Thanks to all the contributors. A lot of patches are first time contributions to
this project. This is very pleasant.

Special thanks to Ilias Tsitsimpis, Eygene Ryabinkin, Chris Coleman our long
time contributors involved in this release and Sebastian Spaeth who is still
paying for the domain name!


#### Authors

- Nicolas Sebrecht (9)
- velleto (6)
- Chris Coleman (1)
- Edgar HIPP (1)
- Eygene Ryabinkin (1)
- Lorenzo (1)
- Michael Billington (1)
- Robbie Harwood (1)


#### Features

- Script to store passwords in a file with GPG or using OSX's secure keychain. [Lorenzo]
- Added support for sha512, sha384, sha256, sha224 hashing algorithms to calculate server certificate fingerprints.. [velleto]

#### Fixes

- Pass username through in GSSAPI connections. [Robbie Harwood]
- Gmail: allow parenthesis in labels. [Nicolas Sebrecht]
- Correct typographical errors in offlineimap.conf. [Michael Billington]
- Create filenames with no path separators in them. [Eygene Ryabinkin]

#### Changes

- imapserver: fix copyright line. [Nicolas Sebrecht]
- Available hashes added to documentation.. [velleto]
- Documented the now allowed use of colon separated fingerprints with examples.. [velleto]
- Allow users to keep colons between each hex pair of server certificate fingerprint in configuration file.. [velleto]
- Removed uneccessary call of list() on zip() object.. [velleto]
- Changed the 'exception raised' message, to be more understandable.. [velleto]
- Make CTRL-C message more clear. [Edgar HIPP]
- setup: add long_description. [Nicolas Sebrecht]
- offlineimap.conf: fix comment about gssapi. [Nicolas Sebrecht]
- Add self to maintainers. Update email address.. [Chris Coleman]
- Makefile: targz: don't set the abbrev in the archive directory name. [Nicolas Sebrecht]
- contrib: learn to build website/_uploads. [Nicolas Sebrecht]
- docs/website-doc.sh: limit the number of exported versions in _data/announces.yml. [Nicolas Sebrecht]
- Makefile: targz: update files. [Nicolas Sebrecht]
- Makefile: clean: remove __pycache__ directories. [Nicolas Sebrecht]


### OfflineIMAP v7.2.0 (2018-04-07)

#### Notes

The biggest change with this release is the introduction of automated tests;
thanks to Chris from http://www.espacenetworks.com.

Robbie Hardwood from RedHat switched the GSSAPI dependency from pykerberos to
python-gssapi because it's more active and has more pleasant interface.

The shebang is fixed back to python2 to fix issues on some environments.

The UI was improved to show both the local and remote foldernames (usefull when
nametrans is enabled).

Thanks to all the contributors.

This release was tested by:

- Nicolas Sebrecht
- Remi Locherer


#### Authors

- Nicolas Sebrecht (9)
- Musashi69 (1)
- Robbie Harwood (1)
- chris001 (1)


#### Features

- Autmomated testing using Travis and CodeCov.io!. [chris001]
- README: travis: add badge for the next branch. [Nicolas Sebrecht]
- travis: add notification to gitter room OfflineIMAP/offlineimap. [Nicolas Sebrecht]

#### Fixes

- offlineimap.py: fix shebang to python2. [Nicolas Sebrecht]
- bin/offlineimap: fix shebang to env python2. [Nicolas Sebrecht]

#### Changes

- Port to python-gssapi from pykerberos. [Robbie Harwood]
- requirements: add gssapi as optional dependency. [Nicolas Sebrecht]
- make UI output show local AND remote dirs involved. [Musashi69]
- maxsyncaccounts: improve documentation. [Nicolas Sebrecht]




### OfflineIMAP v7.1.5 (2018-01-13)

#### Notes

This minor release fixes a bug about maxage failing to upload some emails. Also,
this introduces the snapcraft.yaml to package offlineimap with this packaging
system.

This release was tested by:

- Nicolas Sebrecht
- Remi Locherer


#### Authors

- Nicolas Sebrecht (4)
- Evan Dandrea (1)
- John Ferlito (1)


#### Features

- Initial commit of snapcraft.yaml. [Evan Dandrea]

#### Fixes

- maxage: don't consider negative UIDs when computing min UID. [Nicolas Sebrecht]
- Add missing space to output string. [John Ferlito]

#### Changes

- folder: IMAP: improve search logging. [Nicolas Sebrecht]
- no UIDPLUS: improve logging on failures. [Nicolas Sebrecht]
- github: remove the trick to download the PR. [Nicolas Sebrecht]


### OfflineIMAP v7.1.4 (2017-10-29)

#### Notes

Here is a bugfix release for v7.1.3. Two regressions got fixes and the
--delete-folder CLI option now expects an UTF-8 folder name when utf8foldernames
is enabled.

This release was tested by:

- Nicolas Sebrecht

#### Authors

- Nicolas Sebrecht (5)
- Thomas Merkel (1)

#### Fixes

- utf8foldernames: fix missing decode argument. [Nicolas Sebrecht]
- Fix: if any tunnel (preauth_tunnel or transport_tunnel) the hostname should not be required. [Thomas Merkel]

#### Changes

- utf8foldernames: support --delete-folder with UTF-8 folder name. [Nicolas Sebrecht]
- contrib/release.py improvements


### OfflineIMAP v7.1.3 (2017-10-08)

#### Notes

This release introduces a new experimental utf8foldernames configuration option.

We already had the "tricky" decodefoldernames which is now deprecated. The new
code is the correct implementation for this feature. The changes are neat and
rather small. All the users having decodefoldernames are requested to move to
utf8foldernames. This requires to update almost all the functions like
nametrans, folderfilter, etc, because they work on the UTF-8 encoding. See the
documentation for more. Thank you Urs Liska for this contribution!

In the long run, the idea is to:

1. Remove decodefoldernames in favour of utf8foldernames.
2. Promote utf8foldernames up to stable.
3. Turn utf8foldernames on by default.

Currently, folders with non-ASCII characters in their name have to be fully
re-downloaded. So, there's a bit more work to be done to have (3) and maybe (2).

Also, this release includes a fix about remotehost and transporttunnel that
would require some testing. Thanks Thomas Merkel!

There are documentation improvements, improved errors and minor code cleanups,
too.

This release was tested by:

- Nicolas Sebrecht
- Remi Locherer


#### Authors

- Nicolas Sebrecht (11)
- Urs Liska (8)
- Thomas Merkel (1)

#### Features

- utf8: implement utf8foldernames option. [Urs Liska]
- utf8: document new feature, deprecate old one. [Urs Liska]

#### Fixes

- remotehost should not be required if transporttunnel is used. [Thomas Merkel]
- accounts: error out when no folder to sync. [Nicolas Sebrecht]
- sqlite: provide better message error for insert. [Nicolas Sebrecht]
- folder: Gmail: fix copyright header. [Nicolas Sebrecht]

#### Changes

- man: remove mention of experimental support for python 3. [Nicolas Sebrecht]
- man: mention the supported directions of the syncs. [Nicolas Sebrecht]
- folder: Gmail: remove dead code. [Nicolas Sebrecht]
- upcoming.py: get header template from external file. [Nicolas Sebrecht]
- upcoming.py: display a message with the filename once written. [Nicolas Sebrecht]
- contrib/helpers: sort testers by name. [Nicolas Sebrecht]
- Remove some unnecessary whitespace (in existing code). [Urs Liska]
- MAINTAINERS: Rainer is not currently active. [Nicolas Sebrecht]


### OfflineIMAP v7.1.2 (2017-07-10)

#### Notes

This release introduces better Davmail support, better reliability when in
IMAP/IMAP mode, better output on some errors, and minor fixes. The provided
systemd files are improved.

The imaplib2 requirement is now v2.57.

Remi Locherer is joining our tester team. Great!

Starting with this release, the feedbacks from the testers are recorded in the
release notes, the git logs and the Changelog. Thanks to all of them for
improving the releases.

This release was tested by:

- benutzer193
- Nicolas Sebrecht
- Remi Locherer

#### Authors

- Nicolas Sebrecht (20)
- Hugo Osvaldo Barrera (5)
- Alvaro Pereyra (1)
- benutzer193 (1)

#### Features

- contrib/release.py: consider positive feedbacks from testers. [Nicolas Sebrecht]
- Introduce the github CODEOWNERS file. [Nicolas Sebrecht]
- IMAP/IMAP: continue to sync if the local side does not return a valid UID on upload. [Nicolas Sebrecht]

#### Fixes

- folder/IMAP: introduce dedicated parsing for davmail (not supporting UIDPLUS). [Nicolas Sebrecht]
- offlineimap.conf: minor typo fix. [Alvaro Pereyra]
- Respect systemd conventions for timers. [Hugo Osvaldo Barrera]
- Use a pre-existing target for systemd services. [Hugo Osvaldo Barrera]
- Remove invalid systemd setting. [Hugo Osvaldo Barrera]
- systemd: remove unused watchdog functionality. [benutzer193]
- gitignore generated css file. [Nicolas Sebrecht]
- Changelog: fix syntax. [Nicolas Sebrecht]

#### Changes

- Increase imaplib2 requirement from v2.55 to v2.57. [Nicolas Sebrecht]
- folder/IMAP: improve the warning when we can't parse the returned UID. [Nicolas Sebrecht]
- Provide more details in error message when SSL fails on non-standard port. [Nicolas Sebrecht]
- Use basic logger (since systemd picks up stdout). [Hugo Osvaldo Barrera]
- Explain how to override systemd values. [Hugo Osvaldo Barrera]
- systemd: add documentation entry in configuration files. [Nicolas Sebrecht]
- offlineimap.conf: ssl must be disabled to force STARTTLS in some cases. [Nicolas Sebrecht]
- Advise singlethreadperfolder when offlineimap hangs. [Nicolas Sebrecht]
- offlineimap.conf: minor improvements. [Nicolas Sebrecht]
- contrib: more release automation. [Nicolas Sebrecht]
- MAINTAINERS: Remi Locherer joins the team of testers. [Nicolas Sebrecht]
- systemd: README: credit Hugo as contributor. [Nicolas Sebrecht]


### OfflineIMAP v7.1.1 (2017-05-28)

#### Notes

This release has some interesting fixes, including one for the Blinkenlights UI.

Otherwise, there is no big change since the previous version.

Furthermore, this release was tested by:

- Remi Locherer

#### Authors

- Nicolas Sebrecht (17)
- Chris Coleman (1)
- Ilias Tsitsimpis (1)
- Maximilian Kaul (1)
- benutzer193 (1)
- Ævar Arnfjörð Bjarmason (1)

#### Features

- contrib: introduce a tool to produce the "upcoming notes". [Nicolas Sebrecht]
- contrib: secure HTTPS test internet is connected.. [Chris Coleman]
- Env info (used by -V and banner): add openssl version. [Nicolas Sebrecht]
- docs: learn to build html files for the manual pages. [Nicolas Sebrecht]

#### Fixes

- Acquire lock before updating the CursesLogHandler window. [Ilias Tsitsimpis]
- maxage: use the remote folder first to compute min_uid. [Nicolas Sebrecht]
- Fix systemd.timer: initialize timer after boot. [benutzer193]
- XOAUTH2: don't try this authentication method when not configured. [Nicolas Sebrecht]
- mbnames: don't duplicate entries in autorefresh mode. [Nicolas Sebrecht]
- docs: update the instructions for creating OAuth projects for GMail. [Ævar Arnfjörð Bjarmason]
- Fixed typo in doc: tls_1_2 => tls1_2. [Maximilian Kaul]
- IMAP: UIDPLUS: correctly warn about weird responses from some servers. [Nicolas Sebrecht]
- website-doc: force copy of the new HTML generated man pages. [Nicolas Sebrecht]
- Makefile: fix clean target. [Nicolas Sebrecht]

#### Changes

- MAINTAINERS: benutzer193 joins the testers team. [Nicolas Sebrecht]
- IMAP: UIDPLUS: improve error message on response error for new UID. [Nicolas Sebrecht]
- Display the imaplib and python versions for each normal run. [Nicolas Sebrecht]
- imapserver: provide some SSL info while in imap debug mode. [Nicolas Sebrecht]
- manual: improve the documentation about sqlite migration. [Nicolas Sebrecht]
- documentation: add entry for faulting folders with Microsoft servers. [Nicolas Sebrecht]
- website-doc.sh: add hint on API removal. [Nicolas Sebrecht]
- README: refactorize sections. [Nicolas Sebrecht]



### OfflineIMAP v7.1.0 (2017-04-16)

#### Notes

The most important change is the removal of the status_backend configuration
option and that's why we're moving to v7.1.0.

There are other small bug fixes and improvements. However, the codebase didn't
change much since v7.0.14.

#### Authors

- Nicolas Sebrecht (6)
- benutzer193 (4)
- Ilias Tsitsimpis (1)

#### Fixes

- doc: Fix typo in offlineimap.1 man page. [Ilias Tsitsimpis]
- README: we moved to imaplib2 v2.57. [Nicolas Sebrecht]
- README: mark porting to py3 as stalled. [Nicolas Sebrecht]
- folder: UIDMaps: ignore KeyError failure while removing keys. [Nicolas Sebrecht]

#### Changes

- Remove support for the status_backend configuration option. [Nicolas Sebrecht]
- folder/IMAP: improve handling of "matchinguids" error while searching headers. [Nicolas Sebrecht]
- Adjust README to systemd service file changes. [benutzer193]
- Remove oneshot switch from systemd services. [benutzer193]
- Use oneshot services for systemd timers. [benutzer193]
- Create systemd oneshot services. [benutzer193]
- website-doc.sh: versions.yml: set versions in order. [Nicolas Sebrecht]



### OfflineIMAP v7.0.14 (2017-03-11)

#### Notes

Here is a new small fixup release for the v7.0 series. The first v7.0.0 release
is near to 8 months old. This v7.0.14 release is more reliable than v6.7.0.3.
Hence, I'm deprecating the v6.7 series.

Now, you are all enjoined to migrate to v7.0.14. Migrating back to v6.7 is not
supported so you might like to backup your local maildirs and metadata first.

We will fully remove the legacy text backend driver in near future. The SQLite
driver proved to be better for both performance and reliability.

With this release we use imaplib2 v2.57 to support some faulting IMAP servers,
fix a little bug about the backend migration to SQLite and serialize the sync
processes to prevent from issues when both IDLE and autorefresh are enabled.

Happy sync'ing!

#### Authors

- Nicolas Sebrecht (5)
- 927589452 (2)
- Jens Heinrich (1)
- Stéphane Graber (1)

#### Fixes

- SQLite: avoid concurrent writes on backend migration. [Nicolas Sebrecht]
- Fix ipv6 configuration handling. [Stéphane Graber]
- Prevent synchronization of identical folders from multiple threads. [Nicolas Sebrecht]

#### Changes

- Bump from imaplib2 v2.55 to v2.57. [Nicolas Sebrecht]
- scripts/get-repository.sh: use portable /bin/sh. [Jens Heinrich]
- MAINTAINERS: add new tester. [Nicolas Sebrecht]
- scripts/get-repository.sh: use env to call bash. [mailinglists@927589452.de]



### OfflineIMAP v7.0.13 (2017-01-27)

#### Notes

Here is a small release with some new features. IMAP servers are better supported.

The release cycle was improved. Now, we include a new freeze time before
important releases.

#### Authors

- Nicolas Sebrecht (8)
- lkcl (2)
- Chris Smart (1)

#### Features

- init: register SIGABRT and handle as per SIGUSR2. [Chris Smart]
- add documentation about SIGABRT. [Nicolas Sebrecht]
- learn repository retrycount configuration option. [lkcl]
- learn authproxy configuration option. [lkcl]

#### Fixes

- folder: IMAP: add missing whitespace in error message. [Nicolas Sebrecht]
- repository: IMAP: correctly check the response while listing remote folders. [Nicolas Sebrecht]
- release.sh: correctly sort releases to compute latest stable and rc. [Nicolas Sebrecht]

#### Changes

- manual: KNOWN ISSUES: add documentation about the deletions. [Nicolas Sebrecht]
- folder: IMAP: improve error message when Dovecot returns any data for UID FETCH. [Nicolas Sebrecht]
- MAINTAINERS: add new official testers. [Nicolas Sebrecht]



### OfflineIMAP v7.0.12 (2016-11-30)

#### Notes

Quick small release to fix v7.0.11 for the users of nametrans.

#### Authors

- Abdo Roig-Maranges (1)
- Darshit Shah (1)
- Nicolas Sebrecht (1)

#### Features

- Enable environment variable expansion on Repository.localfolders. [Darshit Shah]

#### Fixes

- repository: Base: fix typo in folder variable name. [Abdo Roig-Maranges]
- MAINTAINERS: minor: fix rendering. [Nicolas Sebrecht]



### OfflineIMAP v7.0.11 (2016-11-30)

#### Notes

Very small release to fix a regression about structure comparison in v7.0.10.

#### Authors

- Nicolas Sebrecht (2)

#### Fixes

- repository: Base: fix folder structure comparison. [Nicolas Sebrecht]

#### Changes

- MAINTAINERS: add all the contributors. [Nicolas Sebrecht]



### OfflineIMAP v7.0.10 (2016-11-28)

#### Notes

This release is mainly about improving reliability. The biggest changes are
about comparing the local and remote structures of folders.

The Gmail repository type allows to tune some predefined options for advanced
use cases.

Offlineimap learns where to find the default OpenSUSE certificate.

Some code refactoring and documentation improvements.

#### Authors

- Nicolas Sebrecht (15)
- Stéphane Albert (4)
- Abdo Roig-Maranges (2)
- Xudong Zhang (1)
- altruizine (1)
- Ævar Arnfjörð Bjarmason (1)

#### Features

- GMail: Add ability to set a custom host/port/ssl etc.. [Ævar Arnfjörð Bjarmason]
- Add OpenSUSE to list of supported distros. [altruizine]

#### Fixes

- repository: Base: fix name of the status folder. [Abdo Roig-Maranges]
- repository: Base: rework the structure folders comparison. [Nicolas Sebrecht]
- Fix remaining instance of check_uid_validity refactoring. [Abdo Roig-Maranges]
- Fix the profile mode. [Nicolas Sebrecht]
- folder: Maildir: actually try to use Delivery-Date if Date is broken. [Nicolas Sebrecht]
- Fix decodefoldernames not applying in folder sync. [Stéphane Albert]
- Fix mbnames writing with folders using utf-8. [Stéphane Albert]
- Fix utf7 decode error not caught. [Stéphane Albert]
- Fix md5 folder generation wanting unicode. [Stéphane Albert]
- Fix bug: should not compare list to int. [Xudong Zhang]

#### Changes

- folder: IMAP: display error message before starting next try. [Nicolas Sebrecht]
- offlineimap.conf: XOAUTH2: certificate validation is required for Gmail. [Nicolas Sebrecht]
- offlineimap.conf: autorefresh points to maxsyncaccounts. [Nicolas Sebrecht]
- offlineimap.conf: use 'Offlineimap' to name the software. [Nicolas Sebrecht]
- offlineimap.conf: add comments for the readonly configuration option. [Nicolas Sebrecht]
- offlineimap.conf: mbnames: provide sample for the folderfilter option. [Nicolas Sebrecht]
- Minor code refactoring. [Nicolas Sebrecht]
- Don't allow negative values for autorefresh. [Nicolas Sebrecht]
- Manual: add known issues entry about XOAUTH2 "invalid_grant". [Nicolas Sebrecht]
- repository: Gmail: fix copyright line. [Nicolas Sebrecht]


### OfflineIMAP v7.0.9 (2016-10-29)

#### Notes

Let's go for this small but still interesting release.

The Blinkenlights UI got fixed. Reliability for IMAP/IMAP setups is improved.

The sqlite backend now honors the fsync configuration option. This allows
commits to the database to be postponed. This might be usefull to disable the
default fsync for some use cases like cache migration from text to sqlite,
syncing after long away periods and more generally when a lot of new email
entries must be written to the cache.

Because of this change the old fsync option is marked EXPERIMENTAL. However,
setups using the plain text cache are not concerned. Bear in mind that disabling
fsync greatly decreases reliability when resuming from unexpected halts.

Small code cleanups, too.

#### Authors

- Nicolas Sebrecht (4)
- Giel van Schijndel (1)
- Ilias Tsitsimpis (1)

#### Features

- SQLite: make postponing transaction committing possible.. [Giel van Schijndel]

#### Fixes

- UIDMaps: ensure we don't update the map file in dry run mode. [Nicolas Sebrecht]
- UIDMaps: prevent from leaving a truncated map file. [Nicolas Sebrecht]
- Fix flickering in Blinkenlights UI. [Ilias Tsitsimpis]

#### Changes

- UIDMaps: reorder imports. [Nicolas Sebrecht]
- folder: IMAP: remove unused import. [Nicolas Sebrecht]



### OfflineIMAP v7.0.8 (2016-10-08)

#### Notes

Very small release to fix the broken UI relying on Curses. Thanks for the
contributors!

#### Authors

- Nicolas Sebrecht (4)
- Ilias Tsitsimpis (1)
- Stéphane Albert (1)

#### Features

- Introduce contrib/README.md. [Nicolas Sebrecht]

#### Fixes

- Import ui before threadutil to resolve circular dependency. [Ilias Tsitsimpis]
- Fix implicit call to unicode() from UI functions. [Stéphane Albert]

#### Changes

- imapserver: minor code cleaning: reorder methods. [Nicolas Sebrecht]
- website-doc.sh: print usage when no argument is given. [Nicolas Sebrecht]
- Changelog: add remark about singlethreadperfolder in the resume. [Nicolas Sebrecht]



### OfflineIMAP v7.0.7 (2016-09-21)

#### Notes

With this release, IDLE mode is a bit improved regarding stability. Offlineimap
learns the default path to the certificate for Gentoo.

The singlethreadperfolder configuration option is marked stable.

There are few improvements for logs and documentation. Minor code refactoring,
too.

#### Authors

- Nicolas Sebrecht (12)
- Dan Loewenherz (1)
- Espen Henriksen (1)

#### Features

- Add gentoo cert path for OS-DEFAULT. [Espen Henriksen]
- Remove EXPERIMENTAL flag for the singlethreadperfolder configuration option. [Nicolas Sebrecht]

#### Fixes

- Ensure logs are in bytes for PLAIN authentication. [Nicolas Sebrecht]
- Minor: utils: distro: fix copyright line. [Nicolas Sebrecht]
- README: minor copy edits. [Dan Loewenherz]
- IDLE: protect all calls to imapobj.noop() (coonection might be dropped). [Nicolas Sebrecht]
- XOAUTH2: raise error if string 'error' is in the response. [Nicolas Sebrecht]

#### Changes

- Set singlethreadperfolder configuration option when in idle mode. [Nicolas Sebrecht]
- repository: IMAP: cache the idle folders in memory. [Nicolas Sebrecht]
- mbnames: add info output messages in dry run mode. [Nicolas Sebrecht]
- mbnames: remove non-required argument. [Nicolas Sebrecht]
- offlineimap.conf: explain hooks in idle mode. [Nicolas Sebrecht]
- Explain how to submit issues in more files. [Nicolas Sebrecht]
- README: explain the a2x dependency to build the man page. [Nicolas Sebrecht]



### OfflineIMAP v7.0.6 (2016-08-21)

#### Notes

Evaluated XOAUTH2 configuration options are fixed. With this release,
offlineimap can try to keep the UIDs in order.

#### Authors

- Nicolas Sebrecht (10)
- James E. Blair (2)

#### Features

- Learn singlethreadperfolder configuration option. [James E. Blair]
- folder: Base: sort message UID list. [James E. Blair]

#### Fixes

- Maildir: add missing exception instance "as e" in except clause. [Nicolas Sebrecht]
- XOAUTH2: fix evaluated configuration options. [Nicolas Sebrecht]

#### Changes

- XOAUTH2: improve error message while trying to get access token. [Nicolas Sebrecht]
- Show python version for -V CLI option. [Nicolas Sebrecht]
- README: link Python 3 version to issues. [Nicolas Sebrecht]
- offlineimap.conf: add note about Gmail\All Mail keeping the emails while deleted. [Nicolas Sebrecht]
- release.sh: minor enhancements. [Nicolas Sebrecht]


### OfflineIMAP v7.0.5 (2016-08-10)

#### Notes

Bugfix release. The machineui is fixed and the dry-run mode is a bit improved.

Thanks to all the contributors and bug reporters. This release is yours.

#### Authors

- Nicolas Sebrecht (6)
- Wieland Hoffmann (2)
- Łukasz Żarnowiecki (2)
- Christopher League (1)

#### Fixes

- don't delete messages in local cache in dry-run mode. [Nicolas Sebrecht]
- Fix typo in format string in machineui. [Christopher League]

#### Changes

- folder: IMAP: change raw assert to OfflineImapError. [Nicolas Sebrecht]
- folder: IMAP: add 'imap' debug output before calling FETCH. [Nicolas Sebrecht]
- explicitly set __hash__ of Base class to None. [Łukasz Żarnowiecki]
- imapserver: change lambdas with map to list comprehension. [Łukasz Żarnowiecki]
- Clarify which settings are required for mbnames. [Wieland Hoffmann]
- Remove an unused import. [Wieland Hoffmann]
- folder: Base: minor style fix. [Nicolas Sebrecht]
- CONTRIBUTING: add link to external page on "How to fix a bug". [Nicolas Sebrecht]
- README: add link to the official repository on top of the page. [Nicolas Sebrecht]



### OfflineIMAP v7.0.4 (2016-08-02)

#### Notes

Small bugfix release for Gmail users.

#### Authors

- Nicolas Sebrecht (1)

#### Fixes

- ConfigHelperMixin must be new-style class to not break inheritance. [Nicolas Sebrecht]


### OfflineIMAP v7.0.3 (2016-07-30)

#### Notes

Here's a new bugfix release for the v7.0.x series. Only time we let us know if
it's a good release. However, I'm more confident.

Thanks for the reports and feedbacks!


#### Authors

- Nicolas Sebrecht (11)


#### Fixes

- Make systemd service kill offlineimap as expected. [Nicolas Sebrecht]
- XOAUTH2: fix the \*\_eval configuration options. [Nicolas Sebrecht]
- IMAP: don't take junk data for valid mail content. [Nicolas Sebrecht]
- offlineimap.conf: allow non-spaces in the account list. [Nicolas Sebrecht]
- Properly ignore folders with invalid characters (sep) in their name. [Nicolas Sebrecht]

#### Changes

- Add the repository name when connecting. [Nicolas Sebrecht]
- Github template: add system/distribution. [Nicolas Sebrecht]
- XOAUTH2: use one "public" attribute everywhere for self.oauth2_request_url. [Nicolas Sebrecht]
- Code style and minor code enhancements. [Nicolas Sebrecht]
- Manual: add known issue about netrc. [Nicolas Sebrecht]



### OfflineIMAP v7.0.2 (2016-07-27)

#### Notes

Small release to fix regression introduced in v7.0.0.

#### Authors

- Nicolas Sebrecht (1)
- Philipp Meier (1)
- Ævar Arnfjörð Bjarmason (1)

#### Features

- offlineimap.conf: learn to evaluate oauth2 related options. [Nicolas Sebrecht]

#### Fixes

- GmailMaildir: don't add a tuple to syncmessagesto_passes. [Philipp Meier]
- Remove double import of "six". [Ævar Arnfjörð Bjarmason]



### OfflineIMAP v7.0.1 (2016-07-26)

#### Notes

This is a small stable release fixing all the reported regressions and issues
about v7.0.0.

#### Authors

- Nicolas Sebrecht (9)

#### Fixes

- sqlite: properly serialize operations on the databases. [Nicolas Sebrecht]
- IMAP/IMAP: fix import issue about UIDMaps. [Nicolas Sebrecht]
- offlineimap.conf: allow non-spaces in the account list. [Nicolas Sebrecht]
- website-doc.sh: fix link in announces.yml. [Nicolas Sebrecht]
- release.sh: don't mess the mainline Changelog with commits in maint. [Nicolas Sebrecht]

#### Changes

- Improve error message when ssl_version must be set due to the tls_level. [Nicolas Sebrecht]
- Code cleanups.
- website-doc: order announces by date. [Nicolas Sebrecht]



### OfflineIMAP v7.0.0 (2016-07-22)

#### Notes

Finally, the new v7.0.0 is ready. This comes with breaking changes:

- Passwords are now expected in Unicode almost everywhere. They are used with
  the UTF-8 charset. However, some configuration options are not UTF-8 friendly
  mostly because of library limitations (e.g.: `remotepass`).

  Users with Unicode caracters in the passwords are recommended to use a file or
  `remotepasseval`.

- The sqlite database is the default.

  Please, read [this blog post]({% post_url 2016-05-19-sqlite-becomes-default %}).

- The PID file is no longer used because offlineimap is able to run multiple
  instances.

Please read the intermediate changelogs.


#### Authors

- Nicolas Sebrecht (9)

#### Features

- release.sh: learn to merge maint branch into next before releasing. [Nicolas Sebrecht]

#### Fixes

- sqlite: close the database when no more threads need access. [Nicolas Sebrecht]
- Fix attribute name _utime_from_header. [Nicolas Sebrecht]
- Maildir: OfflineImapError is missing the severity argument. [Nicolas Sebrecht]
- Fix: configparser does not know about python types like u"". [Nicolas Sebrecht]
- Manual: offlineimapui: fix minor rendering issue. [Nicolas Sebrecht]

#### Changes

- --info: allow user to enter a password. [Nicolas Sebrecht]
- Remove dead code: the description of the passes is never used. [Nicolas Sebrecht]
- offlineimap.conf: improve documentation for copy_ignore_eval. [Nicolas Sebrecht]



### OfflineIMAP v7.0.0-rc5 (2016-07-12)

#### Notes

This is a short -rc5 to stabilize the code with late improvements, mostly.

#### Authors

- Nicolas Sebrecht (9)
- Ævar Arnfjörð Bjarmason (1)

#### Features

- learn --delete-folder CLI option. [Nicolas Sebrecht]

#### Fixes

- mbnames: fix the filename extension for the intermediate files. [Nicolas Sebrecht]
- manual: offlineimap knows -V CLI option. [Nicolas Sebrecht]
- manual: remove unkown --column CLI option. [Nicolas Sebrecht]
- code of conduct: try to clarify what item 3 might mean. [Ævar Arnfjörð Bjarmason]

#### Changes

- mbnames: enable action at correct time. [Nicolas Sebrecht]
- mbnames: output message on errors while reading intermediate files. [Nicolas Sebrecht]
- --help: move -V option up. [Nicolas Sebrecht]
- init: factorize code to get active accounts. [Nicolas Sebrecht]


### OfflineIMAP v7.0.0-rc4 (2016-07-04)

#### Notes

Here we are to stabilize the code. I don't expect to merge features anymore.

When emails failed to download, offlineimap was raising the same issues again
and again. Users can now filter emails based on UID numbers.

The mbnames was missing a way to remove obsolete entries from deleted accounts.
Hence, --mbnames-prune is added.

Syncing folders with the local "sep" characters in their names was causing
troubles on next syncs. They are now filtered with a warning message.

IMAP/IMAP mode is improved: this was suffuring a (rare) bug related to
concurrent writes.

Usual code cleanups and minor improvements are included in this release.

I think this candidate is more stable than the previous v6.7.0 stable. Enjoy!

#### Authors

- Nicolas Sebrecht (17)

#### Features

- Learn to not download UIDs defined by the user. [Nicolas Sebrecht]
- Learn --mbnames-prune CLI option. [Nicolas Sebrecht]

#### Fixes

- UIDMaps (IMAP/IMAP mode): correctly protect from concurrent writes. [Nicolas Sebrecht]
- Correctly reraise errors with six. [Nicolas Sebrecht]
- Don't sync folders with local separator characters in their names. [Nicolas Sebrecht]

#### Changes

- Minor: improve "Copy message" output. [Nicolas Sebrecht]
- threadutil: use 'with' statements for lock. [Nicolas Sebrecht]
- Code cleanups and minor improvements. [Nicolas Sebrecht]
- release.sh: get_git_who(): remove unnecessary blank line. [Nicolas Sebrecht]
- website-doc.sh: fix line continuation. [Nicolas Sebrecht]


### OfflineIMAP v7.0.0-rc3 (2016-06-27)

#### Notes

The most important changes are:

- The passwords (and usernames) are now expected in Unicode.
- The sync_deletes feature is marked stable.
- It is possible to disable STARTTLS if it is failing.
- mbnames correctly honors the `-a` CLI option.

#### Authors

- Nicolas Sebrecht (31)
- Ilias Tsitsimpis (1)

#### Features

- Learn to disable STARTTLS. [Nicolas Sebrecht]
- Require usernames and passwords to be UTF-8 encoded. [Nicolas Sebrecht]
- offlineimap.conf: sync_deletes option is stable. [Nicolas Sebrecht]
- Learn -V CLI option. [Nicolas Sebrecht]

#### Fixes

- Don't try to copy messages with UID == 0. [Nicolas Sebrecht]
- Avoid removing of data when user removed a maildir. [Nicolas Sebrecht]
- When called with -a, mbnames must not erase entries of other accounts. [Nicolas Sebrecht]
- GmailMaildir: quick mode is not compatible with utime_from_header. [Nicolas Sebrecht]
- Manual: offlineimapui: minor typo fix. [Ilias Tsitsimpis]

#### Changes

- --info displays the imaplib2 version and whether it's the bundled or system one. [Nicolas Sebrecht]
- Bump from imaplib2 v2.53 to v2.55. [Nicolas Sebrecht]
- Move requirements.txt to the root directory. [Nicolas Sebrecht]
- README: rename "Requirements" section to "Requirements & dependencies". [Nicolas Sebrecht]
- README: add imaplib2 dependency and remove libraries in the standard libraries. [Nicolas Sebrecht]
- offlineimap.conf: improved comments. [Nicolas Sebrecht]
- sqlite was made mandatory: import error can fail at import time. [Nicolas Sebrecht]
- release.sh: put the authors directly to the AUTHORS section. [Nicolas Sebrecht]
- release.sh: learn users how to get the requirements file for pip. [Nicolas Sebrecht]
- website-doc.sh: include maintenance releases in the list of announces. [Nicolas Sebrecht]
- website-doc.sh: announces.yml: fill the page for the links. [Nicolas Sebrecht]
- Remove dead code and other code cleanups. [Nicolas Sebrecht]
- Style and comments improvements. [Nicolas Sebrecht]



### OfflineIMAP v7.0.0-rc2 (2016-06-04)

#### Notes

Enable offlineimap to run with Python 3. This feature is still experimental but
very welcome those days. Thanks Łukasz Żarnowiecki to work on this!

You are all welcome to test offlineimap with Python 3 and report both sucess and
failures.

Maintainers, we now work with a virtual imaplib2. Under the hood, the imported
imaplib2 can be the bundled version or any other (recent enough) imaplib2
provided by the system. If you already package imaplib2 and want to avoid
duplication of code, just remove the bundled version of imaplib2 while packaging
offlineimap and it should work out of the box. Be care, the filenames have
change.

#### Authors

- Nicolas Sebrecht (9)
- Łukasz Żarnowiecki (2)

#### Features

- Introduce a virtual imaplib2. [Nicolas Sebrecht]
- Mark Python 3 supported and experimental. [Nicolas Sebrecht]
- Allow to run under python3 without special env. [Łukasz Żarnowiecki]
- Maildir: Create top level dir recursively. [Łukasz Żarnowiecki]

#### Fixes

- IMAP: ignore UID with 0 as value when searching for UIDs. [Nicolas Sebrecht]
- Minor: fix copyright date. [Nicolas Sebrecht]

#### Changes

- Threading: improve comments. [Nicolas Sebrecht]
- Bump imaplib2 from v2.52 to v2.53. [Nicolas Sebrecht]
- globals: use whitespaces instead of tabs. [Nicolas Sebrecht]
- six: add requirements for pip. [Nicolas Sebrecht]
- README: add six library requirement. [Nicolas Sebrecht]

### OfflineIMAP v7.0.0-rc1 (2016-05-19)

#### Notes

We are starting a new major release cycle.

The dabatase for the cache is now sqlite by default. This means downgrading to
previous versions is prone to errors if you don't have sqlite enabled in your
configuration. All users should enable the sqlite database now to avoid issues.
Expect the legacy text files to be deprecated and removed in the future.

The long time awaited feature to not delete any message while allowing adding
new messages and sync flags is now implemented and marked stable. Thanks to the
testers and your feedbacks!

Łukasz started the work to support Python 3. Because of this, the six dependency
is required.

If you have scripts using the pid file, be aware this file is no longer used
because running multiple instances of the program is supported for years.

There a lot of code factorization and documentation improvements, especially
around threads.

I'm happy new contributors joined the official team, especially Łukasz and Ilias
(Debian maintainer). Thank you!

#### Authors

- Nicolas Sebrecht (32)
- Łukasz Żarnowiecki (17)
- Dodji Seketeli (1)
- Om Prakash (1)

#### Features

- Make sqlite status cache the default. [Nicolas Sebrecht]
- Learn to not delete messages. [Nicolas Sebrecht]
- Inform when maxage/startdate is in the future. [Łukasz Żarnowiecki]
- offlineimap.conf: XOAUTH2: expose and document the oauth2_request_url option. [Nicolas Sebrecht]
- offlineimap.conf: improve documentation for oauth2. [Nicolas Sebrecht]

#### Fixes

- sqlite: open database when we use it rather than at instantiation time. [Nicolas Sebrecht]
- SQLite: close db when done. [Nicolas Sebrecht]
- conf: newmail_hook is a remote option. [Nicolas Sebrecht]
- folder: utime_from_header is for Maildir only. [Nicolas Sebrecht]
- Handle maxage for davmail correctly. [Łukasz Żarnowiecki]
- XOAUTH2: don't force oauth2_request_url to be defined. [Nicolas Sebrecht]
- XOAUTH2: raise error when oauth_request_url is missing for IMAP type. [Nicolas Sebrecht]
- IMAP: don't try to create empty folders. [Nicolas Sebrecht]
- Really execute the recipe of the 'docs' target in top-most Makefile. [Dodji Seketeli]

#### Changes

- release.sh: make no differences between contributors. [Nicolas Sebrecht]
- threading: fix variable names about namespaces. [Nicolas Sebrecht]
- imapserver: use boolean where it makes sense. [Nicolas Sebrecht]
- threading: suggeststhreads must honor CLI and conf options. [Nicolas Sebrecht]
- threading: improve variable names and factorize code. [Nicolas Sebrecht]
- py3: raise exceptions using six module. [Łukasz Żarnowiecki]
- threading: minor improvements. [Nicolas Sebrecht]
- instancelimitedsems does not need a lock but must be used with global. [Nicolas Sebrecht]
- threading: get rid of the syncaccount function. [Nicolas Sebrecht]
- get rid of offlineimap/syncmaster.py. [Nicolas Sebrecht]
- threading: rename threadslist to accountThreads. [Nicolas Sebrecht]
- threading: simplify names. [Nicolas Sebrecht]
- Encode utf-8 argument for md5 function. [Łukasz Żarnowiecki]
- Replace dictionary iteration methods. [Łukasz Żarnowiecki]
- threading: simplify the monitoring code for threads. [Nicolas Sebrecht]
- threadutil: don't limit the number of threads. [Nicolas Sebrecht]
- threading: add comments. [Nicolas Sebrecht]
- Wrap zip calls with list call. [Łukasz Żarnowiecki]
- Remove xreadlines calls. [Łukasz Żarnowiecki]
- Replace xrange with range. [Łukasz Żarnowiecki]
- Replace has_key method to "key in dict". [Łukasz Żarnowiecki]
- Change filter with lambda to list comprehension. [Łukasz Żarnowiecki]
- Replace calls to long with int calls. [Łukasz Żarnowiecki]
- Add workaround for string.split for Python3. [Łukasz Żarnowiecki]
- Convert basestring to str. [Łukasz Żarnowiecki]
- Rename email.Parser to email.parser. [Łukasz Żarnowiecki]
- Do not mix tabs with spaces. [Łukasz Żarnowiecki]
- Convert except X,T to except X as T. [Łukasz Żarnowiecki]
- Add tags to gitignore. [Łukasz Żarnowiecki]
- don't write a pid file. [Nicolas Sebrecht]
- manual: improve rendering. [Nicolas Sebrecht]
- manual: improve sqlite section. [Nicolas Sebrecht]
- minor: logs: print readonly message in all debug modes. [Nicolas Sebrecht]
- accounts.py: minor improvements. [Nicolas Sebrecht]
- folder: properly factorize initialization and dropping of self.message. [Nicolas Sebrecht]
- offlineimap.txt: minor typo fixes. [Om Prakash]

### OfflineIMAP v6.7.0 (2016-03-10)

#### Notes

New stable release out!

With the work of Ilias, maintainer at Debian, OfflineIMAP is learning a new CLI
option to help fixing filenames for the users using nametrans and updating from
versions prior to v6.3.5.  Distribution maintainers might want to backport this
feature for their packaged versions out after v6.3.5. Have a look at commit
c84d23b65670f to know more.

OfflineIMAP earns the slogan "Get the emails where you need them", authored by
Norbert Preining.

Julien Danjou, the author of the book _The Hacker’s Guide To Python_, shared us
his screenshot of a running session of OfflineIMAP.

I recently created rooms for chat sessions at Gitter. It appears to be really
cool, supports seamless authentication with a github account, persistent logs,
desktop/mobile clients and many more usefull features. Join us at Gitter!

- https://gitter.im/OfflineIMAP/offlineimap  [NEW]
- https://gitter.im/OfflineIMAP/imapfw       [NEW]

Now, the OfflineIMAP community has 2 official websites:

- http://www.offlineimap.org (for offlineimap)
- http://imapfw.offlineimap.org (for imapfw) [NEW]

The Twitter account was resurrected, too. Feel free to join us:

  https://twitter.com/OfflineIMAP

Finally, the teams of the OfflineIMAP organization at Github were renewed to
facilitate the integration of new contributors and directly improve both the
documentation and the websites.

As a side note, the [imapfw repository](https://github.com/OfflineIMAP/imapfw)
has now more than 50 stargazers. This is very encouraging.

Thank you much everybody for your various contributions into OfflineIMAP!

#### Authors

- Ben Boeckel (1)
- Ebben Aries (1)
- Ilias Tsitsimpis (1)

#### Features

- Introduce a code of conduct.
- Add github templates.
- Change hard coding of AF_UNSPEC to user-defined address-families per repository. [Ebben Aries]
- Add documentation for the ipv6 configuration option.

#### Fixes

- Identify and fix messages with FMD5 inconsistencies. [Ilias Tsitsimpis]
- Curses, UIBase: remove references to __bigversion__. [Ben Boeckel]
- Sphinx doc: remove usage of __bigversion__.
- MANIFEST: exclude rfcs (used for Pypi packages).
- Changelog: fix typo.

#### Changes

- release.sh: move the authors section up.
- release.sh: add pypi instructions.
- MAINTAINERS: update.




### OfflineIMAP v6.7.0-rc2 (2016-02-22)

#### Notes

Learn to abruptly abort on multiple Ctrl+C.

Some bugs got fixed. XOAUTH2 now honors the proxy configuration option.  Error
message was improved when it fails to write a new mail in a local Maildir.

I've enabled the hook for integration with Github. You'll get notifications on
updates of the master branch of the repository (mostly for new releases). I may
write some tweets about OfflineIMAP sometimes.

#### Features

- Abort after three Ctrl-C keystrokes.

#### Fixes

- Fix year of copyright.
- Versioning: avoid confusing pip by spliting out __version__ with __revision__.
- Fix: exceptions.OSError might not have attribute EEXIST defined.
- XOAUTH2 handler: urlopen with proxied socket.
- Manual: small grammar fix.
- Fix typos in offlineimap(1) manpage.

#### Changes

- Update links to the new URL www.offlineimap.org.


### OfflineIMAP v6.7.0-rc1 (2016-01-24)

#### Notes

Starting a new cycle with all EXPERIMENTAL and TESTING stuff marked stable.
Otherwise, not much exciting yet. There's pending work that would need some
love by contributors:

- https://github.com/OfflineIMAP/offlineimap/issues/211
- https://github.com/OfflineIMAP/offlineimap/pull/111
- https://github.com/OfflineIMAP/offlineimap/issues/184

#### Features

- Allow authorization via XOAUTH2 using access token.

#### Fixes

- Revert "Don't output initial blurb in "quiet" mode".
- Fix Changelog.

#### Changes

- Declare newmail_hook option stable.
- Declare utime_from_header option stable.
- Decode foldernames is removed EXPERIMENTAL flag.
- Declare XOAUTH2 stable.
- Declare tls_level option stable.
- Declare IMAP Keywords option stable.


### OfflineIMAP v6.6.1 (2015-12-28)

#### Notes

This is a very small new stable release for two fixes.

Amending support for BINARY APPEND which is not correctly implemented. Also,
remove potential harms from dot files in a local maildir.

#### Fixes

- Bump imaplib2 from 2.53 to 2.52. Remove support for binary send.
- Ignore aloo dot files in the Maildir while scanning for mails.


### OfflineIMAP v6.6.0 (2015-12-05)

#### Features

- Maildir learns to mimic Dovecot's format of lower-case letters (a,b,c..) for
  "custom flags" or user keywords.

#### Fixes

- Broken retry loop would break connection management.
- Replace rogue `print` statement by `self.ui.debug`.

#### Changes

- Bump imaplib2 from v2.52 to v2.53.
- Code cleanups.
- Add a full stack of all thread dump upon EXIT or KILL signal in thread debug
  mode.


### OfflineIMAP v6.6.0-rc3 (2015-11-05)

#### Notes

Changes are slowing down and the code is under serious testing by some new
contributors. Everything expected at this time in the release cycle. Thanks to
them.

SSL is now enabled by default to prevent from sending private data in clear
stream to the wild.

#### Features

- Add new config option `filename_use_mail_timestamp`.

#### Fixes

- Bump from imaplib2 v2.51 to v2.52.
- Minor fixes.

#### Changes

- Enable SSL by default.
- Fix: avoid writing password to log.
- offlineimap.conf: improve namtrans doc a bit.


### OfflineIMAP v6.6.0-rc2 (2015-10-15)

#### Notes

Interesting job was done in this release with 3 new features:

- Support for XOAUTH2;
- New 'tls_level' configuration option to automatically discard insecure SSL protocols;
- New interface 'syslog' comes in, next to the -s CLI option. This allows better
  integration with systemd.

I won't merge big changes until the stable is out. IOW, you can seriously start
testing this rc2.

#### Features

- Add a new syslog ui.
- Introduce the 'tls_level' configuration option.
- Learn XOAUTH2 authentication (used by Gmail servers).
- Manual IDLE section improved (minor).

#### Fixes

- Configuration option utime_from_header handles out-of-bounds dates.
- offlineimap.conf: fix erroneous assumption about ssl23.
- Fix status code to reflect success or failure of a sync.
- contrib/release.sh: fix changelog edition.

#### Changes

- Bump imaplib2 from v2.48 to v2.51.
- README: new section status and future.
- Minor code cleanups.
- Makefile: improve building of targz.
- systemd: log to syslog rather than stderr for better integration.


### OfflineIMAP v6.6.0-rc1 (2015-09-28)

#### Notes

Let's go with a new release.

Basic UTF support was implemented while it is still exeprimental. Use this with
care.  OfflineIMAP can now send the logs to syslog and notify on new mail.


#### Features

- logging: add a switch to log to syslog.
- Added the newmail_hook.
- utf-7 feature is set experimental.

#### Fixes

- offlineimap.conf: fix a typo in the new mail hook example.
- Fix language.
- Fix spelling inconsistency.
- offlineimap.conf: don't use quotes for sep option.
- man page: fingerprint can be used with SSL.
- fix #225 « Runonce (offlineimap -o) does not stop if autorefresh is declared in DEFAULT section ».
- CONTRIBUTING: fix links to offlineimap.org.

#### Changes

- Bump imaplib2 from 2.43 to 2.48
- README: small improvements



### OfflineIMAP v6.5.7 (2015-05-15)

#### Notes

Almost no change since last release candidate. This is a sign that this release
is stable. ,-)

There was big changes since previous stable and users - especially distribution
maintainers - should really read the intermediate changelogs.

At the beginning of this year, I've tried to implement Unicode support. As you
know, I was not satisfied with the result. Then, I've published my code analysis
where I talk about doing a lot of refactoring for more proper OOP practices.
What's new is that I've actually done it and stopped this work as soon as I
realized that it means entirely rewriting the software.

On top of this, I'm not fully satisfied with other current limitations:
- old legacy support;
- migration to Python 3;
- complex multithreading design;
- some restrictions of the GPLv2 license;
- etc.

That's why I've started a new product. I'll publish it in the coming weeks under
the MIT license.

#### Features

- Better documentation for Windows users.
- contrib/release.sh (v0.2): fixes and improvements.

#### Fixes

- Report exceptions via exit code.
- Proxy feature leaks DNS support: offlineimap.conf talks about this.
- Email parsing for date coudn't work: fix datetuple dst check.

#### Changes

- Little code refactoring.


### OfflineIMAP v6.5.7-rc4 (2015-04-07)

#### Notes

Contrary to what the detailed following changes look like, here is a much bigger
release than expected.

Most important change is about maxage being sightly revisited. The whole
internal logic was found broken. Janna Martl did the hard work of raising the
issues and get them fixed.

New configuration options are added.

Maintainer Dmitrijs Ledkovs has left the organization. We wish you well! ,-)
Sebastian Spaeth let us know he will be almost inactive. We wish you well, too!

#### Features

- Add configuration option "utime_from_header" (TESTING).
- Add systemd integration files.
- mbnames: add new option "incremental" to write the file once per account.

#### Fixes

- maxage: fix timezone issues, remove IMAP-IMAP support, add startdate option.
- Test suites fixed and improved.
- Fix inaccurate UI messages when some messages are internally excluded from the
  cached lists.

#### Changes

- imaplib2: bump to v2.43.
- More documentations moves to the website.
- Maintainer Dmitrijs has left the organization.
- Remove unnecessary imaplib2 workaround.
- release.sh: script for maintainers improved.


### OfflineIMAP v6.5.7-rc3 (2015-03-19)

#### Notes

Here comes a much bigger release than expected! With this release, the new
website is made official.

Distribution maintainers, be aware that we now have a new man page
offlineimapui(7)!

Also, the man page offlineimap(1) is sightly revised to explain the command line
options. Since `offlineimap --help` won't detail the options anymore, it becomes
critical.

The maxage feature was broken by design and could delete mails on one side. It
is still under heavy work to fix issues when timezones are not synced. Gmail is
known to use different timezones accross mailboxes.

The IMAP library imaplib2 was updated for the upcoming course to Python 3.

The most other important changes are:

- Possibility to use a proxy.
- All the documentation are SIGHTLY revisited and updated from all the available
  places (sources files in the repository, wiki, website). A lot was moved from
  the wiki and the sources to the website.
- the RFCs are available in the repository.

#### Features

- Add proxy support powered by PySocks.
- New man page offlineimapui to explain the available UIs.
- Add a CONTRIBUTING.rst file.
- Add a `TODO.rst` list for the contributors.
- Add a script for maintainers to roll out new releases.
- Add the `scripts/get-repository.sh` script to work on the website and the wiki.
- Doc: add IMAP RFCs.

#### Fixes

- Don't loose local mails because of maxage.
- Properly handle the cached messagelist.
- Do not error if `remoteuser` is not configured.
- imaplibutil: add missing errno import.
- LocalStatusSQLite: labels: don't fail if database returns unexpected None value.
- IDLE: continue trying selecting the folder on `OfflineImapError.Error`.

#### Changes

- imaplib2: bump to v2.42
- `--help` becomes concise.
- Changelogs: move format back to markdown/kramdown to be more compatible with Jekyll.
- README: deep cleanups.
- code cleanups.
- code: more style consistency.
- sqlite: provide offending filename when open fails.
- MANUAL: full refactoring, change format to asciidoc.
- MANUAL: rename "KNOWN BUGS" TO "KNOWN ISSUES".
- MANUAL: add known issues entry about socktimeout for suspended sessions.
- offlineimap.conf: say what is the default value for the sep option.
- sqlite: provide information on what is failing for `OperationalError`.
- remove obsolete documentation.


### OfflineIMAP v6.5.7-rc2 (2015-01-18)

#### Notes

This release candidate should be minor for most users.

The best points are about SSL not falling back on other authentication methods
when failing, better RAM footprint and reduced I/O access.

Documentation had our attention, too.

There's some code cleanups and code refactoring, as usual.

#### Features

* Do not keep reloading pyhtonfile, make it stateful.
* HACKING: how to create tags.
* MANUAL: add minor sample on how to retrieve a password with a helper python file.

#### Fixes

* Make OS-default CA certificate file to be requested explicitely.
* SSL: do not fallback on other authentication mode if it fails.
* Fix regression introduced while style patching.
* API documentation: properly auto-document main class, fixes.
* ui: Machine: remove offending param for a _printData() call.
* Drop caches after having processed folders.

#### Changes

* Fix unexpected garbage code.
* Properly re-raise exception to save original tracebacks.
* Refactoring: avoid redefining various Python keywords.
* Code: improvements of comments and more style consistency.
* Configuration file: better design and other small improvements.
* nametrans documentation: fix minor error.
* Unused import removal.
* Add a note about the incorrect rendering of the docstring with Sphinx.
* Errors handling: log the messages with level ERROR.
* MAINTAINERS: add mailing list maintainers.
* Fixed copyright statement.
* COPYING: fix unexpected characters.


### OfflineIMAP v6.5.7-rc1 (2015-01-07)

#### Notes

I think it's time for a new release candidate. Our release cycles are long
enough and users are asked to use the current TIP of the next branch to test
our recent patches.

The current version makes better support for environment variable expansion and
improves OS portability. Gmail should be better supported: we are still
expecting feedbacks. Embedded library imaplib2 is updated to v2.37.
Debugging messages are added and polished.

There's some code cleanups and refactoring, also.


#### Features

* Expand environment variables in the following
  configuration items:
  - general.pythonfile;
  - general.metadata;
  - mbnames.filename;
  - Repository.localfolders.
  - Repository.sslcacertfile.
  Make tilde and environment variable expansion in the following
  configuration items:
  - Repository.sslclientcert;
  - Repository.sslclientkey.
* Support default CA bundle locations for a couple of
  known Unix systems (Michael Vogt, GutHub pull #19)
* Added default CA bundle location for OpenBSD
  (GitHub pull #120) and DragonFlyBSD.

#### Fixes

* Fix unbounded recursion during flag update (Josh Berry).
* Do not ignore gmail labels if header appears multiple times
* Delete gmail labels header before adding a new one
* Fix improper header separator for X-OfflineIMAP header
* Match header names case-insensitively
* Create SQLite database directory if it doesn't exist
  yet; warn if path is not a directory (Nick Farrell,
  GutHub pull #102)
* Properly manipulate contents of messagelist for folder
* Fix label processing in GmailMaildir
* Properly capitalize OpenSSL
* Fix warning-level message processing by MachineUI
  (GitHub pull #64, GitHub pull #118).
* Properly generate tarball from "sdist" command (GitHub #137)
* Fix Markdown formatting
* Fix typo in apply_xforms invocation
* Merge pull request #136 from aroig/gh/label-fix
* Fix mangled message headers for servers without UIDPLUS:
  X-OfflineIMAP was added with preceeding '\n' instead of
  '\r\n' just before message was uploaded to the IMAP server.
* Add missing version bump for 6.5.6 (it was released with
  6.5.5 in setup.py and other places).

#### Changes

* Warn about a tricky piece of code in addmessageheader
* Rename addmessageheader()'s crlf parameter to linebreak
* addmessageheader: fix case #2 and flesh out docstring
* addmessageheader(): add debug for header insertion
* Add version qualifier to differentiate releases and development ones
* More clearly show results of folder name translation
* IMAP: provide message-id in error messages
* Trade recursion by plain old cycle
* Avoid copying array every time, just slice it
* Added OpenSSL exception clause to our main GPL to allow
  people to link with OpenSSL in run-time.  It is needed
  at least for Debian, see
    https://lists.debian.org/debian-legal/2002/10/msg00113.html
  for details.
* Brought CustomConfig.py into more proper shape
* Updated bundled imaplib2 to 2.37:
  - add missing idle_lock in _handler()
* Imaplib2: trade backticks to repr()
* Introduce CustomConfig method that applies set of transforms
* imaplibutil.py: remove unused imports
* CustomConfig.py: remove unused imports
* init.py: remove unused import
* repository/Base.py: remove unused import
* repository/GmailMaildir.py: remove unused import
* repository/LocalStatus.py: remove unused import
* ui/Curses.py: remove unused import
* ui/UIBase.py: remove unused import
* localeval: comment on security issues
* docs: remove obsolete comment about SubmittingPatches.rst
* utils/const.py: fix ident
* ui/UIBase: folderlist(): avoid built-in list() redefinition
* more consistent style



### OfflineIMAP v6.5.6 (2014-05-14)

* Fix IDLE mode regression (it didn't worked) introduced
  after v6.5.5 (pointy hat goes to Eygene Ryabinkin, kudos --
  to Tomasz Żok)


### OfflineIMAP v6.5.6-rc1 (2014-05-14)

* Add knob to invoke folderfilter dynamically on each sync (GitHub#73)
* Add knob to apply compression to IMAP connections (Abdó Roig-Maranges)
* Add knob to filter some headers before uploading message
  to IMAP server (Abdó Roig-Maranges)
* Allow to sync GMail labels and implement GmailMaildir repository that
  adds mechanics to change message labels (Abdó Roig-Maranges)
* Allow to migrate status data across differend backends
  (Abdó Roig-Maranges)
* Support XDG Base Directory Specification
  (if $XDG_CONFIG_HOME/offlineimap/config exists, use it as the
  default configuration path; ~/.offlineimaprc is still tried after
  XDG location) (GitHub#32)
* Allow multiple certificate fingerprints to be specified inside
  'cert_fingerprint'


### OfflineIMAP v6.5.5 (2013-10-07)

* Avoid lockups for IMAP synchronizations running with the
  "-1" command-line switch (X-Ryl669 <boite.pour.spam@gmail.com>)
* Dump stacktrace for all threads on SIGQUIT: ease debugging
  of threading and other issues
* SIGHUP is now handled as the termination notification rather than
  the signal to reread the configuration (Dmitrijs Ledkovs)
* Honor the timezone of emails (Tobias Thierer)
* Allow mbnames output to be sorted by a custom sort key by specifying
  a 'sort_keyfunc' function in the [mbnames] section of the config.
* Support SASL PLAIN authentication method.  (Andreas Mack)
* Support transport-only tunnels that requre full IMAP authentication.
  (Steve Purcell)
* Make the list of authentication mechanisms to be configurable.
  (Andreas Mack)
* Allow to set message access and modification timestamps based
  on the "Date" header of the message itself.  (Cyril Russo)
* "peritem" format string for [mbnames] got new expansion key
  "localfolders" that corresponds to the same parameter of the
  local repository for the account being processed.
* [regression] pass folder names to the foldersort function,
  revert the documented behaviour
* Fix handling of zero-sized IMAP data items (GitHub#15).
* Updated bundled imaplib2 to 2.35:
  - fix for Gmail sending a BYE response after reading >100 messages
    in a session;
  - includes fix for GitHub#15: patch was accepted upstream.
* Updated bundled imaplib2 to 2.36: it includes support for SSL
  version override that was integrated into our code before,
  no other changes.
* Fixed parsing of quoted strings in IMAP responses: strings like "\\"
  were treated as having \" as the escaped quote, rather than treating
  it as the quoted escaped backslash (GitHub#53).
* Execute pre/post-sync hooks during synchronizations
  toggled by IMAP IDLE message processing. (maxgerer@gmail.com)
* Catch unsuccessful local mail uploads when IMAP server
  responds with "NO" status; that resulted in a loss of such
  local messages. (Adam Spiers)
* Don't create folders if readonly is enabled.
* Learn to deal with readonly folders to properly detect this
  condition and act accordingly.  One example is Gmail's "Chats"
  folder that is read-only, but contains logs of the quick chats. (E.
  Ryabinkin)
* Fix str.format() calls for Python 2.6 (D. Logie)
* Remove APPENDUID hack, previously introduced to fix Gmail, no longer
  necessary, it might have been breaking things. (J. Wiegley)
* Improve regex that could lead to 'NoneType' object has no attribute
  'group' (D. Franke)
* Improved error throwing on repository misconfiguration

### OfflineIMAP v6.5.4 (2012-06-02)

* bump bundled imaplib2 library 2.29 --> 2.33
* Actually perform the SSL fingerprint check (reported by J. Cook)
* Curses UI, don't use colors after we shut down curses already (C.Höger)
* Document that '%' needs encoding as '%%' in configuration files.
* Fix crash when IMAP.quickchanged() led to an Error (reported by sharat87)
* Implement the createfolders setting to disable folder propagation (see docs)

### OfflineIMAP v6.5.3.1 (2012-04-03)

* Don't fail if no dry-run setting exists in offlineimap.conf
  (introduced in 6.5.3)


### OfflineIMAP v6.5.3 (2012-04-02)

* --dry-run mode protects us from performing any actual action.  It will
  not precisely give the exact information what will happen. If e.g. it
  would need to create a folder, it merely outputs "Would create folder
  X", but not how many and which mails it would transfer.

* internal code changes to prepare for Python3

* Improve user documentation of nametrans/folderfilter

* Fixed some cases where invalid nametrans rules were not caught and
  we would not propagate local folders to the remote repository.
  (now tested in test03)

* Revert "* Slight performance enhancement uploading mails to an IMAP
  server in the common case." It might have led to instabilities.

* Revamped documentation structure. `make` in the `docs` dir or `make
  doc` in the root dir will now create the 1) man page and 2) the user
  documentation using sphinx (requiring python-doctools, and
  sphinx). The resulting user docs are in `docs/html`. You can also
  only create the man pages with `make man` in the `docs` dir.

* -f command line option only works on the untranslated remote
  repository folder names now. Previously folderfilters had to match
  both the local AND remote name which caused unwanted behavior in
  combination with nametrans rules. Clarify in the help text.

* Some better output when using nonsensical configuration settings

* Improve compatability of the curses UI with python 2.6

### OfflineIMAP v6.5.2.1 (2012-04-04)

* Fix python2.6 compatibility with the TTYUI backend (crash)

* Fix TTYUI regression from 6.5.2 in refresh loop (crash)

* Fix crashes related to UIDVALIDITY returning "None"

* Beginning of a test suite. So far there is only one test. Configure
  test/credentials.conf and invoke with "python setup.py test"

* Make folders containing quotes work rather than crashing
  (reported by Mark Eichin)

* Improve delete msg performance with SQLITE backend

* Enforce basic UI when using the --info switch

* Remove the Gmail "realdelete" option, as it could lead to potential
  data loss.

### OfflineIMAP v6.5.2 (2012-01-17)

* Gmail "realdelete" option is considered harmful and has the potential
  for data loss. Analysis at
  http://article.gmane.org/gmane.mail.imap.offlineimap.general/5265
  Warnings were added to offlineimap.conf

* Rather than write out the nametrans'lated folder names for mbnames, we
  now write out the local untransformed box names. This is generally
  what we want. This became relevant since we support nametrans rules on
  the local side since only a short time. Reported by Paul Collignan.

* Some sanity checks and improved error messages.

* Revert 6.5.1.1 change to use public imaplib2 function, it was reported to
  not always work.

* Don't fail when ~/netrc is not readable by us.

* Don't emit noisy regular sleeping announcements in Basic UI.

### OfflineIMAP v6.5.1.2 (2012-01-07) - "Baby steps"

Smallish bug fixes that deserve to be put out.

* Fix possible crash during --info run
* Fix reading in Maildirs, where we would attempt to create empty
  directories on REMOTE.
* Do not attempt to sync lower case custom Maildir flags. We do not
  support them (yet) (this prevents many scary bogus sync messages)
* Add filter information to the filter list in --info output

### OfflineIMAP v6.5.1.1 (2012-01-07) - "Das machine control is nicht fur gerfinger-poken und mittengrabben"

Blinkenlights UI 6.5.0 regression fixes only.

* Sleep led to crash ('abort_signal' not existing)

* Make exit via 'q' key work again cleanly

### OfflineIMAP v6.5.1 (2012-01-07) - "Quest for stability"

* Fixed Maildir regression "flagmatchre" not found. (regressed in 6.5.0)

* Have console output go by default to STDOUT and not STDERR (regression
  in 6.5.0)

* Fixed MachineUI to urlencode() output lines again, rather than
  outputting multi-line items. It's ugly as hell, but it had been that
  way for years.

* Remove the old global locking system. We lock only the accounts that
  we currently sync, so you can invoke OfflineImap multiple times now as
  long as you sync different accounts. This system is compatible with
  all releases >= 6.4.0, so don't run older releases simultanous to this
  one.

### OfflineIMAP v6.5.0 (2012-01-06)

This is a CRITICAL bug fix release for everyone who is on the 6.4.x series.
Please upgrade to avoid potential data loss! The version has been bumped to
6.5.0, please let everyone know that the 6.4.x series is problematic.

* Uploading multiple emails to an IMAP server would lead to wrong UIDs
  being returned (ie the same for all), which confused offlineimap and
  led to recurrent upload/download loops and inconsistencies in the
  IMAP<->IMAP uid mapping.

* Uploading of Messages from Maildir and IMAP<->IMAP has been made more
  efficient by renaming files/mapping entries, rather than actually
  loading and saving the message under a new UID.

* Fix regression that broke MachineUI

### OfflineIMAP v6.4.4 (2012-01-06)

This is a bugfix release, fixing regressions occurring in or since 6.4.0.

* Fix the missing folder error that occured when a new remote folder was
  detected (IMAP<->Maildir)

* Possibly fixed bug that prevented us from ever re-reading Maildir
  folders, so flag changes and deletions were not detected when running
  in a refresh loop. This is a regression that was introduced in about
  6.4.0.

* Never mangle maildir file names when using nonstandard Maildir flags
  (such as 'a'), note that they will still be deleted as they are not
  supported in the sync to an IMAP server.

### OfflineIMAP v6.4.3 (2012-01-04)

#### New Features

* add a --info command line switch that outputs useful information about
  the server and the configuration for all enabled accounts.

#### Changes

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


### OfflineIMAP v6.4.2 (2011-12-01)

* IMAP<->IMAP sync with a readonly local IMAP repository failed with a
  rather mysterious "TypeError: expected a character buffer object"
  error. Fix this my retrieving the list of folders early enough even
  for readonly repositories.

* Fix regression from 6.4.0. When using local Maildirs with "/" as a
  folder separator, all folder names would get a trailing slash
  appended, which is plain wrong.

### OfflineIMAP v6.4.1 (2011-11-17)

#### Changes

* Indicate progress when copying many messages (slightly change log format)

* Output how long an account sync took (min:sec).

#### Bug Fixes

* Syncing multiple accounts in single-threaded mode would fail as we try
  to "register" a thread as belonging to two accounts which was
  fatal. Make it non-fatal (it can be legitimate).

* New folders on the remote would be skipped on the very sync run they
  are created and only by synced in subsequent runs. Fixed.

* a readonly parameter to select() was not always treated correctly,
  which could result in some folders being opened read-only when we
  really needed read-write.

### OfflineIMAP v6.4.0 (2011-09-29)

This is the first stable release to support the forward-compatible per-account
locks and remote folder creation that has been introduced in the 6.3.5 series.

* Various regression and bug fixes from the last couple of RCs

### OfflineIMAP v6.3.5-rc3 (2011-09-21)

#### Changes

* Refresh server capabilities after login, so we know that Gmail
  supports UIDPLUS (it only announces that after login, not
  before). This prevents us from adding custom headers to Gmail uploads.

#### Bug Fixes

* Fix the creation of folders on remote repositories, which was still
  botched on rc2.

### OfflineIMAP v6.3.5-rc2 (2011-09-19)

#### New Features

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

#### Changes

* Documentation improvements concerning 'restoreatime' and some code cleanup

* Maildir repositories now also respond to folderfilter= configurations.

#### Bug Fixes

* New emails are not created with "-rwxr-xr-x" but as "-rw-r--r--"
  anymore, fixing a regression in 6.3.4.

### OfflineIMAP v6.3.5-rc1 (2011-09-12)

#### Notes

Idle feature and SQLite backend leave the experimental stage! ,-)

#### New Features

* When a message upload/download fails, we do not abort the whole folder
  synchronization, but only skip that message, informing the user at the
  end of the sync run.

* If you connect via ssl and 'cert_fingerprint' is configured, we check
  that the server certificate is actually known and identical by
  comparing the stored sha1 fingerprint with the current one.

#### Changes

* Refactor our IMAPServer class. Background work without user-visible
  changes.
* Remove the configurability of the Blinkenlights statuschar. It
  cluttered the main configuration file for little gain.
* Updated bundled imaplib2 to version 2.28.

#### Bug Fixes

* We protect more robustly against asking for inexistent messages from the
  IMAP server, when someone else deletes or moves messages while we sync.
* Selecting inexistent folders specified in folderincludes now throws
  nice errors and continues to sync with all other folders rather than
  exiting offlineimap with a traceback.



### OfflineIMAP v6.3.4 (2011-08-10)

#### Notes

Here we are. A nice release since v6.3.3, I think.

#### Changes

* Handle when UID can't be found on saved messages.



### OfflineIMAP v6.3.4-rc4 (2011-07-27)

#### Notes

There is nothing exciting in this release. This is somewhat expected due to the
late merge on -rc3.

#### New Features

* Support maildir for Windows.

#### Changes

* Manual improved.


### OfflineIMAP v6.3.4-rc3 (2011-07-07)

#### Notes

Here is a surprising release. :-)

As expected we have a lot bug fixes in this round (see git log for details),
including a fix for a bug we had for ages (details below) which is a very good
news.

What makes this cycle so unusual is that I merged a feature to support StartTLS
automatically (thanks Sebastian!). Another very good news.

We usually don't do much changes so late in a cycle. Now, things are highly
calming down and I hope a lot of people will test this release. Next one could
be the stable!

#### New Features

* Added StartTLS support, it will automatically be used if the server
  supports it.

#### Bug Fixes

* We protect more robustly against asking for inexistent messages from the
  IMAP server, when someone else deletes or moves messages while we sync.


### OfflineIMAP v6.3.4-rc2 (2011-06-15)

#### Notes

This was a very active rc1 and we could expect a lot of new fixes for the next
release.

The most important fix is about a bug that could lead to data loss. Find more
information about his bug here:

  http://permalink.gmane.org/gmane.mail.imap.offlineimap.general/3803

The IDLE support is merged as experimental feature.

#### New Features

* Implement experimental IDLE feature.

#### Changes

* Maildirs use less memory while syncing.

#### Bug Fixes

* Saving to Maildirs now checks for file existence without race conditions.
* A bug in the underlying imap library has been fixed that could
  potentially lead to data loss if the server interrupted responses with
  unexpected but legal server status responses. This would mainly occur
  in folders with many thousands of emails. Upgrading from the previous
  release is strongly recommended.


### OfflineIMAP v6.3.4-rc1 (2011-05-16)

#### Notes

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

#### New Features

* Begin sphinx-based documentation for the code.
* Enable 1-way synchronization by settting a [Repository ...] to
  readonly = True. When e.g. using offlineimap for backup purposes you
  can thus make sure that no changes in your backup trickle back into
  the main IMAP server.
* Optional: experimental SQLite-based backend for the LocalStatus
  cache. Plain text remains the default.

#### Changes

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

#### Bug Fixes

* Drop connection if synchronization failed. This is needed if resuming the
  system from suspend mode gives a wrong connection.
* Fix the offlineimap crash when invoking debug option 'thread'.
* Make 'thread' command line option work.


### OfflineIMAP v6.3.3 (2011-04-24)

#### Notes

Make this last candidate cycle short. It looks like we don't need more tests as
most issues were raised and solved in the second round. Also, we have huge work
to merge big and expected features into OfflineIMAP.

Thanks to all contributors, again. With such a contribution rate, we can release
stable faster. I hope it will be confirmed in the longer run!

#### Changes

* Improved documentation for querying password.


### OfflineIMAP v6.3.3-rc3 (2011-04-19)

#### Notes

It's more than a week since the previous release. Most of the issues raised were
discussed and fixed since last release. I think we can be glad and confident for
the future while the project live his merry life.

#### Changes

* The -f option did not work with Folder names with spaces. It works
  now, use with quoting e.g. -f "INBOX, Deleted Mails".
* Improved documentation.
* Bump from imaplib2 v2.20 to v2.22.
* Code refactoring.

#### Bug Fixes

* Fix IMAP4 tunnel with imaplib2.


### OfflineIMAP v6.3.3-rc2 (2011-04-07)

#### Notes

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

(my apologies if I forget somebody) ...and all active developers, of course!

The imaplib2 migration looks to go the right way to be definetly released but
still needs more tests.  So, here we go...

#### Changes

* Increase compatability with Gmail servers which claim to not support
  the UIDPLUS extension but in reality do.

#### Bug Fixes

* Fix hang when using Ctrl+C in some cases.


### OfflineIMAP v6.3.3-rc1 (2011-03-16)

#### Notes

Here is time to begin the tests cycle. If feature topics are sent, I may merge
or delay them until the next stable release.

Main change comes from the migration from imaplib to imaplib2. It's internal
code changes and doesn't impact users. UIDPLUS and subjectAltName for SSL are
also great improvements.

This release includes a hang fix due to infinite loop. Users seeing OfflineIMAP
hang and consuming a lot of CPU are asked to update.

That beeing said, this is still an early release candidate you should use for
non-critical data only!

#### New Features

* Implement UIDPLUS extension support. OfflineIMAP will now not insert
  an X-OfflineIMAP header if the mail server supports the UIDPLUS
  extension.
* SSL: support subjectAltName.

#### Changes

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

#### Bug Fixes

* Fix ignoring output while determining the rst2xxx command name to build
  documentation.
* Fix hang because of infinite loop reading EOF.
* Allow SSL connections to send keep-alive messages.
* Fix regression (UIBase is no more).
* Make profiling mode really enforce single-threading
* Do not send localized date strings to the IMAP server as it will
  either ignore or refuse them.


### OfflineIMAP v6.3.2 (2010-02-21)

#### Notes

First of all I'm really happy to announce our new official `website
<http://offlineimap.org>`_. Most of the work started from the impulse
of Philippe LeCavalier with the help of Sebastian Spaeth and other
contributors. Thanks to everybody.

In this release, we are still touched by the "SSL3 write pending" but I think
time was long enough to try to fix it. We have our first entry in the "KNOWN
BUG" section of the manual about that. I'm afraid it could impact a lot of users
if some distribution package any SSL library not having underlying (still
obscure) requirements. Distribution maintainers should be care of it. I hope
this release will help us to have more reports.

This release will also be the root of our long maintenance support.

Other bugs were fixed.

#### Bug Fixes

* Fix craches for getglobalui().
* Fix documentation build.
* Restore compatibiliy with python 2.5.


### OfflineIMAP v6.3.2-rc3 (2010-02-06)

#### Notes

We are still touched by the "SSL3 write pending" bug it would be really nice to
fix before releasing the coming stable. In the worse case, we'll have to add the
first entry in the "KNOWN BUG" section of the manual. I'm afraid it could impact
a lot of users if some distribution package any SSL library not having
underlying (still obscure) requirements.

The best news with this release are the Curse UI fixed and the better reports
on errors.

In this release I won't merge any patch not fixing a bug or a security issue.

More feedbacks on the main issue would be appreciated.

#### Changes

* Sample offlineimap.conf states it expects a PEM formatted certificat.
* Give better trace information if an error occurs.
* Have --version ONLY print the version number.
* Code cleanups.

#### Bug Fixes

* Fix Curses UI (simplified by moving from MultiLock to Rlock implementation).
* Makefile: docutils build work whether python extension command is stripped or not.
* Makefile: clean now removes HTML documentation files.


### OfflineIMAP v6.3.2-rc2 (2010-12-21)

#### Notes

We are beginning a new tests cycle. At this stage, I expect most people will try
to intensively stuck OfflineIMAP. :-)

#### New Features

* Makefile learn to build the package and make it the default.
* Introduce a Changelog to involve community in the releasing process.
* Migrate documentation to restructuredtext.

#### Changes

* Improve CustomConfig documentation.
* Imply single threading mode in debug mode exept for "-d thread".
* Code and import cleanups.
* Allow UI to have arbitrary names.
* Code refactoring around UI and UIBase.
* Improve version managment and make it easier.
* Introduce a true single threading mode.

#### Bug Fixes

* Understand multiple EXISTS replies from servers like Zimbra.
* Only verify hostname if we actually use CA cert.
* Fix ssl ca-cert in the sample configuration file.
* Fix 'Ctrl+C' interruptions in threads.
* Fix makefile clean for files having whitespaces.
* Fix makefile to not remove unrelated files.
* Fixes in README.
* Remove uneeded files.


### OfflineIMAP v6.3.2-rc1 (2010-12-19)

#### Notes

We are beginning a tests cycle. If feature topics are sent, I may merge or
delay them until the next stable release.

#### New Features

* Primitive implementation of SSL certificates check.

#### Changes

* Use OptionParser instead of getopts.
* Code cleanups.

#### Bug Fixes

* Fix reading password from UI.


### OfflineIMAP v6.3.1 (2010-12-11)

#### Notes

Yes, I know I've just annouced the v6.3.0 in the same week. As said, it
was not really a true release for the software. This last release
includes fixes and improvements it might be nice to update to.

Thanks to every body who helped to make this release with patches and
tips through the mailing list. This is clearly a release they own.

#### Changes

* cProfile becomes the default profiler. Sebastian Spaeth did refactoring to
  prepare to the coming unit test suites.
* UI output formating enhanced.
* Some code cleanups.

#### Bug Fixes

* Fix possible overflow while working with Exchange.
* Fix time sleep while exiting threads.


### OfflineIMAP v6.3.0 (2010-12-09)

#### Notes

This release is more "administrative" than anything else and mainly marks the
change of the maintainer. New workflow and policy for developers come in.  BTW,
I don't think I'll maintain debian/changelog. At least, not in the debian way.

Most users and maintainers may rather want to skip this release.

#### Bug Fixes

* Fix terminal display on exit.
* netrc password authentication.
* User name querying from netrc.
