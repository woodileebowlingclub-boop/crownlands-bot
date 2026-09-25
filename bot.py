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
        await ctx.send("You already have a Crownlands account.")
        return

    players[user_id] = {
        "crowns": 250,
        "parcels": 1,
        "timber": 100,
        "sand": 100,
        "brick": 25,
        "buildings": []
    }

    await ctx.send(
        f"🏰 Welcome to Crownlands, {ctx.author.display_name}!\n\n"
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
        await ctx.send("You don't have an account yet. Type **!start** first.")
        return

    p = players[user_id]

    await ctx.send(
        f"🏰 **Crownlands Profile — {ctx.author.display_name}**\n\n"
        f"👑 Crowns: {p['crowns']}\n"
        f"🗺️ Parcels: {p['parcels']}\n"
        f"🪵 Timber: {p['timber']}\n"
        f"🏖️ Sand: {p['sand']}\n"
        f"🧱 Brick: {p['brick']}\n"
        f"🏭 Buildings: {len(p['buildings'])}"
    )


@bot.command()
async def land(ctx):
    user_id = ctx.author.id

    if user_id not in players:
        await ctx.send("Type **!start** first.")
        return

    p = players[user_id]

    used = len(p["buildings"])
    free = p["parcels"] - used

    await ctx.send(
        f"🗺️ **Your Crownlands Land**\n\n"
        f"Total parcels: {p['parcels']}\n"
        f"Developed parcels: {used}\n"
        f"Empty parcels: {free}"
    )


@bot.command()
async def helpme(ctx):
    await ctx.send(
        "🏰 **Crownlands Commands**\n\n"
        "`!start` — create your account\n"
        "`!profile` — view your resources\n"
        "`!land` — view your parcels\n"
        "`!helpme` — show commands"
    )


bot.run(TOKEN)
