from io import BytesIO
import os
import re

import discord
import requests
from PIL import Image

from config import *


def validate_emoji_name(name: str):
    """Check if a string is a valid emoji name, only alphanumeric characters and underscores allowed

    Args:
        name (str): name of proposed emoji

    Returns:
        boolean: True if valid, False if not
    """
    return re.match(r"^[a-zA-Z0-9_]+$", name) is not None


def validate_image_url(url: str,type):
    """Check if a string is a valid image URL

    Args:
        url (str): URL to check
        type (str): type "emoji" or "sticker"

    Returns:
        boolean: True if valid, False if not
    """
    if type == "emoji":
        return re.match(r"^https?://.+?\.(png|jpg|jpeg|gif)$", url) is not None
    elif type == "sticker":
        return re.match(r"^https?://.+?\.(png|apng)$", url) is not None
    else:
        raise ValueError("type must be emoji or sticker")

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


def get_emoji_name_from_poll_message(message: discord.Message):
    """Get the name of the emoji from a poll

    Args:
        message (discord.Message): _description_

    Returns:
        str: name of emoji
    """
    return message.embeds[0].title.split(":")[2]


def get_pillow_image_file_format_from_url(url):
    """Get the file extension of an image from its URL, without the period, in uppercase

    Args:
        url (str): URL of image

    Returns:
        str: file extension of image
    """
    file_format = url.split(".")[-1].upper()
    if file_format == "JPG":
        file_format = "JPEG"
    return file_format


def make_and_resize_image_from_url(url, max_size_px, max_size_bytes, output_file_name = TEMP_IMAGE_FILE_NAME):
    """Resize an image to a maximum size

    Args:
        url (str): URL of image
        max_size_px (int): maximum size of image in pixels
        max_size_bytes (int): maximum size of image in bytes
        output_file_name (str): name of output file that temporary image will be saved as
    """
    image_bytes = BytesIO(requests.get(url).content)
    if url_is_gif(url):
        file_format = "GIF"
    else:
        file_format = 'PNG'
    full_output_file_name = output_file_name + "." + file_format.lower()
    Image.open(image_bytes).save(output_file_name + '.' + file_format.lower(), format = file_format)
    img = Image.open(full_output_file_name)
    
    while img.width * img.height > max_size_px or os.path.getsize(full_output_file_name) > max_size_bytes:
        img = img.resize((img.width // 2, img.height // 2))
        img.save(full_output_file_name, format = file_format)
        img = Image.open(full_output_file_name) # just to be safe that file and the object are in sync
    
    img.save("adding_image_temp." + file_format.lower(), format = file_format)

def url_is_gif(url):
    """Check if a URL is a GIF

    Args:
        url (str): URL to check

    Returns:
        boolean: True if GIF, False if not
    """
    return url.split(".")[-1].lower() == "gif"