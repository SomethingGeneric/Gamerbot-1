import discord
from discord.ext import commands

from util_functions import *

# Hopefully we'll never need logging here


class Random(commands.Cog):
    """Stuff that the developer couldn't find a better category for"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """ pong. """
        await ctx.send(
            "pong. :upside_down: :gun:", file=discord.File("images/pong.jpg")
        )

    @commands.command()
    async def prime(self, ctx, num: int):
        """Check if <num> is prime"""
        if num > 1:
            # Iterate from 2 to n / 2
            for i in range(2, num):
                # If num is divisible by any number between
                # 2 and n / 2, it is not prime
                if (num % i) == 0:
                    await ctx.send(
                        embed=infmsg("Quick mafs", str(num) + " is not a prime number")
                    )
                    break
                else:
                    await ctx.send(
                        embed=infmsg("Quick mafs", str(num) + " is a prime number")
                    )
        else:
            await ctx.send(
                embed=infmsg("Quick mafs", str(num) + " is not a prime number")
            )

    @commands.command()
    async def eval(self, ctx, *, exp):
        """Do simple math on an expression"""
        res = await run_command_shell('echo "' + exp + '" | bc')
        if len(res) != 0:
            if len(res) < 1998:
                await ctx.send(embed=infmsg("Eval", "`" + str(res) + "`"))
            else:
                url = paste(res)
                await ctx.send(
                    embed=infmsg(
                        "Eval", "Output was too many characters. Here's a link: " + url
                    )
                )
        else:
            await ctx.send(embed=warnmsg("Eval", "No output."))

    @commands.command()
    async def source(self, ctx):
        """Bot source code link"""
        await ctx.send(
            embed=infmsg(
                "Source",
                "My source code lives here: https://git.xhec.us/Generic/Gamerbot",
            )
        )

    @commands.command()
    async def report(self, ctx):
        """Report bot issues"""
        await ctx.send(
            embed=infmsg(
                "Issues",
                "You can file issues here: https://git.xhec.us/Generic/Gamerbot",
            )
        )

    @commands.command()
    async def suggest(self, ctx):
        """Suggest bot feature(s)"""
        await ctx.send(
            embed=infmsg(
                "Issues",
                "You can file issues here: https://git.xhec.us/Generic/Gamerbot",
            )
        )

    @commands.command()
    async def version(self, ctx):
        """Bot version"""
        commit_msg = await run_command_shell(
            "git --no-pager log --decorate=short --pretty=oneline -n1"
        )
        msg = ""
        msg += "Latest Git commit: \n"
        msg += "```" + commit_msg + "```"
        await ctx.send(embed=infmsg("Bot Stats", msg))

    @commands.command()
    async def invite(self, ctx):
        """Add me to another server"""
        await ctx.send(
            embed=infmsg(
                "Invite me :)",
                "https://discord.com/api/oauth2/authorize?client_id=763559371628085288&permissions=8&scope=bot%20applications.commands",
            )
        )

    @commands.command()
    async def support(self, ctx):
        """Get support for Gamerbot"""
        await ctx.send(
            embed=infmsg("Join our server. :)", "https://discord.gg/j4nAea7cAs")
        )


def setup(bot):
    bot.add_cog(Random(bot))
