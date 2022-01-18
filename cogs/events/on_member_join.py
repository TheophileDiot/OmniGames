from disnake import Member
from disnake.ext.commands import Cog

from bot import OmniGames
from data import Utils


class Events(Cog, name="events.on_member_join"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    @Cog.listener()
    @Utils.check_bot_starting()
    async def on_member_join(self, member: Member):
        """When a member joins a guild, add him to the database and if the mute_on_join option is on then mute him for a limited amount of time"""
        await self.bot.wait_until_ready()

        if member.bot:
            return

        self.bot.user_repo.update_user(member.guild.id, member.id, f"{member}")


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
