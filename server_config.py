import os, sys, shutil

# Nonstandard to avoid depend loop
from logger import BotLogger

syslog = BotLogger("system_log.txt")


def check(fn):
    if os.path.exists(fn):
        return True
    else:
        return False


class simpledb:
    def __init__(self):
        self.dbroot = "server-data/"
        if not check(self.dbroot):
            os.makedirs(self.dbroot)

    def get(self, server, key):
        serverdb = self.dbroot + server
        keyp = serverdb + "/" + key
        if not check(serverdb):
            return "NOT SET"
        else:
            if not check(keyp):
                return "NOT SET"
            else:
                with open(keyp) as f:
                    return str(f.read())

    def set(self, server, key, value):
        serverdb = self.dbroot + server
        keyp = serverdb + "/" + key
        if not check(serverdb):
            os.makedirs(serverdb)
        with open(keyp, "w") as f:
            f.write(str(value))

    def exists(self, server):
        serverdb = self.dbroot + server
        if check(serverdb):
            return True
        else:
            return False

    def erase(self, server):
        serverdb = self.dbroot + server
        if self.exists(server):
            shutil.rmtree(serverdb)

    def listdata(self, server):
        serverdb = self.dbroot + server
        if self.exists(server):
            data = ""
            for f in os.listdir(serverdb):
                if f != "blank":
                    data += f + " : " + open(serverdb + "/" + f).read() + "\n"
            return data
        else:
            return "No DB for " + server


# ____________________________________________


class serverconfig:
    def __init__(self):
        self.db = simpledb()

    def showdata(self, server):
        server = str(server)
        data = self.db.listdata(server)
        out = "Data for `" + server + "`:\n```" + data + "```"
        return out

    def checkinit(self, server):
        server = str(server)
        if self.db.exists(server):
            return True
        else:
            self.db.set(server, "blank", "blank")
            return False

    def getstring(self, server, key):
        server = str(server)
        return self.db.get(server, key)

    def getint(self, server, key):
        server = str(server)
        val = self.db.get(server, key)
        if val == "NOT SET":
            return -1
        else:
            return int(self.db.get(server, key))

    def getbool(self, server, key):
        server = str(server)
        val = self.db.get(server, key)
        if val == "NOT SET":
            return False
        else:
            if "true" in self.db.get(server, key):
                return True
            else:
                return False

    def set(self, server, key, value):
        server = str(server)
        key = str(key)
        value = str(value)
        self.db.set(server, key, value)

    def rs(self, server):
        server = str(server)
        self.db.erase(server)


# GUILD ID:
#    - mods
#    - swears_censored
#    - require_privileges
#    - announcements
