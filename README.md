Upstream status (`master` branch):
[![OfflineIMAP build status on Travis-CI.org](https://travis-ci.org/OfflineIMAP/offlineimap.svg?branch=master)](https://travis-ci.org/OfflineIMAP/offlineimap)
[![OfflineIMAP code coverage on Codecov.io](https://codecov.io/gh/OfflineIMAP/offlineimap/branch/master/graph/badge.svg)](https://codecov.io/gh/OfflineIMAP/offlineimap)
[![Gitter chat](https://badges.gitter.im/OfflineIMAP/offlineimap.png)](https://gitter.im/OfflineIMAP/offlineimap)

Upstream status (`next` branch):
[![OfflineIMAP build status on Travis-CI.org](https://travis-ci.org/OfflineIMAP/offlineimap.svg?branch=next)](https://travis-ci.org/OfflineIMAP/offlineimap)

Financial contributors: [![Financial Contributors on Open Collective](https://opencollective.com/offlineimap-organization/all/badge.svg?label=financial+contributors)](https://opencollective.com/offlineimap-organization) 

[offlineimap]: http://github.com/OfflineIMAP/offlineimap
[offlineimap3]: http://github.com/OfflineIMAP/offlineimap3
[website]: http://www.offlineimap.org
[wiki]: http://github.com/OfflineIMAP/offlineimap/wiki
[blog]: http://www.offlineimap.org/posts.html

Links:
* Official github code repository: [offlineimap]
* Website: [website]
* Wiki: [wiki]
* Blog: [blog]

# OfflineIMAP

***"Get the emails where you need them."***

[Official offlineimap for python2][offlineimap].
[Official offlineimap for python3][offlineimap3].


## Description

OfflineIMAP is software that downloads your email mailbox(es) as **local
Maildirs**. OfflineIMAP will synchronize both sides via *IMAP*.

## Why should I use OfflineIMAP?

IMAP's main downside is that you have to **trust** your email provider to
not lose your email. While certainly unlikely, it's not impossible.
With OfflineIMAP, you can download your Mailboxes and make you own backups of
your [Maildir](https://en.wikipedia.org/wiki/Maildir).

This allows reading your email offline without the need for your mail
reader (MUA) to support IMAP operations. Need an attachment from a
message without internet connection? No problem, the message is still there.


## Project status and future

The [offlineimap][offlineimap] project was forked to
[offlineimap3][offlineimap3] to support python3. Contributions are welcome to
this project.


## Contributors

### Code Contributors

This project exists thanks to all the people who contribute. [[Contribute](CONTRIBUTING.md)].
<a href="https://github.com/OfflineIMAP/offlineimap/graphs/contributors"><img src="https://opencollective.com/offlineimap-organization/contributors.svg?width=890&button=false" /></a>

### Financial Contributors

Become a financial contributor and help us sustain our community. [[Contribute](https://opencollective.com/offlineimap-organization/contribute)]

#### Individuals

<a href="https://opencollective.com/offlineimap-organization"><img src="https://opencollective.com/offlineimap-organization/individuals.svg?width=890"></a>

#### Organizations

Support this project with your organization. Your logo will show up here with a link to your website. [[Contribute](https://opencollective.com/offlineimap-organization/contribute)]

<a href="https://opencollective.com/offlineimap-organization/organization/0/website"><img src="https://opencollective.com/offlineimap-organization/organization/0/avatar.svg"></a>
<a href="https://opencollective.com/offlineimap-organization/organization/1/website"><img src="https://opencollective.com/offlineimap-organization/organization/1/avatar.svg"></a>
<a href="https://opencollective.com/offlineimap-organization/organization/2/website"><img src="https://opencollective.com/offlineimap-organization/organization/2/avatar.svg"></a>
<a href="https://opencollective.com/offlineimap-organization/organization/3/website"><img src="https://opencollective.com/offlineimap-organization/organization/3/avatar.svg"></a>
<a href="https://opencollective.com/offlineimap-organization/organization/4/website"><img src="https://opencollective.com/offlineimap-organization/organization/4/avatar.svg"></a>
<a href="https://opencollective.com/offlineimap-organization/organization/5/website"><img src="https://opencollective.com/offlineimap-organization/organization/5/avatar.svg"></a>
<a href="https://opencollective.com/offlineimap-organization/organization/6/website"><img src="https://opencollective.com/offlineimap-organization/organization/6/avatar.svg"></a>
<a href="https://opencollective.com/offlineimap-organization/organization/7/website"><img src="https://opencollective.com/offlineimap-organization/organization/7/avatar.svg"></a>
<a href="https://opencollective.com/offlineimap-organization/organization/8/website"><img src="https://opencollective.com/offlineimap-organization/organization/8/avatar.svg"></a>
<a href="https://opencollective.com/offlineimap-organization/organization/9/website"><img src="https://opencollective.com/offlineimap-organization/organization/9/avatar.svg"></a>

## License

GNU General Public License v2.


## Downloads

You should first check if your distribution already packages OfflineIMAP for you.
Downloads releases as [tarball or zipball](https://github.com/OfflineIMAP/offlineimap/tags).

If you are running Linux Os, you can install offlineimap with:

-  openSUSE `zypper in offlineimap`
-  Arch Linux `pacman -S offlineimap`
-  fedora `dnf install offlineimap`

## Feedbacks and contributions

**The user discussions, development, announcements and all the exciting stuff take
place on the mailing list.** While not mandatory to send emails, you can
[subscribe here](http://lists.alioth.debian.org/mailman/listinfo/offlineimap-project).

Bugs, issues and contributions can be requested to both the mailing list or the
[official Github project][offlineimap].  Provide the following information:
- system/distribution (with version)
- offlineimap version (`offlineimap -V`)
- Python version
- server name or domain
- CLI options
- Configuration file (offlineimaprc)
- pythonfile (if any)
- Logs, error
- Steps to reproduce the error


## The community

* OfflineIMAP's main site is the [project page at Github][offlineimap].
* There is the [OfflineIMAP community's website][website].
* And finally, [the wiki][wiki].


## Requirements & dependencies

* Python v2.7+
* six (required)
* rfc6555 (required)
* imaplib2 >= 2.57 (optional)
* gssapi (optional), for Kerberos authentication
* portalocker (optional), if you need to run offlineimap in Cygwin for Windows

* Python v3: See the [offlineimap3][offlineimap3] fork of
  [offlineimap][offlineimap].

## Documentation

All current and updated documentation is on the [community's website][website].


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
