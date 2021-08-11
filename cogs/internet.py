import os, json, random
import urllib.parse
import urllib

import discord
from discord.ext import commands
import asyncio
import gmplot

from util_functions import *
from global_config import configboi

from server_config import serverconfig

# sconf = serverconfig()

from better_profanity import profanity

profanity.load_censor_words(
    whitelist_words=open("whitelist_words.txt").read().split("\n")
)

profanity.add_censor_words(open("blacklist_words.txt").read().split("\n"))

# Fun internet things
class Internet(commands.Cog):
    """Useful tools on the interwebs"""

    def __init__(self, bot):
        self.bot = bot
        self.confmgr = configboi("config.txt", False)
        self.sconf = serverconfig()

    async def getasjson(self, url):
        try:
            data = await run_command_shell('curl "' + url + '"')
            return json.loads(data)
        except Exception as e:
            return '{"haha":"heeho"}'

    @commands.command()
    async def stockprice(self, ctx, *, symbol):
        """Get current price for $symbol"""
        try:
            await ctx.send(
                embed=infmsg(
                    "Stonks",
                    ctx.message.author.mention + ": querying info about $" + symbol,
                )
            )
            price = await run_command_shell(
                'curl "https://finnhub.io/api/v1/quote?symbol=SYMB&token=TKN"'.replace(
                    "SYMB", symbol
                ).replace("TKN", self.confmgr.get("FINNHUB_KEY"))
            )
            data = json.loads(price)
            labels = {
                "o": "Open",
                "h": "High",
                "l": "Low",
                "c": "Current",
                "pc": "Previous Close",
                "t": "Time",
            }
            msg = "```\n"
            for key, val in data.items():
                msg += labels[key] + ": " + str(val) + "\n"
            msg += "```"
            await ctx.send(
                ctx.message.author.mention,
                embed=infmsg(": 🚀 Info for $" + symbol + " 🚀", msg),
            )
        except Exception as e:
            await ctx.send(
                embed=errmsg(
                    "Stonks",
                    "Had issue getting price of " + symbol + ". `" + str(e) + "`",
                )
            )
            syslog.log(
                "Internet-Important",
                "Had issue getting price of " + symbol + ": " + str(e),
            )

    @commands.command()
    async def weather(self, ctx, *, search):
        """Forecast gang"""
        try:
            await ctx.send(
                embed=infmsg("Weather", "Getting data for: `" + search + "`")
            )

            og = search
            search = urllib.parse.quote(search)

            commandstr = "http://api.weatherstack.com/current?access_key=KEY&query=QUERY&units=f".replace(
                "KEY", self.confmgr.get("WS_KEY")
            ).replace(
                "QUERY", search
            )

            data = await self.getasjson(commandstr)

            things = data["current"]

            icon = things["weather_icons"][0]

            data = [
                ("Temperature", things["temperature"]),
                ("Feels like", things["feelslike"]),
                ("Overview", things["weather_descriptions"][0]),
                ("Wind speed", things["wind_speed"]),
                ("Precipitation %", things["precip"]),
                ("Humidity %", things["humidity"]),  # %?
                ("Cloud cover %", things["cloudcover"]),  # %?
                ("Visibility (miles?)", things["visibility"]),
            ]

            final_message = "" + icon + "\n```"

            for item in data:
                disp, val = item
                final_message += disp + ": " + str(val) + "\n"

            final_message += "```"

            await ctx.send(embed=infmsg("Weather", final_message))

        except Exception as e:
            await ctx.send(embed=errmsg("Weather had an error", "`" + str(e) + "`"))
            syslog.log("Internet-Important", "Had an issue with weather: " + str(e))

    @commands.command()
    async def kernel(self, ctx):
        """Get Linux kernel info for host and latest"""
        try:
            await ctx.send(embed=infmsg("Kernel", "Getting kernel info."))
            data = await self.getasjson("https://www.kernel.org/releases.json")
            new_ver = data["latest_stable"]["version"]
            mine = await run_command_shell("uname -r")
            msg = (
                "I'm running: `"
                + mine
                + "`\nKernel.org reports stable is: `"
                + new_ver
                + "`"
            )
            await ctx.send(embed=infmsg("Kernel", msg))
        except Exception as e:
            await ctx.send(
                embed=errmsg("Kernel", "Had an issue getting info: `" + str(e) + "`")
            )
            syslog.log("Internet-Important", "Kernel command had error: " + str(e))

    @commands.command()
    async def search(self, ctx, *, query):
        """ Use if someone is making you do resarch for them """
        url = "https://www.google.com/search?q="
        async with ctx.typing():
            await asyncio.sleep(1)
        await ctx.send(embed=infmsg("Go to", url + urllib.parse.quote(query)))

    @commands.command()
    async def traceroute(self, ctx, *, url):
        """Run traceroute on a url"""
        try:
            if "." in url:
                url.replace(";", "").replace("&", "").replace("&&", "")
                if " " in url:
                    url = url.split(" ")[0]
                await ctx.send(
                    ctx.message.author.mention,
                    embed=warnmsg(
                        "Wait time for traceroute", "This will take a while. Working..."
                    ),
                )

                syslog.log("Internet", "Starting traceroute of " + url)

                out = await run_command_shell("traceroute " + url)
                if len(out) < 1024:
                    await ctx.send(
                        embed=infmsg("Traceroute output", "```" + str(out) + "```")
                    )
                else:
                    link = paste(out)
                    await ctx.send(
                        ctx.message.author.mention,
                        embed=infmsg(
                            "Output",
                            "The traceroute output is too long, so here's a link: "
                            + link,
                        ),
                    )

                syslog.log("Internet", "Finished traceroute of " + url)
            else:
                await ctx.send(
                    ctx.message.author.mention,
                    embed=errmsg("You goofed", " that's not an address :|"),
                )
        except Exception as e:
            await ctx.send(embed=errmsg("Traceroute error", "`" + str(e) + "`"))
            syslog.log(
                "Internet-Imporant", "Had an issue running traceroute: `" + str(e) + "`"
            )

    @commands.command()
    async def whois(self, ctx, *, url):
        """Lookup data on a domain"""
        try:
            if "." in url:
                url.replace(";", "").replace("&", "").replace("&&", "")
                if " " in url:
                    url = url.split(" ")[0]
                await ctx.send(
                    ctx.message.author.mention,
                    embed=warnmsg(
                        "Wait time for whois", "This will take a while. Working..."
                    ),
                )
                syslog.log("Internet", "Querying WHOIS for " + url)
                out = await run_command_shell("whois " + url)
                if len(out) > 1024:
                    link = paste(out)
                    await ctx.send(
                        ctx.message.author.mention,
                        embed=infmsg(
                            "Output",
                            "The whois output is too long, so here's a link: " + link,
                        ),
                    )
                else:
                    await ctx.send(
                        embed=infmsg("Whois output", "```" + str(out) + "```")
                    )
                syslog.log("Internet", "Done querying WHOIS for " + url)
            else:
                await ctx.send(
                    ctx.message.author.mention,
                    embed=errmsg("You goofed", " that's not an address :|"),
                )
        except Exception as e:
            await ctx.send(embed=errmsg("Whois error", "`" + str(e) + "`"))
            syslog.log(
                "Internet-Important", "Had an issue running whois: `" + str(e) + "`"
            )

    @commands.command()
    async def nmap(self, ctx, *, url):
        """Scan a url/ip for open ports"""
        try:
            if "." in url:
                url.replace(";", "").replace("&", "").replace("&&", "")
                if " " in url:
                    url = url.split(" ")[0]
                await ctx.send(
                    ctx.message.author.mention,
                    embed=warnmsg(
                        "Wait time for nmap", "This will take a while. Working..."
                    ),
                )
                syslog.log("Internet", "Querying NMAP for " + url)
                out = await run_command_shell("nmap -A -vv -Pn " + url)
                if len(out) > 1024:
                    link = paste(out)
                    await ctx.send(
                        ctx.message.author.mention,
                        embed=infmsg(
                            "Output",
                            "The nmap output is too long, so here's a link: " + link,
                        ),
                    )
                else:
                    await ctx.send(
                        embed=infmsg("Nmap output", "```" + str(out) + "```")
                    )
                syslog.log("Internet", "Done querying NMAP for " + url)
            else:
                await ctx.send(
                    ctx.message.author.mention,
                    embed=errmsg("You goofed", " that's not an address :|"),
                )
        except Exception as e:
            await ctx.send(embed=errmsg("NMAP error", "`" + str(e) + "`"))
            syslog.log(
                "Internet-Important", "Had an issue running nmap: `" + str(e) + "`"
            )

    @commands.command(aliases=["tuxi"])
    async def ask(self, ctx, *, query):
        """Ask Tuxi anything"""
        if profanity.contains_profanity(query) and self.sconf.getbool(
            ctx.message.guild.id, "swears_censored"
        ):
            author = ctx.message.author
            await ctx.message.delete()
            await ctx.send(
                embed=errmsg("Mean words", author.mention + " how dare you.")
            )
        else:
            try:
                query = query.replace("&", "").replace(";", "")
                await ctx.send(
                    ctx.message.author.mention,
                    embed=infmsg("Tuxi", "Searching: `" + query + "`"),
                )
                out = await run_command_shell('./tuxi -r "' + query + '"')
                await ctx.send(embed=infmsg("Tuxi", "```" + out + "```"))
            except Exception as e:
                await ctx.send(
                    embed=errmsg("Tuxi", "Had an issue running tuxi: `" + str(e) + "`")
                )
                syslog.log(
                    "Internet-Important", "Had an issue running tuxi: `" + str(e) + "`"
                )

    @commands.command()
    async def geoip(self, ctx, *, ip):
        """Get GeoIP of an address"""
        try:
            dat = getgeoip(ip)

            msg = "```"

            for key, value in dat.items():
                msg += key.replace("_", " ") + ": " + str(value) + "\n"

            msg += "```\n"
            msg += "Google maps: http://www.google.com/maps/place/{lat},{lng}".replace(
                "{lat}", str(dat["latitude"])
            ).replace("{lng}", str(dat["longitude"]))

            await ctx.send(embed=infmsg("GeoIP for `" + ip + "`", msg))
            syslog.log("Internet", "Queried GeoIP for " + ip)

        except Exception as e:
            await ctx.send(
                embed=errmsg(
                    "GeoIP error", "Had an issue getting GeoIP data: `" + str(e) + "`"
                )
            )
            syslog.log(
                "Internet-Important",
                "Had an issue getting GeoIP data: `" + str(e) + "`",
            )

    @commands.command(aliases=["tr-map"])
    async def trmap(self, ctx, *, ip):
        """Get a Google Maps view of traceroute"""
        try:

            cmd = "traceroute -n 8.8.8.8 | tail -n+2 | awk '{ print $2 }'".replace(
                "8.8.8.8", ip
            )

            await ctx.send(
                embed=warnmsg(
                    "Trace-map",
                    "Running traceroute for `" + ip + "`\n This will take a while.",
                )
            )

            out = await run_command_shell(cmd)

            addrs = out.split("\n")

            cleanup = []

            sum_hops = ""

            for line in addrs:
                if not "*" in line:
                    if line != "10.0.0.1" and line != "192.168.1.1":
                        cleanup.append(line)
                        sum_hops += "- " + line + "\n"

            await ctx.send(embed=infmsg("Trace-map", "Hops:\n```" + sum_hops + "```"))

            lat_list = []
            long_list = []

            for line in cleanup:
                print("Getting data for: " + line)
                dat = getgeoip(line)
                lat_list.append(float(dat["latitude"]))
                long_list.append(float(dat["longitude"]))

            gmap3 = gmplot.GoogleMapPlotter(
                0.0, 0.0, 0, apikey=self.confmgr.get("MAPS_KEY")
            )

            # Points gang
            gmap3.scatter(lat_list, long_list, "#FF0000", marker=False)

            # Lines gang
            gmap3.plot(lat_list, long_list, "cornflowerblue", edge_width=2.5)

            idh = (
                "".join(random.choices(string.ascii_uppercase + string.digits, k=25))
                + ".html"
            )

            fn = self.confmgr.get("PASTE_BASE") + idh

            # Save time
            gmap3.draw(fn)

            await ctx.send(
                ctx.message.author.mention,
                embed=infmsg(
                    "GeoIP",
                    "Map is available at: " + self.confmgr.get("PASTE_URL_BASE") + idh,
                ),
            )

        except Exception as e:
            await ctx.send(
                ctx.message.author.mention,
                embed=errmsg("GeoIP", "Had an issue making your map: `" + str(e) + "`"),
            )
            syslog.log(
                "Internet-Important", "Had an issue making trmap: `" + str(e) + "`"
            )


# End fun internet things
def setup(bot):
    bot.add_cog(Internet(bot))
