import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
from commands import *
from automoderation import AutoModCog
from join_roles import JoinRoleManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup bot intents
intents = discord.Intents.all()

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name} - {bot.user.id}')
    
    # Setup cogs AFTER the bot is ready
    await setup_bot()
    
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

async def setup_bot():
    await bot.add_cog(AutoModCog(bot))
    await bot.add_cog(JoinRoleManager(bot))
    logger.info("Cogs loaded successfully")

@bot.event
async def on_member_join(member):
    logger.info(f"Member joined: {member.name}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

def main():
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        logger.error("No Discord token found in environment variables!")
        return
    
    logger.info(f"Starting bot...")
    bot.run(TOKEN)

if __name__ == "__main__":
    main()