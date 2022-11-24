import asyncio
import datetime as dt
import logging
import os
from io import BytesIO

import discord
import requests

from config import *
from utils import *

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


@client.event
async def on_ready():
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
                    if get_poll_result(message):
                        # adding emoji/sticker
                        await channel.send(
                                "Poll passes!",
                                reference=message,
                                delete_after=DELETE_NOTIFICATIONS_AFTER,
                            )
                        if AUTOMATICALLY_ADD_EMOJIS:
                            if poll_type.startswith("add"):
                                image_url = message.embeds[0].image.url
                                request = requests.get(image_url)
                                if request.status_code == 200:
                                    name = get_emoji_name_from_poll_message(message)

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
                                        new_emoji = await channel.guild.create_custom_emoji(
                                            name=name, image=image
                                        )
                                        await channel.send(
                                            f"Emoji added: {str(new_emoji)}",
                                            reference=message,
                                        )
                                    # add sticker
                                    elif poll_type.endswith("sticker"):
                                        new_sticker = await channel.guild.create_sticker(
                                            name=name,
                                            description="sticker automatically added by poll",
                                            emoji="🤖",  # not sure what the point of this attribute is, but it's required
                                            file=discord.File(
                                                fp=temp_image_file_name,
                                                filename="sticker.png",
                                            ),
                                        )
                                        await channel.send(
                                            f"Sticker added: :{name}:",
                                            stickers=[new_sticker],
                                            reference=message,
                                        )
                                else:
                                    await channel.send(
                                        "Failed to add emoji, image url returned status code "
                                        + str(request.status_code),
                                        reference=message,
                                    )
                                os.remove(temp_image_file_name)
                            # deleting emoji/sticker
                            elif poll_type.startswith("delete"):
                                name = get_emoji_name_from_poll_message(message)
                                sticker_or_emoji_found = False
                                # deleting emoji
                                if poll_type.endswith("emoji"):
                                    existing_emojis = channel.guild.emojis
                                    for emoji in existing_emojis:
                                        if emoji.name == name:
                                            await emoji.delete()
                                            await channel.send(
                                                f"Emoji deleted: :{name}:",
                                                reference=message,
                                            )
                                            sticker_or_emoji_found = True
                                            break
                                # deleting sticker
                                elif poll_type.endswith("sticker"):
                                    for sticker in channel.guild.stickers:
                                        if sticker.name == name:
                                            await sticker.delete()
                                            await channel.send(
                                                f"Sticker deleted: :{name}:",
                                                reference=message,
                                            )
                                            sticker_or_emoji_found = True
                                            break
                                if not sticker_or_emoji_found:
                                    await channel.send(
                                        f"Failed to delete emoji/sticker, no emoji/sticker with name :{name}: found\nCheck your spelling and capitalization and make sure you're using delete-emoji for emojis and delete-sticker for stickers",
                                        reference=message,
                                    )
                    else:
                        await channel.send("Poll failed to pass", reference=message)
                    os.remove(
                        f"active_polls/{guild_id}/{channel.id}/{message.id}_{poll_type}"
                    )
            except discord.errors.NotFound:
                logging.info(f"Channel {channel} not found, skipping")
                try:
                    os.remove(f"active_polls/{guild_id}/{channel}")
                except FileNotFoundError:
                    pass
        await asyncio.sleep(WAIT_TIME_BETWEEN_CHECKS)


client.run(token)
