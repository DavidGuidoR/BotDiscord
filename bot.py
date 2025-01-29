import discord
from discord.ext import commands
import asyncio
from yt_dlp import YoutubeDL
import re 

# Configurar intents y el bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Cola global de canciones
queues = {}

# Opciones para yt-dlp
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'False', 'default_search': 'ytsearch'}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Función para verificar si el texto es un enlace de YouTube
def is_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+'
    )
    return re.match(youtube_regex, url)

# Asegurar conexión al canal de voz
async def ensure_voice_connection(ctx):
    if not ctx.author.voice:
        await ctx.send("¡Debes estar en un canal de voz para usar este comando!")
        return False
    if not ctx.voice_client:
        channel = ctx.author.voice.channel
        await channel.connect()
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        await ctx.voice_client.move_to(ctx.author.voice.channel)
    return True

# Reproducir canciones desde la cola
async def play_next(ctx):
    

    next_song = queues[ctx.guild.id].pop(0)
    ctx.voice_client.play(discord.FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    await ctx.send(f"Ahi te va puta 🥵: {next_song['title']}")

# Comando para añadir canciones/playlist a la cola
@bot.command(name='play')
async def play(ctx, query):
    if not await ensure_voice_connection(ctx):
        return

    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []

    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            if is_youtube_url(query):
                info = ydl.extract_info(query, download=False)
            else: 
            # Realizar búsqueda en YouTube y tomar el primer resultado
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]

            # Verificar si es playlist o canción única
            if 'entries' in info: 
                for entry in info['entries']:
                    queues[ctx.guild.id].append({'url': entry['url'], 'title': entry['title']})
                await ctx.send(f"Playlist añadida en la cola 💋: {len(info['entries'])} canciones.")
            else:
                queues[ctx.guild.id].append({'url': info['url'], 'title': info['title']})
                await ctx.send(f"Canción añadida en la cola 💋: {info['title']}")
        except Exception as e:
            await ctx.send("No se pudo procesar el enlace de YouTube. Asegúrate de que es válido.")
            print(e)
            return

    if not ctx.voice_client.is_playing():
        await play_next(ctx)

# Comando para saltar a la siguiente canción
@bot.command(name='skip')
async def skip(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("No hay ninguna canción reproduciéndose ahora mismo.")
        return

    await ctx.send("Ñiñiñiñi mejor ponte a chambear ☠")
    ctx.voice_client.stop()

# Comando para mostrar la cola
@bot.command(name='queue')
async def queue(ctx):
    if not queues.get(ctx.guild.id):
        await ctx.send("La cola está vacía.")
        return

    queue_list = [f"{i+1}. {song['title']}" for i, song in enumerate(queues[ctx.guild.id])]
    await ctx.send("Cola actual:\n" + "\n".join(queue_list))

# Comando para salir del canal de voz
@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queues.pop(ctx.guild.id, None)
        await ctx.send("Desconectado del canal de voz y cola eliminada.")
    else:
        await ctx.send("No estoy conectado a ningún canal de voz.")

# Bot listo
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

# Ejecutar el bot
bot.run('')
