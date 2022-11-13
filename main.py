import interactions

f = open('.TOKEN', 'r')
token = f.read().strip()
f.close()

bot = interactions.Client(token)

@bot.command(
    name="poll_to_add_emoji",
    description="check if a user is a zionist",
    options= [
        interactions.Option(
            option_type=interactions.OptionType.STRING,
            name="URL",
            description="URL of image to be made into an emoji",
            focused=False,
            required=True
        ),
        interactions.Option(
            option_type=interactions.OptionType.STRING,
            name="name",
            description="name of emoji",
            focused=False,
            required=True
        )
    ]
)
async def my_first_command(ctx: interactions.CommandContext):
    embed = interactions.Embed(title="POLL FOR NEW EMOJI: :{emoji_name}:".format(ctx.options["name"]), 
                               description="Should we add this emoji? (full size version below this poll)")
    await ctx.send(embed=embed)
    await ctx.send(ctx.options["URL"])
    



bot.start()
