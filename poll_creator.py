import interactions
from utils import *
from config import *
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
        await ctx.delete()
        return

    if not validate_image_url(emoji_url):
        await ctx.send(
            "Invalid image URL, url must end in png, jpg, jpeg, gif, or webp"
        )
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
    try:
        os.mkdir(f"active_polls/{poll_channel.guild_id}")
    except FileExistsError:
        pass
    finally:
        try:
            os.mkdir(f"active_polls/{poll_channel.guild_id}/{poll_channel.id}")
        except FileExistsError:
            pass
    f = open(
        f"active_polls/{poll_channel.guild_id}/{poll_channel.id}/{poll.id}_addemoji",
        "w",
    )
    f.close()


bot.start()
