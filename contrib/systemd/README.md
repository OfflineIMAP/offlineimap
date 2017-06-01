---
layout: page
title: Integrating OfflineIMAP into systemd
author: Ben Boeckel
date: 2015-03-22
contributors: Abdo Roig-Maranges, benutzer193
updated: 2017-06-01
---

<!-- This file is copied to the website by script. -->


## Systemd units

These unit files are meant to be used in the user session. You may drop them
into `/etc/systemd/user` or `${XDG_DATA_HOME}/systemd/user` followed by
`systemctl --user daemon-reload` to have systemd aware of the unit files.

These files are meant to be triggered either manually using `systemctl --user
start offlineimap.service` or by enabling the timer unit using `systemctl --user
enable offlineimap.timer`. Additionally, specific accounts may be triggered by
using `offlineimap@myaccount.timer` or `offlineimap@myaccount.service`.

These unit files are installed as being enabled via a `mail.target` unit which
is intended to be a catch-all for mail-related unit files. A simple
`mail.target` file is also provided.

If the defaults provided by these units doesn't suit your setup, any of the
values may be overridden by using `systemctl --user edit offlineimap.service`.
This'll prevent having to copy-and-edit the original file.
