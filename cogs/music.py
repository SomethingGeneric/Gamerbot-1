# System
import os, datetime, random

# Pip
import discord
from discord.ext import commands
import asyncio
import youtube_dl

# My own
from util_functions import *
from channel_state import VoiceState


class MusicTimer:
    def __init__(self):
        self.count = 0
        syslog.log("Music-Timer", "Initialized")

    def add(self):
        self.count += 1
        syslog.log("Music-Timer", "Tick")

    def reset(self):
        self.count = 0
        syslog.log("Music-Timer", "Timer reset")

    def get(self):
        return self.count
        syslog.log("Music-Timer", "Queried")


class SongsQueue:
    def __init__(self):
        self.queue = []
        self.position = 0
        syslog.log("Music-Queue", "Initialized")

    def next_item(self):
        self.position += 1
        syslog.log("Music-Queue", "Position in queue is now: " + str(self.position))

    def add(self, name):
        self.queue.append(name)
        syslog.log("Music-Queue", "Added " + name)
        syslog.log("Music-Queue", "Full queue looks like: " + str(self.queue))

    def remove(self, name):
        self.queue.remove(name)
        syslog.log("Music-Queue", "Removed " + name)
        syslog.log("Music-Queue", "Full queue looks like: " + str(self.queue))
        self.next_item()

    def clear(self):
        self.queue = []
        self.position = 0
        syslog.log("Music-Queue", "Cleared queue and set position to 0")
        syslog.log("Music-Queue", "Queue looks like: " + str(self.queue))

    def get(self):
        syslog.log("Music-Queue", "Full queue looks like: " + str(self.queue))
        return self.queue

    def get_current(self):
        syslog.log("Music-Queue", "Current item is: " + self.queue[self.position])
        return self.queue[self.position]

    def has_next(self):
        if self.position <= len(self.queue) - 1:
            syslog.log(
                "Music-Queue",
                "We were asked if there's more to the queue, and there is.",
            )
            return True
        else:
            syslog.log(
                "Music-Queue",
                "We were asked if there's more to the queue, and there is not.",
            )
            return False

    def is_empty(self):
        if self.queue == []:
            syslog.log(
                "Music-Queue", "We were asked if the queue is empty, which it is."
            )
            return True
        else:
            syslog.log(
                "Music-Queue", "We were asked if the queue is empty, which it is not."
            )
            return False


class Music(commands.Cog):
    """Music bot go brr"""

    def __init__(self, bot):
        syslog.log("Music-Client", "Initializing.")

        ensure("music")

        self.confmgr = configboi("config.txt", False)
        self.mt = MusicTimer()
        self.vs = VoiceState()
        self.bot = bot

        self.voice_client = None
        self.audiosrc = None
        self.transformed_source = None

        self.np = None

        self.qm = SongsQueue()

        self.killed = False
        self.doSkip = False

        self.preferred_volume = 1.0

        self.mq_ids = []

    def commitSkip(self):
        syslog.log("Music-Client", "Requesting skip")
        self.doSkip = True

    def indexMusic(self):
        syslog.log(
            "Music-Client", "Indexing music. (Output not displayed here. Sorry.)"
        )
        _, _, filenames = next(os.walk("music"))
        msg = []
        for fn in filenames:
            msg.append(fn.replace(".mp3", ""))
        return msg

    async def printQueue(self, ctx):
        if not self.qm.is_empty():
            syslog.log("Music-Client", "Serving up non-empty queue for a client.")
            items = self.qm.get()
            them = "```"
            for item in items:
                them += "- `" + item + "`\n"
            them += "```"
            await ctx.send(embed=infmsg("Queue", them))
        else:
            await ctx.send(embed=warnmsg("Queue", "The queue is empty."))

    async def safeLeave(self, ctx):
        if self.voice_client is not None:
            syslog.log(
                "Music-Client", "Attempting to safely shut down voice connection."
            )
            try:
                self.voice_client.stop()
                await ctx.voice_client.disconnect()
                self.voice_client = None
                self.audiosrc = None
                self.transformed_source = None
                self.np = None
                self.killed = True
                self.qm.clear()
                self.vs.set_state("0")
                syslog.log("Music-Client", "Succesfully shut down voice connection.")
            except Exception as e:
                syslog.log(
                    "Music-Client-Important",
                    "Failed to shut down voice correctly. Error: " + str(e),
                )
                await ctx.send(embed=errmsg("Music", "`" + str(e) + "`"))
        else:
            await ctx.send(
                embed=warnmsg("Music", "It appears I'm not playing right now.")
            )

    async def clearQueue(self):
        syslog.log("Music-Client", "Running clear on our SongQueue instance.")
        self.qm.clear()

    async def sendPlaying(self, ctx):
        if self.np is not None:
            syslog.log("Music-Client", "Sending our playing status to chat")
            syslog.log(
                "Music-Client",
                "Now playing: `"
                + self.np
                + "`, ⏱: `"
                + str(datetime.timedelta(seconds=self.mt.get()))
                + "`",
            )
            await ctx.send(
                embed=infmsg(
                    "Music",
                    "Now playing: `"
                    + self.np
                    + "`, ⏱: `"
                    + str(datetime.timedelta(seconds=self.mt.get()))
                    + "`",
                )
            )
        else:
            await ctx.send(embed=warnmsg("Music", "I'm not playing anything."))

    @commands.command(aliases=["mq"])
    async def mass_queue(self, ctx):
        self.mq_ids.append(ctx.author.id)
        await ctx.send(
            embed=infmsg(
                "Mass Queue",
                ctx.author.mention
                + ", you've entered mass-queue mode. Any message you send will be considered commands until you enter `!done`",
            )
        )

    @commands.command(aliases=["stop"])
    async def leave(self, ctx):
        """Leave current channel and stop playing"""
        syslog.log("Music-Client", "Calling safeLeave and clearQueue as instructed.")
        await ctx.send(embed=infmsg("Music", "Bye :wave:"))
        await self.safeLeave(ctx)
        await self.clearQueue()

    # This should be removed(?)
    @commands.command(aliases=["rq", "cq"])
    async def clearqueue(self, ctx):
        """Clears queue and stops music"""
        syslog.log(
            "Music-Client",
            "THIS SHOULD BE REMOVED (or fixed?): Same function as `leave` currently.",
        )
        syslog.log("Music-Client", "Calling clearQueue and safeLeave")
        await self.clearQueue()
        await ctx.send(embed=infmsg("Music", "Bye!"))
        await self.safeLeave(ctx)

    @commands.command()
    async def dequeue(self, ctx, *, song):
        """Remove item from queue"""
        try:
            syslog.log("Music-Client", "Trying to remove a song from queue")
            if not self.qm.is_empty():
                self.qm.remove(song)
                await ctx.send(
                    embed=infmsg("Music", "Removed `" + song + "` from queue.")
                )
            else:
                await ctx.send(embed=warnmsg("Music", "Seems like queue is empty?"))
        except Exception as e:
            syslog.log(
                "Music-Client-Important",
                "Failed to run dequeue and send. Error: " + str(e),
            )
            await ctx.send(embed=errmsg("Music", "`" + str(e) + "`"))

    @commands.command(aliases=["lm", "songs"])
    async def listmusic(self, ctx):
        """List all locally available mp3 music"""
        try:
            syslog.log("Music-Client", "Running indexMusic and displaying to client")
            await ctx.send(
                embed=infmsg("Music", "Indexing available music. Please wait.")
            )
            dat = self.indexMusic()
            msg = "Availalbe songs: \n```"
            if len(dat) != 0:
                for sn in dat:
                    msg += "- " + sn + "\n"
            else:
                msg += "none :("
            msg += "```"
            if len(msg) > 2000:
                url = paste(msg)
                await ctx.send(embed=infmsg("Music", "Link to songs: " + url))
            else:
                await ctx.send(embed=infmsg("Music - all songs", msg))
        except Exception as e:
            syslog.log(
                "Music-Client-Important",
                "Failed to run indexMusic and send. Error: " + str(e),
            )
            await ctx.send(embed=errmsg("Music", "`" + str(e) + "`"))

    @commands.command(aliases=["sm"])
    async def searchmusic(self, ctx, *, query):
        query = query.lower()
        all_songs = self.indexMusic()
        maybe = []
        for song in all_songs:
            if query in song or query in song.lower():
                maybe.append("- `" + song + "`")
        await ctx.send(
            embed=infmsg("Music", "Maybe you meant one of: \n" + "\n".join(maybe))
        )

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, fn):
        """Play file from our local cache. (use listmusic to check)"""

        syslog.log("Music-Client", "Starting play function. Running Opus check")

        discord.opus.load_opus(self.confmgr.get("OPUS_FN"))
        opusGood = discord.opus.is_loaded()

        if opusGood:
            syslog.log("Music-Client", "Opus is good, proceeding")
            self.killed = False
            if self.voice_client == None:
                syslog.log(
                    "Music-Client",
                    "There's no client already. We're here for the long run",
                )
                syslog.log(
                    "Music-Client", "Adding " + fn + " to our (empty) queue for later"
                )
                self.qm.add(fn)
                syslog.log(
                    "Music-Client",
                    "Checking if "
                    + ctx.author.display_name
                    + " is in a voice channel.",
                )
                target_channel = ctx.author.voice.channel
                syslog.log(
                    "Music-Client",
                    "Also checking to ensure there's no other voice session in another Cog (we should be doing this earlier to save power.)",
                )
                if target_channel is not None and not self.vs.check_state():
                    syslog.log(
                        "Music-Client",
                        "We have a target channel, and are the only (requested) audio process. Attempting connection to target channel.",
                    )
                    self.voice_client = await target_channel.connect()
                    self.vs.set_state("1")
                    syslog.log("Music-Client", "We've got a connection to a channel!")
                    while self.qm.has_next():
                        syslog.log(
                            "Music-Client",
                            "Player is moving to the next item in queue.",
                        )
                        current = self.qm.get_current()
                        target = "music/" + current + ".mp3"
                        syslog.log(
                            "Music-Client",
                            "Next target is " + target + ". Checking it.",
                        )
                        if check(target):
                            syslog.log("Music-Client", target + " is good. Playing it.")
                            await ctx.send(
                                embed=infmsg("Music", "Now playing: `" + current + "`")
                            )
                            self.voice_client.stop()
                            self.audiosrc = discord.FFmpegPCMAudio(target)
                            self.transformed_source = discord.PCMVolumeTransformer(
                                self.audiosrc
                            )
                            self.transformed_source.volume = self.preferred_volume
                            self.mt.reset()
                            self.voice_client.play(
                                self.transformed_source,
                                after=lambda e: print("Player error: %s" % e)
                                if e
                                else self.commitSkip(),
                            )
                            self.np = current

                            syslog.log(
                                "Music-Client",
                                "Player is now going, and we're entering the hold loop.",
                            )

                            while (not self.killed) and (
                                self.voice_client.is_playing()
                                or self.voice_client.is_paused()
                            ):
                                self.doSkip = False
                                await asyncio.sleep(1)

                                if (
                                    self.voice_client.is_playing()
                                    and not self.voice_client.is_paused()
                                ):
                                    self.mt.add()

                                if self.doSkip:
                                    syslog.log(
                                        "Music-Client",
                                        "We've recieved a skip event. Leaving the hold loop.",
                                    )
                                    self.voice_client.pause()
                                    break
                        else:
                            syslog.log(
                                "Music-Client",
                                "Target " + target + " not found, moving on to next.",
                            )
                            await ctx.send(
                                embed=warnmsg(
                                    "Music",
                                    "Could not find `" + current + "`, skipping...",
                                )
                            )
                        syslog.log(
                            "Music-Client",
                            "Finished playing: "
                            + target
                            + ". Moving to next queue item and starting over.",
                        )
                        await ctx.send(
                            embed=infmsg(
                                "Music",
                                "That was `"
                                + self.np
                                + "`, ⏱: `"
                                + str(datetime.timedelta(seconds=self.mt.get()))
                                + "`",
                            )
                        )
                        self.qm.next_item()

                    syslog.log(
                        "Music-Client", "Queue is empty. Calling cleanup function."
                    )
                    await ctx.send(
                        embed=infmsg("Music", "Nothing else in queue. Goodbye.")
                    )
                    await self.safeLeave(ctx)
                else:
                    syslog.log(
                        "Music-Client",
                        "We've either been instructed by a user w/o voice channel, or another Cog is using voice.",
                    )
                    await ctx.send(
                        embed=warnmsg(
                            "Music", "I'm already in a voice channel, and busy."
                        )
                    )
                    self.clearQueue()
            else:
                syslog.log(
                    "Music-Client",
                    "We're already playing music within this Cog, so we're adding to queue instead.",
                )
                await ctx.send(
                    embed=infmsg("Music", "Adding `" + fn + "` to the queue")
                )
                syslog.log("Music-Client", "Added " + fn + "to queue")
                self.qm.add(fn)
                await asyncio.sleep(0.5)
                await self.sendPlaying(ctx)
                await self.printQueue(ctx)

        else:
            syslog.log("Music-Client", "We couldn't load Opus. No music today.")
            await ctx.send(
                embed=errmsg("Music", "Opus couldn't be loaded. Is it installed?")
            )

    @commands.command()
    async def pause(self, ctx):
        """Pause the music that's playing"""
        if self.voice_client is not None:
            syslog.log(
                "Music-Client", "Trying to pause the player. (Which we are running)"
            )
            try:
                self.voice_client.pause()
                await ctx.send(embed=infmsg("Music", "Paused 👍"))
                syslog.log("Music-Client", "Player paused.")
            except Exception as e:
                await ctx.send(
                    embed=errmsg("Music", "Failed to pause. `" + str(e) + "`")
                )
                syslog.log(
                    "Music-Client-Important", "Failed to pause player: " + str(e)
                )
        else:
            await ctx.send(
                embed=warnmsg("Music", "It appears I'm not playing right now.")
            )

    @commands.command()
    async def resume(self, ctx):
        """Resume music if paused"""
        if self.voice_client is not None:
            syslog.log("Music-Client", "Trying to resume the paused player")
            try:
                self.voice_client.resume()
                await ctx.send(embed=infmsg("Music", "Playing 👍"))
                syslog.log("Music-Client", "Succesfully resumed the paused player.")
            except Exception as e:
                await ctx.send(
                    embed=errmsg("Music", "Failed to resume. `" + str(e) + "`")
                )
                syslog.log(
                    "Music-Client-Important", "Failed to resume the player: " + str(e)
                )
        else:
            await ctx.send(
                embed=warnmsg("Music", "It appears I'm not playing right now.")
            )

    @commands.command()
    async def skip(self, ctx):
        """Skip currently playing song."""
        if self.voice_client is not None:
            self.doSkip = True
            await ctx.send(embed=infmsg("Music", "Skipped the song. 👍"))
            syslog.log(
                "Music-Client",
                "We've requested a skip condition. You'll see outcome below.",
            )
        else:
            await ctx.send(embed=warnmsg("Music", "Not playing."))

    # Not currently logging (no room for improvement imo)
    @commands.command(aliases=["v", "vol"])
    async def volume(self, ctx, volume=None):
        """Set or show the volume of music being played (Scale: 0.0 - 1.0)"""
        if self.voice_client is not None:
            if volume != None:
                try:
                    tgt = float(volume)
                    self.transformed_source.volume = tgt
                    self.preferred_volume = tgt
                    await ctx.send(
                        embed=infmsg("Music", "Set volume to: `" + volume + "`")
                    )
                except Exception as e:
                    await ctx.send(
                        embed=errmsg("Music", "Failed to set volume: `" + str(e) + "`")
                    )
            else:
                try:
                    await ctx.send(
                        embed=infmsg(
                            "Music",
                            "Current volume is: `"
                            + str(self.transformed_source.volume)
                            + "`",
                        )
                    )
                except Exception as e:
                    await ctx.send(
                        embed=errmsg("Music", "Failed to get volume: `" + str(e) + "`")
                    )
                    syslog.log(
                        "Music-Client-Important",
                        "Failed to get volume: `" + str(e) + "`",
                    )
        else:
            await ctx.send(
                embed=warnmsg("Music", "It appears I'm not playing right now.")
            )

    # Not currently logging (no room for improvement imo)
    @commands.command()
    async def np(self, ctx):
        """Display the filename that's playing."""
        await self.sendPlaying(ctx)

    # Not currently logging (no room for improvement imo)
    @commands.command(aliases=["q", "lq", "queue"])
    async def listqueue(self, ctx):
        """Show the queue to be played"""
        await self.sendPlaying(ctx)
        await self.printQueue(ctx)

    @commands.command(aliases=["ransongs"])
    async def addrandom(self, ctx, number=10):
        """Add [number] amount of random songs to the queue."""
        if self.voice_client is not None:
            await ctx.send(embed=infmsg("Music", "Getting random songs. Please wait."))
            syslog.log(
                "Music-Client",
                "We're getting some random music, and adding to the queue.",
            )
            dat = self.indexMusic()
            chosen = random.sample(dat, number)
            for song in chosen:
                self.qm.add(song)
            await ctx.send(embed=infmsf("Music", "Added random songs."))
            await self.sendPlaying(ctx)
            await self.printQueue(ctx)
            syslog.log("Music-Client", "We've succesfully modified the queue!")
        else:
            await ctx.send(
                embed=warnmsg("Music", "It appears I'm not playing right now.")
            )

    @commands.command()
    async def youtubeget(self, ctx, url, *, songname):
        """Save YouTube link as mp3 to play"""
        try:
            syslog.log(
                "Music-Client",
                "Trying to download " + url + " with getytvid() in util_functions.",
            )
            await ctx.send(embed=infmsg("Music", "Downloading: " + url))
            getytvid(url, songname)
            await ctx.send(
                embed=infmsg(
                    "Music",
                    "Download of "
                    + url
                    + " complete. Listen with `-play "
                    + songname
                    + "`",
                )
            )
            syslog.log(
                "Music-Client", "Download complete. (Download output should be above)"
            )
        except Exception as e:
            await ctx.send(embed=errmsg("Music", "We had an issue: `" + str(e) + "`"))
            syslog.log(
                "Music-Client-Important",
                "We had an issue while calling getytvid(): " + str(e),
            )

    @commands.command(aliases=["ytp"])
    async def play_yt(self, ctx, url, *, songname):
        """Save and then play a YouTube link"""
        try:
            syslog.log(
                "Music-Client", "Calling getytvid() then playing a song. Target: " + url
            )
            await ctx.send(embed=infmsg("Music", "Downloading: " + url))
            getytvid(url, songname)
            await ctx.send(
                embed=infmsg("Music", "Download of " + url + " complete. One moment.")
            )
            syslog.log(
                "Music-Client", "Called getytvid() successfully. Checking for player"
            )
            if self.voice_client is not None:
                syslog.log("Music-Client", "We have a player, adding.")
                await ctx.send(
                    embed=infmsg(
                        "Music",
                        "Adding `"
                        + songname
                        + "` to the queue, since it is now ready.",
                    )
                )
                self.qm.add(songname)
                await self.printQueue(ctx)
                syslog.log(
                    "Music-Client", "Done. We also printed queue for brownie points"
                )
            else:
                syslog.log(
                    "Music-Client",
                    "Someone tried play_yt w/o current player. Shame on us for being lazy.",
                )
                await ctx.send(
                    embed=warnmsg(
                        "Music",
                        "This doesn't work yet without a current voice session. Please use `-play` first.",
                    )
                )

        except Exception as e:
            await ctx.send(embed=errmsg("Music", "We had an issue: `" + str(e) + "`"))
            syslog.log("Music-Client-Important", "Play_YT had an issue: " + str(e))

    @commands.command()
    async def youtubegetpl(self, ctx, url):
        """Save YouTube playlist link as mp3s to play"""
        try:
            syslog.log(
                "Music-Client", "Trying to download playlist with the external script."
            )
            await ctx.send(
                embed=warnmsg(
                    "Music",
                    "This will take a while. Go relax, or play some existing music :)",
                )
            )
            syslog.log(
                "Music-Client", "Spawning the other process. Results may take a WHILE."
            )
            result = await run_command_shell("python3 playlist-download.py " + url)

            debug_url = paste(result)
            syslog.log(
                "Music-Client", "Here's the paste URL for the output: " + debug_url
            )

            await ctx.send(
                ctx.message.author.mention,
                embed=infmsg("Music", "All done. Songs should appear in `-listmusic`"),
            )
            """
            await ctx.send(
                "Also, debug output is here: "
                + debug_url
                + ", for if you'd like a peak"
            )
            """
            syslog.log("Music-Client", "Songs are in place. All done.")
        except Exception as e:
            await ctx.send(embed=errmsg("Music", "We had an issue: `" + str(e) + "`"))
            syslog.log("Music-Client-Important", "Get-Playlist had an issue: " + str(e))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in self.mq_ids:
            parts = []
            if " " in message.content:
                parts = message.content.split(" ")
            else:
                parts = [message.content]

            command = parts[0]
            response = ""
            if command != "-mq":
                if command == "!done":
                    response = "You're no longer in Mass Queue mode"
                    self.mq_ids.remove(message.author.id)
                elif command == "help" or command == "h":
                    response = "Commands: \n`sk` - Skip current song\n`lq` - Show queue\n`queue [n]` or `q [n]` - Append new song to queue\n`search [t]` or `s [t]` - Search library for [t]\n`v [new]` - Get volume or set it to [new]\n`ytq [url] [n]` or `youtubequeue [url] [n]` - Get new youtube song, save it, queue it"
                elif command == "lq":
                    items = self.qm.get()
                    them = ""
                    for item in items:
                        them += "- `" + item + "`\n"
                    response = "Queue:\n" + them
                elif command == "queue" or command == "q":
                    if len(parts) > 1:
                        del parts[0]
                        name = " ".join(parts)
                        syslog.log(
                            "Music-Client",
                            "Added " + name + "to queue, per MQ instruction",
                        )
                        self.qm.add(name)
                        response = "Queued `" + name + "`"
                    else:
                        response = "Usage: `q [n]`"
                elif command == "s" or command == "search":
                    if len(parts) > 1:
                        del parts[0]
                        query = "".join(parts).lower()
                        all_songs = self.indexMusic()
                        maybe = []
                        for song in all_songs:
                            if query in song or query in song.lower():
                                maybe.append("- `" + song + "`\n")
                        response = "Maybe you're looking for one of these:\n" + "".join(
                            maybe
                        )
                    else:
                        response = "Usage: `s [term]`"
                elif command == "v":
                    if len(parts) > 1:
                        del parts[0]
                        vol = parts[0]
                        try:
                            self.transformed_source.volume = float(vol)
                            self.preferred_volume = float(vol)
                            response = "Set volume to: `" + vol + "`"
                        except:
                            response = "Make sure you're using a number to set volume."
                    else:
                        response = (
                            "Volume is `" + str(self.transformed_source.volume) + "`"
                        )
                elif command == "sk":
                    self.commitSkip()
                    response = "Skipped song."
                elif command == "ytq" or command == "youtubequeue":
                    response = "Not there yet. Sorry."
                else:
                    response = "Not sure what `" + command + "` is. Try `help`?"
                await message.channel.send(response)


# End music
def setup(bot):
    bot.add_cog(Music(bot))
