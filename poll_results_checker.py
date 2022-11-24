import discord
from utils import *
from config import *
import os
import logging
import asyncio
import datetime as dt
import requests
import shutil
from io import BytesIO

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


@client.event
async def on_ready():
    while True:
        for guild in os.listdir("active_polls"):
            for channel in os.listdir(f"active_polls/{guild}"):
                try:
                    channel = client.get_channel(int(channel))
                    for message in os.listdir(f"active_polls/{guild}/{channel.id}"):
                        message_id, poll_type = message.split("_")
                        message = await channel.fetch_message(int(message_id))
                        if (
                            dt.datetime.now(dt.timezone.utc) - message.created_at
                        ).total_seconds() > POLL_DURATION:
                            if get_poll_result(message):
                                if poll_type == "add-emoji":
                                    await channel.send(
                                        "Poll passed, adding emoji",
                                        reference=message,
                                        delete_after=DELETE_NOTIFICATIONS_AFTER,
                                    )
                                    request = requests.get(message.embeds[0].image.url)
                                    file_extension = get_image_file_extension_from_url(
                                        message.embeds[0].image.url
                                    )
                                    if request.status_code == 200:
                                        name = get_emoji_name_from_poll_message(message)
                                        with BytesIO(request.content) as image:
                                            new_emoji = await channel.guild.create_custom_emoji(
                                                name=name, image=image.read()
                                            )
                                            await channel.send(
                                                "Emoji added: " + str(new_emoji),
                                                reference=message,
                                            )
                                    else:
                                        await channel.send(
                                        "Failed to add emoji, image url returned status code "
                                        + str(request.status_code),
                                        reference=message,
                                    )
                            else:
                                await channel.send("Poll failed", reference=message)
                            os.remove(f"active_polls/{guild}/{channel.id}/{message.id}_{poll_type}")
                except discord.errors.NotFound:
                    logging.info(f"Channel {channel} not found, skipping")
                    os.remove(f"active_polls/{guild}/{channel}")
        await asyncio.sleep(WAIT_TIME_BETWEEN_CHECKS)


client.run(token)
