#!/usr/bin/python3

"""

Put into Public Domain, by Nicolas Sebrecht.

Manage the feedbacks of the testers for the release notes.

"""

from os import system
import argparse

from helpers import CACHEDIR, EDITOR, Testers, User, Git


class App(object):
    def __init__(self):
        self.args = None
        self.testers = Testers()
        self.feedbacks = None


    def _getTestersByFeedback(self):
        if self.feedbacks is not None:
            return self.feedbacks

        feedbackOk = []
        feedbackNo = []

        for tester in self.testers.get():
            if tester.getFeedback() is True:
                feedbackOk.append(tester)
            else:
                feedbackNo.append(tester)

        for array in [feedbackOk, feedbackNo]:
            array.sort(key=lambda t: t.getName())

        self.feedbacks = feedbackOk + feedbackNo

    def parseArgs(self):
        parser = argparse.ArgumentParser(description='Manage the feedbacks.')

        parser.add_argument('--add', '-a', dest='add_tester',
                help='Add tester')
        parser.add_argument('--delete', '-d', dest='delete_tester',
                type=int,
                help='Delete tester NUMBER')
        parser.add_argument('--list', '-l', dest='list_all_testers',
                action='store_true',
                help='List the testers')
        parser.add_argument('--switchFeedback', '-s', dest='switch_feedback',
                action='store_true',
                help='Switch the feedback of a tester')

        self.args = parser.parse_args()

    def run(self):
        if self.args.list_all_testers is True:
            self.listTesters()
        if self.args.switch_feedback is True:
            self.switchFeedback()
        elif self.args.add_tester:
            self.addTester(self.args.add_tester)
        elif type(self.args.delete_tester) == int:
            self.deleteTester(self.args.delete_tester)

    def addTester(self, strTester):
        try:
            splitted = strTester.split('<')
            name = splitted[0].strip()
            email = "<{}".format(splitted[1]).strip()
        except Exception as e:
            print(e)
            print("expected format is: 'Firstname Lastname <email>'")
            exit(2)
        self.testers.add(name, email)
        self.testers.write()

    def deleteTester(self, number):
        self.listTesters()
        removed = self.feedbacks.pop(number)
        self.testers.remove(removed)

        print("New list:")
        self.feedbacks = None
        self.listTesters()
        print("Removed: {}".format(removed))
        ans = User.request("Save on disk? (s/Q)").lower()
        if ans in ['s']:
            self.testers.write()


    def listTesters(self):
        self._getTestersByFeedback()

        count = 0
        for tester in self.feedbacks:
            feedback = "ok"
            if tester.getFeedback() is not True:
                feedback = "no"
            print("{:02d} - {} {}: {}".format(
                    count, tester.getName(), tester.getEmail(), feedback
                )
            )
            count += 1

    def switchFeedback(self):
        self._getTestersByFeedback()
        msg = "Switch tester: [<number>/s/q]"

        self.listTesters()
        number = User.request(msg)
        while number.lower() not in ['s', 'save', 'q', 'quit']:
            if number == '':
                continue
            try:
                number = int(number)
                self.feedbacks[number].switchFeedback()
            except (ValueError, IndexError) as e:
                print(e)
                exit(1)
            finally:
                self.listTesters()
                number = User.request(msg)
        if number in ['s', 'save']:
            self.testers.write()
        self.listTesters()

    def reset(self):
        self.testers.reset()
        self.testers.write()

    #def updateMailaliases(self):

if __name__ == '__main__':
    Git.chdirToRepositoryTopLevel()

    app = App()
    app.parseArgs()
    app.run()
