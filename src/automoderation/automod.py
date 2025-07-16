import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict, deque
import os
import yaml
import logging

# Settings for moderation filters
BAD_WORDS = {"badword1", "badword2"}
BLOCKED_LINKS = {"discord.gg", "bit.ly"}
MAX_MENTIONS = 5
MAX_CAPS_RATIO = 0.7
BLOCKED_FILETYPES = {".exe", ".bat", ".js"}

# Spam detection settings
SPAM_INTERVAL = 10  # seconds window
SPAM_THRESHOLD = 5  # messages allowed in SPAM_INTERVAL

# Anti-raid settings
JOIN_TIME_FRAME = 10  # seconds window for join tracking
JOIN_THRESHOLD = 5    # number of joins allowed in JOIN_TIME_FRAME

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class Automoderator:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = {}
        # Tracking recent messages per user for spam detection
        self.spam_logs = defaultdict(deque)
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            logger.info("Automod rules loaded from config.")
        except Exception as e:
            logger.error(f"Failed to load automod config: {e}")
            self.config = {}

    async def send_mod_alert(self, guild: discord.Guild, message: str):
        if self.mod_channel_id:
            channel = guild.get_channel(self.mod_channel_id)
            if channel:
                await channel.send(message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content = message.content
        now = datetime.utcnow()

        # --- Bad Words Filter ---
        for word in BAD_WORDS:
            if word in content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, please refrain from using inappropriate language.", delete_after=5)
                return

        # --- Link Blocking ---
        if any(link in content for link in BLOCKED_LINKS):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, posting that kind of link is not allowed.", delete_after=5)
            return

        # --- Mass Mention Protection ---
        if len(message.mentions) > MAX_MENTIONS:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, you mentioned too many people at once.", delete_after=5)
            return

        # --- Caps Lock Filter ---
        if len(content) > 10:
            caps_count = sum(1 for c in content if c.isupper())
            if (caps_count / len(content)) > MAX_CAPS_RATIO:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, please avoid excessive use of caps.", delete_after=5)
                return

        # --- Attachment/File Type Filter ---
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ft) for ft in BLOCKED_FILETYPES):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, that file type is not allowed.", delete_after=5)
                return

        # --- Spam Detection ---
        user_log = self.spam_logs[message.author.id]
        user_log.append(now)
        # Remove messages older than SPAM_INTERVAL
        while user_log and (now - user_log[0]).total_seconds() > SPAM_INTERVAL:
            user_log.popleft()
        if len(user_log) >= SPAM_THRESHOLD:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, you're sending messages too quickly. Please slow down.", delete_after=5)
            # Optionally, add further actions like temporary mute here.
            return

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        now = datetime.utcnow()
        guild = member.guild
        join_deque = self.join_times[guild.id]
        join_deque.append(now)
        # Remove join entries older than JOIN_TIME_FRAME seconds
        while join_deque and (now - join_deque[0]).total_seconds() > JOIN_TIME_FRAME:
            join_deque.popleft()
        if len(join_deque) > JOIN_THRESHOLD:
            # Detected potential raid activity.
            alert = f"Raid alert: More than {JOIN_THRESHOLD} members have joined within {JOIN_TIME_FRAME} seconds."
            await self.send_mod_alert(guild, alert)

    # --- Slash Command for Automoderation Status ---
    # This uses discord.app_commands which is integrated in discord.py 2.0+
    @discord.app_commands.command(name="automod_status", description="Shows current automoderation settings")
    async def automod_status(self, interaction: discord.Interaction):
        settings = (
            f"**Bad Words:** {', '.join(BAD_WORDS)}\n"
            f"**Blocked Links:** {', '.join(BLOCKED_LINKS)}\n"
            f"**Max Mentions:** {MAX_MENTIONS}\n"
            f"**Max Caps Ratio:** {MAX_CAPS_RATIO}\n"
            f"**Blocked Filetypes:** {', '.join(BLOCKED_FILETYPES)}\n"
            f"**Spam Settings:** Max {SPAM_THRESHOLD} messages every {SPAM_INTERVAL} seconds\n"
            f"**Anti-Raid:** More than {JOIN_THRESHOLD} joins in {JOIN_TIME_FRAME} seconds triggers an alert."
        )
        await interaction.response.send_message(settings, ephemeral=True)

    # To register the slash command, add this to the Cog's setup
    async def cog_load(self):
        self.bot.tree.add_command(self.automod_status)

class Automoderator:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = {}
        self.spam_logs = {}
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
            logger.info("Automod rules loaded from config.")
        except Exception as e:
            logger.error(f"Failed to load automod config: {e}")
            self.config = {}

    def check_message(self, message):
        content = message.content.lower()

        try:
            if self.config.get("badword_rule"):
                bad_words = set(self.config["badword_rule"].get("bad_words", []))
                if any(word in content for word in bad_words):
                    self.handle_warning(message.author, "Bad Word")
                    return

            if self.config.get("link_blocking_rule"):
                blocked_links = set(self.config["link_blocking_rule"].get("blocked_links", []))
                if any(link in content for link in blocked_links):
                    self.handle_warning(message.author, "Blocked Link")
                    return

            if self.config.get("mass_mention_rule"):
                max_mentions = self.config["mass_mention_rule"].get("max_mentions", 5)
                if len(message.mentions) > max_mentions:
                    self.handle_warning(message.author, "Mass Mention")
                    return

            if self.config.get("caps_rule"):
                max_caps_ratio = self.config["caps_rule"].get("max_caps_ratio", 0.7)
                min_length = self.config["caps_rule"].get("min_length", 10)
                if len(content) >= min_length:
                    caps_count = sum(1 for c in message.content if c.isupper())
                    if len(message.content) and (caps_count / len(message.content)) > max_caps_ratio:
                        self.handle_warning(message.author, "Excessive Caps")
                        return

            if self.config.get("attachment_rule"):
                blocked_filetypes = set(self.config["attachment_rule"].get("blocked_filetypes", []))
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ft.lower()) for ft in blocked_filetypes):
                        self.handle_warning(message.author, "Blocked Filetype")
                        return

            if self.config.get("spam_rule"):
                spam_interval = self.config["spam_rule"].get("spam_interval", 10)
                spam_threshold = self.config["spam_rule"].get("spam_threshold", 5)
                now = datetime.utcnow()
                user_id = message.author.id
                if user_id not in self.spam_logs:
                    self.spam_logs[user_id] = deque()
                logs = self.spam_logs[user_id]
                logs.append(now)
                while logs and (now - logs[0]).total_seconds() > spam_interval:
                    logs.popleft()
                if len(logs) >= spam_threshold:
                    self.handle_warning(message.author, "Spam")
                    return
        except Exception as ex:
            logger.exception(f"Error while checking message: {ex}")

    def handle_warning(self, user, reason):
        logger.info(f"Issuing warning to {user} for {reason}.")

    async def check_message(self, message):
        """Check a message against all automod rules"""
        content = message.content.lower()

        # Bad Words Check
        if self.config.get("badword_rule"):
            bad_words = set(self.config["badword_rule"].get("bad_words", []))
            if any(word in content for word in bad_words):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, watch your language!", delete_after=5)
                return

        # Link Blocking Check
        if self.config.get("link_blocking_rule"):
            blocked_links = set(self.config["link_blocking_rule"].get("blocked_links", []))
            if any(link in content for link in blocked_links):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, that kind of link is not allowed!", delete_after=5)
                return

        # Mass Mention Check
        if self.config.get("mass_mention_rule"):
            max_mentions = self.config["mass_mention_rule"].get("max_mentions", 5)
            if len(message.mentions) > max_mentions:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, too many mentions!", delete_after=5)
                return

        # Caps Check
        if self.config.get("caps_rule"):
            max_caps_ratio = self.config["caps_rule"].get("max_caps_ratio", 0.7)
            min_length = self.config["caps_rule"].get("min_length", 10)
            if len(message.content) >= min_length:
                caps_count = sum(1 for c in message.content if c.isupper())
                if caps_count / len(message.content) > max_caps_ratio:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, please avoid excessive caps!", delete_after=5)
                    return

        # Attachment Check
        if self.config.get("attachment_rule"):
            blocked_filetypes = set(self.config["attachment_rule"].get("blocked_filetypes", []))
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ft) for ft in blocked_filetypes):
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, that file type is not allowed!", delete_after=5)
                    return

        # Spam Check
        if self.config.get("spam_rule"):
            spam_interval = self.config["spam_rule"].get("spam_interval", 10)
            spam_threshold = self.config["spam_rule"].get("spam_threshold", 5)
            
            now = datetime.utcnow()
            user_log = self.spam_logs[message.author.id]
            user_log.append(now)
            
            while user_log and (now - user_log[0]).total_seconds() > spam_interval:
                user_log.popleft()
                
            if len(user_log) >= spam_threshold:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, you're sending messages too quickly!", delete_after=5)
                return