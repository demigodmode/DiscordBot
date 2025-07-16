# Discord Bot Project

This project is a Discord bot built using the `discord.py` library. It includes general-purpose functionalities such as automoderation and role assignment for new members, utilizing Slash commands for user interaction.

## Features

- **Automoderation**: Automatically checks messages for inappropriate content and manages user warnings.
- **Join Roles**: Automatically assigns roles to users when they join the server.
- **Slash Commands**: Provides a user-friendly way to interact with the bot using Slash commands.

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd discord-bot-project
   ```

2. **Install dependencies**:
   Ensure you have Python 3.8 or higher installed. Then, run:
   ```
   pip install -r requirements.txt
   ```

3. **Configure the bot**:
   Create a `.env` file in the root directory and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_token_here
   ```

4. **Run the bot**:
   Execute the following command to start the bot:
   ```
   python src/bot.py
   ```

## Usage

- Use `/help` to get a list of available commands.
- The bot will automatically assign roles to new members and enforce rules through automoderation.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.