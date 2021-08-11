import sys, datetime

import discord
from discord.ext import commands, tasks

from global_config import configboi

from util_functions import *


class Status(commands.Cog):
    """This cog keeps the bot status in sync"""

    def __init__(self, bot):
        self.bot = bot
        self.confmgr = configboi("config.txt", False)

        self.status_task.start()
        self.uptime_logger.start()

        self.upt = 0

    def cog_unload(self):
        self.status_task.cancel()

    async def setDefaultStatus(self):
        if self.confmgr.get("DEFAULT_STATUS_TYPE") == "watching":
            ac_type = discord.ActivityType.watching
        elif self.confmgr.get("DEFAULT_STATUS_TYPE") == "listening":
            ac_type = discord.ActivityType.listening
        else:
            syslog.log(
                "Bot Status", "Please check DEFAULT_STATUS_TYPE in config.txt! Exiting!"
            )
            sys.exit(1)

        total = 0
        if "{number_users}" in self.confmgr.get("DEFAULT_STATUS_TEXT"):
            guilds = self.bot.guilds
            for guild in guilds:
                total += guild.member_count

        await self.bot.change_presence(
            activity=discord.Activity(
                type=ac_type,
                name=self.confmgr.get("DEFAULT_STATUS_TEXT")
                .replace("{guild_count}", str(len(list(self.bot.guilds))))
                .replace("{number_users}", str(total)),
            )
        )

    @commands.Cog.listener()
    async def on_ready(self):
        syslog.log("Bot Status", "Setting default status as per config")
        await self.setDefaultStatus()

    @tasks.loop(seconds=60.0)
    async def status_task(self):
        await self.setDefaultStatus()

    @status_task.before_loop
    async def before_status_task(self):
        syslog.log(
            "Bot Status", "Waiting for bot to be ready before starting updater task"
        )
        await self.bot.wait_until_ready()
        syslog.log("Bot Status", "Bot is ready. Enabling update task")

    @tasks.loop(seconds=1.0)
    async def uptime_logger(self):
        self.upt += 1

    @uptime_logger.before_loop
    async def before_logger_task(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def getuptime(self, ctx):
        await ctx.send(
            embed=infmsg(
                "Bot Stats",
                "Uptime: `" + str(datetime.timedelta(seconds=self.upt)) + "`",
            )
        )


def setup(bot):
    bot.add_cog(Status(bot))
