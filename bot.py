import os
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class CrownlandsClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=1553031209594920970)

        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        print("Crownlands commands synced to Discord server.")


client = CrownlandsClient()

players = {}


@client.event
async def on_ready():
    print(f"Crownlands is online as {client.user}")


@client.tree.command(
    name="start",
    description="Start your Crownlands adventure"
)
async def start(interaction: discord.Interaction):
    user_id = interaction.user.id

    if user_id in players:
        player = players[user_id]

        await interaction.response.send_message(
            f"🏰 You already have a Crownlands account.\n\n"
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

    await interaction.response.send_message(
        f"🏰 Welcome to Crownlands, {interaction.user.display_name}!\n\n"
        f"Your starter pack:\n"
        f"👑 Crowns: 250\n"
        f"🗺️ Parcels: 1\n"
        f"🪵 Timber: 100\n"
        f"🏖️ Sand: 100\n"
        f"🧱 Brick: 25"
    )


@client.tree.command(
    name="profile",
    description="View your Crownlands account"
)
async def profile(interaction: discord.Interaction):
    user_id = interaction.user.id

    if user_id not in players:
        await interaction.response.send_message(
            "You don't have a Crownlands account yet. Use /start first."
        )
        return

    player = players[user_id]

    await interaction.response.send_message(
        f"🏰 Crownlands Profile — {interaction.user.display_name}\n\n"
        f"👑 Crowns: {player['crowns']}\n"
        f"🗺️ Parcels: {player['parcels']}\n"
        f"🪵 Timber: {player['timber']}\n"
        f"🏖️ Sand: {player['sand']}\n"
        f"🧱 Brick: {player['brick']}"
    )


client.run(TOKEN)
