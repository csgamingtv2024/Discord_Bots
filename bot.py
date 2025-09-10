import requests
import json
import sys
import os
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp as youtube_dl
from dotenv import load_dotenv
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Bot-Setup
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ANNOUNCE_CHANNEL_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID", "0"))
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

volume_level = 0.5
queue = []
playing = False
abort_loading = False

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot ist online als {bot.user}")

@tree.command(name="join", description="Tritt einem Sprachkanal bei")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Du musst in einem Sprachkanal sein.", ephemeral=True)
        return
    channel = interaction.user.voice.channel
    await channel.connect()
    await interaction.response.send_message(f"✅ Beigetreten: {channel.name}", ephemeral=True)

def play_next(vc):
    global playing
    if queue:
        info = queue.pop(0)
        vc.play(
            discord.FFmpegPCMAudio(
                info['url'],
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options=f"-filter:a 'volume={volume_level}'"
            ),
            after=lambda e: play_next(vc)
        )
        playing = True

        if ANNOUNCE_CHANNEL_ID:
            channel_obj = bot.get_channel(ANNOUNCE_CHANNEL_ID)
            if channel_obj:
                coro = channel_obj.send(f"🎶 Spiele jetzt: **{info['title']}**")
                asyncio.run_coroutine_threadsafe(coro, bot.loop)
    else:
        playing = False

@tree.command(name="play", description="Spielt ein einzelnes YouTube-Video ab")
@app_commands.describe(url="YouTube-Video-URL")
async def play(interaction: discord.Interaction, url: str):
    global playing, queue
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Du musst in einem Sprachkanal sein.", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    if not interaction.guild.voice_client:
        await channel.connect()

    await interaction.response.send_message("🎵 Lade und spiele den Song...")

    try:
        with youtube_dl.YoutubeDL({'format': 'bestaudio', 'cookiefile': 'cookies.txt'}) as ydl:
            info = ydl.extract_info(url, download=False)
            vc = interaction.guild.voice_client
            queue.insert(0, {
                'url': info['url'],
                'title': info.get('title', 'Unbekannter Titel')
            })
            if not playing:
                play_next(vc)
    except Exception as e:
        await interaction.followup.send(f"❌ Fehler beim Abspielen: {str(e)}", ephemeral=True)
        return

    await interaction.followup.send("▶️ Song wird abgespielt.")

@tree.command(name="playlist", description="Spielt eine YouTube-Playlist ab")
@app_commands.describe(url="YouTube-Playlist-URL")
async def playlist(interaction: discord.Interaction, url: str):
    global playing, abort_loading
    abort_loading = False
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Du musst in einem Sprachkanal sein.", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    if not interaction.guild.voice_client:
        await channel.connect()

    await interaction.response.send_message("📥 Lade Playlist...")

    ydl_opts_flat = {
        'format': 'bestaudio',
        'cookiefile': 'cookies.txt',
        'extract_flat': True,
        'noplaylist': False
    }

    entries = []
    try:
        with youtube_dl.YoutubeDL(ydl_opts_flat) as ydl:
            data = ydl.extract_info(url, download=False)
            entries = data['entries']
    except Exception as e:
        await interaction.followup.send(f"❌ Fehler beim Laden der Playlist: {str(e)}", ephemeral=True)
        return

    def build_url(entry):
        return f"https://www.youtube.com/watch?v={entry['id']}"

    vc = interaction.guild.voice_client

    for index, entry in enumerate(entries):
        if abort_loading:
            await interaction.followup.send("⛔ Playlist-Ladevorgang abgebrochen.")
            break

        try:
            with youtube_dl.YoutubeDL({'format': 'bestaudio', 'cookiefile': 'cookies.txt'}) as ydl:
                info = ydl.extract_info(build_url(entry), download=False)
                queue.append({
                    'url': info['url'],
                    'title': info.get('title', 'Unbekannter Titel')
                })

                if not playing and index == 0:
                    play_next(vc)

                await asyncio.sleep(0.1)
        except Exception:
            continue

    if not abort_loading:
        await interaction.followup.send("🎶 Playlist wird abgespielt.")
        
@tree.command(name="volume", description="Setzt die Lautstärke (0-100%)")
@app_commands.describe(percent="Lautstärke in Prozent")
async def volume(interaction: discord.Interaction, percent: int):
    global volume_level
    volume_level = max(0.01, min(percent / 100, 2.0))
    
@tree.command(name="stop", description="Stoppt die Wiedergabe und leert die Queue")
async def stop(interaction: discord.Interaction):
    global queue, playing, abort_loading
    abort_loading = True
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
    queue = []
    playing = False
    await interaction.response.send_message("⏹️ Wiedergabe gestoppt und Queue geleert.")

@tree.command(name="quit", description="Verlässt den Sprachkanal")
async def quit(interaction: discord.Interaction):
    global playing, queue, abort_loading
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        queue = []
        playing = False
        abort_loading = True
        await interaction.response.send_message("👋 Bot hat den Kanal verlassen.")
    else:
        await interaction.response.send_message("❌ Der Bot ist in keinem Sprachkanal.", ephemeral=True)

@tree.command(name="skip", description="Überspringt den aktuellen Song")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_connected():
        await interaction.response.send_message("❌ Der Bot ist in keinem Sprachkanal.", ephemeral=True)
        return
    if not vc.is_playing():
        await interaction.response.send_message("ℹ️ Kein Song läuft gerade.", ephemeral=True)
        return
    vc.stop()
    await interaction.response.send_message("⏭️ Titel übersprungen.")

@tree.command(name="upload_cookies", description="Lade deine cookies.txt hoch")
async def upload_cookies(interaction: discord.Interaction):
    await interaction.response.send_message("📎 Lade bitte jetzt die Datei `cookies.txt` hoch (als Antwort).", ephemeral=True)

    def check(m):
        return (
            m.author.id == interaction.user.id and
            m.channel.id == interaction.channel.id and
            m.attachments and
            m.attachments[0].filename.endswith(".txt")
        )

    try:
        msg = await bot.wait_for("message", timeout=60, check=check)
        attachment = msg.attachments[0]
        await attachment.save("cookies.txt")
        await msg.reply("✅ `cookies.txt` gespeichert.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ Zeitüberschreitung – kein Upload erkannt.", ephemeral=True)

# 🔁 Restart-Befehl
@tree.command(name="restart", description="Startet den Bot-Prozess neu")
async def restart(interaction: discord.Interaction):
    await interaction.response.send_message("🔁 Starte neu...", ephemeral=True)
    await bot.close()
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ⬇️ Update-Befehl: Neue bot.py herunterladen und neu starten
@tree.command(name="update", description="Lädt neuen Code von bot.cs-gamingtv.de und startet neu")
async def update(interaction: discord.Interaction):
    await interaction.response.send_message("🔄 Lade neue Bot-Version herunter...", ephemeral=True)

    try:
        url = "https://bot.cs-gamingtv.de/bot.py"
        response = requests.get(url)

        if response.status_code == 200:
            with open("bot.py", "wb") as f:
                f.write(response.content)

            await interaction.followup.send("✅ Update erfolgreich. Starte neu...")
            await bot.close()
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            await interaction.followup.send(f"❌ Fehler beim Herunterladen: HTTP {response.status_code}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Update fehlgeschlagen: {e}", ephemeral=True)

# NEUER Befehl: Spotify-Playlist
@tree.command(name="sp_playlist", description="Spielt eine Spotify-Playlist ab")
@app_commands.describe(url="Spotify-Playlist-URL")
async def sp_playlist(interaction: discord.Interaction, url: str):
    global playing, abort_loading
    abort_loading = False
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Du musst in einem Sprachkanal sein.", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    if not interaction.guild.voice_client:
        await channel.connect()

    await interaction.response.send_message("📥 Lade Spotify-Playlist...")

    # Spotify Playlist ID extrahieren
    try:
        playlist_id = url.split("/")[-1].split("?")[0]
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
    except Exception as e:
        await interaction.followup.send(f"❌ Fehler beim Laden der Spotify-Playlist: {str(e)}", ephemeral=True)
        return

    vc = interaction.guild.voice_client

    for index, item in enumerate(tracks):
        if abort_loading:
            await interaction.followup.send("⛔ Playlist-Ladevorgang abgebrochen.")
            break
        track = item['track']
        search_query = f"{track['name']} {track['artists'][0]['name']}"

        # YouTube-Link abrufen
        try:
            with youtube_dl.YoutubeDL({'format': 'bestaudio', 'cookiefile': 'cookies.txt'}) as ydl:
                info = ydl.extract_info(f"ytsearch:{search_query}", download=False)['entries'][0]
                queue.append({'url': info['url'], 'title': info.get('title', 'Unbekannter Titel')})

                if not playing and index == 0:
                    play_next(vc)

                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"⚠️ Fehler bei Track {search_query}: {e}")
            continue

    if not abort_loading:
        await interaction.followup.send("🎶 Spotify-Playlist wird abgespielt.")

# Restliche Befehle (volume, stop, skip, quit, upload_cookies, restart, update) bleiben unverändert
# ... (füge hier deinen bestehenden Code für diese Befehle ein)

bot.run(TOKEN)
