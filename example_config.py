# DO NOT PLACE ANY SENSITIVE INFORMATION, LIKE TOKENS OR PASSWORDS, IN THE CONFIG FILE
# ITS FULL CONTENTS CAN BE DISPLAYED BY ANYONE ON THE SERVER WITH THE `/show-config` COMMAND
# % of the people who voted must have voted yes
POLL_PASS_THRESHOLD = 2 / 3
# Time before poll is closed, in seconds
POLL_DURATION = 24 * 60 * 60
# emoji to use for the poll's "yes" option
POLL_YES_EMOJI = "✅"
# emoji to use for the poll's "no" option
POLL_NO_EMOJI = "❌"
# file containing the bot's token
TOKEN_FILE_NAME = ".TOKEN"
# Time between checks for poll results, in seconds
WAIT_TIME_BETWEEN_CHECKS = 10 * 60
# Max area of image in pixels, set by discord so be careful changing this
MAX_IMAGE_SIZE = 320**2
# Max file size of image, set by discord so be careful changing this)
MAX_IMAGE_FILE_SIZE = 256000
# Name of temporary image file for adding emojis and stickers
TEMP_IMAGE_FILE_NAME = "adding_image_temp"
# Whether to automatically add/delete emojis/stickers
AUTOMATICALLY_ADD_EMOJIS = True
# Minimum number of votes for a poll to be considered valid
MINIMUM_VOTES_FOR_POLL = 1
# User IDs of users that get have an additional weight to their votes, you can find these by using developer options in discord
PRIVILEGED_USER_IDS = [
    # 123456789012345678,   # Example user ID
]
# How much more weight a privileged user's vote has, multiplicative
PRIVILEGED_USER_VOTE_WEIGHT = 1
# Channel IDs of channels where the bot can be used
ALLOWED_CHANNEL_IDS = [
    # 123456789012345678,   # Example channel ID
]
# Emoji names that can not be modified by the bot
PROTECTED_EMOTE_NAMES = []
# Hours to post poll updates, in UTC
POLL_UPDATE_POST_TIMES = []
# How many polls can be active at once per user
ACTIVE_POLLS_PER_USER_LIMIT = 2


# Function to Determine how Nitro Booster Voting Weight scales with # months
# The end weight will be 1 + NITRO_USER_VOTING_WEIGHT_FUNCTION(months_boosting)
def NITRO_USER_VOTING_WEIGHT_FUNCTION(days_boosting):
    # no weight
    return 0
