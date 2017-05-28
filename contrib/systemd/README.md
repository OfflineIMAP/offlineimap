---
layout: page
title: Integrating OfflineIMAP into systemd
author: Ben Boeckel
date: 2015-03-22
contributors: Abdo Roig-Maranges
updated: 2015-03-25
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

## Signals

Systemd supports a watchdog (via the WatchdogSec service file option) which
will send the program a SIGABRT when the timer expires.

Offlineimap handles it in the same manner as SIGUSR2, so that the current
synchronisation is completed before the program exits safely.

This makes offlineimap more flexible and robust for persistent setups that make
use of holdconnectionopen and autorefresh options.

For example, it may be useful in assisting with the occasional situation where
offlineimap may not return successfully after a suspend and resume.

To make use of this, users could add the following to the [Service] section of
their systemd offlineimap service file (restart every 5 minutes):

``` conf
Restart=on-watchdog
WatchdogSec=300
```

