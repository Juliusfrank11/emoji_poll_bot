import re
import discord
from config import *
from PIL import Image
import os


def validate_emoji_name(name: str):
    """Check if a string is a valid emoji name, only alphanumeric characters and underscores allowed

    Args:
        name (str): name of proposed emoji

    Returns:
        boolean: True if valid, False if not
    """
    return re.match(r"^[a-zA-Z0-9_]+$", name) is not None


def validate_image_url(url: str):
    """Check if a string is a valid image URL

    Args:
        url (str): URL to check

    Returns:
        boolean: True if valid, False if not
    """
    return re.match(r"^https?://.+?\.(png|jpg|jpeg|gif)$", url) is not None


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
        print(yes_count / (yes_count + no_count))
        if yes_count / (yes_count + no_count) >= POLL_PASS_THRESHOLD:
            return True
        else:
            return False


def get_emoji_name_from_poll_message(message: discord.Message):
    """Get the name of the emoji from a poll

    Args:
        message (discord.Message): _description_

    Returns:
        str: name of emoji
    """
    return message.embeds[0].title.split(":")[2]


def get_image_file_extension_from_url(url):
    """Get the file extension of an image from its URL, with . in front

    Args:
        url (str): URL of image

    Returns:
        str: file extension of image
    """
    return "." + url.split(".")[-1]
