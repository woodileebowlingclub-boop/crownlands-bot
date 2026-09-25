import os
import discord
from discord.ext import commands
from supabase import create_client

# =========================
# Crownlands settings
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# =========================
# Database helpers
# =========================

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


def update_player(discord_id, changes):
    return (
        supabase.table("players")
        .update(changes)
        .eq("discord_id", str(discord_id))
        .execute()
    )

# =========================
# Ready
# =========================

@bot.event
async def on_ready():
    print(f"Crownlands is online as {bot.user}")

# =========================
# Start
# =========================

@bot.command()
async def start(ctx):
    try:
        player = get_player(ctx.author.id)

        if player:
            await ctx.send(
                "🏰 **You already have a Crownlands account.**\n\n"
                f"👑 Crowns: {player['crowns']}\n"
                f"🗺️ Parcels: {player['parcels']}\n"
                f"🪵 Timber: {player['timber']}\n"
                f"🏖️ Sand: {player['sand']}\n"
                f"🧱 Brick: {player['brick']}\n"
                f"🏭 Buildings: {player['buildings']}"
            )
            return

        new_player = {
            "discord_id": str(ctx.author.id),
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
            f"🏰 **Welcome to Crownlands, {ctx.author.display_name}!**\n\n"
            "Your starter pack:\n"
            "👑 Crowns: 250\n"
            "🗺️ Parcels: 1\n"
            "🪵 Timber: 100\n"
            "🏖️ Sand: 100\n"
            "🧱 Brick: 25"
        )

    except Exception as error:
        print("START ERROR:", error)
        await ctx.send("❌ Crownlands had a database problem.")

# =========================
# Profile
# =========================

@bot.command()
async def profile(ctx):
    try:
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

    except Exception as error:
        print("PROFILE ERROR:", error)
        await ctx.send("❌ I couldn't read your account.")

# =========================
# Land
# =========================

@bot.command()
async def land(ctx):
    try:
        player = get_player(ctx.author.id)

        if not player:
            await ctx.send("Type **!start** first.")
            return

        empty_parcels = player["parcels"] - player["buildings"]

        await ctx.send(
            "🗺️ **Your Crownlands Land**\n\n"
            f"Total parcels: {player['parcels']}\n"
            f"Developed parcels: {player['buildings']}\n"
            f"Empty parcels: {empty_parcels}"
        )

    except Exception as error:
        print("LAND ERROR:", error)
        await ctx.send("❌ I couldn't read your land.")

# =========================
# Build
# =========================

@bot.command()
async def build(ctx, building_name=None):
    try:
        player = get_player(ctx.author.id)

        if not player:
            await ctx.send("Type **!start** first.")
            return

        if building_name is None:
            await ctx.send(
                "🏗️ **Available buildings**\n\n"
                "🪵 `!build timberyard`\n"
                "Cost: 50 Crowns + 25 Timber + 5 Brick\n\n"
                "⛏️ `!build quarry`\n"
                "Cost: 60 Crowns + 20 Timber + 5 Brick"
            )
            return

        building_name = building_name.lower()

        empty_parcels = player["parcels"] - player["buildings"]

        if empty_parcels <= 0:
            await ctx.send(
                "❌ You have no empty parcels available."
            )
            return

        if building_name == "timberyard":
            crown_cost = 50
            timber_cost = 25
            brick_cost = 5

            if (
                player["crowns"] < crown_cost
                or player["timber"] < timber_cost
                or player["brick"] < brick_cost
            ):
                await ctx.send(
                    "❌ You cannot afford a Timber Yard.\n\n"
                    "Cost:\n"
                    "👑 50 Crowns\n"
                    "🪵 25 Timber\n"
                    "🧱 5 Brick"
                )
                return

            update_player(
                ctx.author.id,
                {
                    "crowns": player["crowns"] - crown_cost,
                    "timber": player["timber"] - timber_cost,
                    "brick": player["brick"] - brick_cost,
                    "buildings": player["buildings"] + 1
                }
            )

            await ctx.send(
                "🪵 **Timber Yard built!**\n\n"
                "You used 1 parcel.\n\n"
                "Cost:\n"
                "👑 50 Crowns\n"
                "🪵 25 Timber\n"
                "🧱 5 Brick"
            )

        elif building_name == "quarry":
            crown_cost = 60
            timber_cost = 20
            brick_cost = 5

            if (
                player["crowns"] < crown_cost
                or player["timber"] < timber_cost
                or player["brick"] < brick_cost
            ):
                await ctx.send(
                    "❌ You cannot afford a Quarry.\n\n"
                    "Cost:\n"
                    "👑 60 Crowns\n"
                    "🪵 20 Timber\n"
                    "🧱 5 Brick"
                )
                return

            update_player(
                ctx.author.id,
                {
                    "crowns": player["crowns"] - crown_cost,
                    "timber": player["timber"] - timber_cost,
                    "brick": player["brick"] - brick_cost,
                    "buildings": player["buildings"] + 1
                }
            )

            await ctx.send(
                "⛏️ **Quarry built!**\n\n"
                "You used 1 parcel.\n\n"
                "Cost:\n"
                "👑 60 Crowns\n"
                "🪵 20 Timber\n"
                "🧱 5 Brick"
            )

        else:
            await ctx.send(
                "❌ Unknown building.\n\n"
                "Try:\n"
                "`!build timberyard`\n"
                "`!build quarry`"
            )

    except Exception as error:
        print("BUILD ERROR:", error)
        await ctx.send("❌ Something went wrong while building.")

# =========================
# Help
# =========================

@bot.command(name="help", aliases=["helpme"])
async def crownlands_help(ctx):
    await ctx.send(
        "🏰 **CROWNLANDS COMMANDS**\n\n"
        "`!start` — create your account\n"
        "`!profile` — show your resources\n"
        "`!land` — show your land\n"
        "`!build` — show available buildings\n"
        "`!build timberyard` — build a Timber Yard\n"
        "`!build quarry` — build a Quarry\n"
        "`!help` — show this list"
    )

# =========================
# Start bot
# =========================

bot.run(TOKEN)
