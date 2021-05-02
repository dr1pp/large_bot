import discord
import random as rand
import spotipy as sp
import youtube_dl
import os
import asyncio

from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from youtube_search import YoutubeSearch

PLAYLIST_ID = "0EhIVTYDVaurXWRIXqB9At"

spotify = sp.Spotify(client_credentials_manager=SpotifyClientCredentials())

ydl_ops = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }


class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.first = get_random_track()
        download_yt_as(self.first.youtube_url, "next")


    @commands.command(name="join",
                      aliases=["play", "radio"])
    async def join(self, ctx):

        async def play_track(track):
            os.rename("next.mp3", "song.mp3")

            self.now_playing = track

            next = get_random_track()
            await self.channel.edit(name=f"📻 {track.readable_name} 📻")
            self.voice.play(discord.FFmpegPCMAudio("song.mp3"),
                            after=lambda e: asyncio.run_coroutine_threadsafe(play_track(next), self.bot.loop))
            download_yt_as(next.youtube_url, "next")

        self.channel = ctx.guild.get_channel(838175571216564264)
        self.voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not self.voice:
            self.voice = await self.channel.connect()

        elif not self.voice.is_connected():
            await self.channel.connect()
        else:
            await self.voice.move_to(self.channel)

        await play_track(self.first)


    @commands.command(name="disconnect",
                      aliases=["dc", "leave"])
    async def disconnect(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice.is_connected():
                await voice.disconnect()
            else:
                await ctx.send("The bot is not connected to a voice channel")


    @commands.command(name="playlist")
    async def playlist(self, ctx):
        await ctx.send(f"https://open.spotify.com/playlist/{PLAYLIST_ID}")


    @commands.command(name="nowplaying",
                      aliases=["np"])
    async def now_playing(self, ctx):
        embed = discord.Embed(title=f"{self.now_playing.readable_name} 🎵",
                              url=self.now_playing.youtube_url,
                              description=f"[Spotify Link]({self.now_playing.spotify_url})")
        embed.set_thumbnail(url=self.now_playing.album_cover_url)
        embed.set_footer(text=f"Added by: {self.now_playing.added_by.name}", icon_url=self.now_playing.added_by.image_url)
        embed.add_field(name="Length", value=self.now_playing.duration_readable)
        await ctx.send(embed=embed)


class Track:

    def __init__(self, track_info):
        self.info = track_info
        self.title = self.info['track']['name']
        self.artist = self.info['track']['album']['artists'][0]['name']
        self.readable_name = f"{self.artist} - {self.title}"
        self.spotify_url = self.info['track']['external_urls']['spotify']
        url_suffix = YoutubeSearch(self.readable_name, max_results=1).to_dict()[0]['url_suffix']
        self.youtube_url = f"https://www.youtube.com{url_suffix}"
        self.album_cover_url = self.info['track']['album']['images'][1]['url']
        self.added_by = SpotifyUser(spotify.user(self.info['added_by']['id']))
        self.duration_seconds = round(int(self.info['track']['duration_ms'])/1000)
        self.duration_readable = f"{self.duration_seconds//60}:{self.duration_seconds%60}"


class SpotifyUser:

    def __init__(self, user_info):
        self.info = user_info
        self.name = self.info['display_name']
        self.image_url = self.info['images'][0]['url']


def get_random_track():
    track_info = get_random_track_info()
    return Track(track_info)


def get_random_track_info():
    tracks = []
    total_tracks = int(spotify.playlist(PLAYLIST_ID)['tracks']['total'])
    while len(tracks) < total_tracks:
        results = spotify.playlist_items(PLAYLIST_ID, limit=100, offset=len(tracks))
        tracks.extend(results["items"])
    return rand.choice(tracks)

def download_yt_as(url, filename):
    with youtube_dl.YoutubeDL(ydl_ops) as ydl:
        ydl.download([url])

    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, f"{filename}.mp3")

def setup(bot):
    bot.add_cog(Radio(bot))
