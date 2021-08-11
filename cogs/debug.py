import discord
from discord.ext import commands

from util_functions import *
from global_config import configboi
from server_config import serverconfig

# Hopefully we'll never need logging here


class Debug(commands.Cog):
    """Stuff that the developer couldn't find a better category for"""

    def __init__(self, bot):
        self.bot = bot
        self.confmgr = configboi("config.txt", False)
        self.sconf = serverconfig()

    @commands.command()
    async def resetgd(self, ctx):
        if ctx.message.author.id == ctx.message.guild.owner_id:
            self.sconf.rs(str(ctx.message.guild.id))
            await ctx.send(":thumbsup:")

    @commands.command()
    async def checkcog(self, ctx, *, n):
        """ check if cog is a thing """
        try:
            if ctx.bot.get_cog(n) is not None:
                await ctx.send(
                    embed=infmsg("Debug Tools", "Bot was able to find `" + n + "`")
                )
            else:
                await ctx.send(
                    embed=errmsg("Debug Tools", "Bot was not able to find `" + n + "`")
                )
        except Exception as e:
            await ctx.send(
                embed=errmsg(
                    "Debug Tools - ERROR",
                    "Had error `" + str(e) + "` while checking cog `" + n + "`",
                )
            )

    @commands.command()
    async def restart(self, ctx):
        """Restart the bot (Mod. only)"""
        if ctx.message.author.id in MOD_IDS:
            await ctx.send(embed=infmsg("Sad", "Ok, restarting"))
            if ctx.voice_client is not None:
                await ctx.voice_client.disconnect()
            await ctx.bot.logout()
            syslog.log(
                "Admin-Important",
                "Bot is restarting because "
                + ctx.message.author.display_name
                + " requested we do so.",
            )
            save("restarted.txt", str(ctx.message.channel.id))
            await login(os.environ["bottoken"], bot=True)
        else:
            await ctx.send(embed=errmsg("Oops", wrongperms("restart")))

    @commands.command()
    async def update(self, ctx):
        """Update bot from GitHub, and restart (Mod. only)"""
        if ctx.message.author.id in MOD_IDS:
            await ctx.send(embed=infmsg("Updater", "Updating..."))
            syslog.log(
                "Admin-Important",
                "Bot is updating & restarting because "
                + ctx.message.author.display_name
                + " requested we do so.",
            )
            # are these being upset?
            pull_out = await run_command_shell("git pull -v")
            commit_msg = await run_command_shell(
                "git --no-pager log --decorate=short --pretty=oneline -n1"
            )
            msg = (
                "Changes:"
                + "\n```"
                + pull_out
                + "```\nCommit message:\n"
                + "```"
                + commit_msg
                + "```"
            )
            await ctx.send(embed=infmsg("Updater", msg))

            await run_command_shell("pip3 install --upgrade -r requirements.txt")
            await ctx.send(embed=infmsg("Updater", "Restarting"))
            if ctx.voice_client is not None:
                await ctx.voice_client.disconnect()
            await ctx.bot.logout()
            save("restarted.txt", str(ctx.message.channel.id))
            await login(os.environ["bottoken"], bot=True)
        else:
            await ctx.send(embed=errmsg("Oops", wrongperms("update")))

    @commands.command()
    async def bash(self, ctx, *, args):
        """Run a command in bash (Mod. only)"""
        if self.confmgr.getasbool("BASH_ANY"):
            await ctx.send(embed=infmsg("Shell", "Ok, running: `" + args + "`"))
            syslog.log(
                "Admin",
                "Running bash command because "
                + ctx.message.author.display_name
                + " requested we do so.",
            )
            syslog.log("Admin", "Bash command is: '" + args + "'")
            async with ctx.typing():
                await asyncio.sleep(1)
            try:
                if "rm" not in args:
                    stdout = await run_command_shell(args)
                    if len(stdout) != 0:
                        if len(stdout) < 1994:
                            await ctx.send(
                                embed=infmsg("Output", "```" + stdout.strip() + "```")
                            )
                        else:
                            url = paste(stdout)
                            await ctx.send(
                                embed=infmsg(
                                    "Output",
                                    "Output is too long, so here's a link: " + url,
                                )
                            )
                    else:
                        await ctx.send(
                            embed=warnmsg(
                                "Output", "It seems that there was no output."
                            )
                        )
                else:
                    await ctx.send(
                        embed=errmsg(
                            "NOPE", "I refuse to use the `rm` command. :triumph:"
                        )
                    )
            except Exception as e:
                await ctx.send(
                    embed=errmsg("Output", "Failed to run command. :( `" + str(e) + "`")
                )
        else:
            if ctx.message.author.id in MOD_IDS:
                await ctx.send(embed=infmsg("Shell", "Ok, running: `" + args + "`"))
                syslog.log(
                    "Admin",
                    "Running bash command because "
                    + ctx.message.author.display_name
                    + " requested we do so.",
                )
                syslog.log("Admin", "Bash command is: '" + args + "'")
                async with ctx.typing():
                    await asyncio.sleep(1)
                try:
                    stdout = await run_command_shell(args)
                    if len(stdout) != 0:
                        if len(stdout) < 1994:
                            await ctx.send(
                                embed=infmsg("Output", "```" + stdout.strip() + "```")
                            )
                        else:
                            url = paste(stdout)
                            await ctx.send(
                                embed=infmsg(
                                    "Output",
                                    "Output is too long, so here's a link: " + url,
                                )
                            )
                    else:
                        await ctx.send(
                            embed=warnmsg(
                                "Output", "It seems that there was no output."
                            )
                        )
                except Exception as e:
                    await ctx.send(
                        embed=errmsg(
                            "Output", "Failed to run command. :( `" + str(e) + "`"
                        )
                    )
            else:
                await ctx.send(embed=errmsg("Oops", wrongperms("bash")))


def setup(bot):
    bot.add_cog(Debug(bot))
