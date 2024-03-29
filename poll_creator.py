import os

import interactions

from config import ACTIVE_POLLS_PER_USER_LIMIT
from config import ALLOWED_CHANNEL_IDS
from config import POLL_NO_EMOJI
from config import POLL_YES_EMOJI
from config import PROTECTED_EMOTE_NAMES
from config import TOKEN_FILE_NAME
from utils import check_if_user_reach_poll_limit
from utils import display_percent_str
from utils import extract_emoji_name_from_syntax
from utils import get_emoji_formatted_str
from utils import get_existing_emoji_by_name
from utils import pretty_poll_type
from utils import validate_emoji_name
from utils import validate_image_url


# Setup
## read token from file
f = open(TOKEN_FILE_NAME, "r")
token = f.read().strip()
f.close()

# emoji and sticker limits for premium tiers
emoji_limits = {
    0: 50,
    1: 100,
    2: 150,
    3: 250,
}
sticker_limits = {
    0: 5,
    1: 15,
    2: 30,
    3: 60,
}

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


async def check_emoji_is_modifiable(emoji_name, ctx):
    """Check if an emoji name is modifiable

    Args:
        emoji_name (str): name of emoji
        ctx (interactions.Context): context object

    Returns:
        bool: whether emoji is modifiable
    """
    if emoji_name in PROTECTED_EMOTE_NAMES:
        await ctx.send("This name is protected and can not be modified", ephemeral=True)
        return False
    else:
        return True


async def check_user_reached_limit(ctx: interactions.CommandContext):
    guild = await ctx.get_guild()

    guild_id = guild.id

    if check_if_user_reach_poll_limit(guild_id, ctx.channel_id, int(ctx.user.id)):
        await ctx.send(
            f"You have reached the limit of number of active polls per user, {ACTIVE_POLLS_PER_USER_LIMIT}",
            ephemeral=True,
        )
        return True
    else:
        return False


def save_poll_to_memory(guild_id, channel_id, message_id, user_id, poll_type):
    """Save a poll to memory

    Args:
        guild_id (int): ID of guild
        channel_id (int): ID of channel
        message_id (int): ID of message
        user_id (Snowflake): ID of poll creator
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
    with open(
        f"active_polls/{guild_id}/{channel_id}/{message_id}_{poll_type}",
        "w",
    ) as f:
        f.write(str(user_id))


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
    emoji_name = kwargs["name"]
    emoji_url = kwargs["url"]

    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return
    if await check_user_reached_limit(ctx):
        return

    if not await check_emoji_is_modifiable(emoji_name, ctx):
        return

    guild = await ctx.get_guild()
    existing_emojis = guild.emojis
    if get_existing_emoji_by_name(emoji_name, existing_emojis) is not None:
        await ctx.send("Emoji name already on this server", ephemeral=True)
        return

    if (
        len([e for e in existing_emojis if not e.animated])
        + len(
            [
                p
                for p in os.listdir(f"active_polls/{guild.id}/{ctx.channel_id}")
                if p.endswith("addemoji")
            ]
        )
        >= emoji_limits[guild.premium_tier]
    ):
        await ctx.send(
            "Emoji limit reached for this server OR too many active adding polls",
            ephemeral=True,
        )
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
        f"POLL FOR NEW EMOJI: :{emoji_name}:",
        "Should we add this emoji? (full size version below this poll)",
        emoji_url,
        emoji_url,
    )

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(
        poll_channel.guild_id, poll_channel.id, poll_id, ctx.user.id, "addemoji"
    )


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
        ctx (interactions.CommandContext): context of the command,
            inherited from decorator
        url (str): URL of image to be made into an sticker
        name (str): name of the sticker
    """
    sticker_name = kwargs["name"]
    sticker_url = kwargs["url"]

    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return
    if await check_user_reached_limit(ctx):
        return
    if not await check_emoji_is_modifiable(sticker_name, ctx):
        return

    guild = await ctx.get_guild()
    existing_stickers = guild.stickers
    if get_existing_emoji_by_name(sticker_name, existing_stickers) is not None:
        await ctx.send("Sticker name already exists on this server", ephemeral=True)
        return
    if (
        len(existing_stickers)
        + len(
            [
                p
                for p in os.listdir(f"active_polls/{guild.id}/{ctx.channel_id}")
                if p.endswith("addsticker")
            ]
        )
        >= sticker_limits[guild.premium_tier]
    ):
        await ctx.send(
            "Sticker limit reached for this server OR too many active adding polls",
            ephemeral=True,
        )
        return

    # not sure if there are any restrictions on sticker names,
    # but we can't have `:` for sure
    if ":" in sticker_name:
        await ctx.send("Sticker name cannot contain `:`", ephemeral=True)
        return

    if not validate_image_url(sticker_url):
        await ctx.send(
            """Invalid image URL, stick url must end in png, jpg, or 
            jpeg (Animated stickers are not currently supported)""",
            ephemeral=True,
        )
        return

    poll_id = await create_poll_message(
        ctx,
        f"POLL FOR NEW STICKER: :{sticker_name}:",
        "Should we add this sticker? (full size version below this poll)",
        sticker_url,
        sticker_url,
    )

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(
        poll_channel.guild_id, poll_channel.id, poll_id, ctx.user.id, "addsticker"
    )


@bot.command(
    name="delete-emoji",
    description="Make a poll to delete an emoji from the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="emoji-name",
            description="emoji name",
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
    emoji_name = extract_emoji_name_from_syntax(kwargs["emoji-name"])

    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return
    if await check_user_reached_limit(ctx):
        return

    if not await check_emoji_is_modifiable(emoji_name, ctx):
        return

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
    save_poll_to_memory(
        poll_channel.guild_id, poll_channel.id, poll_id, ctx.user.id, "deleteemoji"
    )


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
    sticker_name = kwargs["sticker-name"]

    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return
    if await check_user_reached_limit(ctx):
        return

    if not await check_emoji_is_modifiable(sticker_name, ctx):
        return

    # check if sticker exists and get sticker object if it does
    guild = await ctx.get_guild()
    existing_stickers = guild.stickers
    sticker = get_existing_emoji_by_name(sticker_name, existing_stickers)
    if sticker is None:
        await ctx.send("Sticker does not exist on this server", ephemeral=True)
        return

    poll_id = await create_poll_message(
        ctx,
        f"POLL FOR DELETING STICKER: :{sticker_name}:",
        "Should we delete this sticker? (full size version below this poll)",
        f"https://cdn.discordapp.com/stickers/{sticker.id}.png",
        f"https://cdn.discordapp.com/stickers/{sticker.id}.png",
    )

    # save poll to active_polls directory
    poll_channel = await ctx.get_channel()
    save_poll_to_memory(
        poll_channel.guild_id, poll_channel.id, poll_id, ctx.user.id, "deletesticker"
    )


@bot.command(
    name="rename-emoji",
    description="Make a poll to rename an existing emoji on the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="emoji-name",
            description="CURRENT emoji name",
            focused=False,
            required=True,
        ),
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="new-emoji-name",
            description="NEW emoji name",
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
    current_name = extract_emoji_name_from_syntax(kwargs["emoji-name"])
    new_name = extract_emoji_name_from_syntax(kwargs["new-emoji-name"])

    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return
    if await check_user_reached_limit(ctx):
        return

    if not await check_emoji_is_modifiable(current_name, ctx):
        return

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
    save_poll_to_memory(
        poll_channel.guild_id, poll_channel.id, poll_id, ctx.user.id, "renameemoji"
    )


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

    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return
    if await check_user_reached_limit(ctx):
        return

    if not await check_emoji_is_modifiable(current_name, ctx):
        return

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
    save_poll_to_memory(
        channel.guild_id, channel.id, poll_id, ctx.user.id, "renamesticker"
    )


@bot.command(
    name="change-emoji",
    description="Make a poll to change the image of an existing emoji on the server",
    options=[
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="emoji-name",
            description="emoji name",
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
    emoji_name = extract_emoji_name_from_syntax(kwargs["emoji-name"])
    image_url = kwargs["image-url"]

    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return
    if await check_user_reached_limit(ctx):
        return

    if not await check_emoji_is_modifiable(emoji_name, ctx):
        return

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
    save_poll_to_memory(
        poll_channel.guild_id, poll_channel.id, poll_id, ctx.user.id, "changeemoji"
    )


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
    sticker_name = kwargs["sticker-name"]
    image_url = kwargs["image-url"]

    if not await check_channel_is_allowed(ctx.channel_id, ctx):
        return
    if await check_user_reached_limit(ctx):
        return

    if not await check_emoji_is_modifiable(sticker_name, ctx):
        return

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
        "Should we change this sticker to this image?",
        image_url,
        image_url,
    )
    save_poll_to_memory(
        ctx.guild_id, ctx.channel_id, poll_id, ctx.user.id, "changesticker"
    )


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


@bot.command(
    name="show-polls",
    description="Show currently active polls",
)
async def show_polls(ctx: interactions.CommandContext):
    """Show currently active polls

    Args:
        ctx (interactions.CommandContext): command context, inherited from decorator
    """
    polls = []
    guild = await ctx.get_guild()
    if os.path.exists(f"active_polls/{guild.id}"):
        for channel_id in os.listdir(f"active_polls/{guild.id}"):
            for poll in os.listdir(f"active_polls/{guild.id}/{channel_id}"):
                poll_id, poll_type = poll.split("_")
                # TODO: figure out how to print emoji name like in poll_results_check.post_update
                # Might need to finally migrate off interactions and make these commands properly
                polls.append(
                    "https://discord.com/channels/{}/{}/{} {}".format(
                        guild.id,
                        channel_id,
                        poll_id,
                        ctx.user.id,
                        pretty_poll_type(poll_type),
                    )
                )
    else:
        await ctx.send("No active polls", ephemeral=True)
    if len(polls) > 0:
        message = ""
        while len(message) < 2000 and len(polls) > 0:
            message += polls.pop(0) + "\n"
        await ctx.send(message, ephemeral=True)
    else:
        await ctx.send("No active polls", ephemeral=True)


@bot.command(
    name="show-limits",
    description="Show the current emoji and sticker limits for the server",
)
async def show_limits(ctx: interactions.CommandContext):
    """Show the current emoji and sticker limits for the server

    Args:
        ctx (interactions.CommandContext): command context, inherited from decorator
    """
    guild = await ctx.get_guild()
    premium_tier = guild.premium_tier
    emoji_count = len([e for e in guild.emojis if not e.animated])
    animated_emoji_count = len([e for e in guild.emojis if e.animated])
    sticker_count = len(guild.stickers)

    emoji_limit = emoji_limits[premium_tier]
    animated_emoji_limit = 50
    sticker_limit = sticker_limits[premium_tier]

    emoji_count_message = f"{emoji_limit - emoji_count} emoji slots left ({display_percent_str(emoji_count/emoji_limit)} used)"
    animated_emoji_count_message = f"{animated_emoji_limit - animated_emoji_count} animated emoji slots left ({display_percent_str(animated_emoji_count/animated_emoji_limit)} used)"
    sticker_count_message = f"{sticker_limit - sticker_count} sticker slots left ({display_percent_str(sticker_count/sticker_limit)} used)"

    await ctx.send(
        f"{emoji_count_message}\n{animated_emoji_count_message}\n{sticker_count_message}",
        ephemeral=True,
    )


bot.start()
