from disnake import (
    ButtonStyle,
    MessageInteraction,
)
from disnake.ext.commands import Cog
from disnake.ui import Button, View

from bot import OmniGames


class Events(Cog, name="events.on_button_click"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    @Cog.listener()
    async def on_button_click(self, interaction: MessageInteraction):
        await self.bot.wait_until_ready()

        if (
            "games" in self.bot.configs[interaction.guild.id]
            and self.bot.configs[interaction.guild.id]["games"]
            and str(interaction.channel.id)
            in self.bot.configs[interaction.guild.id]["games"]
        ):
            pass


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
