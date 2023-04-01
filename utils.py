import datetime as dt
import os
import re
from io import BytesIO

import discord
import requests
from PIL import Image

from config import MINIMUM_VOTES_FOR_POLL
from config import NITRO_USER_VOTING_WEIGHT_FUNCTION
from config import POLL_NO_EMOJI
from config import POLL_PASS_THRESHOLD
from config import POLL_YES_EMOJI
from config import PRIVILEGED_USER_IDS
from config import PRIVILEGED_USER_VOTE_WEIGHT
from config import TEMP_IMAGE_FILE_NAME


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
        type (str): type "emoji" or "sticker"

    Returns:
        boolean: True if valid, False if not
    """
    return re.match(r"^https?://.+?\.(png|jpg|jpeg|PNG|JPG|JPEG)$", url) is not None


async def get_votes(message: discord.Message, self_bot_id: int,guild: discord.Guild):
    """Get the votes for a poll

    Args:
        message (discord.Message): message object of the poll
        self_bot_id (int): ID of the bot running the check (to ignore its own reactions)
        guild (discord.guild): Guild object representing the server

    Returns:
        int, int: (weighted) number of votes for and number of votes against
    """
    yes_count = 0
    no_count = 0
    for reaction in message.reactions:
        if reaction.emoji == POLL_YES_EMOJI:
            async for user in reaction.users():
                if user.id == self_bot_id:
                    continue
                elif user.id in PRIVILEGED_USER_IDS:
                    yes_count += 1 + PRIVILEGED_USER_VOTE_WEIGHT
                else:
                    yes_count += 1
                member = guild.get_member(user.id)
                if member is not None:
                    if member.premium_since is not None:
                        yes_count += NITRO_USER_VOTING_WEIGHT_FUNCTION(
                            abs(
                                (dt.datetime.now(dt.timezone.utc) - member.premium_since).days
                            )
                        )
        elif reaction.emoji == POLL_NO_EMOJI:
            async for user in reaction.users():
                if user.id == self_bot_id:
                    continue
                elif user.id in PRIVILEGED_USER_IDS:
                    no_count += 1 + PRIVILEGED_USER_VOTE_WEIGHT
                else:
                    no_count += 1
                member = guild.get_member(user.id)
                if member is not None:
                    if member.premium_since is not None:
                        no_count += NITRO_USER_VOTING_WEIGHT_FUNCTION(
                            abs(
                                (dt.datetime.now(dt.timezone.utc) - member.premium_since).days
                            )
                        )
    return (yes_count, no_count)


async def get_poll_result(
    message: discord.Message, self_bot_id: int, yes_count=None, no_count=None
):
    """Get the result of a poll

    Args:
        message (discord.Message): message object of the poll
        self_bot_id (int): ID of the bot running the check (to ignore its own reactions)
        yes_count (int, Optional): number of votes for yes, if already pre-calculated
        no_count (int, Optional): number of votes for no, if already pre-calculated

    Returns:
        boolean: True if poll passes, False if not. Based on POLL_PASS_THRESHOLD in config.py
    """
    if yes_count is None and no_count is None:
        yes_count, no_count = await get_votes(message, self_bot_id, message.guild)
    if yes_count + no_count < MINIMUM_VOTES_FOR_POLL or yes_count + no_count == 0:
        return False
    else:
        if yes_count / (yes_count + no_count) >= POLL_PASS_THRESHOLD:
            return True
        else:
            return False


async def get_print_string_for_poll_result(
    message: discord.Message,
    self_bot_id: int,
    poll_type: str,
    yes_count=None,
    no_count=None,
):
    """Get a string to print for the result of a poll

    Args:
        message (discord.Message): message object of the poll
        self_bot_id (int): ID of the bot running the check (to ignore its own reactions)
        poll_type (str): string indicating the poll type, e.g. "changeemoji"
        yes_count (int, Optional): number of votes for yes, if already pre-calculated
        no_count (int, Optional): number of votes for no, if already pre-calculated

    Returns:
        str: string to print
    """

    poll_short_title = f"***Poll to {pretty_poll_type(poll_type)} `{get_emoji_name_from_poll_message(message)}` results***:\n"

    if yes_count is None and no_count is None:
        yes_count, no_count = await get_votes(message, self_bot_id, message.guild)
    if yes_count + no_count < MINIMUM_VOTES_FOR_POLL or yes_count + no_count == 0:
        return f"Poll didn't reach the minimum number of votes ({MINIMUM_VOTES_FOR_POLL}) to pass. Had only {yes_count + no_count} vote(s)."
    result = display_percent_str(yes_count / (yes_count + no_count))
    poll_passed = await get_poll_result(message, self_bot_id)
    if poll_passed:
        return (
            poll_short_title
            + f"Poll passed with {yes_count} vote(s) for and {no_count} vote(s) against, leading to a {result} show in favor, above the threshold of "
            + display_percent_str(POLL_PASS_THRESHOLD)
            + " needed to pass."
        )
    else:
        return (
            poll_short_title
            + f"Poll failed with {yes_count} vote(s) for and {no_count} vote(s) against, leading to a {result} show in favor, below the threshold of "
            + display_percent_str(POLL_PASS_THRESHOLD)
            + " needed to pass."
        )


def get_emoji_name_from_poll_message(message: discord.Message, new=False):
    """Get the name of the emoji from a poll

    Args:
        message (discord.Message): message object of the poll
        new (boolean, Optional): whether the poll to get the new emoji name, only used in renaming polls

    Returns:
        str: name of emoji
    """
    if new:
        return message.embeds[0].title.split(":")[4]
    else:
        return message.embeds[0].title.split(":")[2]


def make_and_resize_image_from_url(
    url, max_size_px, max_size_bytes, output_file_name=TEMP_IMAGE_FILE_NAME
):
    """Resize an image to a maximum size

    Args:
        url (str): URL of image
        max_size_px (int): maximum size of image in pixels
        max_size_bytes (int): maximum size of image in bytes
        output_file_name (str): name of output file that temporary image will be saved as
    """
    image_bytes = BytesIO(requests.get(url).content)

    full_output_file_name = output_file_name + ".png"
    Image.open(image_bytes).save(full_output_file_name, format="PNG")
    img = Image.open(full_output_file_name)

    while (
        img.width * img.height > max_size_px
        or os.path.getsize(full_output_file_name) > max_size_bytes
    ):
        img = img.resize((img.width // 2, img.height // 2))
        img.save(full_output_file_name, format="PNG")
        img = Image.open(
            full_output_file_name
        )  # just to be safe that file and the object are in sync

    img.save(full_output_file_name, format="PNG")


def get_existing_emoji_by_name(name, existing_emojis):
    """Get an existing emoji (or sticker) by name

    Args:
        name (str): name of emoji/sticker
        existing_emojis (list[Union(interaction.Emoji,discord.Emoji)]): list of existing emojis/stickers
    """
    existing_emoji_names = [emoji.name for emoji in existing_emojis]
    if name not in existing_emoji_names:
        return None
    else:
        for existing_emoji in existing_emojis:
            if existing_emoji.name == name:
                return existing_emoji


def get_emoji_formatted_str(emoji):
    """Get a string to print for an emoji

    Args:
        emoji (Union(interaction.Emoji,discord.Emoji)): emoji to print

    Returns:
        str: string to print
    """
    if emoji.animated:
        animated_str = "a"
    else:
        animated_str = ""
    return f"<{animated_str}:{emoji.name}:{emoji.id}>"


def display_percent_str(n):
    """Get a string to print for a percentage

    Args:
        n (float): percentage to print

    Returns:
        str: string to print
    """
    return str(round(n * 100, 2)) + "%"


def extract_emoji_name_from_syntax(emoji_syntax):
    """Extract emoji name from a discord

    Args:
        emoji_syntax (str): discord-formatted string in `<:NAME:ID>` (e.g. `<:BigChungus:54897465321321>`)

    Returns:
        str: emoji name if found, returns the string if format did not produce a match
    """
    match = re.match(r"<:(\w+):\d+>", emoji_syntax)

    if match:
        emoji_name = match.group(1)
        return emoji_name
    else:
        return emoji_syntax


def pretty_poll_type(poll_type):
    """Puts a space between the poll type and the object it is about, e.g. "changeemoji" -> "change emoji"

    Args:
        poll_type (str): string representing the poll type of the poll

    Returns:
        str: string with a space as described above
    """
    pretty_name = poll_type
    emoji_like_names = ("emoji", "sticker")
    for name in emoji_like_names:
        if name in poll_type:
            pretty_name = pretty_name.replace(name, " " + name)
    return pretty_name
