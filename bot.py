import os
import discord
from discord.ext import commands
from supabase import create_client

TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Crownlands is online as {bot.user}")


def get_player(discord_id):
    result = (
        supabase.table("players")
        .select("*")
        .eq("discord_id", str(discord_id))
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


@bot.command()
async def start(ctx):
    discord_id = str(ctx.author.id)

    player = get_player(discord_id)

    if player:
        await ctx.send(
            "🏰 You already have a Crownlands account.\n\n"
            f"👑 Crowns: {player['crowns']}\n"
            f"🗺️ Parcels: {player['parcels']}\n"
            f"🪵 Timber: {player['timber']}\n"
            f"🏖️ Sand: {player['sand']}\n"
            f"🧱 Brick: {player['brick']}\n"
            f"🏭 Buildings: {player['buildings']}"
        )
        return

    new_player = {
        "discord_id": discord_id,
        "player_name": ctx.author.display_name,
        "crowns": 250,
        "parcels": 1,
        "timber": 100,
        "sand": 100,
        "brick": 25,
        "buildings": 0
    }

    supabase.table("players").insert(new_player).execute()

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
    player = get_player(ctx.author.id)

    if not player:
        await ctx.send("You don't have an account yet. Type **!start** first.")
        return

    await ctx.send(
        f"🏰 **Crownlands Profile — {player['player_name']}**\n\n"
        f"👑 Crowns: {player['crowns']}\n"
        f"🗺️ Parcels: {player['parcels']}\n"
        f"🪵 Timber: {player['timber']}\n"
        f"🏖️ Sand: {player['sand']}\n"
        f"🧱 Brick: {player['brick']}\n"
        f"🏭 Buildings: {player['buildings']}"
    )


@bot.command()
async def land(ctx):
    player = get_player(ctx.author.id)

    if not player:
        await ctx.send("Type **!start** first.")
        return

    free = player["parcels"] - player["buildings"]

    await ctx.send(
        f"🗺️ **Your Crownlands Land**\n\n"
        f"Total parcels: {player['parcels']}\n"
        f"Developed parcels: {player['buildings']}\n"
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
