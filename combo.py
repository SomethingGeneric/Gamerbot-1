#!/usr/bin/env python3

# Token is BOTTOKEN in env-vars
# E.G. "BOTTOKEN=<something> python3 combo.py"

# Standard python imports
import os, string, unicodedata, sys, re, random, time, datetime, subprocess, json, traceback
import urllib.parse
import importlib

from os import listdir
from os.path import isfile, join

# Discord.py
import discord
from discord.ext import commands

# Kind've discord related
from pretty_help import DefaultMenu, PrettyHelp

# Other pip packages
from PIL import Image, ImageDraw, ImageFont
from better_profanity import profanity
import asyncio
import requests

# My own classes n such
from global_config import configboi
from util_functions import *

from server_config import serverconfig

sconf = serverconfig()

profanity.load_censor_words(
    whitelist_words=open("whitelist_words.txt").read().split("\n")
)

profanity.add_censor_words(open("blacklist_words.txt").read().split("\n"))

intents = discord.Intents.default()
intents.members = True

# Start event handling and bot creation
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("-"),
    description="It's always gamer hour",
    intents=intents,
)

helpmenu = DefaultMenu("◀️", "▶️", "❌")
bot.help_command = PrettyHelp(no_category='Commands', navigation=helpmenu, color=discord.Colour.blurple())

# Startup event
@bot.event
async def on_ready():
    syslog.log("Main-Important", "Bot has restarted at " + getstamp())
    syslog.log("Main", f"\n{bot.user} has connected to Discord!\n")

    if check("restarted.txt"):
        channel = get("restarted.txt")
        chan = bot.get_channel(int(channel))
        await chan.send(
            embed=infmsg("System", "Finished restarting at: `" + getstamp() + "`")
        )
        os.remove("restarted.txt")

    ownerman = await bot.fetch_user(OWNER)

    notifyowner = confmgr.getasbool("OWNER_DM_RESTART")

    cogs_dir = "cogs"
    for extension in [
        f.replace(".py", "") for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))
    ]:
        try:
            bot.load_extension(cogs_dir + "." + extension)
            syslog.log("Main", "Loaded " + extension)
            # await ownerman.send(embed=infmsg("System","Loaded `" + extension + "`"))
        except (discord.ClientException, ModuleNotFoundError) as e:
            await ownerman.send(
                embed=errmsg(
                    "System", "Error from cog: " + extension + ": ```" + str(e) + "```"
                )
            )
            syslog.log("Main", f"Failed to load extension {extension}.")
            traceback.print_exc()

    if notifyowner:
        await ownerman.send(
            embed=infmsg("System", "Started/restarted at: `" + getstamp() + "`")
        )


@bot.event
async def on_message(message):

    if message.author != bot.user:

        wasRude = False

        if not isinstance(message.channel, discord.channel.DMChannel):
            if sconf.getbool(message.guild.id, "swears_censored"):
                mc = message.content.lower()
                if profanity.contains_profanity(mc):
                    await message.delete()
                    await message.channel.send(
                        message.author.mention
                        + ": "
                        + str(profanity.censor(message.content))
                    )

                    wasRude = True

        listw = message.content.split(" ")
        links = ""
        hasl = False
        for word in listw:
            # Match any link
            if re.match("((http:\/\/)|(https:\/\/))\S*", word):
                hasl = True
                links += word + "\n"

        if hasl:
            save(
                "link_log.txt",
                "Links from " + message.author.display_name + ": " + links.strip(),
            )

        mc = message.content
        if "bot" in mc:
            # we're being talked to
            if "bad" in mc or "sucks" in mc:
                await message.channel.send(":(")

        if not wasRude:
            await bot.process_commands(message)
            syslog.log(
                "Main", "Finished processing commands in: '" + message.content + "'"
            )


@bot.event
async def on_message_edit(before, after):
    if not isinstance(after.channel, discord.channel.DMChannel):
        if sconf.getbool(after.guild.id, "swears_censored"):
            mc = after.content.lower()
            if profanity.contains_profanity(mc):
                await after.delete()
                await after.channel.send(
                    after.author.mention + ": " + str(profanity.censor(after.content))
                )


"""
@bot.event
async def on_member_join(member):
    # do something
"""


@bot.event
async def on_command_error(ctx, error):
    """
    ownerman = await bot.fetch_user(OWNER)
    if isinstance(error, commands.errors.CheckFailure):
        await ownerman.send(embed=errmsg("Oopsies", "```" + str(error) + "```"))
    else:
        await ownerman.send(embed=errmsg("Oopsies", "```" + str(error) + "```"))
    """
    await ctx.send(embed=errmsg("Error", "```" + str(error) + "```"))


@bot.command()
async def removecog(ctx, name):
    """Un-load a cog that was loaded by default. """
    if ctx.message.author.id in MOD_IDS:
        await ctx.send(embed=infmsg("Gotcha", "Ok, I'll try to disable `" + name + "`"))
        try:
            bot.remove_cog(name)
            syslog.log("Main", "Disabled cog: " + name)
            await ctx.send(embed=warnmsg("Done", "Disabled: `" + name + "`."))
        except Exception as e:
            await ctx.send(
                embed=errmsg("Broke", "Something went wrong: `" + str(e) + "`.")
            )
    else:
        await ctx.send(embed=errmsg("Oops", wrongperms("removecog")))


@bot.command()
async def getsyslog(ctx):
    """Get a copy of the system log"""
    if ctx.message.author.id in MOD_IDS:
        log = syslog.getlog()
        if len(log) > 1994:
            text = paste(log)
            await ctx.send(embed=infmsg("Output", text))
        else:
            text = "```" + log + "```"
            await ctx.send("Here you go:")
            await ctx.send(text)
    else:
        await ctx.send(embed=errmsg("Oops", wrongperms("getsyslog")))


if UNLOAD_COGS is not None:
    # Remove any cogs as per config
    for item in UNLOAD_COGS:
        syslog.log("Main", "Trying to remove '" + item + "'")
        try:
            bot.remove_cog(item)
            syslog.log("Main", "Removed '" + item + "'")
        except:
            syslog.log("Main", "Failed to remove '" + item + "'")

bot.run(os.environ["bottoken"])
