#!/usr/bin/python3

"""

Put into Public Domain, by Nicolas Sebrecht.

Produce the "upcoming release" notes.

"""

from os import system

from helpers import (
    MAILING_LIST, CACHEDIR, EDITOR, Testers, Git, OfflineimapInfo, User
)



UPCOMING_FILE = "{}/upcoming.txt".format(CACHEDIR)
UPCOMING_HEADER = "{}/upcoming-header.txt".format(CACHEDIR)

# Header is like:
#
#Message-Id: <{messageId}>
#Date: {date}
#From: {name} <{email}>
#To: {mailinglist}
#Cc: {ccList}
#Subject: [ANNOUNCE] upcoming offlineimap v{expectedVersion}
#
## Notes
#
#I think it's time for a new release.
#
#I aim to make the new release in one week, approximately. If you'd like more
#time, please let me know. ,-)
#
#Please, send me a mail to confirm it works for you. This will be written in the
#release notes and the git logs.
#
#
## Authors
#


if __name__ == '__main__':
    offlineimapInfo = OfflineimapInfo()

    print("Will read headers from {}".format(UPCOMING_HEADER))
    Git.chdirToRepositoryTopLevel()
    oVersion = offlineimapInfo.getVersion()
    ccList = Testers.listTestersInTeam()
    authors = Git.getAuthorsList(oVersion)
    for author in authors:
        email = author.getEmail()
        if email not in ccList:
            ccList.append(email)

    with open(UPCOMING_FILE, 'w') as upcoming, \
         open(UPCOMING_HEADER, 'r') as fd_header:
        header = {}

        header['messageId'] = Git.buildMessageId()
        header['date'] = Git.buildDate()
        header['name'], header['email'] = Git.getLocalUser()
        header['mailinglist'] = MAILING_LIST
        header['expectedVersion'] = User.request("Expected new version?")
        header['ccList'] = ", ".join(ccList)

        upcoming.write(fd_header.read().format(**header).lstrip())
        upcoming.write(Git.getShortlog(oVersion))

        upcoming.write("\n\n# Diffstat\n\n")
        upcoming.write(Git.getDiffstat(oVersion))
        upcoming.write("\n\n\n-- \n{}\n".format(Git.getLocalUser()[0]))

    system("{} {}".format(EDITOR, UPCOMING_FILE))
    print("{} written".format(UPCOMING_FILE))
