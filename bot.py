import os
import discord
from discord.ext import commands
from supabase import create_client

# =========================================================
# CROWNLANDS SETTINGS
# =========================================================

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


# =========================================================
# DATABASE HELPERS
# =========================================================

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


def get_buildings(discord_id):
    result = (
        supabase.table("buildings")
        .select("*")
        .eq("discord_id", str(discord_id))
        .order("id")
        .execute()
    )

    return result.data or []


def sync_building_count(discord_id):
    buildings = get_buildings(discord_id)
    count = len(buildings)

    update_player(
        discord_id,
        {
            "buildings": count
        }
    )

    return count


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():
    print(f"Crownlands is online as {bot.user}")


# =========================================================
# START ACCOUNT
# =========================================================

@bot.command()
async def start(ctx):
    try:
        discord_id = str(ctx.author.id)

        player = get_player(discord_id)

        if player:
            building_count = sync_building_count(discord_id)

            player = get_player(discord_id)

            await ctx.send(
                "🏰 **You already have a Crownlands account.**\n\n"
                f"👑 Crowns: {player['crowns']}\n"
                f"🗺️ Parcels: {player['parcels']}\n"
                f"🪵 Timber: {player['timber']}\n"
                f"🏖️ Sand: {player['sand']}\n"
                f"🧱 Brick: {player['brick']}\n"
                f"🏭 Buildings: {building_count}"
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
        await ctx.send(
            "❌ Crownlands had a database problem while creating your account."
        )


# =========================================================
# PROFILE
# =========================================================

@bot.command()
async def profile(ctx):
    try:
        player = get_player(ctx.author.id)

        if not player:
            await ctx.send(
                "You don't have a Crownlands account yet.\n"
                "Type **!start** first."
            )
            return

        building_count = sync_building_count(ctx.author.id)

        player = get_player(ctx.author.id)

        await ctx.send(
            f"🏰 **Crownlands Profile — {player['player_name']}**\n\n"
            f"👑 Crowns: {player['crowns']}\n"
            f"🗺️ Parcels: {player['parcels']}\n"
            f"🪵 Timber: {player['timber']}\n"
            f"🏖️ Sand: {player['sand']}\n"
            f"🧱 Brick: {player['brick']}\n"
            f"🏭 Buildings: {building_count}"
        )

    except Exception as error:
        print("PROFILE ERROR:", error)
        await ctx.send(
            "❌ I couldn't read your Crownlands account."
        )


# =========================================================
# LAND
# =========================================================

@bot.command()
async def land(ctx):
    try:
        player = get_player(ctx.author.id)

        if not player:
            await ctx.send("Type **!start** first.")
            return

        buildings = get_buildings(ctx.author.id)

        developed_parcels = len(buildings)
        empty_parcels = player["parcels"] - developed_parcels

        if empty_parcels < 0:
            empty_parcels = 0

        await ctx.send(
            "🗺️ **Your Crownlands Land**\n\n"
            f"Total parcels: {player['parcels']}\n"
            f"Developed parcels: {developed_parcels}\n"
            f"Empty parcels: {empty_parcels}"
        )

    except Exception as error:
        print("LAND ERROR:", error)
        await ctx.send(
            "❌ I couldn't read your Crownlands land."
        )


# =========================================================
# BUILDINGS LIST
# =========================================================

@bot.command()
async def buildings(ctx):
    try:
        player = get_player(ctx.author.id)

        if not player:
            await ctx.send("Type **!start** first.")
            return

        owned_buildings = get_buildings(ctx.author.id)

        if not owned_buildings:
            await ctx.send(
                "🏭 **Your Buildings**\n\n"
                "You don't own any buildings yet."
            )
            return

        lines = []

        for number, building in enumerate(owned_buildings, start=1):

            building_type = building["building_type"]
            level = building["level"]

            if building_type == "timberyard":
                name = "🪵 Timber Yard"

            elif building_type == "quarry":
                name = "⛏️ Quarry"

            else:
                name = f"🏭 {building_type.title()}"

            lines.append(
                f"{number}. {name} — Level {level}"
            )

        message = (
            "🏭 **Your Crownlands Buildings**\n\n"
            + "\n".join(lines)
            + f"\n\nTotal buildings: {len(owned_buildings)}"
        )

        await ctx.send(message)

    except Exception as error:
        print("BUILDINGS ERROR:", error)
        await ctx.send(
            "❌ I couldn't read your buildings."
        )


# =========================================================
# BUILD COMMAND
# =========================================================

@bot.command()
async def build(ctx, building_name=None):
    try:
        player = get_player(ctx.author.id)

        if not player:
            await ctx.send("Type **!start** first.")
            return

        if building_name is None:
            await ctx.send(
                "🏗️ **Available Buildings**\n\n"
                "🪵 `!build timberyard`\n"
                "Cost: 50 Crowns + 25 Timber + 5 Brick\n\n"
                "⛏️ `!build quarry`\n"
                "Cost: 60 Crowns + 20 Timber + 5 Brick"
            )
            return

        building_name = building_name.lower()

        owned_buildings = get_buildings(ctx.author.id)

        developed_parcels = len(owned_buildings)
        empty_parcels = player["parcels"] - developed_parcels

        if empty_parcels <= 0:
            await ctx.send(
                "❌ You have no empty parcels available.\n\n"
                "You need more land before you can build again."
            )
            return


        # =================================================
        # TIMBER YARD
        # =================================================

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
                    "❌ You cannot afford a **Timber Yard**.\n\n"
                    "Cost:\n"
                    "👑 50 Crowns\n"
                    "🪵 25 Timber\n"
                    "🧱 5 Brick"
                )
                return

            new_building = {
                "discord_id": str(ctx.author.id),
                "building_type": "timberyard",
                "level": 1
            }

            insert_result = (
                supabase.table("buildings")
                .insert(new_building)
                .execute()
            )

            try:
                update_player(
                    ctx.author.id,
                    {
                        "crowns": player["crowns"] - crown_cost,
                        "timber": player["timber"] - timber_cost,
                        "brick": player["brick"] - brick_cost,
                        "buildings": developed_parcels + 1
                    }
                )

            except Exception:
                if insert_result.data:
                    new_id = insert_result.data[0]["id"]

                    (
                        supabase.table("buildings")
                        .delete()
                        .eq("id", new_id)
                        .execute()
                    )

                raise

            await ctx.send(
                "🪵 **Timber Yard built!**\n\n"
                "You used 1 parcel.\n\n"
                "Cost:\n"
                "👑 50 Crowns\n"
                "🪵 25 Timber\n"
                "🧱 5 Brick\n\n"
                "The Timber Yard is now permanently recorded."
            )


        # =================================================
        # QUARRY
        # =================================================

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
                    "❌ You cannot afford a **Quarry**.\n\n"
                    "Cost:\n"
                    "👑 60 Crowns\n"
                    "🪵 20 Timber\n"
                    "🧱 5 Brick"
                )
                return

            new_building = {
                "discord_id": str(ctx.author.id),
                "building_type": "quarry",
                "level": 1
            }

            insert_result = (
                supabase.table("buildings")
                .insert(new_building)
                .execute()
            )

            try:
                update_player(
                    ctx.author.id,
                    {
                        "crowns": player["crowns"] - crown_cost,
                        "timber": player["timber"] - timber_cost,
                        "brick": player["brick"] - brick_cost,
                        "buildings": developed_parcels + 1
                    }
                )

            except Exception:
                if insert_result.data:
                    new_id = insert_result.data[0]["id"]

                    (
                        supabase.table("buildings")
                        .delete()
                        .eq("id", new_id)
                        .execute()
                    )

                raise

            await ctx.send(
                "⛏️ **Quarry built!**\n\n"
                "You used 1 parcel.\n\n"
                "Cost:\n"
                "👑 60 Crowns\n"
                "🪵 20 Timber\n"
                "🧱 5 Brick\n\n"
                "The Quarry is now permanently recorded."
            )


        # =================================================
        # UNKNOWN BUILDING
        # =================================================

        else:
            await ctx.send(
                "❌ I don't recognise that building.\n\n"
                "Available buildings:\n"
                "`!build timberyard`\n"
                "`!build quarry`"
            )

    except Exception as error:
        print("BUILD ERROR:", error)

        await ctx.send(
            "❌ Something went wrong while trying to build.\n"
            "Your existing account has not been deliberately reset."
        )


# =========================================================
# HELP
# =========================================================

@bot.command(name="help", aliases=["helpme"])
async def crownlands_help(ctx):
    await ctx.send(
        "🏰 **CROWNLANDS COMMANDS**\n\n"
        "👤 `!start` — create your account\n"
        "📋 `!profile` — show your resources\n"
        "🗺️ `!land` — show your parcels\n"
        "🏭 `!buildings` — show buildings you own\n"
        "🏗️ `!build` — show available buildings\n"
        "🪵 `!build timberyard` — build a Timber Yard\n"
        "⛏️ `!build quarry` — build a Quarry\n"
        "❓ `!help` — show this command list"
    )


# =========================================================
# START CROWNLANDS
# =========================================================

bot.run(TOKEN)
