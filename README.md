Upstream status (`master` branch):
[![OfflineIMAP build status on Travis-CI.org](https://travis-ci.org/OfflineIMAP/offlineimap.svg?branch=master)](https://travis-ci.org/OfflineIMAP/offlineimap)
[![OfflineIMAP code coverage on Codecov.io](https://codecov.io/gh/OfflineIMAP/offlineimap/branch/master/graph/badge.svg)](https://codecov.io/gh/OfflineIMAP/offlineimap)
[![Gitter chat](https://badges.gitter.im/OfflineIMAP/offlineimap.png)](https://gitter.im/OfflineIMAP/offlineimap)
[![Say thanks to OfflineIMAP](https://img.shields.io/badge/Say%20Thanks-!-______.svg)](https://saythanks.io/to/OfflineIMAP)

Upstream status (`next` branch):
[![OfflineIMAP build status on Travis-CI.org](https://travis-ci.org/OfflineIMAP/offlineimap.svg?branch=next)](https://travis-ci.org/OfflineIMAP/offlineimap)

[![Github All Releases](https://img.shields.io/github/downloads/atom/atom/total.svg)](https://github.com/OfflineIMAP/offlineimap/graphs/traffic)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![GitHub contributors](https://img.shields.io/github/contributors/OfflineIMAP/offlineimap.svg)](https://github.com/OfflineIMAP/offlineimap/graphs/contributors)
[![Snap status](https://build.snapcraft.io/badge/snapcrafters/offlineimap.svg)](https://build.snapcraft.io/user/snapcrafters/offlineimap)

[![Python versions supported](https://img.shields.io/pypi/pyversions/offlineimap.svg)](https://pypi.python.org/pypi/offlineimap)
[![Package stability](https://img.shields.io/pypi/status/offlineimap.svg)](https://pypi.python.org/pypi/offlineimap)
[![PyPI status](https://badge.fury.io/py/offlineimap.svg)](https://pypi.python.org/pypi/offlineimap)

[![GitHub last commit](https://img.shields.io/github/last-commit/OfflineIMAP/offlineimap.svg)](https://github.com/OfflineIMAP/offlineimap/commits/master)
[![Github Tag](https://img.shields.io/github/tag/OfflineIMAP/offlineimap.svg)](https://github.com/OfflineIMAP/offlineimap/releases)
[![Follow on twitter](https://img.shields.io/twitter/follow/OfflineIMAP.svg?style=social&logo=twitter)](https://twitter.com/intent/follow?screen_name=OfflineIMAP)

[offlineimap]: https://github.com/OfflineIMAP/offlineimap
[website]: http://www.offlineimap.org
[wiki]: https://github.com/OfflineIMAP/offlineimap/wiki
[blog]: http://www.offlineimap.org/posts.html
[docs]: https://offlineimap.readthedocs.io/
[mailing_list]: http://lists.alioth.debian.org/mailman/listinfo/offlineimap-project
[mailing_list_archive]: http://dir.gmane.org/gmane.mail.imap.offlineimap.general
[code_of_conduct]: https://github.com/OfflineIMAP/offlineimap/blob/master/CODE_OF_CONDUCT.md
[copying_license]: https://github.com/OfflineIMAP/offlineimap/blob/master/COPYING
[changelog]: https://github.com/OfflineIMAP/offlineimap/blob/master/Changelog.md
[maintainers]: https://github.com/OfflineIMAP/offlineimap/blob/master/MAINTAINERS.rst
[manifest]: https://github.com/OfflineIMAP/offlineimap/blob/master/MANIFEST.in
[todo]: https://github.com/OfflineIMAP/offlineimap/blob/master/TODO.rst
[conf]: https://github.com/OfflineIMAP/offlineimap/blob/master/offlineimap.conf
[conf_minimal]: https://github.com/OfflineIMAP/offlineimap/blob/master/offlineimap.conf.minimal
[issues_new]: https://github.com/OfflineIMAP/offlineimap/issues/new
[pull_request_new]: https://github.com/OfflineIMAP/offlineimap/compare
[issues_need_contrib]: https://github.com/OfflineIMAP/offlineimap/issues?q=is%3Aopen+is%3Aissue+label%3A"need+contributor!"
[homebrew_mac_install]: https://brewinstall.org/Install-offlineimap-on-Mac-with-Brew/
[macports_mac_install]: https://www.macports.org/ports.php?by=name&substr=offlineimap

<p style="center">
<h1><img src="https://upload.wikimedia.org/wikipedia/commons/1/13/OfflineIMAP_logo.png" alt="OfflineIMAP"/>OfflineIMAP</h1>
<b><i>"Get the emails where you need them."</i></b>
<h2> Read/sync your IMAP mailboxes. Tested on Linux, Mac OSX. Also works on BSD and Windows.</h2>
</p>

Links:
* [Official (upstream) github code repository][offlineimap]
* [Website][website]
* [Wiki][wiki]
* [Blog][blog]
* [![Documentation](https://readthedocs.org/projects/offlineimap/badge/?version=latest&style=flat)](https://offlineimap.readthedocs.io/)
* [Subscribe to the Mailing List][mailing_list]
* [Read/Search the Mailing List Archive][mailing_list_archive]


## Description

* OfflineIMAP is software that downloads your email mailbox(es) as **[local Maildirs](https://en.wikipedia.org/wiki/Maildir)**.
* OfflineIMAP will synchronize mailboxes between two mail servers via *[IMAP](https://en.wikipedia.org/wiki/Internet_Message_Access_Protocol)*.
* Most up to date [Change Log][changelog].

## Why should I use OfflineIMAP?

IMAP's main downside is that you have to **trust** your email provider to
not lose your email. While certainly unlikely, it's not impossible.
With OfflineIMAP, you can download your Mailboxes and make you own backups of
your [Maildir](https://en.wikipedia.org/wiki/Maildir).

This allows reading your email offline without the need for your mail
reader ([MUA](https://en.wikipedia.org/wiki/Email_client)) to support IMAP operations. 
Need an [attachment](https://en.wikipedia.org/wiki/Email_attachment) from a
message without internet connection? No problem, the message is still there.


## Project status and future

> As one of the maintainer of OfflineIMAP, I'd like to put my efforts into
> [imapfw](http://github.com/OfflineIMAP/imapfw). **imapfw** is software in
> development that I intend to replace OfflineIMAP with in the long term.
>
> That's why I'm not going to continue OfflineIMAP development. I'll continue
> to maintain OfflineIMAP (fixing small bugs, reviewing patches and merging,
> and rolling out new releases), but that's all.
>
> While I keep tracking issues for OfflineIMAP, you should not expect future support.
>
> You won't be left at the side. OfflineIMAP's community is large enough so that
> you'll find people for most of your issues.
>
> Get news from the [blog][blog].
>
>                                  Nicolas Sebrecht. ,-)


## License

[GNU General Public License v2][copying_license].


## Downloads

* You should first check if your distribution already packages OfflineIMAP for you, most Linux have it. 
* On MacOSX thru [Homebrew][homebrew_mac_install], [MacPorts][macports_mac_install], and others.
* Downloads releases as [tarball or zipball](https://github.com/OfflineIMAP/offlineimap/tags).
* You can easily [Install as a Snap](https://snapcraft.io/offlineimap)
`sudo snap install offlineimap`
The configuration file for offlineimap should be placed in ```$HOME/snap/offlineimap/current/.offlineimaprc```
([Don't have snapd installed?](https://snapcraft.io/docs/core/install))
Example [minimal conf file][conf_minimal], and [conf file with all options described in full][conf].

## Feedbacks and contributions

* **The user discussions, development, announcements and all the exciting stuff take
place on the mailing list.** While not mandatory to send emails, you can
[subscribe to the Mailing List here][mailing_list],
and [read/search the Mailing List Archive][mailing_list_archive].

* Bugs, issues and contributions can be requested to both the mailing list or the
[official Github project][offlineimap].  Open a [new issue][issues_new], and provide the following information:
- system/distribution (with version)
- offlineimap version (`offlineimap -V`)
- Python version
- server name or domain
- CLI options
- Configuration file (`~/.offlineimaprc`)
- pythonfile (if any)
- Logs, error
- Steps to reproduce the error

* Have a look at the ["To Do" list][todo], and the ["need contributor!" issues][issues_need_contrib], 
then, contribute your code to solve the issue by [opening a pull request][pull_request_new].
* Remember to heed the [Code of Conduct][code_of_conduct].

## The community

* OfflineIMAP's main site is the [project page at Github][offlineimap].
* There is the [OfflineIMAP community's website][website].
* And finally, [the wiki][wiki].


## Requirements & dependencies

* Python v2.7+
* Python v3.4+ ***[STALLED](experimental: [see known issues](https://github.com/OfflineIMAP/offlineimap/issues?q=is%3Aissue+is%3Aopen+label%3APy3))***
* six (required)
* imaplib2 >= 2.57 (optional)
* gssapi (optional), for Kerberos login authentication.


## Documentation

* All current and updated documentation is on the [community's website][website].
* The current [Change Log][changelog].

### Read documentation locally

You might want to read the documentation locally. Get the sources of the website.
For the other documentation, run the appropriate make target:

```sh
$ ./scripts/get-repository.sh website
$ cd docs
$ make html  # Requires rst2html
$ make man   # Requires a2x (http://asciidoc.org)
$ make api   # Requires sphinx
```

# Maintainers

Our current list of [Maintainers][maintainers].

# Contributors

OfflineIMAP exists thanks to [all the people who contribute](https://github.com/OfflineIMAP/offlineimap/graphs/contributors).

[How To Contribute](CONTRIBUTING.rst).

