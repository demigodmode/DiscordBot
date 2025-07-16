import discord
from discord.ext import commands
from discord import app_commands
import os
import yaml

from .automod import Automoderator

# Define the path to the YAML config file.
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "config", "automod_config.yaml")

class AutoModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize the Automoderator with the config file path.
        self.automod = Automoderator(CONFIG_FILE)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        await self.automod.check_message(message)

    # Optional: a slash command to reload configuration.
    @app_commands.command(name="reload_automod", description="Reload automoderation configuration")
    async def reload_automod(self, interaction: discord.Interaction):
        self.automod.load_config()
        await interaction.response.send_message("Automoderation config reloaded.", ephemeral=True)

def setup(bot):
    bot.add_cog(AutoModCog(bot))