# emoji_poll_bot
A Discord Bot that creates polls to add/delete new emojis/stickers

The bot uses slash commands to create polls.
- `/add-emoji`
- `/delete-emoji`
- `/add-sticker`
- `/delete-sticker`

Various settings for the bot can be edited in `config.py`

# Setup
You'll need to create a `.TOKEN` file (or whatever you put for `TOKEN_FILE_NAME` in `config.py`) with your [discord bot token](https://www.writebots.com/discord-bot-token/). Don't share this with anyone!

You'll also need to make a `config.py` file, you can just rename `example_config.py` if you like the settings there

After cloning the repo, make a python virtual environment and install the requirements

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then run

```
bash run.sh
```

and invite the bot to your server with the permissions integer `1073743936` and approve all permissions.
