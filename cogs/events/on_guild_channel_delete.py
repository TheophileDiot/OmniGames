from typing import Union
from disnake import StageChannel
from disnake.abc import GuildChannel
from disnake.ext.commands import Cog
from disnake.errors import Forbidden, NotFound as disnake_NotFound
from google.api_core.exceptions import NotFound as google_NotFound

from bot import OmniGames
from data import Utils


class Events(Cog, name="events.on_guild_channel_delete"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    def delete_game_channel(self, channel: Union[GuildChannel, str]):
        del self.bot.configs[channel.guild.id]["games"][
            str(channel.id) if isinstance(channel, GuildChannel) else channel
        ]
        self.bot.games_repo.remove_game(
            channel.guild.id,
            channel.id if isinstance(channel, GuildChannel) else channel,
        )

        if isinstance(channel, GuildChannel) and channel.name.startswith("monopoly-"):
            try:
                self.bot.games_repo.delete_monopoly_game(channel.id)
            except google_NotFound:
                pass

    @Cog.listener()
    @Utils.check_bot_starting()
    async def on_guild_channel_delete(self, channel: GuildChannel):
        if isinstance(channel, StageChannel):
            return

        if (
            "games_category" in self.bot.configs[channel.guild.id]
            and "games" in self.bot.configs[channel.guild.id]
            and self.bot.configs[channel.guild.id]["games_category"] == channel
        ):
            games = dict(self.bot.configs[channel.guild.id]["games"])
            for channel_id in games:
                try:
                    _channel: GuildChannel = channel.guild.get_channel(
                        channel_id
                    ) or await channel.guild.fetch_channel(channel_id)

                    try:
                        await _channel.delete()
                    except Forbidden:
                        pass
                except disnake_NotFound:
                    _channel: str = channel_id

                self.delete_game_channel(_channel)

            del self.bot.configs[channel.guild.id]["games_category"]
            self.bot.config_repo.set_games_category(channel.guild.id, None)
        elif (
            "games_category" in self.bot.configs[channel.guild.id]
            and self.bot.configs[channel.guild.id]["games_category"] == channel.category
            and "games" in self.bot.configs[channel.guild.id]
            and str(channel.id) in self.bot.configs[channel.guild.id]["games"]
        ):
            self.delete_game_channel(channel)


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
