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


def update_player(discord_id, changes):
    (
        supabase.table("players")
        .update(changes)
        .eq("discord_id", str(discord_id))
        .execute()
    )


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
async def build(ctx, building_name: str = None):
    player = get_player(ctx.author.id)

    if not player:
        await ctx.send("Type **!start** first.")
        return

    if not building_name:
        await ctx.send(
            "🏗️ Choose a building:\n\n"
            "`!build timberyard`\n"
            "`!build quarry`"
        )
        return

    building_name = building_name.lower()

    free_parcels = player["parcels"] - player["buildings"]

    if free_parcels <= 0:
        await ctx.send("❌ You have no empty parcels available.")
        return

    if building_name == "timberyard":
        cost_crowns = 50
        cost_timber = 25
        cost_brick = 5

        if (
            player["crowns"] < cost_crowns
            or player["timber"] < cost_timber
            or player["brick"] < cost_brick
        ):
            await ctx.send(
                "❌ You cannot afford a Timber Yard.\n\n"
                "Cost: 50 Crowns, 25 Timber, 5 Brick"
            )
            return

        update_player(
            ctx.author.id,
            {
                "crowns": player["crowns"] - cost_crowns,
                "timber": player["timber"] - cost_timber,
                "brick": player["brick"] - cost_brick,
                "buildings": player["buildings"] + 1
            }
        )

        await ctx.send(
            "🪵 **Timber Yard built!**\n\n"
            "Cost:\n"
            "👑 50 Crowns\n"
            "🪵 25 Timber\n"
            "🧱 5 Brick"
        )

    elif building_name == "quarry":
        cost_crowns = 60
        cost_timber = 20
        cost_brick = 5

        if (
            player["crowns"] < cost_crowns
            or player["timber"] < cost_timber
            or player["brick"] < cost_brick
        ):
            await ctx.send(
                "❌ You cannot afford a Quarry.\n\n"
                "Cost: 60 Crowns, 20 Timber, 5 Brick"
            )
            return

        update_player(
            ctx.author.id,
            {
                "crowns": player["crowns"] - cost_crowns,
                "timber": player["timber"] - cost_timber,
                "brick": player["brick"] - cost_brick,
                "buildings": player["buildings"] + 1
            }
        )

        await ctx.send(
            "⛏️ **Quarry built!**\n\n"
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


@bot.command()
async def helpme(ctx):
    await ctx.send(
        "🏰 **Crownlands Commands**\n\n"
        "`!start` — create your account\n"
        "`!profile` — view your resources\n"
        "`!land` — view your parcels\n"
        "`!build timberyard` — build a Timber Yard\n"
        "`!build quarry` — build a Quarry\n"
        "`!helpme` — show commands"
    )


bot.run(TOKEN)
