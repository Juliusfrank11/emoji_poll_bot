import re
import discord

def validate_emoji_name(name: str):
    return re.match(r'^[a-zA-Z0-9_]+$', name) is not None
