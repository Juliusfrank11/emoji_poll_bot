import discord
from utils import *
from config import *
import os
import logging
import asyncio
import datetime as dt

#Setup
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
        for guild in os.listdir('active_polls'):
            for channel in os.listdir(f'active_polls/{guild}'):
                try:
                    channel = client.get_channel(int(channel))
                    for message in os.listdir(f'active_polls/{guild}/{channel.id}'):
                        message_id, poll_type = message.split('_')
                        message = await channel.fetch_message(int(message_id))
                        if (dt.datetime.utcnow() - message.created_at).total_seconds() > POLL_DURATION:
                            if get_poll_result(message):
                                await channel.send('Poll passed, adding emoji')
                            else:
                                await channel.send('Poll failed, not adding emoji')
                except discord.errors.NotFound:
                    logging.info(f"Channel {channel} not found, skipping")
                    os.remove(f'active_polls/{guild}/{channel}')
        await asyncio.sleep(WAIT_TIME_BETWEEN_CHECKS)
        
                                    
        
            
client.run(token)