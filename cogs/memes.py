import os, re, random

import discord
from discord.ext import commands

import asyncio
from PIL import Image, ImageDraw, ImageFont

from util_functions import *
from server_config import serverconfig

from better_profanity import profanity

profanity.load_censor_words(
    whitelist_words=open("whitelist_words.txt").read().split("\n")
)

profanity.add_censor_words(open("blacklist_words.txt").read().split("\n"))

# Hopefully we'll never need logging here
# (but who knows)

# Start memes
class Memes(commands.Cog):
    """Haha image manipulation go brr"""

    def __init__(self, bot):
        self.bot = bot
        self.sconf = serverconfig()

    @commands.Cog.listener()
    async def on_message(self, message):
        mc = message.content.lower()
        mchan = message.channel

        triggers = {
            "java": "ew gross programming language",
            "scratch": "all my homies hate scratch",
            "tesla": "elon morel like pee-lon",
            "elon": "elon morel like pee-lon",
            "rms": "RMS is a pedo",
            "stallman": "RMS is a pedo",
            "epstein": "He didn't kill himself",
        }

        if message.author != self.bot.user:
            if "hello there" in mc:
                await mchan.send(
                    "General Kenobi\nhttps://media1.giphy.com/media/UIeLsVh8P64G4/giphy.gif"
                )
            else:
                try:
                    if " " in mc:
                        tw = 0
                        act = ""
                        for word in mc.split(" "):
                            if word in triggers:
                                tw += 1
                                act = word
                        if tw == 1:
                            await mchan.send(triggers[act])
                        elif tw > 1:
                            await mchan.send(
                                message.author.mention + " don't be an asshat. :angry:"
                            )
                    else:
                        if mc in triggers:
                            await mchan.send(triggers[mc])
                except Exception as e:
                    await mchan.send(embed=errmsg("Error", "```" + str(e) + "```"))

            stonks = re.findall(r"\$[a-z][a-z][a-z]", mc)
            if stonks != None and message.author.id != self.bot.user.id:
                for stonk in stonks:
                    if stonk == "gme" or stonk == "amc" or stonk == "nok":
                        await mchan.send("🚀 " + stonk.upper() + " TO THE MOON! 🚀")

            if "comrade sharkfact" in mc:
                with open("sharkfacts.txt", encoding="cp1252") as f:
                    sharkList = f.read().split("\n")
                await mchan.send(embed=infmsg("Sharkfact", random.choice(sharkList)))

            if DO_IMAGE_RESPONSE:
                if random.randint(
                    1, IMAGE_RESPONSE_PROB
                ) == IMAGE_RESPONSE_PROB and "filename" in str(message.attachments):
                    await mchan.send(random.choice(IMAGE_RESPONSES))

    @commands.command()
    async def figlet(self, ctx, *, text):
        """Fun text art :)"""
        if self.sconf.getbool(
            ctx.message.guild.id, "swears_censored"
        ) and profanity.contains_profanity(text):
            await ctx.message.delete()
            await ctx.send(
                embed=errmsg(
                    "Error",
                    "This server does not allow profanity. Feel free to run this command in a DM",
                )
            )
        else:
            try:
                out = await run_command_shell("figlet " + text)
                if len(out) < 1994:
                    await ctx.send("```\n " + str(out) + "```")
                else:
                    link = paste(out)
                    await ctx.send(
                        ctx.message.author.mention
                        + ", the figlet output is too long, so here's a link: "
                        + link
                    )
            except Exception as e:
                await ctx.send(
                    embed=errmsg(
                        "Error", "Had an issue running figlet: `" + str(e) + "`"
                    )
                )
                syslog.log(
                    "Memes-Important", "Had an issue running figlet: `" + str(e) + "`"
                )

    @commands.command()
    async def crab(self, ctx):
        """🦀🦀🦀🦀🦀"""
        await ctx.send(
            "https://media.tenor.com/images/a16246936101a550918944740789de8a/tenor.gif",
        )

    @commands.command()
    async def deadchat(self, ctx):
        await ctx.send(
            "https://media.tenor.com/images/f799b7d7993b74a7852e1eaf2695d9d7/tenor.gif",
        )

    @commands.command()
    async def xd(self, ctx):
        """😂😂😂😂😂"""
        await ctx.send(file=discord.File("images/LMAO.jpg"))

    @commands.command()
    async def kat(self, ctx):
        """*sad cat noises*"""
        await ctx.send(file=discord.File("images/krying_kat.png"))

    @commands.command()
    async def yea(self, ctx):
        """it do be like that"""
        await ctx.send(file=discord.File("images/yeah.png"))

    @commands.command()
    async def bonk(self, ctx, *, text=""):
        """Bonk a buddy"""

        if text == "":
            text = ctx.message.author.mention

        if self.sconf.getbool(
            ctx.message.guild.id, "swears_censored"
        ) and profanity.contains_profanity(text):
            await ctx.message.delete()
            await ctx.send(
                embed=errmsg(
                    "Error",
                    "This server does not allow profanity. Feel free to run this command in a DM",
                )
            )
        else:
            newtext = text.strip()
            extra = ""

            if "<@!" in newtext or "<@" in newtext:
                try:
                    pid = newtext.replace("<@!", "").replace("<@", "").replace(">", "")
                    person = await self.bot.fetch_user(int(pid))
                    if person != None:
                        newtext = person.display_name
                        extra = "Get bonked, " + person.mention
                    else:
                        await ctx.send("Had trouble getting a user from: " + text)
                except Exception as e:
                    await ctx.send("We had a failure: `" + str(e) + "`")

            if newtext != "":
                img = Image.open("images/bonk.png")
                bfont = ImageFont.truetype("fonts/arial.ttf", (50 - len(str(newtext))))
                draw = ImageDraw.Draw(img)
                draw.text(
                    (525 - len(str(newtext)) * 5, 300),
                    str(newtext),
                    (0, 0, 0),
                    font=bfont,
                )
                img.save("bonk-s.png")
                await ctx.send(extra, file=discord.File("bonk-s.png"))
                os.remove("bonk-s.png")
            else:
                await ctx.send(file=discord.File("images/bonk.png"))

    @commands.command()
    async def space(self, ctx, *, who):
        """ Send ur friends to space lol """
        user = who.strip()

        if "<@!" in user or "<@" in user:
            try:
                pid = user.replace("<@!", "").replace("<@", "").replace(">", "")
                person = await self.bot.fetch_user(int(pid))
                if person != None:
                    pfp = str(person.avatar_url)
                    os.system("wget " + pfp + " -O prof.webp")
                    bg = Image.open("images/spacex.jpg")
                    fg = Image.open("prof.webp")
                    fg = fg.resize((128, 128))
                    bg.paste(fg, (620, 0), fg.convert("RGBA"))
                    bg.save("temp.png")
                    await ctx.send(
                        ":rocket::sparkles: See ya later "
                        + person.mention
                        + " :sparkles::rocket:",
                        file=discord.File("temp.png"),
                    )
                    os.remove("temp.png")
                    os.remove("prof.webp")
                else:
                    await ctx.send("Had trouble getting a user from: " + text)
            except Exception as e:
                await ctx.send("We had a failure: `" + str(e) + "`")
        else:
            await ctx.send(
                ctx.message.author.mention + ", who are you sending to space?"
            )

    @commands.command()
    async def pfp(self, ctx, *, who):
        """Yoink a cool PFP from a user"""
        user = who.strip()

        if "<@!" in user or "<@" in user:
            try:
                pid = user.replace("<@!", "").replace("<@", "").replace(">", "")
                person = await self.bot.fetch_user(int(pid))
                if person != None:
                    pfp = str(person.avatar_url)
                    await ctx.send(ctx.message.author.mention + " here: " + pfp)
                else:
                    await ctx.send("Had trouble getting a user from: " + text)
            except Exception as e:
                await ctx.send("We had a failure: `" + str(e) + "`")
        else:
            await ctx.send(ctx.message.author.mention + ", that ain't a user.")

    @commands.command(hidden=True)
    async def ivp(self, ctx, fake, real):
        await ctx.message.delete()
        await ctx.send(fake + "||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||" + real)

    @commands.command(hidden=True)
    async def ivd(self, ctx, fake, real):
        await ctx.message.delete()
        await ctx.send("```" + fake + "||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||" + real + "```")


# End memes
def setup(bot):
    bot.add_cog(Memes(bot))
