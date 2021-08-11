import os, sys

from mailer import BotMailer

FROM_EMAIL = "mcompton2002@gmail.com"
TO_EMAIL = "3019745990@vtext.com"


def getstamp():
    if sys.platform != "win32":
        os.system("date >> stamp")
        with open("stamp") as f:
            s = f.read()
        os.remove("stamp")
        return s
    else:
        return ""


class BotLogger:
    def __init__(self, filename):
        self.fn = filename
        self.mailer = BotMailer(
            FROM_EMAIL,
            open("emailpass.txt").read().strip(),
            TO_EMAIL,
        )

    def log(self, caller, text):
        info = getstamp().strip() + " --> " + caller + ": " + text
        with open(self.fn, "a+") as f:
            f.write("\n" + info + "\n")
        print(info)
        if (
            "error" in info.lower()
            or "warning" in info.lower()
            or "important" in caller.lower()
        ):
            self.mailer.send("Discord Bot Logger", info)

    def getlog(self):
        with open(self.fn) as f:
            return f.read()
