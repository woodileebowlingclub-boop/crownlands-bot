import os
import aiohttp
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
WEB_URL = os.getenv("CROWNLANDS_WEB_URL", "https://foundry-town.onrender.com").rstrip("/")
LINK_SECRET = os.getenv("CROWNLANDS_DISCORD_SECRET", "")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


async def web_request(method, path, **kwargs):
    if not LINK_SECRET:
        raise RuntimeError("CROWNLANDS_DISCORD_SECRET is not configured")
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {LINK_SECRET}"
    async with aiohttp.ClientSession() as session:
        async with session.request(method, f"{WEB_URL}{path}", headers=headers, **kwargs) as response:
            try:
                data = await response.json()
            except Exception:
                data = {"error": "Crownlands returned an unreadable response."}
            return response.status, data


@bot.event
async def on_ready():
    print(f"Crownlands Discord companion is online as {bot.user}")


@bot.command()
async def start(ctx):
    await ctx.send(
        "🏰 **Crownlands is played on the web.**\n\n"
        f"Play here: {WEB_URL}\n\n"
        "To connect this Discord account to your web game:\n"
        f"1. Sign in at {WEB_URL}\n"
        f"2. Open {WEB_URL}/discord\n"
        "3. Generate a linking code\n"
        "4. Type !link YOURCODE here"
    )


@bot.command()
async def link(ctx, code=None):
    if not code:
        await ctx.send(
            "🔗 **Link your Crownlands account**\n\n"
            f"Open {WEB_URL}/discord while signed in, generate a code, then type:\n"
            "!link YOURCODE"
        )
        return

    try:
        status, data = await web_request(
            "POST",
            "/api/discord-link",
            json={
                "action": "redeem",
                "code": str(code).strip().upper(),
                "discordId": str(ctx.author.id),
            },
        )

        if status != 200:
            await ctx.send(f"❌ {data.get('error', 'Could not link that account.')}")
            return

        await ctx.send(
            f"✅ **Discord linked to Crownlands.**\n\n"
            f"Web account: **{data.get('username', 'Crownlands player')}**\n\n"
            "Type !profile to see your real web-game data."
        )
    except Exception as error:
        print("LINK ERROR:", error)
        await ctx.send("❌ Discord linking is not configured correctly yet.")


@bot.command()
async def profile(ctx):
    try:
        status, data = await web_request(
            "GET",
            f"/api/discord-profile?discordId={ctx.author.id}",
        )

        if status != 200:
            message = data.get("error", "Could not load your Crownlands profile.")
            if status == 404:
                message += f"\n\nOpen {WEB_URL}/discord and link your account first."
            await ctx.send(f"❌ {message}")
            return

        await ctx.send(
            f"🏰 **Crownlands Profile — {data.get('playerName', data.get('username', 'Player'))}**\n\n"
            f"👑 Crowns: {data.get('crowns', 0)}\n"
            f"🗺️ Owned plots: {data.get('ownedPlots', 0)}\n"
            f"🏭 Buildings: {data.get('buildings', 0)}\n"
            f"🪵 Timber: {data.get('timber', 0)}\n"
            f"⛰️ Clay: {data.get('clay', 0)}\n"
            f"🧱 Bricks: {data.get('bricks', 0)}\n"
            f"🌾 Food: {data.get('food', 0)}\n"
            f"⚙️ Metal: {data.get('metal', 0)}\n"
            f"📜 Land permits: {data.get('permits', 0)}"
        )
    except Exception as error:
        print("PROFILE ERROR:", error)
        await ctx.send("❌ I couldn't reach the Crownlands web game.")


@bot.command(name="help", aliases=["helpme"])
async def crownlands_help(ctx):
    await ctx.send(
        "🏰 **CROWNLANDS DISCORD COMMANDS**\n\n"
        "!start — where to play and how to link\n"
        "!link CODE — link Discord to your web account\n"
        "!profile — show your real Crownlands web-game profile\n"
        "!help — show this list\n\n"
        "Game actions stay on the Crownlands website so Discord and the web game use one set of data."
    )


bot.run(TOKEN)
