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
        await self.tree.sync()

client = CrownlandsClient()

players = {}

@client.tree.command(name="start", description="Start your Crownlands adventure")
async def start(interaction: discord.Interaction):
    user_id = interaction.user.id

    if user_id in players:
        await interaction.response.send_message(
            "You already have a Crownlands account."
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
        f"👑 Crowns: 250\n"
        f"🗺️ Parcels: 1\n"
        f"🪵 Timber: 100\n"
        f"🏖️ Sand: 100\n"
        f"🧱 Brick: 25"
    )

client.run(TOKEN)
