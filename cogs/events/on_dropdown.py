from disnake import MessageInteraction
from disnake.ext.commands import Cog

from bot import OmniGames


class Events(Cog, name="events.on_dropdown"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    @Cog.listener()
    async def on_dropdown(self, interaction: MessageInteraction):
        return


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
