from time import monotonic

from disnake import ApplicationCommandInteraction
from disnake.ext.commands import (
    Cog,
    slash_command,
)

from bot import OmniGames


class Miscellaneous(Cog, name="misc.ping"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    """ COMMANDS """

    @slash_command(name="ping", description="Checks the bot latency!")
    async def ping_slash_command(self, inter: ApplicationCommandInteraction):
        """
        This slash command checks bot latency!

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        """
        before = monotonic()

        await inter.response.send_message("ℹ️ - Pong!")
        await inter.edit_original_message(
            content=f"ℹ️ - Pong!  `{int((monotonic() - before) * 1000)}ms`"
        )


def setup(bot: OmniGames):
    bot.add_cog(Miscellaneous(bot))
