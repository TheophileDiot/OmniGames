from disnake import CategoryChannel, StageChannel
from disnake.abc import GuildChannel
from disnake.ext.commands import Cog

from bot import OmniGames
from data import Utils


class Events(Cog, name="events.on_guild_channel_delete"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    @Cog.listener()
    @Utils.check_bot_starting()
    async def on_guild_channel_delete(self, channel: GuildChannel):
        if isinstance(channel, StageChannel):
            return

        # TODO add a check for the games_category deletion

        if (
            "games_category" in self.bot.configs[channel.guild.id]
            and self.bot.configs[channel.guild.id]["games_category"] == channel.category
            and "games" in self.bot.configs[channel.guild.id]
            and str(channel.id) in self.bot.configs[channel.guild.id]["games"]
        ):
            del self.bot.configs[channel.guild.id]["games"][str(channel.id)]
            self.bot.games_repo.remove_game(channel.guild.id, channel.id)


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
