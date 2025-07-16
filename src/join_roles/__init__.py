import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class JoinRoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_role = None  # This will be set by configuration

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event handler for when a member joins the server"""
        try:
            # For now, let's get the first role named 'Member' as default
            if not self.default_role:
                self.default_role = discord.utils.get(member.guild.roles, name="Member")
            
            if self.default_role:
                await member.add_roles(self.default_role)
                logger.info(f"Added role {self.default_role.name} to {member.name}")
            else:
                logger.warning(f"No default role found for {member.guild.name}")
        except Exception as e:
            logger.error(f"Error assigning role to {member.name}: {e}")

    @app_commands.command(name="set_join_role", description="Set the default role for new members")
    @app_commands.default_permissions(administrator=True)
    async def set_join_role(self, interaction: discord.Interaction, role: discord.Role):
        """Set the default role that will be assigned to new members"""
        self.default_role = role
        await interaction.response.send_message(
            f"Default role set to {role.name}",
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(JoinRoleManager(bot))