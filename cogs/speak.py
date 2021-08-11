# System
import os, random

# Pip
import discord
from discord.ext import commands
import asyncio

# Mine
from channel_state import VoiceState
from util_functions import *
from server_config import serverconfig


class Speak(commands.Cog):
    """Text to speech go brr"""

    def __init__(self, bot):

        self.sconf = serverconfig
        self.vs = VoiceState()

        self.bot = bot
        self.voice_client = None
        self.audiosrc = None
        self.isDone = False

        syslog.log("Speak-Client", "Instance created and setup")

    def setDone(self):
        self.isDone = True

    async def speakInChannel(self, ctx, text, chan=None, stealth=False):
        if self.voice_client is None and not self.vs.check_state():
            syslog.log(
                "Speak-Client",
                "This cog was not playing, nor were others. It's go time.",
            )

            try:

                if ctx.author.voice is not None:
                    channel = ctx.author.voice.channel
                else:
                    channel = self.bot.get_channel(int(chan))

                if channel is not None:
                    syslog.log(
                        "Speak-Client",
                        "The author is in a channel, so we're attempting to join them.",
                    )
                    await run_command_shell('espeak -w espeak.wav "' + text + '"')
                    syslog.log(
                        "Speak-Client", "We have the TTS audio file ready. Playing it."
                    )
                    self.voice_client = await channel.connect()
                    self.vs.set_state("1")
                    syslog.log("Speak-Client", "We're in voice now.")
                    self.audiosrc = discord.FFmpegPCMAudio("espeak.wav")
                    self.isDone = False
                    self.voice_client.play(
                        self.audiosrc,
                        after=lambda e: print("Player error: %s" % e)
                        if e
                        else self.setDone(),
                    )
                    while self.voice_client.is_playing():
                        self.isDone = False
                        if self.isDone == True:
                            break
                        await asyncio.sleep(1)
                    syslog.log("Speak-Client", "We're done playing. Cleaning up.")

                    await self.voice_client.disconnect()
                    self.voice_client = None
                    self.audiosrc = None
                    self.isDone = True
                    await run_command_shell("rm espeak.wav")
                    self.vs.set_state("0")
                    syslog.log("Speak-Client", "We're done cleaning up. All done!")
                    if stealth:
                        return True
                else:
                    if not stealth:
                        await ctx.send(
                            embed=errmsg(
                                "Spoken Word", "You're not in a voice channel."
                            )
                        )
                    else:
                        return False
            except Exception as e:
                syslog.log("Speak-Client-Important", "Error: " + str(e))
                await ctx.send(embed=errmsg("Spoken Word", "`" + str(e) + "`"))

        else:
            await ctx.send(
                embed=errmsg("Spoken Word", "I'm already in a voice channel, and busy.")
            )
            syslog.log("Speak-Client", "VC is busy somewhere. Doing nothing.")

    @commands.command()
    async def tts(self, ctx, *, thing, stealth=False):
        """Talk in voice channel"""
        if self.sconf.getbool(
            ctx.message.guild.id, "swears_censored"
        ) and profanity.contains_profanity(text):
            await ctx.message.delete()
            await ctx.send(
                embed=errmsg(
                    "Error",
                    "This server does not allow profanity.",
                )
            )
        else:
            syslog.log(
                "Speak-Client", "Calling speakInChannel for " + ctx.author.display_name
            )
            await self.speakInChannel(ctx, thing, None, False)

    @commands.command()
    async def vcask(self, ctx, *, query):
        """Tuxi output in VC"""

        if self.sconf.getbool(
            ctx.message.guild.id, "swears_censored"
        ) and profanity.contains_profanity(text):
            await ctx.message.delete()
            await ctx.send(
                embed=errmsg(
                    "Error",
                    "This server does not allow profanity.",
                )
            )
        else:
            syslog.log(
                "Speak-Client", "Calling speakInChannel for " + ctx.author.display_name
            )
            try:
                query = query.replace("&", "").replace(";", "")
                thing = await run_command_shell('./tuxi -r "' + query + '"')

                await ctx.send(embed=infmsg("Tuxi Result", "```" + thing + "```"))
                if not "no result" in thing.lower():
                    await self.speakInChannel(ctx, query + " is " + thing, None, False)
                else:
                    await self.speakInChannel(
                        ctx,
                        "Tuxi had no good results. The links are in chat",
                        None,
                        False,
                    )
            except Exception as e:
                await self.speakInChannel(ctx, "We had an issue with tuxi: " + str(e))
                await ctx.send(
                    embed=errmsg(
                        "Spoken Word - Tuxi", "We had an issue with tuxi: " + str(e)
                    )
                )

    @commands.Cog.listener()
    async def on_message(self, message):
        if " bee " in message.content.lower() or " bees " in message.content.lower():
            syslog.log("Speak-Memes", "BEE MOVIE ALERT!!")
            with open("bee.txt") as f:
                quote = random.choice(f.read().split("\n"))
                if message.author.voice is not None:
                    ctx = await self.bot.get_context(message)
                    syslog.log("Speak-Client", "Initializing meme session")
                    tried = await self.speakInChannel(ctx, quote, None, True)
                    if tried:
                        syslog.log(
                            "Speak-Memes", "SPOKE BEE MOVIE QUOTE IN VOICE CHANNEL!!"
                        )
                    else:
                        syslog.log(
                            "Speak-Client",
                            "Falling back to text since voice is too busy for memes.",
                        )
                        await message.channel.send("`" + quote + "`")
                        syslog.log("Speak-Memes", "SENT BEE MOVIE QUOTE IN TEXT CHAT")
                else:
                    syslog.log(
                        "Speak-Client",
                        "Falling back to text since voice is too busy for memes. (Voice not attempted)",
                    )
                    await message.channel.send("`" + quote + "`")
                    syslog.log("Speak-Memes", "SENT BEE MOVIE QUOTE IN TEXT CHAT")


def setup(bot):
    bot.add_cog(Speak(bot))
