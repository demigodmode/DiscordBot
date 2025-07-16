from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import yaml
import os
from dotenv import load_dotenv
import logging
from functools import wraps
import secrets
from datetime import timedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for troubleshooting
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to False for localhost development
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
)

# Add Discord OAuth2 configuration
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"  # Remove in production

app.config["DISCORD_CLIENT_ID"] = os.getenv('DISCORD_CLIENT_ID')
app.config["DISCORD_CLIENT_SECRET"] = os.getenv('DISCORD_CLIENT_SECRET')
app.config["DISCORD_REDIRECT_URI"] = "http://localhost:5000/callback"  # Hardcode for testing
app.config["DISCORD_BOT_TOKEN"] = os.getenv('DISCORD_TOKEN')  # Your bot token
app.config["DISCORD_GUILD_ID"] = os.getenv('DISCORD_GUILD_ID')  # Your server ID

logger.info(f"Discord Client ID: {app.config['DISCORD_CLIENT_ID']}")
logger.info(f"Discord Redirect URI: {app.config['DISCORD_REDIRECT_URI']}")
logger.info(f"Discord Guild ID: {app.config['DISCORD_GUILD_ID']}")

# Initialize Discord OAuth2
discord = DiscordOAuth2Session(app)

# Initialize security extensions
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["30 per minute"],
    storage_uri="memory://"
)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "automod_config.yaml")

@app.route("/")
def index():
    """Root route that checks if user is logged in"""
    logger.debug(f"Index route - Authorized: {discord.authorized}")
    logger.debug(f"Session data: {dict(session)}")
    
    if discord.authorized:
        try:
            user = discord.fetch_user()
            logger.info(f"User is authorized: {user.username}")
            return redirect(url_for("config"))
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            session.clear()
            return redirect(url_for("login"))
    return redirect(url_for("login"))

@app.route("/login")
def login():
    """Initiates Discord OAuth2 login"""
    logger.info("Starting Discord OAuth2 login")
    # Add bot scope to access guild member info
    return discord.create_session(scope=['identify', 'guilds', 'guilds.members.read'])

@app.route("/callback")
def callback():
    """Discord OAuth2 callback"""
    logger.info("OAuth2 callback received")
    logger.debug(f"Callback args: {request.args}")
    
    try:
        discord.callback()
        
        # Test if we can fetch user
        user = discord.fetch_user()
        logger.info(f"OAuth2 successful - User: {user.username} (ID: {user.id})")
        
        # Force session to be permanent
        session.permanent = True
        session.modified = True
        
        return redirect(url_for("index"))
    except Exception as e:
        logger.error(f"OAuth2 callback failed: {type(e).__name__}: {str(e)}")
        logger.exception("Full traceback:")
        flash("Authentication failed. Please try again.", "error")
        session.clear()
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    """Logout and revoke Discord session"""
    logger.info("User logging out")
    discord.revoke()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    """Handle unauthorized access"""
    logger.warning("Unauthorized access attempt")
    session.clear()
    return redirect(url_for("login"))

def is_admin():
    """Check if the logged-in user is an admin in the configured guild"""
    if not discord.authorized:
        return False
    try:
        user = discord.fetch_user()
        logger.info(f"Checking admin status for user: {user.username}")
        
        # Get user's guilds
        guilds = discord.fetch_guilds()
        guild_id = app.config['DISCORD_GUILD_ID']
        
        # Check if user is in the target guild
        user_guild = next((g for g in guilds if str(g.id) == str(guild_id)), None)
        if not user_guild:
            logger.warning(f"User not in guild {guild_id}")
            return False
        
        # Fix: Convert permissions to int first
        permissions = user_guild.permissions
        if hasattr(permissions, 'value'):
            # If it's a Permissions object with a value attribute
            permissions_int = permissions.value
        else:
            # Try to convert to int
            permissions_int = int(permissions)
        
        is_admin = bool(permissions_int & 0x8)  # ADMINISTRATOR permission
        logger.info(f"User {user.username} admin status: {is_admin} (permissions: {permissions_int})")
        return is_admin
    except Exception as e:
        logger.error(f"Failed to check admin status: {e}")
        logger.exception("Full traceback:")
        return False

@app.route('/config', methods=['GET', 'POST'])
@requires_authorization
def config():
    """Main configuration page"""
    # Debug info
    try:
        user = discord.fetch_user()
        logger.info(f"Config page accessed by: {user.username}")
    except:
        pass
    
    if not is_admin():
        flash("You need to be a server administrator to access this page.", "error")
        return redirect(url_for("logout"))

    if request.method == 'POST':
        # Load current config or start with an empty dict
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            config_data = {}

        # Update config from form input
        bad_words = request.form.get('bad_words', '')
        config_data['badword_rule'] = {"bad_words": [w.strip() for w in bad_words.split(',') if w.strip()]}

        blocked_links = request.form.get('blocked_links', '')
        config_data['link_blocking_rule'] = {"blocked_links": [l.strip() for l in blocked_links.split(',') if l.strip()]}

        max_mentions = int(request.form.get('max_mentions', 5))
        config_data['mass_mention_rule'] = {"max_mentions": max_mentions}

        max_caps_ratio = float(request.form.get('max_caps_ratio', 0.7))
        min_length = int(request.form.get('min_length', 10))
        config_data['caps_rule'] = {"max_caps_ratio": max_caps_ratio, "min_length": min_length}

        blocked_filetypes = request.form.get('blocked_filetypes', '')
        config_data['attachment_rule'] = {"blocked_filetypes": [ft.strip() for ft in blocked_filetypes.split(',') if ft.strip()]}

        spam_interval = int(request.form.get('spam_interval', 10))
        spam_threshold = int(request.form.get('spam_threshold', 5))
        config_data['spam_rule'] = {"spam_interval": spam_interval, "spam_threshold": spam_threshold}

        # Write the updated configuration back to the YAML file
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                yaml.dump(config_data, f)
            flash('Configuration updated successfully!', 'success')
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            flash('Failed to save configuration.', 'error')
        
        return redirect(url_for('config'))
    else:
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load config, using defaults: {e}")
            config_data = {}
        return render_template('config.html', config=config_data)

@app.route('/debug')
def debug_session():
    """Debug route to check session state"""
    return {
        'authorized': discord.authorized,
        'session': dict(session),
        'client_id': app.config.get('DISCORD_CLIENT_ID'),
        'redirect_uri': app.config.get('DISCORD_REDIRECT_URI')
    }

if __name__ == '__main__':
    # Check if all required environment variables are set
    required_vars = ['DISCORD_CLIENT_ID', 'DISCORD_CLIENT_SECRET', 'DISCORD_TOKEN', 'DISCORD_GUILD_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file")
        exit(1)
    
    logger.info("Starting Flask app...")
    app.run(debug=True, host='127.0.0.1', port=5000)