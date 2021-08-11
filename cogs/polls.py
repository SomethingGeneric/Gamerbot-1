import discord
from discord.ext import commands

# Hopefully this will never need logging
# (but who knows :/)

from util_functions import *
from server_config import serverconfig

# Start polls
class Polls(commands.Cog):
    """Do I look like I care about your opinion?"""

    def __init__(self, bot):
        self.bot = bot
        self.sconf = serverconfig()

    @commands.command()
    async def tfpoll(self, ctx, *, question):
        """ Make a yes/no poll """
        await ctx.message.delete()
        if self.sconf.getbool(
            ctx.message.guild.id, "swears_censored"
        ) and profanity.contains_profanity(question):
            await ctx.send(
                embed=errmsg("Error", "This server does not allow profanity.")
            )
        else:
            embed = discord.Embed(
                color=discord.colour.blurple(), title=f"Poll: {question}"
            )
            msg = await ctx.send(embed=embed)
            reactions = ["\N{THUMBS UP SIGN}", "\N{THUMBS DOWN SIGN}"]
            for react in reactions:
                await msg.add_reaction(react)

    @commands.command()
    async def poll(self, ctx, *, info=None):
        """Make a poll with numeric options"""
        EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        if not info:
            await ctx.send(
                "Please format your poll like: `-poll question,option1,option2, ... `"
            )
        else:
            if self.sconf.getbool(
                ctx.message.guild.id, "swears_censored"
            ) and profanity.contains_profanity(info):
                await ctx.send(
                    embed=errmsg("Error", "This server does not allow profanity.")
                )
                await ctx.message.delete()
            else:
                if not "," in info:
                    await ctx.send(
                        "Please format your poll like: `-poll question,option1,option2, ... `"
                    )
                else:
                    things = info.split(",")
                    embed = discord.Embed(
                        color=discord.Colour.blurple(),
                        title=f"Poll: {things[0]}",
                    )
                    await ctx.message.delete()
                    things.pop(0)
                    if len(things) < 10:
                        eid = 0
                        for choice in things:
                            embed.add_field(
                                name=f"{choice}", value=f"{EMOJIS[eid]}", inline=False
                            )
                            eid += 1
                        embed.set_footer(
                            text="Remember, count reactions-1 as total votes."
                        )
                        msg = await ctx.send(embed=embed)
                        eid = 0
                        for choice in things:
                            await msg.add_reaction(EMOJIS[eid])
                            eid += 1
                    else:
                        await ctx.send("Too many choices :(")


# End polls
def setup(bot):
    bot.add_cog(Polls(bot))
