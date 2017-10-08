"""

Put into Public Domain, by Nicolas Sebrecht.

Helpers for maintenance scripts.

"""

from os import chdir, makedirs, system, getcwd
from os.path import expanduser
import shlex
from subprocess import check_output, check_call, CalledProcessError

import yaml


FS_ENCODING = 'UTF-8'
ENCODING = 'UTF-8'

MAILING_LIST = 'offlineimap-project@lists.alioth.debian.org'
CACHEDIR = '.git/offlineimap-release'
EDITOR = 'vim'
MAILALIASES_FILE = expanduser('~/.mutt/mail_aliases')
TESTERS_FILE = "{}/testers.yml".format(CACHEDIR)
ME = "Nicolas Sebrecht <nicolas.s-dev@laposte.net>"


def run(cmd):
    return check_output(cmd, timeout=5).rstrip()

def goTo(path):
    try:
        chdir(path)
        return True
    except FileNotFoundError:
        print("Could not find the '{}' directory in '{}'...".format(
            path, getcwd())
        )
    return False


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
    def add(files):
        cmd = shlex.split("git add -- {}".format(files))
        return run(cmd).decode(ENCODING)

    @staticmethod
    def commit(msg):
        cmd = shlex.split("git commit -s -m '{}'".format(msg))
        return run(cmd).decode(ENCODING)

    @staticmethod
    def tag(version):
        cmd = shlex.split("git tag -a 'v{}' -m 'v{}'".format(version, version))
        return run(cmd).decode(ENCODING)

    @staticmethod
    def stash(msg):
        cmd = shlex.split("git stash create '{}'".format(msg))
        return run(cmd).decode(ENCODING)

    @staticmethod
    def mergeFF(ref):
        cmd = shlex.split("git merge --ff '{}'".format(ref))
        return run(cmd).decode(ENCODING)

    @staticmethod
    def getDiffstat(ref):
        cmd = shlex.split("git diff --stat v{}..".format(ref))
        return run(cmd).decode(ENCODING)

    @staticmethod
    def isClean():
        try:
            check_call(shlex.split("git diff --quiet"))
            check_call(shlex.split("git diff --cached --quiet"))
        except CalledProcessError:
            return False
        return True

    @staticmethod
    def buildMessageId():
        cmd = shlex.split(
            "git log HEAD~1.. --oneline --pretty='%H.%t.upcoming.%ce'")
        return run(cmd).decode(ENCODING)

    @staticmethod
    def resetKeep(ref):
        return run(shlex.split("git reset --keep {}".format(ref)))

    @staticmethod
    def getRef(ref):
        return run(shlex.split("git rev-parse {}".format(ref))).rstrip()

    @staticmethod
    def rmTag(tag):
        return run(shlex.split("git tag -d {}".format(tag)))

    @staticmethod
    def checkout(ref, create=False):
        if create:
            create = "-b"
        else:
            create = ""

        cmd = shlex.split("git checkout {} {}".format(create, ref))
        run(cmd)
        head = shlex.split("git rev-parse HEAD")
        revparseRef = shlex.split("git rev-parse {}".format(ref))
        if run(head) != run(revparseRef):
            raise Exception("checkout to '{}' did not work".format(ref))

    @staticmethod
    def makeCacheDir():
        try:
            makedirs(CACHEDIR)
        except FileExistsError:
            pass

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
    def getAuthorsList(sinceRef):
        authors = []

        cmd = shlex.split("git shortlog --no-merges -sne v{}..".format(sinceRef))
        output = run(cmd).decode(ENCODING)

        for line in output.split("\n"):
            count, full = line.strip().split("\t")
            full = full.split(' ')
            name = ' '.join(full[:-1])
            email = full[-1]

            authors.append(Author(name, count, email))

        return authors

    @staticmethod
    def getCommitsList(sinceRef):
        cmd = shlex.split(
            "git log --no-merges --format='- %h %s. [%aN]' v{}..".format(sinceRef)
        )
        return run(cmd).decode(ENCODING)

    @staticmethod
    def chdirToRepositoryTopLevel():
        cmd = shlex.split("git rev-parse --show-toplevel")
        topLevel = run(cmd)

        chdir(topLevel)


class OfflineimapInfo(object):
    def getVersion(self):
        cmd = shlex.split("./offlineimap.py --version")
        return run(cmd).rstrip().decode(FS_ENCODING)

    def editInit(self):
        return system("{} ./offlineimap/__init__.py".format(EDITOR))



class User(object):
    """Interact with the user."""

    @staticmethod
    def request(msg, prompt='--> '):
        print(msg)
        return input(prompt)

    @staticmethod
    def pause(msg=False):
        return User.request(msg, prompt="Press Enter to continue..")

    @staticmethod
    def yesNo(msg, defaultToYes=False, prompt='--> '):
        endMsg = " [y/N]: No"
        if defaultToYes:
            endMsg = " [Y/n]: Yes"
        msg += endMsg
        answer = User.request(msg, prompt).lower()
        if answer in ['y', 'yes']:
            return True
        if defaultToYes is not False and answer not in ['n', 'no']:
            return True
        return False


class Tester(object):
    def __init__(self, name, email, feedback):
        self.name = name
        self.email = email
        self.feedback = feedback

    def __str__(self):
        return "{} {}".format(self.name, self.email)

    def getName(self):
        return self.name

    def getEmail(self):
        return self.email

    def getFeedback(self):
        return self.feedback

    def positiveFeedback(self):
        return self.feedback is True

    def setFeedback(self, feedback):
        assert feedback in [True, False, None]
        self.feedback = feedback

    def switchFeedback(self):
        self.feedback = not self.feedback


class Testers(object):
    def __init__(self):
        self.testers = None
        self._read()

    def _read(self):
        self.testers = []
        with open(TESTERS_FILE, 'r') as fd:
            testers = yaml.load(fd)
            for tester in testers:
                name = tester['name']
                email = tester['email']
                feedback = tester['feedback']
                self.testers.append(Tester(name, email, feedback))
        self.testers.sort(key=lambda x: x.getName().lower())

    @staticmethod
    def listTestersInTeam():
        """Returns a list of emails extracted from my mailaliases file."""

        cmd = shlex.split("grep offlineimap-testers {}".format(MAILALIASES_FILE))
        output = run(cmd).decode(ENCODING)
        emails = output.lstrip("alias offlineimap-testers ").split(', ')
        return emails

    def add(self, name, email, feedback=None):
        self.testers.append(Tester(name, email, feedback))

    def remove(self, tester):
        self.testers.remove(tester)

    def get(self):
        return self.testers

    def getList(self):
        testersList = ""
        for tester in self.testers:
            testersList += "- {}\n".format(tester.getName())
        return testersList

    def getListOk(self):
        testersOk = []
        for tester in self.testers:
            if tester.positiveFeedback():
                testersOk.append(tester)
        return testersOk

    def reset(self):
        for tester in self.testers:
            tester.setFeedback(None)

    def write(self):
        testers = []
        for tester in self.testers:
            testers.append({
                'name': tester.getName(),
                'email': tester.getEmail(),
                'feedback': tester.getFeedback(),
            })
        with open(TESTERS_FILE, 'w') as fd:
            fd.write(yaml.dump(testers))

