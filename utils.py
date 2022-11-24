import re
import discord
from config import *

def validate_emoji_name(name: str):
    """Check if a string is a valid emoji name, only alphanumeric characters and underscores allowed

    Args:
        name (str): name of proposed emoji

    Returns:
        boolean: True if valid, False if not
    """
    return re.match(r'^[a-zA-Z0-9_]+$', name) is not None

def validate_image_url(url: str):
    """Check if a string is a valid image URL
    
    Args:
        url (str): URL to check
    
    Returns:
        boolean: True if valid, False if not
    """
    return re.match(r'^https?://.+?\.(png|jpg|jpeg|gif|webp)$', url) is not None

def get_poll_result(message: discord.Message):
    """Get the result of a poll

    Args:
        message (discord.Message): _description_
    
    Returns:
        boolean: True if poll passes, False if not. Based on POLL_PASS_THRESHOLD in config.py
    """
    yes_count = 0
    no_count = 0
    for reaction in message.reactions:
        if reaction.emoji == POLL_YES_EMOJI:
            yes_count = reaction.count - 1
        elif reaction.emoji == POLL_NO_EMOJI:
            no_count = reaction.count - 1
    if yes_count + no_count == 0:
        return False
    else:
        if yes_count / (yes_count + no_count) >= POLL_PASS_THRESHOLD:
            return True
        else:
            return False