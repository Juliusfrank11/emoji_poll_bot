import asyncio
import copy
import datetime as dt
import logging
import os

import discord
import requests

from config import AUTOMATICALLY_ADD_EMOJIS
from config import MAX_IMAGE_FILE_SIZE
from config import MAX_IMAGE_SIZE
from config import POLL_DURATION
from config import POLL_UPDATE_POST_TIMES
from config import TEMP_IMAGE_FILE_NAME
from config import TOKEN_FILE_NAME
from config import WAIT_TIME_BETWEEN_CHECKS
from utils import get_emoji_name_from_poll_message
from utils import get_existing_emoji_by_name
from utils import get_poll_result
from utils import get_print_string_for_poll_result
from utils import get_votes
from utils import make_and_resize_image_from_url
from utils import pretty_poll_type

# Setup
## read token from file
f = open(TOKEN_FILE_NAME, "r")
token = f.read().strip()
f.close()

## make active_polls directory if it doesn't exist
if "active_polls" not in os.listdir():
    os.mkdir("active_polls")

# used to get poll results
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# clean existing images
for file_name in os.listdir():
    if file_name.startswith(TEMP_IMAGE_FILE_NAME):
        os.remove(file_name)


def get_active_polls_list_from_memory():
    """gets a list of (guild_id, channel_id, message_id, poll_type) tuples for each active poll in memory

    Returns:
        List[Tuple[int,int,int,str]]: List of (guild_id, channel_id, message_id, poll_type) tuples
        poll_type is one of "addemoji", "deleteemoji", "addsticker", "deletesticker"
    """
    combos = []
    for guild_id in os.listdir("active_polls"):
        for channel_id in os.listdir(f"active_polls/{guild_id}"):
            for poll in os.listdir(f"active_polls/{guild_id}/{channel_id}"):
                poll_id, poll_type = poll.split("_")
                combos.append((int(guild_id), int(channel_id), int(poll_id), poll_type))
    return combos


async def add_poll_result(poll: discord.Message, poll_type: str):
    """Add an emoji to the server

    Args:
        poll (discord.Message): poll message
        poll_type (str): type of poll, either "emoji" or "sticker"
    """
    image_url = poll.embeds[0].image.url
    request = requests.get(image_url)
    if request.status_code == 200:
        name = get_emoji_name_from_poll_message(poll)

        # resizing image if necessary
        make_and_resize_image_from_url(
            image_url,
            MAX_IMAGE_SIZE,
            MAX_IMAGE_FILE_SIZE,
            TEMP_IMAGE_FILE_NAME,
        )

        # getting image bytes
        for file in os.listdir():
            if file.startswith("adding_image_temp."):
                temp_image_file_name = file
                f = open(temp_image_file_name, "rb")
                image = f.read()
                f.close()
                break

        # adding emoji
        if poll_type.endswith("emoji"):
            new_emoji = await poll.channel.guild.create_custom_emoji(
                name=name, image=image
            )
            await poll.channel.send(
                f"Emoji added: {str(new_emoji)}",
                reference=poll,
            )
        # add sticker
        elif poll_type.endswith("sticker"):
            new_sticker = await poll.channel.guild.create_sticker(
                name=name,
                description="sticker automatically added by poll",
                emoji="🤖",  # not sure what the point of this attribute is, but it's required
                file=discord.File(
                    fp=temp_image_file_name,
                    filename="sticker.png",
                ),
            )
            await poll.channel.send(
                f"Sticker added: :{name}:",
                stickers=[new_sticker],
                reference=poll,
            )
    else:
        await poll.channel.send(
            "Failed to add emoji/sticker, image could not be retrieved, Status code: "
            + str(request.status_code),
            reference=poll,
        )


async def delete_poll_result(poll: discord.Message, poll_type: str):
    """Delete an emoji from the server

    Args:
        poll (discord.Message): poll message
        poll_type (str): type of poll, either "emoji" or "sticker"
    """
    name = get_emoji_name_from_poll_message(poll)
    emoji_or_sticker_found = False
    if poll_type.endswith("emoji"):
        emoji = get_existing_emoji_by_name(name, poll.channel.guild.emojis)
        if emoji is not None:
            await emoji.delete()
            emoji_or_sticker_found = True
            await poll.channel.send(
                f"Emoji deleted: {str(emoji)}",
                reference=poll,
            )
    elif poll_type.endswith("sticker"):
        sticker = get_existing_emoji_by_name(name, poll.channel.guild.stickers)
        if sticker is not None:
            await sticker.delete()
            emoji_or_sticker_found = True
            await poll.channel.send(
                f"Sticker deleted: :{name}:",
                reference=poll,
            )
    if not emoji_or_sticker_found:
        await poll.channel.send(
            "Failed to delete emoji/sticker, emoji/sticker not found",
            reference=poll,
        )


async def rename_poll_result(poll: discord.Message, poll_type: str):
    """Rename an emoji from the server

    Args:
        poll (discord.Message): poll message
        poll_type (str): type of poll, either "emoji" or "sticker"
    """
    old_name = get_emoji_name_from_poll_message(poll)
    new_name = get_emoji_name_from_poll_message(poll, new=True)
    emoji_or_sticker_found = False
    if poll_type.endswith("emoji"):
        emoji = get_existing_emoji_by_name(old_name, poll.channel.guild.emojis)
        if emoji is not None:
            emoji = await emoji.edit(name=new_name)
            emoji_or_sticker_found = True
            await poll.channel.send(
                f"Emoji ({str(emoji)}) renamed `:{old_name}: -> :{new_name}:`",
                reference=poll,
            )

    elif poll_type.endswith("sticker"):
        sticker = get_existing_emoji_by_name(old_name, poll.channel.guild.stickers)
        if sticker is not None:
            sticker = await sticker.edit(name=new_name)
            emoji_or_sticker_found = True
            await poll.channel.send(
                f"Sticker renamed: `:{old_name}: -> :{new_name}:`",
                stickers=[sticker],
                reference=poll,
            )
    if not emoji_or_sticker_found:
        await poll.channel.send(
            "Failed to rename emoji/sticker, emoji/sticker not found",
            reference=poll,
        )


async def change_poll_result(poll: discord.Message, poll_type: str):
    image_url = poll.embeds[0].image.url
    request = requests.get(image_url)
    name = get_emoji_name_from_poll_message(poll)
    emoji_or_sticker_found = False
    if request.status_code == 200:
        make_and_resize_image_from_url(
            image_url,
            MAX_IMAGE_SIZE,
            MAX_IMAGE_FILE_SIZE,
            TEMP_IMAGE_FILE_NAME,
        )

        # getting image bytes
        for file in os.listdir():
            if file.startswith("adding_image_temp."):
                temp_image_file_name = file
                f = open(temp_image_file_name, "rb")
                image = f.read()
                f.close()
                break

        if poll_type.endswith("emoji"):
            emoji = get_existing_emoji_by_name(name, poll.channel.guild.emojis)
            if emoji is not None:
                emoji_or_sticker_found = True
                await emoji.delete()
                new_emoji = await poll.guild.create_custom_emoji(name=name, image=image)
                await poll.channel.send(
                    f"Emoji changed: {str(new_emoji)}",
                    reference=poll,
                )
        elif poll_type.endswith("sticker"):
            sticker = get_existing_emoji_by_name(name, poll.channel.guild.stickers)
            if sticker is not None:
                emoji_or_sticker_found = True
                await sticker.delete()
                new_sticker = await poll.channel.guild.create_sticker(
                    name=name,
                    description="sticker automatically added by poll",
                    emoji="🤖",  # not sure what the point of this attribute is, but it's required
                    file=discord.File(
                        fp=temp_image_file_name,
                        filename="sticker.png",
                    ),
                )
                await poll.channel.send(
                    f"Sticker changed: :{name}:",
                    stickers=[new_sticker],
                    reference=poll,
                )
        if not emoji_or_sticker_found:
            await poll.channel.send(
                "Failed to change emoji/sticker, emoji/sticker not found",
                reference=poll,
            )
    else:
        await poll.channel.send(
            "Failed to add emoji/sticker, image could not be retrieved, Status code: "
            + str(request.status_code),
            reference=poll,
        )


async def post_update():
    """Post updates"""
    channels_to_polls = {}
    for (
        guild_id,
        channel_id,
        message_id,
        poll_type,
    ) in get_active_polls_list_from_memory():
        for channel_id in os.listdir(f"active_polls/{guild_id}"):
            # if there are active polls, create strings for the update message
            if len(os.listdir(f"active_polls/{guild_id}/{channel_id}")) > 0:
                channel_id = int(channel_id)
                channels_to_polls[channel_id] = []
                channel = client.get_channel(channel_id)
                for poll in os.listdir(f"active_polls/{guild_id}/{channel_id}"):
                    poll_id, poll_type = poll.split("_")
                    channels_to_polls[channel_id].append(
                        "> https://discord.com/channels/{}/{}/{} {} `{}`\n".format(
                            guild_id,
                            channel_id,
                            poll_id,
                            pretty_poll_type(poll_type),
                            get_emoji_name_from_poll_message(
                                await channel.fetch_message(poll_id)
                            ),
                        )
                    )
    # put together and post update message
    for channel_id_to_post_to, polls in channels_to_polls.items():
        if len(polls) > 0:
            channel_to_post_to = client.get_channel(channel_id_to_post_to)
            message = "Here's an update on currently active polls:\n"
            while len(message) < 2000 and len(polls) > 0:
                try:
                    if len(message + polls[0]) < 2000:
                        message += polls.pop(0)
                    else:
                        await channel_to_post_to.send(message)
                        message = ""
                except IndexError:
                    await channel_to_post_to.send(message)


@client.event
async def on_ready():
    last_update_hour = -1
    while True:
        for (
            guild_id,
            channel_id,
            message_id,
            poll_type,
        ) in get_active_polls_list_from_memory():
            try:
                channel = client.get_channel(channel_id)
                message = await channel.fetch_message(message_id)
                if (
                    dt.datetime.now(dt.timezone.utc) - message.created_at
                ).total_seconds() > POLL_DURATION:
                    yes_count, no_count = await get_votes(
                        message, self_bot_id=client.user.id
                    )
                    await channel.send(
                        await get_print_string_for_poll_result(
                            message,
                            self_bot_id=client.user.id,
                            poll_type=poll_type,
                            yes_count=yes_count,
                            no_count=no_count,
                        ),
                        reference=message,
                    )
                    if (
                        await get_poll_result(
                            message,
                            self_bot_id=client.user.id,
                            yes_count=yes_count,
                            no_count=no_count,
                        )
                        and AUTOMATICALLY_ADD_EMOJIS
                    ):
                        if poll_type.startswith("add"):
                            await add_poll_result(message, poll_type)
                        elif poll_type.startswith("delete"):
                            await delete_poll_result(message, poll_type)
                        elif poll_type.startswith("rename"):
                            await rename_poll_result(message, poll_type)
                        elif poll_type.startswith("change"):
                            await change_poll_result(message, poll_type)
                    os.remove(
                        f"active_polls/{guild_id}/{channel.id}/{message.id}_{poll_type}"
                    )
            except discord.errors.NotFound:
                logging.info(
                    f"Message {guild_id}-{channel_id}-{message_id} not found, skipping"
                )
                try:
                    os.remove(
                        f"active_polls/{guild_id}/{channel_id}/{message_id}_{poll_type}"
                    )
                except FileNotFoundError:
                    pass
        # post updates
        hour_right_now = dt.datetime.utcnow().hour
        if (
            hour_right_now in POLL_UPDATE_POST_TIMES
            and hour_right_now != last_update_hour
        ):
            await post_update()
            last_update_hour = hour_right_now

        await asyncio.sleep(WAIT_TIME_BETWEEN_CHECKS)


client.run(token)
