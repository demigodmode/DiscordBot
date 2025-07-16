import discord
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
print(f"Token: {TOKEN[:20]}...{TOKEN[-20:]}")
print(f"Token length: {len(TOKEN)}")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

client.run(TOKEN)