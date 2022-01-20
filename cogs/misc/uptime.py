from datetime import datetime

from disnake import ApplicationCommandInteraction
from disnake.ext.commands import (
    Cog,
    slash_command,
)

from bot import OmniGames


class Miscellaneous(Cog, name="misc.uptime"):
    def __init__(self, bot: OmniGames):
        self.bot = bot
        self.start_time = datetime.now()

    @slash_command(
        name="uptime",
        description="Shows how long the bot has been connected!",
    )
    async def uptime_slash_command(self, inter: ApplicationCommandInteraction):
        """
        This slash command shows how long the bot has been connected!

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        """
        await inter.response.send_message(
            f"ℹ️ - I have been connected since: `{self.bot.utils_class.duration((datetime.now() - self.start_time).total_seconds())}`"
        )


def setup(bot: OmniGames):
    bot.add_cog(Miscellaneous(bot))
