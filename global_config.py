import os

# Nonstandard to avoid depend loop
from logger import BotLogger

syslog = BotLogger("system_log.txt")


def check(fn):
    if os.path.exists(fn):
        return True
    else:
        return False


class configboi:
    def __init__(self, fn, logging=True):
        self.config = {}
        if not check(fn):
            if logging:
                syslog.log("Config", "No config found!")
        else:
            if logging:
                syslog.log("Config", "----- Loading config values -----")
            with open(fn) as f:
                config_lines = f.read().split("\n")
            for line in config_lines:
                if line != "" and line != "\n":
                    if line[0] != "#":
                        bits = line.split(":")
                        key = bits[0]
                        val = bits[1]
                        if logging:
                            syslog.log("Config", "Added " + key + ": " + val)
                        self.config[key] = val
            self.islogging = logging

    def reloadconfig(self):
        if not check(fn):
            if self.logging:
                syslog.log("Config", "No config found!")
        else:
            if self.logging:
                syslog.log("Config", "----- Loading config values -----")
            with open(fn) as f:
                config_lines = f.read().split("\n")
            for line in config_lines:
                if line != "" and line != "\n":
                    if line[0] != "#":
                        bits = line.split(":")
                        key = bits[0]
                        val = bits[1]
                        if self.logging:
                            syslog.log("Config", "Added " + key + ": " + val)
                        self.config[key] = val

    def get(self, key):
        if key in self.config:
            return self.config[key].replace("//", "://")
        else:
            return "Not found"

    def getasint(self, key):
        if key in self.config:
            return int(self.config[key])
        else:
            return 0

    def getasbool(self, key):
        if key in self.config:
            result = self.config[key]
            if result == "true" or result == "True":
                return True
            else:
                return False
        else:
            return False

    def getaslist(self, key):
        if key in self.config:
            if "," in self.config[key]:
                return self.config[key].split(",")
            else:
                return [self.config[key]]
        else:
            return None

    def getasintlist(self, key):
        if key in self.config:
            if "," in self.config[key]:
                data = self.config[key].split(",")
                newdata = []
                for item in data:
                    newdata.append(int(item))
                return newdata
            else:
                return [int(self.config[key])]
        else:
            return [0]
