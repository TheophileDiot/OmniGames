from logging import info

from disnake import Activity, ActivityType
from disnake.ext.commands import Cog

from bot import OmniGames


class Events(Cog, name="events.on_ready"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        """Check on start if any guilds that the bot is in are not in the DB else initialise moderators list for every guild in the DB"""
        db_guilds = set([int(k) for k in self.bot.main_repo.get_guilds().keys()])
        guilds = set(self.bot.guilds)

        for guild in guilds:

            """GUILDS CHECK"""

            if guild.id not in db_guilds:
                self.bot.main_repo.create_guild(
                    guild.id, guild.name, f"{guild.owner}"
                )  # If guild is not in DB, create it

            db_guild = self.bot.main_repo.get_guild(guild.id)

            if guild.id in db_guilds and not db_guild["present"]:
                self.bot.main_repo.update_guild(guild.id, {"present": True})
            elif not db_guild["present"]:
                continue

            await self.bot.utils_class.init_guild(guild)

        print("OmniGames is ready.")
        info("OmniGames successfully started")

        await self.bot.change_presence(
            activity=Activity(type=ActivityType.listening, name=f"Slash commands")
        )

        self.bot.starting = False


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
