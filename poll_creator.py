import interactions
from utils import *
from config import *
import asyncio
import os

# Setup
## read token from file
f = open(TOKEN_FILE_NAME, "r")
token = f.read().strip()
f.close()

## make active_polls directory if it doesn't exist
if "active_polls" not in os.listdir():
    os.mkdir("active_polls")

# used to create polls
bot = interactions.Client(token)


def save_poll_to_memory(guild_id, channel_id, message_id, poll_type):
    """Save a poll to memory

    Args:
        guild_id (int): ID of guild
        channel_id (int): ID of channel
        message_id (int): ID of message
        poll_type (str): type of poll
    """
    try:
        os.mkdir(f"active_polls/{guild_id}")
    except FileExistsError:
        pass
    finally:
        try:
            os.mkdir(f"active_polls/{guild_id}/{channel_id}")
        except FileExistsError:
            pass
    f = open(
        f"active_polls/{guild_id}/{channel_id}/{message_id}_{poll_type}",
        "w",
    )
    f.close()


@bot.command(
    name="add-emoji",
    description="Make a poll to add an emoji to the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="url",
            description="URL of image to be made into an emoji",
            focused=False,
            required=True,
        ),
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="name",
            description="name of emoji",
            focused=False,
            required=True,
        ),
    ],
)
async def add_emoji(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to add an emoji to the server


    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        url (str): URL of image to be made into an emoji
        name (str): name of the emoji
    """
    emoji_name = kwargs["name"]
    emoji_url = kwargs["url"]

    if not validate_emoji_name(emoji_name):
        await ctx.send(
            "Emoji name must be alphanumeric characters and underscores only"
        )
        await asyncio.sleep(DELETE_NOTIFICATIONS_AFTER)
        await ctx.delete()
        return

    if not validate_image_url(emoji_url):
        await ctx.send("Invalid image URL, url must end in png, jpg, jpeg, or gif")
        await asyncio.sleep(DELETE_NOTIFICATIONS_AFTER)
        await ctx.delete()
        return

    embed = interactions.Embed(
        title=f"POLL FOR NEW EMOJI: :{emoji_name}:",
        description="Should we add this emoji? (full size version below this poll)",
        url=emoji_url,
    )
    embed.set_image(url=emoji_url)
    poll = await ctx.send(embeds=embed)
    await poll.create_reaction(POLL_YES_EMOJI)
    await poll.create_reaction(POLL_NO_EMOJI)

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(poll_channel.guild_id, poll_channel.id, poll.id, "addemoji")


@bot.command(
    name="add-sticker",
    description="Make a poll to add an sticker to the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="url",
            description="URL of image to be made into an sticker",
            focused=False,
            required=True,
        ),
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="name",
            description="name of sticker",
            focused=False,
            required=True,
        ),
    ],
)
async def add_sticker(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to add a sticker to the server


    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        url (str): URL of image to be made into an sticker
        name (str): name of the sticker
    """
    sticker_name = kwargs["name"]
    sticker_url = kwargs["url"]

    # not sure if there are any restrictions on sticker names, but we can't have `:` for sure
    if ":" in sticker_name:
        await ctx.send("Sticker name cannot contain `:`")
        await asyncio.sleep(DELETE_NOTIFICATIONS_AFTER)
        await ctx.delete()
        return

    if not validate_image_url(sticker_url):
        await ctx.send("Invalid image URL, url must end in png, jpg, jpeg, or gif")
        await asyncio.sleep(DELETE_NOTIFICATIONS_AFTER)
        await ctx.delete()
        return

    embed = interactions.Embed(
        title=f"POLL FOR NEW STICKER: :{sticker_name}:",
        description="Should we add this sticker? (full size version below this poll)",
        url=sticker_url,
    )
    embed.set_image(url=sticker_url)
    poll = await ctx.send(embeds=embed)
    await poll.create_reaction(POLL_YES_EMOJI)
    await poll.create_reaction(POLL_NO_EMOJI)

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(poll_channel.guild_id, poll_channel.id, poll.id, "addsticker")

@bot.command(
    name="delete-emoji",
    description="Make a poll to delete an emoji from the server",
    options=[
        interactions.Option(
            type = interactions.OptionType.STRING,
            name = "emoji-name",
            description = "emoji name, WITHOUT the colons",
            focused = False,
            required = True,
        )
    ]
)
async def delete_emoji(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to delete an emoji from the server


    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        emoji_name (str): name of emoji to delete
    """
    emoji_name = kwargs["emoji-name"]
    
    existing_emojis = await ctx.get_guild().emojis
    existing_emoji_names = [emoji.name for emoji in existing_emojis]
    if emoji_name not in existing_emoji_names:
        await ctx.send("Emoji does not exist on this server")
        await asyncio.sleep(DELETE_NOTIFICATIONS_AFTER)
        await ctx.delete()
        return

    embed = interactions.Embed(
        title=f"POLL FOR DELETING EMOJI: :{emoji_name}:",
        description="Should we delete this emoji?",
    )
    poll = await ctx.send(embeds=embed)
    await poll.create_reaction(POLL_YES_EMOJI)
    await poll.create_reaction(POLL_NO_EMOJI)

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(poll_channel.guild_id, poll_channel.id, poll.id, "deleteemoji")

@bot.command(
    name="delete-sticker",
    description="Make a poll to delete an sticker from the server",
    options=[
        interactions.Option(
            type = interactions.OptionType.STRING,
            name = "sticker-name",
            description = "sticker name, WITHOUT the colons, EXACTLY as it appears in the sticker list",
            focused = False,
            required = True,
        )
    ]
)
async def delete_emoji(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to delete an emoji from the server


    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        sticker_name (str): name of sticker to delete
    """
    sticker_name = kwargs["sticker-name"]
    
    existing_stickers = await ctx.get_guild().stickers
    existing_sticker_names = [emoji.name for emoji in existing_stickers]
    if sticker_name not in existing_sticker_names:
        await ctx.send("sticker does not exist on this server")
        await asyncio.sleep(DELETE_NOTIFICATIONS_AFTER)
        await ctx.delete()
        return

    embed = interactions.Embed(
        title=f"POLL FOR DELETING STICKER: :{sticker_name}:",
        description="Should we delete this sticker?",
    )
    poll = await ctx.send(embeds=embed)
    await poll.create_reaction(POLL_YES_EMOJI)
    await poll.create_reaction(POLL_NO_EMOJI)

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(poll_channel.guild_id, poll_channel.id, poll.id, "deletesticker")


bot.start()