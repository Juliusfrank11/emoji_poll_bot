import interactions
import asyncio
from utils import *
from config import *

f = open(TOKEN_FILE_NAME, 'r')
token = f.read().strip()
f.close()

bot = interactions.Client(token)

@bot.command(
    name="add-emoji",
    description="check if a user is a zionist",
    options= [
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="url",
            description="URL of image to be made into an emoji",
            focused=False,
            required=True
        ),
        interactions.Option(
            type=interactions.OptionType.STRING,
            name="name",
            description="name of emoji",
            focused=False,
            required=True
        )
    ]
)
async def add_emoji(ctx: interactions.CommandContext, **kwargs):
    """Create a poll to add an emoji to the server
    

    Args:
        ctx (interactions.CommandContext): context of the command, inherited from decorator
        url (str): URL of image to be made into an emoji
        name (str): name of the emoji
    """
    emoji_name = kwargs['name']
    emoji_url = kwargs['url']
    
    if not validate_emoji_name(emoji_name):
        await ctx.respond("Invalid emoji name")
    
    embed = interactions.Embed(title=f"POLL FOR NEW EMOJI: :{emoji_name}:", 
                               description="Should we add this emoji? (full size version below this poll)")
    poll = await ctx.send(embeds=embed) # message object
    await ctx.send(emoji_url)
    await poll.create_reaction(POLL_YES_EMOJI)
    await poll.create_reaction(POLL_NO_EMOJI)
    print(poll.reactions)
    



bot.start()
