# DiscordBot Wiki

Welcome to the **DiscordBot** project wiki!
This repository contains a Discord bot with automoderation, join roles, and a web configuration interface.

## Features
- **Automoderation**: Filters messages for bad words, blocked links, excessive mentions, caps usage, file attachments, and spam. Configuration is stored in `config/automod_config.yaml`.
- **Join Roles**: Automatically assigns a default role to new members joining your server.
- **Slash Commands**: Provides commands for reloading automod configuration and setting join roles.
- **Web Dashboard**: Simple Flask app (`web/app.py`) for OAuth2 login and editing automod settings.

## Setup
1. Clone the repository and install dependencies (Python 3.12+ recommended):
   ```bash
   git clone <repository-url>
   cd DiscordBot
   pip install -e .
   ```
2. Copy `.env.example` to `.env` and fill in your Discord credentials.
3. Run the bot:
   ```bash
   python src/bot.py
   ```
4. Optionally start the web interface:
   ```bash
   python web/app.py
   ```

## Tests
Unit tests for the automoderator live in `tests/`. Run them with `pytest`.

## Contributing
Feel free to open issues or pull requests if you find bugs or have suggestions.
