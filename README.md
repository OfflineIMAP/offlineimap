[offlineimap]: https://github.com/OfflineIMAP/offlineimap
[website]: http://offlineimap.github.io
[wiki]: http://github.com/OfflineIMAP/offlineimap/wiki

# OfflineImap

## Description

OfflineIMAP is a software to dispose your e-mail mailbox(es) as a local Maildir.

For example, this allows reading the mails while offline without the need for your mail reader (MUA) to support disconnected operations.

OfflineIMAP will synchronize both sides via *IMAP*.


## License

GNU General Public License v2.


## Why should I use OfflineIMAP?

* It is **fast**.
* It is **reliable**.
* It is **flexible**.
* It is **safe**.


## Downloads

You should first check if your distribution already package OfflineIMAP for you.
Downloads releases as [tarball or zipball](https://github.com/OfflineIMAP/offlineimap/tags).


## Feedbacks and contributions

**The user discussions, development, announces and all the exciting stuff take
place in the mailing list.** While not mandatory to send emails, you can
[subscribe here](http://lists.alioth.debian.org/mailman/listinfo/offlineimap-project).

Bugs, issues and contributions can be requested to both the mailing list or the
[official Github project][offlineimap].


## The community

* OfflineIMAP's main site is the [project page at Github][offlineimap].
* There is the [OfflineIMAP community's website][website].
* And finally, [the wiki][wiki].


## Requirements

* Python v2.7
* Python SQlite (optional while recommended)


## Documentation

The documentation is included (in .rst format) in the `docs` directory.
Read it directly or generate nice html docs (python-sphinx needed) and/or
the man page (python-docutils needed) while being in the `docs` dir via:

    'make doc' (user docs), 'make man' (man page only) or 'make' (both)

    (`make html` will simply create html versions of all *.rst files in /docs)

The resulting user documentation will be in `docs/html`. The full user
docs are also at: http://docs.offlineimap.org. Please see there for
detailed information on how to install and configure OfflineImap.
