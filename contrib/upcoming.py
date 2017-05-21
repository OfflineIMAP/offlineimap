#!/usr/bin/python3

"""

Put into Public Domain, by Nicolas Sebrecht.

Produce the "upcoming release" notes.

"""

from os import chdir, system
from os.path import expanduser
import shlex
from subprocess import check_output


__VERSION__ = "0.1"

FS_ENCODING = 'UTF-8'
ENCODING = 'UTF-8'

MAILING_LIST = 'offlineimap-project@lists.alioth.debian.org'
CACHEDIR = '.git/offlineimap-release'
UPCOMING_FILE = "{}/upcoming.txt".format(CACHEDIR)
EDITOR = 'vim'
MAILALIASES_FILE = expanduser('~/.mutt/mail_aliases')

UPCOMING_HEADER = """
Message-Id: <{messageId}>
Date: {date}
From: {name} <{email}>
To: {mailinglist}
Cc: {ccList}
Subject: [ANNOUNCE] upcoming offlineimap v{expectedVersion}

# Notes

I think it's time for a new release.

I aim to make the new release in one week, approximately. If you'd like more
time, please let me know. ,-)


# Authors

"""


def run(cmd):
    return check_output(cmd, timeout=5).rstrip()


def getTesters():
    """Returns a list of emails extracted from my mailaliases file."""

    cmd = shlex.split("grep offlineimap-testers {}".format(MAILALIASES_FILE))
    output = run(cmd).decode(ENCODING)
    emails = output.lstrip("alias offlineimap-testers ").split(', ')
    return emails


class Author(object):
    def __init__(self, name, count, email):
        self.name = name
        self.count = count
        self.email = email

    def getName(self):
        return self.name

    def getCount(self):
        return self.count

    def getEmail(self):
        return self.email


class Git(object):
    @staticmethod
    def getShortlog(ref):
        shortlog = ""

        cmd = shlex.split("git shortlog --no-merges -n v{}..".format(ref))
        output = run(cmd).decode(ENCODING)

        for line in output.split("\n"):
            if len(line) > 0:
                if line[0] != " ":
                    line = "  {}\n".format(line)
                else:
                    line = "     {}\n".format(line.lstrip())
            else:
                line = "\n"

            shortlog += line

        return shortlog

    @staticmethod
    def getDiffstat(ref):
        cmd = shlex.split("git diff --stat v{}..".format(ref))
        return run(cmd).decode(ENCODING)

    @staticmethod
    def buildMessageId():
        cmd = shlex.split(
            "git log HEAD~1.. --oneline --pretty='%H.%t.upcoming.%ce'")
        return run(cmd).decode(ENCODING)

    @staticmethod
    def getLocalUser():
        cmd = shlex.split("git config --get user.name")
        name = run(cmd).decode(ENCODING)
        cmd = shlex.split("git config --get user.email")
        email = run(cmd).decode(ENCODING)
        return name, email

    @staticmethod
    def buildDate():
        cmd = shlex.split("git log HEAD~1.. --oneline --pretty='%cD'")
        return run(cmd).decode(ENCODING)

    @staticmethod
    def getAuthors(ref):
        authors = []

        cmd = shlex.split("git shortlog --no-merges -sne v{}..".format(ref))
        output = run(cmd).decode(ENCODING)

        for line in output.split("\n"):
            count, full = line.strip().split("\t")
            full = full.split(' ')
            name = ' '.join(full[:-1])
            email = full[-1]

            authors.append(Author(name, count, email))

        return authors

    @staticmethod
    def chdirToRepositoryTopLevel():
        cmd = shlex.split("git rev-parse --show-toplevel")
        topLevel = run(cmd)

        chdir(topLevel)


class OfflineimapInfo(object):
    def __init__(self):
        self.version = None

    def getCurrentVersion(self):
        if self.version is None:
            cmd = shlex.split("./offlineimap.py --version")
            self.version = run(cmd).rstrip().decode(FS_ENCODING)
        return self.version


class User(object):
    """Interact with the user."""

    prompt = '-> '

    @staticmethod
    def request(msg):
        print(msg)
        return input(User.prompt)


if __name__ == '__main__':
    offlineimapInfo = OfflineimapInfo()

    Git.chdirToRepositoryTopLevel()
    oVersion = offlineimapInfo.getCurrentVersion()
    ccList = getTesters()
    authors = Git.getAuthors(oVersion)
    for author in authors:
        email = author.getEmail()
        if email not in ccList:
            ccList.append(email)

    with open(UPCOMING_FILE, 'w') as upcoming:
        header = {}

        header['messageId'] = Git.buildMessageId()
        header['date'] = Git.buildDate()
        header['name'], header['email'] = Git.getLocalUser()
        header['mailinglist'] = MAILING_LIST
        header['expectedVersion'] = User.request("Expected new version?")
        header['ccList'] = ", ".join(ccList)

        upcoming.write(UPCOMING_HEADER.format(**header).lstrip())
        upcoming.write(Git.getShortlog(oVersion))

        upcoming.write("\n\n# Diffstat\n\n")
        upcoming.write(Git.getDiffstat(oVersion))
        upcoming.write("\n\n\n-- \n{}\n".format(Git.getLocalUser()[0]))

    system("{} {}".format(EDITOR, UPCOMING_FILE))
