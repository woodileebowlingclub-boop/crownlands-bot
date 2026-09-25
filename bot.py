import os
from datetime import datetime, timezone

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

PRODUCTION_CYCLE_SECONDS = 300  # 5 minutes

TIMBER_PER_CYCLE = 10
SAND_PER_CYCLE = 8


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


def parse_supabase_time(value):
    if not value:
        return datetime.now(timezone.utc)

    text = str(value)

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    return datetime.fromisoformat(text)


def production_summary(discord_id):
    player = get_player(discord_id)

    if not player:
        return None

    buildings = get_buildings(discord_id)

    timber_yards = sum(
        1 for building in buildings
        if building["building_type"] == "timberyard"
    )

    quarries = sum(
        1 for building in buildings
        if building["building_type"] == "quarry"
    )

    last_collected = parse_supabase_time(
        player.get("last_collected")
    )

    now = datetime.now(timezone.utc)

    elapsed_seconds = max(
        0,
        int((now - last_collected).total_seconds())
    )

    cycles = elapsed_seconds // PRODUCTION_CYCLE_SECONDS

    timber_generated = (
        cycles
        * timber_yards
        * TIMBER_PER_CYCLE
    )

    sand_generated = (
        cycles
        * quarries
        * SAND_PER_CYCLE
    )

    seconds_into_cycle = (
        elapsed_seconds
        % PRODUCTION_CYCLE_SECONDS
    )

    seconds_until_next_cycle = (
        PRODUCTION_CYCLE_SECONDS
        - seconds_into_cycle
    )

    if cycles == 0 and elapsed_seconds == 0:
        seconds_until_next_cycle = PRODUCTION_CYCLE_SECONDS

    return {
        "player": player,
        "buildings": buildings,
        "timber_yards": timber_yards,
        "quarries": quarries,
        "cycles": cycles,
        "timber_generated": timber_generated,
        "sand_generated": sand_generated,
        "seconds_until_next_cycle": seconds_until_next_cycle,
        "now": now
    }


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

        now = datetime.now(timezone.utc).isoformat()

        new_player = {
            "discord_id": discord_id,
            "player_name": ctx.author.display_name,
            "crowns": 250,
            "parcels": 1,
            "timber": 100,
            "sand": 100,
            "brick": 25,
            "buildings": 0,
            "last_collected": now
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

        for number, building in enumerate(
            owned_buildings,
            start=1
        ):
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
# PRODUCTION STATUS
# =========================================================

@bot.command()
async def production(ctx):
    try:
        summary = production_summary(ctx.author.id)

        if not summary:
            await ctx.send("Type **!start** first.")
            return

        timber_yards = summary["timber_yards"]
        quarries = summary["quarries"]
        cycles = summary["cycles"]
        timber_generated = summary["timber_generated"]
        sand_generated = summary["sand_generated"]
        seconds_left = summary["seconds_until_next_cycle"]

        minutes_left = seconds_left // 60
        seconds_remainder = seconds_left % 60

        await ctx.send(
            "🏭 **Crownlands Production**\n\n"
            f"🪵 Timber Yards: {timber_yards}\n"
            f"⛏️ Quarries: {quarries}\n\n"
            f"⏱️ Completed 5-minute cycles waiting: {cycles}\n\n"
            f"Ready to collect:\n"
            f"🪵 Timber: {timber_generated}\n"
            f"🏖️ Sand: {sand_generated}\n\n"
            f"Next cycle in about "
            f"{minutes_left}m {seconds_remainder}s\n\n"
            "Use `!collect` to collect production."
        )

    except Exception as error:
        print("PRODUCTION ERROR:", error)

        await ctx.send(
            "❌ I couldn't calculate your production."
        )


# =========================================================
# COLLECT PRODUCTION
# =========================================================

@bot.command()
async def collect(ctx):
    try:
        summary = production_summary(ctx.author.id)

        if not summary:
            await ctx.send("Type **!start** first.")
            return

        player = summary["player"]
        cycles = summary["cycles"]
        timber_generated = summary["timber_generated"]
        sand_generated = summary["sand_generated"]
        timber_yards = summary["timber_yards"]
        quarries = summary["quarries"]

        if timber_yards == 0 and quarries == 0:
            await ctx.send(
                "❌ You don't own any production buildings yet."
            )
            return

        if cycles <= 0:
            await ctx.send(
                "⏳ Nothing is ready yet.\n\n"
                "Production works in 5-minute cycles.\n"
                "Try `!production` to see the timer."
            )
            return

        new_timber = player["timber"] + timber_generated
        new_sand = player["sand"] + sand_generated

        now = datetime.now(timezone.utc).isoformat()

        update_player(
            ctx.author.id,
            {
                "timber": new_timber,
                "sand": new_sand,
                "last_collected": now
            }
        )

        await ctx.send(
            "📦 **Production collected!**\n\n"
            f"Completed cycles: {cycles}\n\n"
            f"🪵 Timber collected: {timber_generated}\n"
            f"🏖️ Sand collected: {sand_generated}\n\n"
            f"New totals:\n"
            f"🪵 Timber: {new_timber}\n"
            f"🏖️ Sand: {new_sand}"
        )

    except Exception as error:
        print("COLLECT ERROR:", error)

        await ctx.send(
            "❌ Something went wrong while collecting production."
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
                "Cost: 50 Crowns + 25 Timber + 5 Brick\n"
                "Produces: 10 Timber every 5 minutes\n\n"
                "⛏️ `!build quarry`\n"
                "Cost: 60 Crowns + 20 Timber + 5 Brick\n"
                "Produces: 8 Sand every 5 minutes"
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
                "Production:\n"
                "🪵 10 Timber every 5 minutes"
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
                "Production:\n"
                "🏖️ 8 Sand every 5 minutes"
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
            "❌ Something went wrong while trying to build."
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
        "⚙️ `!production` — check production waiting\n"
        "📦 `!collect` — collect produced resources\n"
        "❓ `!help` — show this command list"
    )


# =========================================================
# START CROWNLANDS
# =========================================================

bot.run(TOKEN)
