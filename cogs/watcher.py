import os

import discord
from discord.ext import commands, tasks

from util_functions import *
from global_config import configboi
from server_config import serverconfig

class monitor:
    def __init__(self,server,channel,find,ping):
        self.server = server
        self.channel = channel
        self.find = find
        self.ping = ping

class Watcher(commands.Cog):
    """Watches for messages in channels and pings specified role"""

    def __init__(self, bot):
        self.bot = bot
        self.confmgr = configboi("config.txt", False)
        self.sconf = serverconfig()
        self.data = []
        self.seen = []
        if os.path.exists(".sent_messages"):
            with open(".sent_messages") as f:
                seen = f.read().split("\n")
                for id in seen:
                    self.seen.append(id)
        self.refresh_data()

    def refresh_data(self):
        for server in self.bot.guilds:
            watched = self.sconf.getstring(server.id, "watched_channels")
            if watched != "NOT SET":
                if ";" not in watched:
                    pass
                else:
                    sets = watched.split(";")
                    for set in sets:
                        if "," in set:
                            data = set.split(",")
                            m = monitor(int(data[0]),int(data[1]),data[2],int(data[3]))
                            self.data.append(m)


    @commands.Cog.listener()
    async def on_message(self, message):
        self.refresh_data()
        for obj in self.data:
            if message.channel.id == obj.channel:
                if obj.find in message.content.lower() and message.id not in self.seen:
                    role = message.guild.get_role(obj.ping)
                    mention = role.mention
                    await message.channel.send(mention + " get in here!")
                    self.seen.append(message.id)
                    with open(".sent_messages","a+") as f:
                        f.write(str(message.id) + "\n")

def setup(bot):
    bot.add_cog(Watcher(bot))
