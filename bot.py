import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

players = {}


@bot.event
async def on_ready():
    print(f"Crownlands is online as {bot.user}")


@bot.command()
async def start(ctx):
    user_id = ctx.author.id

    if user_id in players:
        player = players[user_id]

        await ctx.send(
            f"🏰 {ctx.author.display_name}, you already have a Crownlands account.\n\n"
            f"👑 Crowns: {player['crowns']}\n"
            f"🗺️ Parcels: {player['parcels']}\n"
            f"🪵 Timber: {player['timber']}\n"
            f"🏖️ Sand: {player['sand']}\n"
            f"🧱 Brick: {player['brick']}"
        )
        return

    players[user_id] = {
        "crowns": 250,
        "parcels": 1,
        "timber": 100,
        "sand": 100,
        "brick": 25
    }

    await ctx.send(
        f"🏰 Welcome to Crownlands, {ctx.author.display_name}!\n\n"
        f"Your starter pack:\n"
        f"👑 Crowns: 250\n"
        f"🗺️ Parcels: 1\n"
        f"🪵 Timber: 100\n"
        f"🏖️ Sand: 100\n"
        f"🧱 Brick: 25"
    )


@bot.command()
async def profile(ctx):
    user_id = ctx.author.id

    if user_id not in players:
        await ctx.send(
            "You don't have a Crownlands account yet. Type **!start** first."
        )
        return

    player = players[user_id]

    await ctx.send(
        f"🏰 Crownlands Profile — {ctx.author.display_name}\n\n"
        f"👑 Crowns: {player['crowns']}\n"
        f"🗺️ Parcels: {player['parcels']}\n"
        f"🪵 Timber: {player['timber']}\n"
        f"🏖️ Sand: {player['sand']}\n"
        f"🧱 Brick: {player['brick']}"
    )


bot.run(TOKEN)
