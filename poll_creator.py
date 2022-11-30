import asyncio
import os

import interactions

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

# used to create polls
bot = interactions.Client(token)


async def check_channel_is_allowed(channel_id, ctx):
    """Check if a channel is allowed to be used for polls

    Args:
        channel_id (int): ID of channel
        ctx (interactions.Context): context object

    Returns:
        bool: whether channel is allowed
    """
    if channel_id in ALLOWED_CHANNEL_IDS:
        return True
    else:
        channel_mention = " ".join([f"<#{i}>" for i in ALLOWED_CHANNEL_IDS])
        await ctx.send(
            "This channel is not allowed to be used for polls. Please use one of the following channels: "
            + channel_mention,
            ephemeral=True,
        )
        return False


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


async def create_poll_message(ctx, title, description, url=None, image_url=None):
    """Create a poll message

    Args:
        ctx (interactions.Context): context object
        title (str): title of embed
        description (str): body of embed
        url (str, optional): url that title hyperlinks to. Defaults to None.
        image_url (str, optional): url of embed image. Defaults to None.

    Returns:
        int: ID of created poll
    """
    embed = interactions.Embed(title=title, url=url, description=description)
    embed.set_image(url=image_url)
    poll = await ctx.send(embeds=[embed])
    await poll.create_reaction(POLL_YES_EMOJI)
    await poll.create_reaction(POLL_NO_EMOJI)
    return poll.id


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
    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return

    emoji_name = kwargs["name"]
    emoji_url = kwargs["url"]

    guild = await ctx.get_guild()
    existing_emojis = guild.emojis
    existing_emoji_names = [emoji.name for emoji in existing_emojis]
    if emoji_name in existing_emoji_names:
        await ctx.send("Emoji name already on this server", ephemeral=True)
        return

    if not validate_emoji_name(emoji_name):
        await ctx.send(
            "Emoji name must be alphanumeric characters and underscores only",
            ephemeral=True,
        )
        return

    if not validate_image_url(emoji_url):
        await ctx.send(
            "Invalid image URL, emoji url must end in png, jpg, or jpeg (Animated Emojis are not currently supported)",
            ephemeral=True,
        )
        return

    poll_id = await create_poll_message(
        ctx,
        "POLL FOR NEW EMOJI: :{emoji_name}:",
        f"Should we add this emoji? (full size version below this poll)",
        emoji_url,
        emoji_url,
    )

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(poll_channel.guild_id, poll_channel.id, poll_id, "addemoji")


@bot.command(
    name="add-sticker",
    description="Make a poll to add a sticker to the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="url",
            description="URL of image to be made into a sticker",
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
    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return

    sticker_name = kwargs["name"]
    sticker_url = kwargs["url"]

    guild = await ctx.get_guild()
    existing_stickers = guild.stickers
    existing_sticker_names = [emoji.name for emoji in existing_stickers]
    if sticker_name in existing_sticker_names:
        await ctx.send("Sticker name already exists on this server", ephemeral=True)
        return

    # not sure if there are any restrictions on sticker names, but we can't have `:` for sure
    if ":" in sticker_name:
        await ctx.send("Sticker name cannot contain `:`", ephemeral=True)
        return

    if not validate_image_url(sticker_url):
        await ctx.send(
            "Invalid image URL, stick url must end in png, jpg, or jpeg (Animated stickers are not currently supported)",
            ephemeral=True,
        )
        return

    poll_id = await create_poll_message(
        ctx,
        f"POLL FOR NEW STICKER: :{sticker_name}:",
        f"Should we add this sticker? (full size version below this poll)",
        sticker_url,
        sticker_url,
    )

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(poll_channel.guild_id, poll_channel.id, poll_id, "addsticker")


@bot.command(
    name="delete-emoji",
    description="Make a poll to delete an emoji from the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="emoji-name",
            description="emoji name, WITHOUT the colons",
            focused=False,
            required=True,
        )
    ],
)
async def delete_emoji(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to delete an emoji from the server


    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        emoji_name (str): name of emoji to delete
    """
    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return

    emoji_name = kwargs["emoji-name"]

    # check if emoji exists and get emoji object if it does
    guild = await ctx.get_guild()
    existing_emojis = guild.emojis
    emoji = get_existing_emoji_by_name(emoji_name, existing_emojis)
    if emoji is None:
        await ctx.send("Emoji does not exist on this server", ephemeral=True)
        return

    emoji_str = get_emoji_formatted_str(emoji)

    poll_id = await create_poll_message(
        ctx,
        f"POLL FOR DELETING EMOJI: :{emoji_name}:",
        f"Should we delete this emoji? {emoji_str} (full size version below this poll)",
        f"https://cdn.discordapp.com/emojis/{emoji.id}.png?size=128&quality=lossless",
        f"https://cdn.discordapp.com/emojis/{emoji.id}.png?size=128&quality=lossless",
    )

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(poll_channel.guild_id, poll_channel.id, poll_id, "deleteemoji")


@bot.command(
    name="delete-sticker",
    description="Make a poll to delete an sticker from the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="sticker-name",
            description="sticker name, WITHOUT the colons, EXACTLY as it appears in the sticker list",
            focused=False,
            required=True,
        )
    ],
)
async def delete_sticker(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to delete an emoji from the server


    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        sticker_name (str): name of sticker to delete
    """
    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return

    sticker_name = kwargs["sticker-name"]

    # check if sticker exists and get sticker object if it does
    guild = await ctx.get_guild()
    existing_stickers = guild.stickers
    sticker = get_existing_emoji_by_name(sticker_name, existing_stickers)
    if sticker is None:
        ctx.send("Sticker does not exist on this server", ephemeral=True)
        return

    poll_id = await create_poll_message(
        ctx,
        f"POLL FOR DELETING STICKER: :{sticker_name}:",
        f"Should we delete this sticker? (full size version below this poll)",
        f"https://cdn.discordapp.com/stickers/{sticker.id}.png",
        f"https://cdn.discordapp.com/stickers/{sticker.id}.png",
    )

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(
        poll_channel.guild_id, poll_channel.id, poll_id, "deletesticker"
    )


@bot.command(
    name="rename-emoji",
    description="Make a poll to rename an existing emoji on the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="emoji-name",
            description="CURRENT emoji name, WITHOUT the colons",
            focused=False,
            required=True,
        ),
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="new-emoji-name",
            description="NEW emoji name, WITHOUT the colons",
            focused=False,
            required=True,
        ),
    ],
)
async def rename_emoji(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to rename an emoji on the server

    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        current_name (str): current name of the emoji
        new_name (str): proposed new name of the emoji
    """
    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return

    current_name = kwargs["emoji-name"]
    new_name = kwargs["new-emoji-name"]

    guild = await ctx.get_guild()
    existing_emojis = guild.emojis

    if not validate_emoji_name(new_name):
        await ctx.send("Invalid emoji name", ephemeral=True)
        return

    emoji = get_existing_emoji_by_name(current_name, existing_emojis)
    if emoji is None:
        await ctx.send("Emoji does not exist on this server", ephemeral=True)
        return

    # get string representation of emoji
    emoji_str = get_emoji_formatted_str(emoji)

    poll_id = await create_poll_message(
        ctx,
        f"POLL FOR RENAMING EMOJI: :{current_name}: -> :{new_name}:",
        f"Should we rename this emoji ({emoji_str}) to :{new_name}:?",
        f"https://cdn.discordapp.com/emojis/{emoji.id}.png?size=128&quality=lossless",
        f"https://cdn.discordapp.com/emojis/{emoji.id}.png?size=128&quality=lossless",
    )

    poll_channel = await ctx.get_channel()
    save_poll_to_memory(poll_channel.guild_id, poll_channel.id, poll_id, "renameemoji")


@bot.command(
    name="rename-sticker",
    description="Make a poll to rename an existing sticker on the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="sticker-name",
            description="CURRENT sticker name, WITHOUT the colons",
            focused=False,
            required=True,
        ),
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="new-sticker-name",
            description="NEW sticker name, WITHOUT the colons",
            focused=False,
            required=True,
        ),
    ],
)
async def rename_sticker(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to rename an sticker on the server

    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        current_name (str): current name of the sticker
        new_name (str): proposed new name of the sticker
    """
    current_name = kwargs["sticker-name"]
    new_name = kwargs["new-sticker-name"]

    if ":" in new_name:
        ctx.send("Sticker name cannot contain colons", ephemeral=True)
        return

    guild = await ctx.get_guild()
    existing_stickers = guild.stickers
    sticker = get_existing_emoji_by_name(current_name, existing_stickers)
    if sticker is None:
        ctx.send("Sticker does not exist on this server", ephemeral=True)
        return

    poll_id = await create_poll_message(
        ctx,
        f"POLL FOR RENAMING STICKER: :{current_name}: -> :{new_name}:",
        f"Should we rename this sticker to :{new_name}:?",
        f"https://cdn.discordapp.com/stickers/{sticker.id}.png",
        f"https://cdn.discordapp.com/stickers/{sticker.id}.png",
    )

    channel = await ctx.get_channel()
    save_poll_to_memory(channel.guild_id, channel.id, poll_id, "renamesticker")


@bot.command(
    name="change-emoji",
    description="Make a poll to change the image of an existing emoji on the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="emoji-name",
            description="emoji name, WITHOUT the colons",
            focused=False,
            required=True,
        ),
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="image-url",
            description="URL of the image to change the emoji to",
            focused=False,
            required=True,
        ),
    ],
)
async def change_emoji(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to change the image of an emoji on the server

    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        emoji_name (str): name of the emoji to change
        image_url (str): url of the image to change the emoji to
    """
    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return

    emoji_name = kwargs["emoji-name"]
    image_url = kwargs["image-url"]

    if not validate_image_url(image_url):
        await ctx.send("Invalid image URL", ephemeral=True)
        return

    guild = await ctx.get_guild()
    existing_emojis = guild.emojis
    emoji = get_existing_emoji_by_name(emoji_name, existing_emojis)
    if emoji is None:
        await ctx.send("Emoji does not exist on this server", ephemeral=True)
        return

    # get string representation of emoji
    emoji_str = get_emoji_formatted_str(emoji)

    poll_id = await create_poll_message(
        ctx,
        f"POLL FOR CHANGING EMOJI: :{emoji_name}:",
        f"Should we change this emoji ({emoji_str}) to this image?",
        image_url,
        image_url,
    )

    poll_channel = await ctx.get_channel()
    save_poll_to_memory(poll_channel.guild_id, poll_channel.id, poll_id, "changeemoji")


@bot.command(
    name="change-sticker",
    description="Make a poll to change the image of an existing sticker on the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="sticker-name",
            description="sticker name, WITHOUT the colons",
            focused=False,
            required=True,
        ),
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="image-url",
            description="URL of the image to change the sticker to",
            focused=False,
            required=True,
        ),
    ],
)
async def change_sticker(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to change the image of a sticker on the server

    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        sticker_name (str): name of the sticker to change
        image_url (str): url of the image to change the sticker to
    """
    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return

    sticker_name = kwargs["sticker-name"]
    image_url = kwargs["image-url"]

    if not validate_image_url(image_url):
        await ctx.send("Invalid image URL", ephemeral=True)
        return

    guild = await ctx.get_guild()
    existing_stickers = guild.stickers
    sticker = get_existing_emoji_by_name(sticker_name, existing_stickers)
    if sticker is None:
        await ctx.send("Sticker does not exist on this server", ephemeral=True)
        return

    poll_id = await create_poll_message(
        ctx,
        f"POLL FOR CHANGING STICKER: :{sticker_name}:",
        f"Should we change this sticker to this image?",
        image_url,
        image_url,
    )
    save_poll_to_memory(ctx.guild_id, ctx.channel_id, poll_id, "changesticker")

@bot.command(
    name="show-config",
    description="Show the current configuration of the bot",
)
async def show_config(ctx: interactions.CommandContext):
    """Show the current configuration of the bot
    Prints the current contents of `config.py` to the channel


    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
    """
    with open("config.py", "r") as f:
        config = f.read()
    f.close()
    await ctx.send(f"```py\n{config}\n```", ephemeral=True)

bot.start()
